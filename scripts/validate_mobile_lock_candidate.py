#!/usr/bin/env python3
"""Validate a candidate mobile npm lock without installing or executing packages."""
from __future__ import annotations
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import unittest

VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?")
NAME = re.compile(r"(?:@[a-z0-9._-]+/)?[a-z0-9._-]+")
MAX_BYTES = 16 * 1024 * 1024
SEVERITIES = ("info", "low", "moderate", "high", "critical")

def load(data):
    if len(data) > MAX_BYTES:
        raise ValueError("Oversized JSON")
    def pairs(values):
        out = {}
        for k, v in values:
            if k in out:
                raise ValueError("Duplicate JSON key")
            out[k] = v
        return out
    def reject(_):
        raise ValueError("Non-finite JSON")
    return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=reject)

def inspect(manifest, lock):
    if manifest.get("name") != "sinjira-mobile-native" or manifest.get("private") is not True:
        raise ValueError("Manifest identity")
    if lock.get("lockfileVersion") != 3 or lock.get("name") != manifest["name"] or lock.get("version") != manifest["version"]:
        raise ValueError("Lock identity")
    packages = lock["packages"]
    if not isinstance(packages, dict) or not 1 < len(packages) <= 20000:
        raise ValueError("Package count")
    root = packages[""]
    if root.get("name") != manifest["name"] or root.get("version") != manifest["version"]:
        raise ValueError("Root identity")
    for field in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        if root.get(field, {}) != manifest.get(field, {}):
            raise ValueError("Root dependencies mismatch")
        for name, version in manifest.get(field, {}).items():
            if not NAME.fullmatch(name) or not VERSION.fullmatch(version):
                raise ValueError("Direct dependency not pinned")
            if packages.get("node_modules/" + name, {}).get("version") != version:
                raise ValueError("Direct dependency resolution")
    for path, entry in packages.items():
        if not path:
            continue
        if not re.fullmatch(r"(?:node_modules/(?:@[a-z0-9._-]+/)?[a-z0-9._-]+)(?:/node_modules/(?:@[a-z0-9._-]+/)?[a-z0-9._-]+)*", path) or any(part in (".", "..") for part in path.split("/")):
            raise ValueError("Unexpected package path")
        if not isinstance(entry, dict) or entry.get("link") or entry.get("inBundle"):
            raise ValueError("Linked or bundled dependency requires review")
        name = path.rsplit("node_modules/", 1)[-1]
        if entry.get("name", name) != name:
            raise ValueError("Aliased dependency requires review")
        if not VERSION.fullmatch(entry["version"]):
            raise ValueError("Invalid resolved version")
        sri = entry["integrity"]
        if not isinstance(sri, str) or not sri.startswith("sha512-") or len(base64.b64decode(sri[7:], validate=True)) != 64:
            raise ValueError("Invalid integrity")
        url = urlsplit(entry["resolved"])
        expected_path = "/" + name + "/-/" + name.rsplit("/", 1)[-1] + "-" + entry["version"] + ".tgz"
        if url.scheme != "https" or url.netloc != "registry.npmjs.org" or url.path != expected_path or url.query or url.fragment:
            raise ValueError("Unexpected tarball origin or identity")
    return {"locked_entries": len(packages)-1,
            "unique_name_versions": len({(p.rsplit("node_modules/", 1)[-1], e["version"]) for p,e in packages.items() if p}),
            "direct_dependencies": sum(len(manifest.get(f, {})) for f in ("dependencies","devDependencies","optionalDependencies","peerDependencies"))}

def audit_counts(report, code):
    if code not in (0, 1) or report.get("error") or report.get("auditReportVersion") != 2:
        raise ValueError("Audit unavailable")
    counts = report["metadata"]["vulnerabilities"]
    if set(counts) != set(SEVERITIES) | {"total"} or any(type(n) is not int or n < 0 for n in counts.values()):
        raise ValueError("Invalid audit counts")
    if sum(counts[k] for k in SEVERITIES) != counts["total"] or (code == 0) != (counts["total"] == 0):
        raise ValueError("Inconsistent audit result")
    return counts

class Tests(unittest.TestCase):
    def test_contract(self):
        manifest = {"name":"sinjira-mobile-native","version":"1.0.0","private":True,"dependencies":{"example":"1.0.0"}}
        lock = {"name":manifest["name"],"version":"1.0.0","lockfileVersion":3,"packages":{
            "":{"name":manifest["name"],"version":"1.0.0","dependencies":{"example":"1.0.0"}},
            "node_modules/example":{"version":"1.0.0","integrity":"sha512-"+base64.b64encode(bytes(64)).decode(),
            "resolved":"https://registry.npmjs.org/example/-/example-1.0.0.tgz"}}}
        self.assertEqual(inspect(manifest,lock)["locked_entries"],1)
        for key,value in (("version","2.0.0"),("integrity","sha512-AA=="),("resolved","https://example.org/example.tgz"),("resolved","https://registry.npmjs.org/other/-/other-1.0.0.tgz"),("link",True),("name","other"),("inBundle",True)):
            mutant=copy.deepcopy(lock)
            mutant["packages"]["node_modules/example"][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                inspect(manifest,mutant)
        with self.assertRaises(ValueError): load(b'{"a":1,"a":2}')
        with self.assertRaises(ValueError): load(b'{"a":NaN}')
        report={"auditReportVersion":2,"metadata":{"vulnerabilities":{k:0 for k in (*SEVERITIES,"total")}}}
        self.assertEqual(audit_counts(report,0)["total"],0)
        with self.assertRaises(ValueError): audit_counts(report,1)
        with self.assertRaises(ValueError): audit_counts(report,2)
        report["metadata"]["vulnerabilities"]["high"]=1
        with self.assertRaises(ValueError): audit_counts(report,1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--manifest",type=Path)
    p.add_argument("--lock",type=Path)
    p.add_argument("--audit",type=Path)
    p.add_argument("--audit-exit",type=int)
    p.add_argument("--receipt",type=Path)
    p.add_argument("--source-sha")
    args=p.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if not all((args.manifest,args.lock,args.audit,args.receipt,args.source_sha)) or args.audit_exit is None or not re.fullmatch(r"[0-9a-f]{40}",args.source_sha):
        p.error("Missing input")
    try:
        manifest=args.manifest.read_bytes(); lock=args.lock.read_bytes()
        coverage=inspect(load(manifest),load(lock))
        counts=audit_counts(load(args.audit.read_bytes()),args.audit_exit)
        receipt={"source_sha":args.source_sha,"npm":"10.9.8","manifest_sha256":hashlib.sha256(manifest).hexdigest(),
            "lock_sha256":hashlib.sha256(lock).hexdigest(),**coverage,"audit_counts":counts,
            "high_critical_gate_pass":counts["high"]==0 and counts["critical"]==0,"status":"candidate-not-approved"}
        with args.receipt.open("x",encoding="utf-8") as out:
            json.dump(receipt,out,indent=2,sort_keys=True);out.write("\n")
        print("PASS: lock provenance",coverage,"audit severity totals",counts)
    except (ValueError,KeyError,TypeError,AttributeError,OSError) as exc:
        print("FAIL: mobile lock candidate rejected ("+type(exc).__name__+")")
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
