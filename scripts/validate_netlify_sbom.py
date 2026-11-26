#!/usr/bin/env python3
"""Check npm-generated CycloneDX against a reviewed lockfile; no network."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

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

def inspect(lock, bom):
    if lock.get("lockfileVersion") != 3 or bom.get("bomFormat") != "CycloneDX" or bom.get("specVersion") not in ("1.5", "1.6", "1.7"):
        raise ValueError("Unexpected inventory format")
    packages = lock["packages"]
    root = packages[""]
    metadata = bom["metadata"]["component"]
    if metadata["name"] != root["name"] or metadata["version"] != root["version"]:
        raise ValueError("Root identity mismatch")
    components = bom["components"]
    if not isinstance(components, list) or not components:
        raise ValueError("Empty inventory")
    seen = set()
    refs = {metadata["bom-ref"]}
    for component in components:
        paths = [prop["value"] for prop in component["properties"] if prop["name"] == "cdx:npm:package:path"]
        if len(paths) != 1:
            raise ValueError("Missing or ambiguous component path")
        path = paths[0]
        if not isinstance(path, str) or not path or path not in packages or path in seen:
            raise ValueError("Unknown or duplicate component path")
        expected = packages[path]
        expected_name = expected.get("name", path.rsplit("node_modules/", 1)[-1])
        name = component["name"]
        group = component.get("group")
        if group and not name.startswith("@"):
            name = group + "/" + name
        if name != expected_name or component["version"] != expected["version"]:
            raise ValueError("Component identity mismatch")
        sri = expected["integrity"]
        if not sri.startswith("sha512-"):
            raise ValueError("Unexpected lock integrity algorithm")
        expected_hash = base64.b64decode(sri[7:], validate=True)
        hashes = [h["content"] for h in component["hashes"] if h["alg"] == "SHA-512"]
        if len(expected_hash) != 64 or len(hashes) != 1 or hashes[0].lower() != expected_hash.hex():
            raise ValueError("Component integrity mismatch")
        ref = component["bom-ref"]
        if not isinstance(ref, str) or not ref or ref in refs:
            raise ValueError("Duplicate or invalid component reference")
        refs.add(ref)
        seen.add(path)
    missing = sorted(set(packages) - {""} - seen)
    # npm may exclude platform-specific optional packages. Never hide the gap.
    if any(packages[path].get("optional") is not True for path in missing):
        raise ValueError("Required locked component missing")
    if any("node_modules/" + name not in seen for name in root.get("dependencies", {})):
        raise ValueError("Direct dependency missing")
    graph_refs = set()
    for edge in bom["dependencies"]:
        ref = edge["ref"]
        targets = edge["dependsOn"]
        if ref not in refs or ref in graph_refs or not isinstance(targets, list) or any(x not in refs for x in targets):
            raise ValueError("Invalid dependency graph reference")
        graph_refs.add(ref)
    if metadata["bom-ref"] not in graph_refs:
        raise ValueError("Root dependency graph missing")
    return {"locked_entries": len(packages) - 1, "covered_entries": len(seen),
            "missing_optional_entries": missing,
            "complete_lock_coverage": not missing}

class Tests(unittest.TestCase):
    def test_contract(self):
        binary = bytes(64)
        sri = "sha512-" + base64.b64encode(binary).decode()
        lock = {"lockfileVersion": 3, "packages": {
            "": {"name": "fixture", "version": "1.0.0", "dependencies": {"sample": "1.0.0"}},
            "node_modules/sample": {"version": "1.0.0", "integrity": sri},
            "node_modules/optional": {"version": "1.0.0", "integrity": sri, "optional": True}}}
        comp = {"name": "sample", "version": "1.0.0", "bom-ref": "sample",
                "properties": [{"name": "cdx:npm:package:path", "value": "node_modules/sample"}],
                "hashes": [{"alg": "SHA-512", "content": binary.hex()}]}
        bom = {"bomFormat": "CycloneDX", "specVersion": "1.5",
               "metadata": {"component": {"name": "fixture", "version": "1.0.0", "bom-ref": "root"}},
               "components": [comp], "dependencies": [{"ref": "root", "dependsOn": ["sample"]}, {"ref": "sample", "dependsOn": []}]}
        self.assertEqual(inspect(lock, bom)["missing_optional_entries"], ["node_modules/optional"])
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--sbom", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--npm-version")
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if not all((args.lock, args.sbom, args.receipt, args.source_sha, args.npm_version)):
        parser.error("lock, SBOM, receipt, source SHA and npm version required")
    if not SHA.fullmatch(args.source_sha) or not re.fullmatch(r"\d+\.\d+\.\d+", args.npm_version):
        parser.error("Invalid source SHA or npm version")
    try:
        lock_bytes = args.lock.read_bytes()
        bom_bytes = args.sbom.read_bytes()
        coverage = inspect(strict_json(lock_bytes), strict_json(bom_bytes))
        receipt = {"scope": "tools/netlify-cli/package-lock.json", "source_sha": args.source_sha,
                   "npm_version": args.npm_version, "lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
                   "sbom_sha256": hashlib.sha256(bom_bytes).hexdigest(), **coverage}
        with args.receipt.open("x", encoding="utf-8") as out:
            json.dump(receipt, out, indent=2, sort_keys=True)
            out.write("\n")
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        print("FAIL: SBOM contract rejected (" + type(exc).__name__ + ")")
        return 1
    print("PASS: lock entries", coverage["locked_entries"], "covered", coverage["covered_entries"],
          "optional missing", len(coverage["missing_optional_entries"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
