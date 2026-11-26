#!/usr/bin/env python3
"""Verify an exact uploaded Pages ZIP and its single TAR member without extraction."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import stat
import tempfile
import unittest
import zipfile

MAX_ZIP = 1_100_000_000
MAX_TAR = 1_000_000_000
SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)

def hash_exact(stream, size):
    h = hashlib.sha256()
    remaining = size
    while remaining:
        chunk = stream.read(min(remaining, 1024 * 1024))
        if not chunk:
            raise ValueError("Truncated artifact")
        h.update(chunk)
        remaining -= len(chunk)
    if stream.read(1):
        raise ValueError("Artifact exceeds declared size")
    return h.hexdigest()

def verify(path: Path, zip_sha: str, tar_sha: str):
    if not SHA256.fullmatch(zip_sha) or not SHA256.fullmatch(tar_sha):
        raise ValueError("Invalid digest")
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_ZIP:
        raise ValueError("Invalid ZIP file")
    with path.open("rb") as source:
        if hash_exact(source, info.st_size) != zip_sha:
            raise ValueError("ZIP digest mismatch")
        source.seek(0)
        with zipfile.ZipFile(source) as archive:
            members = archive.infolist()
            if len(members) != 1:
                raise ValueError("Unexpected ZIP member count")
            entry = members[0]
            mode = stat.S_IFMT(entry.external_attr >> 16)
            if (entry.filename != "artifact.tar" or entry.orig_filename != "artifact.tar"
                    or entry.is_dir() or mode not in (0, stat.S_IFREG)
                    or entry.flag_bits & 1 or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                    or not 0 < entry.file_size <= MAX_TAR):
                raise ValueError("Unexpected ZIP member")
            with archive.open(entry, "r") as stream:
                if hash_exact(stream, entry.file_size) != tar_sha:
                    raise ValueError("TAR digest mismatch")

class Tests(unittest.TestCase):
    def test_valid_and_hostile_archives(self):
        tar = b"synthetic tar"
        digest = hashlib.sha256(tar).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "artifact.zip"
            def fixture(entries):
                with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
                    for name, payload in entries:
                        z.writestr(name, payload)
                return hashlib.sha256(path.read_bytes()).hexdigest()
            sha = fixture([("artifact.tar", tar)])
            verify(path, sha, digest)
            for wrong in ("0" * 64, "invalid", sha.upper()):
                with self.assertRaises(ValueError):
                    verify(path, wrong, digest)
            with self.assertRaises(ValueError):
                verify(path, sha, "0" * 64)
            for entries in ([], [("../artifact.tar", tar)], [("nested/artifact.tar", tar)],
                            [("artifact.tar", tar), ("extra", b"x")],
                            [("artifact.tar/", b"")], [("artifact.tar", b"")],
                            [("artifact.tar", b"changed")]):
                with self.subTest(entries=entries), self.assertRaises(ValueError):
                    verify(path, fixture(entries), digest)
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                sha = fixture([("artifact.tar", tar), ("artifact.tar", tar)])
            with self.assertRaises(ValueError):
                verify(path, sha, digest)
            info = zipfile.ZipInfo("artifact.tar")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            sha = fixture([(info, tar)])
            with self.assertRaises(ValueError):
                verify(path, sha, digest)
            sha = fixture([("artifact.tar", tar)])
            alias = root / "alias.zip"
            alias.symlink_to(path)
            with self.assertRaises(ValueError):
                verify(alias, sha, digest)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("zip_path", nargs="?", type=Path)
    parser.add_argument("zip_sha", nargs="?")
    parser.add_argument("tar_sha", nargs="?")
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if args.zip_path is None or args.zip_sha is None or args.tar_sha is None:
        parser.error("ZIP and both SHA-256 digests required")
    verify(args.zip_path, args.zip_sha, args.tar_sha)
    print("PASS: exact Pages ZIP and TAR SHA-256 verified without extraction.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
