#!/usr/bin/env python3
"""Temporary scoped remediation experiment for GHSA-g3hv-75wg-m249."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import unittest
from validate_mobile_lock_candidate import inspect, load
from verify_mobile_lock_artifact import audit_summary, LOCK_SHA, MANIFEST_SHA

OVERRIDE = {"@expo/fingerprint@0.20.17": {"minimatch": "11.0.9"}}
def digest(data):
    return hashlib.sha256(data).hexdigest()

def prepare(manifest):
    if "overrides" in manifest:
        raise ValueError("Unexpected existing overrides")
    return {**manifest, "overrides": copy.deepcopy(OVERRIDE)}

def identities(lock):
    return {(p.rsplit("node_modules/", 1)[-1], e["version"], e["integrity"], e["resolved"])
            for p,e in lock["packages"].items() if p}

def validate(original, baseline, candidate, lock):
    if candidate != prepare(original):
        raise ValueError("Unexpected manifest change")
    coverage = inspect(candidate, lock)
    fingerprint = lock["packages"]["node_modules/@expo/fingerprint"]
    if fingerprint["version"] != "0.20.17":
        raise ValueError("Fingerprint version changed")
    before, after = identities(baseline), identities(lock)
    old = {x for x in before if x[0] == "minimatch" and x[1] == "10.2.6"}
    fixed = {x for x in before if x[0] == "minimatch" and x[1] == "11.0.9"}
    if len(old) != 1 or len(fixed) != 1 or after != before - old:
        raise ValueError("Unexpected package identity drift or unpatched minimatch")
    versions = {x[1] for x in after if x[0] == "minimatch"}
    if versions != {"11.0.9"}:
        raise ValueError("Unexpected minimatch versions")
    return coverage

def clean_audit(report, code):
    result = audit_summary(report, code)
    if result["counts"]["total"] != 0 or result["packages"]:
        raise ValueError("Known vulnerabilities remain in remediation candidate")
    return result["counts"]

class Tests(unittest.TestCase):
    def test_manifest_and_audit(self):
        from validate_mobile_lock_candidate import SEVERITIES
        root={"name":"sinjira-mobile-native"}
        self.assertEqual(prepare(root)["overrides"], OVERRIDE)
        self.assertNotIn("overrides", root)
        with self.assertRaises(ValueError):
            prepare({"overrides":{}})
        stats={k:0 for k in (*SEVERITIES,"total")}
        report={"auditReportVersion":2,"metadata":{"vulnerabilities":stats},"vulnerabilities":{}}
        self.assertEqual(clean_audit(report,0)["total"],0)
        with self.assertRaises(ValueError):
            clean_audit(report,1)
        stats.update(moderate=1,total=1)
        report["vulnerabilities"]["minimatch"]={"name":"minimatch","severity":"moderate","via":[]}
        with self.assertRaises(ValueError):
            clean_audit(report,1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--original",type=Path)
    p.add_argument("--baseline",type=Path)
    p.add_argument("--manifest",type=Path)
    p.add_argument("--lock",type=Path)
    p.add_argument("--prepare",action="store_true")
    p.add_argument("--audit",type=Path)
    p.add_argument("--audit-exit",type=int)
    p.add_argument("--receipt",type=Path)
    args=p.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    try:
        original=args.original.read_bytes()
        baseline=args.baseline.read_bytes()
        if digest(original)!=MANIFEST_SHA or digest(baseline)!=LOCK_SHA:
            raise ValueError("Baseline digest mismatch")
        if args.prepare:
            candidate=prepare(load(original))
            # Only a disposable manifest is supplied by the CI caller.
            if args.manifest.read_bytes()!=original:
                raise ValueError("Unexpected temporary manifest")
            args.manifest.write_text(json.dumps(candidate,indent=2)+"\n",encoding="utf-8")
            return 0
        candidate=args.manifest.read_bytes()
        lock=args.lock.read_bytes()
        coverage=validate(load(original),load(baseline),load(candidate),load(lock))
        print("PASS: same reviewed package identities except vulnerable minimatch 10.2.6 removed",coverage)
        if args.audit is not None:
            counts=clean_audit(load(args.audit.read_bytes()),args.audit_exit)
            receipt={"status":"candidate-not-approved","advisory":"GHSA-g3hv-75wg-m249",
                "baseline_lock_sha256":LOCK_SHA,"candidate_lock_sha256":digest(lock),
                "candidate_manifest_sha256":digest(candidate),"override":OVERRIDE,
                "audit_counts":counts,**coverage}
            with args.receipt.open("x",encoding="utf-8") as out:
                json.dump(receipt,out,indent=2,sort_keys=True);out.write("\n")
            print("PASS: zero vulnerabilities reported by npm for the exact candidate.")
    except (ValueError,KeyError,TypeError,AttributeError,OSError) as exc:
        print("FAIL: remediation rejected ("+type(exc).__name__+")")
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
