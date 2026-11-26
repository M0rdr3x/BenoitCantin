#!/usr/bin/env python3
"""Review gate for the exact mobile dependency remediation, no installation."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
import unittest

from validate_mobile_lock_candidate import inspect, load, audit_counts, NAME, SEVERITIES

MANIFEST_SHA = "5202b2130b4a04ad3c95afca01503a9b5082c6dd32aa9a3ddf2f175ef97b70f9"
LOCK_SHA = "66af9f87a206f7f73e15c2807c399f3ee5a12dd8d75470065051cff710ad1b0b"
LOCK_BLOB_SHA = "615cb83607f8354f86ea928d19ce4106836b3eec"
EXPECTED = {"locked_entries":498,"unique_name_versions":466,"direct_dependencies":13}
OVERRIDE = {"@expo/fingerprint@0.20.17":{"minimatch":"11.0.9"}}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def git_blob_sha(data):
    return hashlib.sha1(("blob %d\0" % len(data)).encode("ascii") + data).hexdigest()

def verified_bytes(manifest, lock):
    if digest(manifest) != MANIFEST_SHA or digest(lock) != LOCK_SHA or git_blob_sha(lock) != LOCK_BLOB_SHA:
        raise ValueError("Reviewed dependency snapshot changed")
    project, inventory = load(manifest), load(lock)
    if project.get("overrides") != OVERRIDE or inspect(project, inventory) != EXPECTED:
        raise ValueError("Unexpected reviewed inventory")
    packages = inventory["packages"]
    minimatch = {p:e["version"] for p,e in packages.items() if p and p.rsplit("node_modules/",1)[-1]=="minimatch"}
    if minimatch != {"node_modules/minimatch":"11.0.9"}:
        raise ValueError("Vulnerable or unexpected minimatch resolution")
    if packages["node_modules/@expo/fingerprint"]["version"] != "0.20.17":
        raise ValueError("Unexpected fingerprint version")
    return EXPECTED.copy()

def audit_summary(report, code):
    counts = audit_counts(report, code)
    packages = report["vulnerabilities"]
    if not isinstance(packages, dict) or len(packages) != counts["total"]:
        raise ValueError("Audit package count mismatch")
    actual = {k:0 for k in SEVERITIES}
    summaries = []
    for name, advisory in sorted(packages.items()):
        severity = advisory["severity"]
        if not NAME.fullmatch(name) or severity not in actual or advisory.get("name") != name:
            raise ValueError("Invalid audit package")
        actual[severity] += 1
        ids = set()
        indirect = set()
        for item in advisory["via"]:
            if isinstance(item, str):
                if not NAME.fullmatch(item):
                    raise ValueError("Invalid indirect advisory")
                indirect.add(item)
            elif isinstance(item, dict):
                url = item.get("url", "")
                match = re.fullmatch(r"https://github\.com/advisories/(GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4})", url)
                if match:
                    ids.add(match[1])
            else:
                raise ValueError("Invalid advisory record")
        summaries.append({"name":name,"severity":severity,"ghsa":sorted(ids),"via_packages":sorted(indirect)})
    if any(actual[k] != counts[k] for k in SEVERITIES):
        raise ValueError("Audit severities mismatch")
    return {"counts":counts,"packages":summaries}

def zero_audit(payload, code):
    result = audit_summary(load(payload), code)
    if result["counts"]["total"] != 0 or result["packages"]:
        raise ValueError("Audit reports vulnerabilities")
    return result["counts"]

class Tests(unittest.TestCase):
    def test_digest_gate(self):
        with self.assertRaises(ValueError):
            verified_bytes(b"{}",b"{}")
        self.assertEqual(git_blob_sha(b""),"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
    def test_zero_audit(self):
        counts={k:0 for k in ("info","low","moderate","high","critical","total")}
        report={"auditReportVersion":2,"metadata":{"vulnerabilities":counts},"vulnerabilities":{}}
        self.assertEqual(zero_audit(json.dumps(report).encode(),0)["total"],0)
        with self.assertRaises(ValueError):
            zero_audit(json.dumps(report).encode(),1)
        counts.update(moderate=1,total=1)
        report["vulnerabilities"]={"example":{"name":"example","severity":"moderate","via":[]}}
        with self.assertRaises(ValueError):
            zero_audit(json.dumps(report).encode(),1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--manifest",type=Path)
    p.add_argument("--lock",type=Path)
    p.add_argument("--audit",type=Path)
    p.add_argument("--audit-exit",type=int)
    args=p.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if not args.manifest or not args.lock:
        p.error("Manifest and lock required")
    try:
        manifest,lock=args.manifest.read_bytes(),args.lock.read_bytes()
        coverage=verified_bytes(manifest,lock)
        if args.audit is not None:
            if args.audit_exit is None:
                p.error("Audit exit status required")
            zero_audit(args.audit.read_bytes(),args.audit_exit)
        print("PASS: reviewed mobile lock",coverage)
    except (ValueError,KeyError,TypeError,AttributeError,OSError) as exc:
        print("FAIL: mobile snapshot rejected ("+type(exc).__name__+")",file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
