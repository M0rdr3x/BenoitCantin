#!/usr/bin/env python3
"""Verify the exact reviewed mobile lock candidate before disposable npm ci."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import stat
import zipfile
import unittest
import tempfile
import json

from validate_mobile_lock_candidate import load, inspect, audit_counts, NAME, SEVERITIES

ARTIFACT_ID = "15136205966"
ZIP_SHA = "fb6f9573e57aa83b6493ae1ba4406d4ea2c3170feb3c0d4e96a12f0cccda44dd"
LOCK_SHA = "52c59065d2f6105e983e6f785ff8ab75b7733b3b843faca920c31ae3b81c8f96"
MANIFEST_SHA = "5bb58e2ff419de20b0b68f94d53c8412981e64efa69c6b89b6d9ef80bda5d54c"
SOURCE_SHA = "7a83f4c6f9317056f466a85a9a3d1de77ad3bc23"
LIMITS = {"package-lock.json": 2 * 1024 * 1024, "receipt.json": 8192}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_member(archive, info):
    mode = stat.S_IFMT(info.external_attr >> 16)
    if (info.filename not in LIMITS or info.orig_filename != info.filename
            or mode not in (0, stat.S_IFREG) or info.is_dir()
            or info.flag_bits & 1 or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
            or not 0 < info.file_size <= LIMITS[info.filename]):
        raise ValueError("Unexpected ZIP member")
    with archive.open(info) as stream:
        data = stream.read(LIMITS[info.filename] + 1)
        if len(data) != info.file_size or stream.read(1):
            raise ValueError("Invalid ZIP member size")
    return data

def read_zip(path, expected_sha=ZIP_SHA):
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or not 0 < st.st_size <= 2 * 1024 * 1024:
        raise ValueError("Invalid ZIP")
    data = path.read_bytes()
    if sha(data) != expected_sha:
        raise ValueError("ZIP digest mismatch")
    import io
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) != len(LIMITS) or {i.filename for i in entries} != set(LIMITS):
            raise ValueError("Unexpected ZIP membership")
        return {i.filename: read_member(archive, i) for i in entries}

def verified_lock(path, manifest):
    if sha(manifest) != MANIFEST_SHA:
        raise ValueError("Reviewed manifest changed")
    data = read_zip(path)
    lock = data["package-lock.json"]
    receipt = load(data["receipt.json"])
    if sha(lock) != LOCK_SHA or receipt != {
        "audit_counts": {"critical":0,"high":0,"info":0,"low":0,"moderate":3,"total":3},
        "direct_dependencies":13, "high_critical_gate_pass":True,
        "lock_sha256":LOCK_SHA, "locked_entries":499, "manifest_sha256":MANIFEST_SHA,
        "npm":"10.9.8", "source_sha":SOURCE_SHA, "status":"candidate-not-approved",
        "unique_name_versions":467,
    } or receipt["high_critical_gate_pass"] is not True:
        raise ValueError("Reviewed receipt mismatch")
    if inspect(load(manifest), load(lock)) != {"locked_entries":499,"unique_name_versions":467,"direct_dependencies":13}:
        raise ValueError("Reviewed inventory mismatch")
    return lock

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

class Tests(unittest.TestCase):
    def test_zip_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.zip"
            def fixture(entries):
                with zipfile.ZipFile(path,"w") as z:
                    for name,content in entries:
                        z.writestr(name,content)
                return sha(path.read_bytes())
            good=[("package-lock.json",b"lock"),("receipt.json",b"receipt")]
            digest=fixture(good)
            self.assertEqual(read_zip(path,digest)["package-lock.json"],b"lock")
            with self.assertRaises(ValueError):
                read_zip(path,"0"*64)
            for entries in ([],good[:1],good+[("extra",b"x")],
                            [("../package-lock.json",b"x"),good[1]],
                            [("package-lock.json",b""),good[1]],
                            [("package-lock.json",b"x"),("package-lock.json",b"y")]):
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore",UserWarning)
                    digest=fixture(entries)
                with self.subTest(entries=entries),self.assertRaises(ValueError):
                    read_zip(path,digest)
            info=zipfile.ZipInfo("package-lock.json")
            info.create_system=3
            info.external_attr=(stat.S_IFLNK|0o777)<<16
            with self.assertRaises(ValueError):
                read_zip(path,fixture([(info,b"link"),good[1]]))

    def test_audit_summary(self):
        counts={k:0 for k in (*SEVERITIES,"total")}
        counts.update(moderate=1,total=1)
        report={"auditReportVersion":2,"metadata":{"vulnerabilities":counts},
                "vulnerabilities":{"example":{"name":"example","severity":"moderate","via":[
                    {"url":"https://github.com/advisories/GHSA-1234-abcd-5678"}]}}}
        self.assertEqual(audit_summary(report,1)["packages"][0]["ghsa"],["GHSA-1234-abcd-5678"])
        report["vulnerabilities"]["example"]["severity"]="high"
        with self.assertRaises(ValueError):
            audit_summary(report,1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--zip",type=Path)
    p.add_argument("--manifest",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--audit",type=Path)
    p.add_argument("--audit-exit",type=int)
    p.add_argument("--summary-only",action="store_true")
    p.add_argument("--lock",type=Path)
    args=p.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if args.audit is not None:
        result=audit_summary(load(args.audit.read_bytes()),args.audit_exit)
        if args.lock is not None:
            lock_digest = sha(args.lock.read_bytes())
            result["lock_sha256"] = lock_digest
            result["matches_reviewed_lock"] = lock_digest == LOCK_SHA
        if args.summary_only and args.lock is None:
            p.error("summary-only requires lock identity")
        print(json.dumps(result,sort_keys=True))
        # The generation job still uploads the candidate for review before its
        # existing high/critical gate. The installation job never bypasses it.
        return 0 if args.summary_only else int(bool(result["counts"]["high"] or result["counts"]["critical"]))
    if not all((args.zip,args.manifest,args.output)):
        p.error("ZIP, manifest and output required")
    lock=verified_lock(args.zip,args.manifest.read_bytes())
    with args.output.open("xb") as out:
        out.write(lock)
    print("PASS: reviewed ZIP, manifest, receipt and lock verified; 499 locked entries.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
