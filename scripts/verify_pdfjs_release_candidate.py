#!/usr/bin/env python3
"""Inventory the exact reviewed upstream PDF.js release, without executing it."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import unittest
import zipfile
import io

VERSION = "6.5.438"
SIZE = 6911254
DIGEST = "55138aa33b5f1f6f68809895338b947f395f344eb6381d424b2420d6daa6a844"
URL = "https://github.com/mozilla/pdf.js/releases/download/v6.5.438/pdfjs-6.5.438-legacy-dist.zip"
ASSET_ID = 699100251
MAX_MEMBER = 20 * 1024 * 1024
MAX_TOTAL = 80 * 1024 * 1024
MAX_ENTRIES = 2000
REQUIRED = {"build/pdf.mjs", "build/pdf.worker.mjs", "LICENSE"}
PATH = re.compile(r"[A-Za-z0-9._+@/-]{1,256}")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def inspect_zip(payload):
    seen, files, total = set(), {}, 0
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        entries = archive.infolist()
        if not 0 < len(entries) <= MAX_ENTRIES:
            raise ValueError("Archive entry limit")
        for item in entries:
            name = item.orig_filename
            clean = name.rstrip("/")
            path = PurePosixPath(clean)
            mode = stat.S_IFMT(item.external_attr >> 16)
            if (not PATH.fullmatch(name) or name != item.filename or path.is_absolute()
                    or any(part in ("", ".", "..") for part in clean.split("/"))
                    or name in seen or item.flag_bits & 1
                    or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                    or mode not in (0, stat.S_IFDIR if item.is_dir() else stat.S_IFREG)):
                raise ValueError("Unsafe archive member")
            seen.add(name)
            if item.is_dir():
                if item.file_size != 0:
                    raise ValueError("Invalid directory")
                continue
            if not 0 <= item.file_size <= MAX_MEMBER or total + item.file_size > MAX_TOTAL:
                raise ValueError("Archive size limit")
            with archive.open(item) as stream:
                data = stream.read(MAX_MEMBER + 1)
            if len(data) != item.file_size:
                raise ValueError("Archive length mismatch")
            total += len(data)
            files[name] = {"path":name,"bytes":len(data),"sha256":sha(data)}
            if name in ("build/pdf.mjs","build/pdf.worker.mjs"):
                if VERSION.encode() not in data or not data:
                    raise ValueError("Release version absent")
    if not REQUIRED <= files.keys():
        raise ValueError("Required release members absent")
    # Detect prefix collisions, including files shadowing directories.
    for name in files:
        if any(str(parent) in files for parent in PurePosixPath(name).parents):
            raise ValueError("Archive path collision")
    return {"entries":len(files),"uncompressed_bytes":total,
            "files":[files[name] for name in sorted(files)],
            "candidate_runtime":[name for name in sorted(files) if name.startswith(("build/","web/cmaps/","web/standard_fonts/","web/wasm/","web/iccs/")) and not name.endswith(".map")]}

def verify(payload):
    if len(payload) != SIZE or sha(payload) != DIGEST:
        raise ValueError("Unreviewed release digest or size")
    return inspect_zip(payload)

class Tests(unittest.TestCase):
    def fixture(self, extra=None, missing=None):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w",compression=zipfile.ZIP_DEFLATED) as z:
            for name in REQUIRED-{missing}:
                z.writestr(name,VERSION.encode())
            if extra:
                z.writestr(*extra)
        return buf.getvalue()
    def test_archive(self):
        self.assertEqual(inspect_zip(self.fixture())["entries"],3)
        for name in ("../bad","/absolute","build/../bad","build\\bad","build//bad","build/pdf.mjs/child"):
            with self.subTest(name=name),self.assertRaises(ValueError):
                inspect_zip(self.fixture((name,b"test")))
        with self.assertRaises(ValueError):
            inspect_zip(self.fixture(missing="LICENSE"))
        with self.assertRaises(ValueError):
            verify(self.fixture())
        link=zipfile.ZipInfo("link")
        link.create_system=3
        link.external_attr=(stat.S_IFLNK|0o777)<<16
        with self.assertRaises(ValueError):
            inspect_zip(self.fixture((link,b"target")))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--archive",type=Path)
    p.add_argument("--receipt",type=Path)
    p.add_argument("--source-sha")
    args=p.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if not args.archive or not args.receipt or not re.fullmatch(r"[0-9a-f]{40}",args.source_sha or ""):
        p.error("Archive, receipt and source SHA required")
    try:
        st=args.archive.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1 or st.st_size!=SIZE:
            raise ValueError("Invalid release archive")
        with args.archive.open("rb") as stream:
            payload=stream.read(SIZE+1)
        inventory=verify(payload)
        receipt={"status":"candidate-not-approved","version":VERSION,"asset_id":ASSET_ID,
                 "url":URL,"archive_bytes":SIZE,"archive_sha256":DIGEST,"source_sha":args.source_sha,**inventory}
        with args.receipt.open("x",encoding="utf-8") as out:
            json.dump(receipt,out,indent=2,sort_keys=True)
            out.write("\n")
        print("PASS: verified PDF.js release archive; files",inventory["entries"],
              "uncompressed bytes",inventory["uncompressed_bytes"],"runtime candidates",len(inventory["candidate_runtime"]))
    except (OSError,ValueError,zipfile.BadZipFile,RuntimeError,NotImplementedError):
        print("FAIL: PDF.js candidate rejected")
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
