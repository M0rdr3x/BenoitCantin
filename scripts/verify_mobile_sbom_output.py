#!/usr/bin/env python3
"""Independent final-output gate for the reviewed mobile CycloneDX inventory."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import unittest
from validate_mobile_lock_candidate import load
from validate_mobile_locked_dependencies import verified_bytes, MANIFEST_SHA, LOCK_SHA

SBOM_SHA = "ccd9f7c264d0c44c22f3700f5707abc01e3767b4846daec825b629069c2f46ab"
HEX = re.compile(r"[0-9a-f]{64}")
SHA = re.compile(r"[0-9a-f]{40}")
REF = re.compile(r"npm-path:[0-9a-f]{64}")
LIMIT = 2 * 1024 * 1024
RECEIPT_FIELDS = {
    "scope", "source_sha", "manifest_sha256", "npm_version", "lock_sha256",
    "npm_raw_sbom_sha256", "sbom_sha256", "locked_entries", "covered_entries",
    "missing_optional_entries", "complete_lock_coverage", "duplicate_npm_reference_groups",
    "resolved_edges", "unresolved_optional_edges",
}

def digest(payload):
    return hashlib.sha256(payload).hexdigest()

def read_regular(path, limit=LIMIT):
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or not 0 < st.st_size <= limit:
        raise ValueError("Invalid report file")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) != st.st_size:
        raise ValueError("Report size mismatch")
    return data

def graph_counts(bom):
    if bom.get("bomFormat") != "CycloneDX" or bom.get("specVersion") != "1.5" or bom.get("version") != 1:
        raise ValueError("Unexpected report format")
    root = bom["metadata"]["component"]["bom-ref"]
    refs = [root, *(x["bom-ref"] for x in bom["components"])]
    if any(not isinstance(ref,str) or not REF.fullmatch(ref) for ref in refs) or len(set(refs)) != len(refs):
        raise ValueError("Duplicate or invalid component identity")
    known = set(refs)
    graph = {}
    for edge in bom["dependencies"]:
        ref, targets = edge["ref"], edge["dependsOn"]
        if ref in graph or ref not in known or not isinstance(targets,list) or len(set(targets)) != len(targets) or not set(targets) <= known:
            raise ValueError("Invalid dependency graph")
        graph[ref] = targets
    if set(graph) != known:
        raise ValueError("Missing graph node")
    seen, pending = set(), [root]
    while pending:
        ref = pending.pop()
        if ref not in seen:
            seen.add(ref)
            pending.extend(graph[ref])
    if seen != known:
        raise ValueError("Unreachable dependency")
    return len(refs)-1, sum(map(len,graph.values()))

def verify_report(manifest, lock, sbom, receipt, raw, source_sha):
    verified_bytes(manifest, lock)
    if not SHA.fullmatch(source_sha) or digest(sbom) != SBOM_SHA:
        raise ValueError("Unreviewed final SBOM")
    report, proof = load(sbom), load(receipt)
    if set(proof) != RECEIPT_FIELDS or proof["scope"] != "mobile-native/package-lock.json" or proof["source_sha"] != source_sha:
        raise ValueError("Receipt identity mismatch")
    expected = {
        "manifest_sha256": MANIFEST_SHA, "lock_sha256": LOCK_SHA, "sbom_sha256": SBOM_SHA,
        "npm_raw_sbom_sha256": digest(raw), "npm_version": "10.9.8",
        "locked_entries": 498, "covered_entries": 498, "resolved_edges": 1036,
        "duplicate_npm_reference_groups": 20, "missing_optional_entries": [],
    }
    if any(proof[k] != v for k,v in expected.items()) or proof["complete_lock_coverage"] is not True:
        raise ValueError("Receipt content mismatch")
    missing = proof["unresolved_optional_edges"]
    if not isinstance(missing,list) or len(missing) != 20 or any(not isinstance(x,dict) or set(x)!={"path","dependency"} for x in missing):
        raise ValueError("Optional edge accounting mismatch")
    # Validate the exact absent declarations against the reviewed lock, not just a count.
    packages = load(lock)["packages"]
    pairs = set()
    for edge in missing:
        path, name = edge["path"], edge["dependency"]
        entry = packages[path]
        if (path,name) in pairs or not (name in entry.get("optionalDependencies",{}) or
                (name in entry.get("peerDependencies",{}) and entry.get("peerDependenciesMeta",{}).get(name,{}).get("optional") is True)):
            raise ValueError("Unexpected optional declaration")
        pairs.add((path,name))
    if graph_counts(report) != (498,1036):
        raise ValueError("Final graph accounting mismatch")
    return proof

class Tests(unittest.TestCase):
    def test_graph_mutations(self):
        import copy
        a,b,c = ["npm-path:"+x*64 for x in "abc"]
        good={"bomFormat":"CycloneDX","specVersion":"1.5","version":1,
              "metadata":{"component":{"bom-ref":a}},
              "components":[{"bom-ref":b},{"bom-ref":c}],
              "dependencies":[{"ref":a,"dependsOn":[b]},{"ref":b,"dependsOn":[c]},{"ref":c,"dependsOn":[]}]}
        self.assertEqual(graph_counts(good),(2,2))
        for mode in ("duplicate", "dangling", "orphan", "missing", "duplicate-edge", "duplicate-target"):
            mutant=copy.deepcopy(good)
            if mode=="duplicate": mutant["components"].append({"bom-ref":b})
            elif mode=="dangling": mutant["dependencies"][0]["dependsOn"]=["npm-path:"+"d"*64]
            elif mode=="orphan": mutant["dependencies"][1]["dependsOn"]=[]
            elif mode=="missing": mutant["dependencies"].pop()
            elif mode=="duplicate-edge": mutant["dependencies"].append({"ref":a,"dependsOn":[b]})
            else: mutant["dependencies"][0]["dependsOn"]=[b,b]
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                graph_counts(mutant)
    def test_file_boundary(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"file"
            path.write_bytes(b"test")
            self.assertEqual(read_regular(path,4),b"test")
            with self.assertRaises(ValueError): read_regular(path,3)
            alias=Path(temp)/"alias"
            alias.symlink_to(path)
            with self.assertRaises(ValueError): read_regular(alias)
            path.write_bytes(b"")
            with self.assertRaises(ValueError): read_regular(path)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    for arg in ("manifest","lock","sbom","receipt","raw"):
        p.add_argument("--"+arg,type=Path)
    p.add_argument("--source-sha")
    args=p.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if not all((args.manifest,args.lock,args.sbom,args.receipt,args.raw,args.source_sha)):
        p.error("All report inputs required")
    try:
        verify_report(*(read_regular(path) for path in (args.manifest,args.lock,args.sbom,args.receipt,args.raw)),args.source_sha)
        print("PASS: exact reviewed SBOM, receipt, source digest and 499 reachable graph nodes verified.")
    except (ValueError,KeyError,TypeError,AttributeError,OSError) as exc:
        print("FAIL: final mobile inventory rejected ("+type(exc).__name__+")")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
