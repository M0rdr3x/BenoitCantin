#!/usr/bin/env python3
"""Validate and normalize the mobile npm SBOM against its reviewed lockfile."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest
from collections import Counter
from urllib.parse import quote
from validate_mobile_locked_dependencies import verified_bytes, EXPECTED

MAX_JSON = 32 * 1024 * 1024
SHA = re.compile(r"[0-9a-f]{40}")
def strict_json(data):
    if len(data) > MAX_JSON:
        raise ValueError("Oversized inventory")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def reject(_):
        raise ValueError("Non-finite JSON value")
    return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=reject)

def package_name(path, entry):
    return entry.get("name", path.rsplit("node_modules/", 1)[-1])

def ref_for(path):
    return "npm-path:" + hashlib.sha256(path.encode("utf-8")).hexdigest()

def parent_package(path):
    return path.rsplit("/node_modules/", 1)[0] if "/node_modules/" in path else ""

def resolve_target(packages, path, name, peer):
    # npm packages resolve from their nearest node_modules ancestor;
    # peer dependencies resolve from the parent, not inside the package.
    if not re.fullmatch(r"(?:@[a-zA-Z0-9._~-]+/)?[a-zA-Z0-9._~-]+", name) or name in (".", ".."):
        raise ValueError("Invalid dependency name")
    cursor = parent_package(path) if peer and path else path
    while True:
        candidate = (cursor + "/" if cursor else "") + "node_modules/" + name
        if candidate in packages:
            return candidate
        if not cursor:
            return None
        cursor = parent_package(cursor)

def inspect(lock, bom):
    if lock.get("lockfileVersion") != 3 or bom.get("bomFormat") != "CycloneDX" or bom.get("specVersion") != "1.5":
        raise ValueError("Unexpected inventory format")
    packages = lock["packages"]
    root = packages[""]
    metadata = bom["metadata"]["component"]
    if metadata["name"] != root["name"] or metadata["version"] != root["version"]:
        raise ValueError("Root identity mismatch")
    root_paths = [prop["value"] for prop in metadata["properties"] if prop["name"] == "cdx:npm:package:path"]
    if root_paths != [""]:
        raise ValueError("Root path mismatch")
    if metadata.get("purl") != "pkg:npm/" + quote(root["name"], safe="/") + "@" + quote(root["version"], safe=""):
        raise ValueError("Root package URL mismatch")
    root_raw_ref = root["name"] + "@" + root["version"]
    if metadata["bom-ref"] != root_raw_ref:
        raise ValueError("Root reference mismatch")
    components = bom["components"]
    if not isinstance(components, list) or not components:
        raise ValueError("Empty inventory")
    seen = set()
    raw_refs = Counter({root_raw_ref: 1})
    normalized = {}
    for component in components:
        paths = [prop["value"] for prop in component["properties"] if prop["name"] == "cdx:npm:package:path"]
        if len(paths) != 1:
            raise ValueError("Missing or ambiguous component path")
        path = paths[0]
        if not isinstance(path, str) or not path or path not in packages or path in seen:
            raise ValueError("Unknown or duplicate component path")
        expected = packages[path]
        name = package_name(path, expected)
        if component["name"] != name or component["version"] != expected["version"]:
            raise ValueError("Component identity mismatch")
        sri = expected["integrity"]
        if not sri.startswith("sha512-"):
            raise ValueError("Unexpected lock integrity algorithm")
        expected_hash = base64.b64decode(sri[7:], validate=True)
        hashes = [h["content"] for h in component["hashes"] if h["alg"] == "SHA-512"]
        if len(expected_hash) != 64 or len(hashes) != 1 or hashes[0].lower() != expected_hash.hex():
            raise ValueError("Component integrity mismatch")
        raw_ref = name + "@" + expected["version"]
        if component["bom-ref"] != raw_ref:
            raise ValueError("Unexpected npm component reference")
        raw_refs[raw_ref] += 1
        # Do not reuse ambiguous npm name@version references or graph edges.
        normalized[path] = {
            "type": "library", "bom-ref": ref_for(path), "name": name,
            "version": expected["version"],
            "purl": "pkg:npm/" + quote(name, safe="/") + "@" + quote(expected["version"], safe=""),
            "scope": "optional" if expected.get("optional") is True else "required",
            "hashes": [{"alg": "SHA-512", "content": expected_hash.hex()}],
            "properties": [{"name": "cdx:npm:package:path", "value": path}],
            "externalReferences": [{"type": "distribution", "url": expected["resolved"]}],
        }
        seen.add(path)
    missing = sorted(set(packages) - {""} - seen)
    if any(packages[path].get("optional") is not True for path in missing):
        raise ValueError("Required locked component missing")
    direct = set().union(*(root.get(field, {}) for field in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")))
    if any("node_modules/" + name not in seen for name in direct):
        raise ValueError("Direct dependency missing")
    graph_refs = Counter()
    for edge in bom["dependencies"]:
        ref = edge["ref"]
        targets = edge["dependsOn"]
        if ref not in raw_refs or not isinstance(targets, list) or any(x not in raw_refs for x in targets):
            raise ValueError("Invalid npm dependency graph reference")
        graph_refs[ref] += 1
    if graph_refs != raw_refs:
        raise ValueError("Incomplete npm graph inventory")
    # The npm graph cannot distinguish repeated names/versions. Rebuild the
    # graph by lockfile installation paths instead of guessing which edge
    # belongs to which component.
    graph = []
    optional_missing = []
    included = seen | {""}
    for path in sorted(included):
        entry = packages[path]
        deps = dict(entry.get("dependencies", {}))
        if not path:
            deps.update(entry.get("devDependencies", {}))
        optional = entry.get("optionalDependencies", {})
        peers = entry.get("peerDependencies", {})
        peer_meta = entry.get("peerDependenciesMeta", {})
        targets = set()
        for name in sorted(set(deps) | set(optional) | set(peers)):
            peer = name in peers and name not in deps and name not in optional
            target = resolve_target(packages, path, name, peer)
            if target not in included:
                if name in optional or (peer and peer_meta.get(name, {}).get("optional") is True):
                    optional_missing.append({"path": path, "dependency": name})
                    continue
                raise ValueError("Required dependency edge unresolved")
            targets.add(ref_for(target))
        graph.append({"ref": ref_for(path), "dependsOn": sorted(targets)})
    canonical = {
        "bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
        "metadata": {"component": {"type": "application", "name": root["name"],
                                    "version": root["version"], "bom-ref": ref_for("")},
                     "properties": [{"name": "sinjira:inventory:source", "value": "npm-lockfile-path-graph"}]},
        "components": [normalized[path] for path in sorted(normalized)],
        "dependencies": graph,
    }
    coverage = {"locked_entries": len(packages) - 1, "covered_entries": len(seen),
                "missing_optional_entries": missing,
                "complete_lock_coverage": not missing,
                "duplicate_npm_reference_groups": sum(n > 1 for n in raw_refs.values()),
                "resolved_edges": sum(len(edge["dependsOn"]) for edge in graph),
                "unresolved_optional_edges": optional_missing}
    return coverage, canonical

def require_complete(coverage):
    if (coverage["locked_entries"] != EXPECTED["locked_entries"] or coverage["covered_entries"] != EXPECTED["locked_entries"]
            or coverage["missing_optional_entries"] or coverage["complete_lock_coverage"] is not True):
        raise ValueError("Complete mobile lock coverage required")

class Tests(unittest.TestCase):
    def test_contract(self):
        binary = bytes(64)
        sri = "sha512-" + base64.b64encode(binary).decode()
        lock = {"lockfileVersion": 3, "packages": {
            "": {"name": "fixture", "version": "1.0.0", "dependencies": {"sample": "1.0.0"}},
            "node_modules/sample": {"version": "1.0.0", "integrity": sri, "resolved": "https://registry.npmjs.org/sample/-/sample-1.0.0.tgz"},
            "node_modules/optional": {"version": "1.0.0", "integrity": sri, "optional": True, "resolved": "https://registry.npmjs.org/optional/-/optional-1.0.0.tgz"}}}
        comp = {"name": "sample", "version": "1.0.0", "bom-ref": "sample@1.0.0",
                "properties": [{"name": "cdx:npm:package:path", "value": "node_modules/sample"}],
                "hashes": [{"alg": "SHA-512", "content": binary.hex()}]}
        bom = {"bomFormat": "CycloneDX", "specVersion": "1.5",
               "metadata": {"component": {"name": "fixture", "version": "1.0.0", "bom-ref": "fixture@1.0.0",
                                          "purl": "pkg:npm/fixture@1.0.0",
                                          "properties": [{"name": "cdx:npm:package:path", "value": ""}]}},
               "components": [comp], "dependencies": [{"ref": "fixture@1.0.0", "dependsOn": ["sample@1.0.0"]}, {"ref": "sample@1.0.0", "dependsOn": []}]}
        coverage, canonical = inspect(lock, bom)
        self.assertEqual(coverage["missing_optional_entries"], ["node_modules/optional"])
        with self.assertRaises(ValueError):
            require_complete(coverage)
        dev_lock = copy.deepcopy(lock)
        dev_lock["packages"][""]["devDependencies"] = {"optional": "1.0.0"}
        with self.assertRaises(ValueError):
            inspect(dev_lock, bom)
        dev_bom = copy.deepcopy(bom)
        dev_comp = copy.deepcopy(comp)
        dev_comp.update(name="optional", **{"bom-ref":"optional@1.0.0"})
        dev_comp["properties"][0]["value"] = "node_modules/optional"
        dev_bom["components"].append(dev_comp)
        dev_bom["dependencies"].append({"ref":"optional@1.0.0","dependsOn":[]})
        _, dev_normalized = inspect(dev_lock, dev_bom)
        root_graph = next(edge for edge in dev_normalized["dependencies"] if edge["ref"] == ref_for(""))
        self.assertIn(ref_for("node_modules/optional"), root_graph["dependsOn"])
        self.assertEqual(canonical["components"][0]["bom-ref"], ref_for("node_modules/sample"))
        for field, value in (
            ("name", "tmp.random"),
            ("version", "2.0.0"),
            ("purl", "pkg:npm/other@1.0.0"),
            ("bom-ref", "other@1.0.0"),
            ("properties", []),
            ("properties", [{"name": "cdx:npm:package:path", "value": "node_modules/fixture"}]),
            ("properties", [{"name": "cdx:npm:package:path", "value": ""}] * 2),
        ):
            changed = copy.deepcopy(bom)
            changed["metadata"]["component"][field] = value
            with self.subTest(root_field=field, value=value), self.assertRaises(ValueError):
                inspect(lock, changed)
        # npm emits identical raw refs for separate installations.
        repeated_lock = copy.deepcopy(lock)
        repeated_bom = copy.deepcopy(bom)
        nested = "node_modules/sample/node_modules/sample"
        repeated_lock["packages"][nested] = copy.deepcopy(lock["packages"]["node_modules/sample"])
        repeated = copy.deepcopy(comp)
        repeated["properties"][0]["value"] = nested
        repeated_bom["components"].append(repeated)
        repeated_bom["dependencies"].append({"ref": "sample@1.0.0", "dependsOn": []})
        count, result = inspect(repeated_lock, repeated_bom)
        self.assertEqual(count["duplicate_npm_reference_groups"], 1)
        self.assertEqual(len({item["bom-ref"] for item in result["components"]}), 2)
        self.assertEqual(resolve_target(repeated_lock["packages"], "node_modules/sample", "sample", False), nested)
        self.assertEqual(resolve_target(repeated_lock["packages"], "node_modules/sample", "sample", True), "node_modules/sample")
        repeated_bom["dependencies"].pop()
        with self.assertRaises(ValueError):
            inspect(repeated_lock, repeated_bom)
        for field, value in (("name", "other"), ("version", "2.0.0"), ("hashes", []),
                             ("properties", []), ("bom-ref", "root")):
            changed = copy.deepcopy(bom)
            changed["components"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                inspect(lock, changed)
        for mode in ("unknown", "duplicate", "missing", "dangling"):
            changed = copy.deepcopy(bom)
            if mode == "unknown":
                changed["components"][0]["properties"][0]["value"] = "node_modules/other"
            elif mode == "duplicate":
                changed["components"].append(copy.deepcopy(comp))
            elif mode == "missing":
                changed["components"] = []
            else:
                changed["dependencies"][0]["dependsOn"] = ["other"]
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                inspect(lock, changed)
        changed_lock = copy.deepcopy(lock)
        changed_lock["packages"]["node_modules/optional"]["optional"] = False
        with self.assertRaises(ValueError):
            inspect(changed_lock, bom)
        for invalid in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}'):
            with self.assertRaises(ValueError):
                strict_json(invalid)

SAFE_REASONS = frozenset(["Complete mobile lock coverage required","Invalid inventory input","Reviewed dependency snapshot changed","Unexpected reviewed inventory","Vulnerable or unexpected minimatch resolution","Unexpected fingerprint version","Oversized inventory","Duplicate JSON key","Non-finite JSON value","Invalid dependency name","Unexpected inventory format","Root identity mismatch","Root path mismatch","Root package URL mismatch","Root reference mismatch","Empty inventory","Missing or ambiguous component path","Unknown or duplicate component path","Component identity mismatch","Unexpected lock integrity algorithm","Component integrity mismatch","Unexpected npm component reference","Required locked component missing","Direct dependency missing","Invalid npm dependency graph reference","Incomplete npm graph inventory","Required dependency edge unresolved","Unexpected npm generator identity"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--sbom", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--normalized", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--npm-version")
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if not all((args.manifest, args.lock, args.sbom, args.receipt, args.normalized, args.source_sha, args.npm_version)):
        parser.error("manifest, lock, SBOM, receipt, source SHA and npm version required")
    if not SHA.fullmatch(args.source_sha) or not re.fullmatch(r"\d+\.\d+\.\d+", args.npm_version):
        parser.error("Invalid source SHA or npm version")
    try:
        for path in (args.manifest, args.lock, args.sbom):
            if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= MAX_JSON:
                raise ValueError("Invalid inventory input")
        manifest_bytes = args.manifest.read_bytes()
        lock_bytes = args.lock.read_bytes()
        verified_bytes(manifest_bytes, lock_bytes)
        bom_bytes = args.sbom.read_bytes()
        lock = strict_json(lock_bytes)
        raw = strict_json(bom_bytes)
        tools = raw["metadata"]["tools"]
        if tools != [{"vendor": "npm", "name": "cli", "version": args.npm_version}]:
            raise ValueError("Unexpected npm generator identity")
        coverage, canonical = inspect(lock, raw)
        require_complete(coverage)
        normalized_bytes = (json.dumps(canonical, indent=2, sort_keys=True) + "\n").encode("utf-8")
        with args.normalized.open("xb") as out:
            out.write(normalized_bytes)
        receipt = {"scope": "mobile-native/package-lock.json", "source_sha": args.source_sha,
                   "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                   "npm_version": args.npm_version, "lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
                   "npm_raw_sbom_sha256": hashlib.sha256(bom_bytes).hexdigest(),
                   "sbom_sha256": hashlib.sha256(normalized_bytes).hexdigest(), **coverage}
        with args.receipt.open("x", encoding="utf-8") as out:
            json.dump(receipt, out, indent=2, sort_keys=True)
            out.write("\n")
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        # All explicit ValueErrors above contain fixed diagnostic text only.
        reason = str(exc) if type(exc) is ValueError and str(exc) in SAFE_REASONS else type(exc).__name__
        print("FAIL: SBOM contract rejected (" + reason + ")")
        return 1
    print("PASS: lock entries", coverage["locked_entries"], "covered", coverage["covered_entries"],
          "optional missing", len(coverage["missing_optional_entries"]),
          "resolved graph edges", coverage["resolved_edges"],
          "unresolved optional edges", len(coverage["unresolved_optional_edges"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
