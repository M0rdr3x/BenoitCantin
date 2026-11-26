#!/usr/bin/env python3
"""Create a bounded, reproducible Pages archive from the reviewed public tree.
No extraction, symlink traversal, or network access.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import stat
import tarfile
import tempfile
import unittest

MAX_BYTES = 1_000_000_000
MAX_FILES = 20_000
FORBIDDEN = {".git", ".github", "supabase", "scripts", "docs", "tests", "mobile-native", "tools", "security"}
ALLOWED_HIDDEN_PATHS = {
    ".well-known", ".well-known/security.txt",
    ".well-known/release.json", ".nojekyll",
}

def check_public_path(name: str, is_directory: bool):
    parts = name.split("/")
    if any(part.casefold() in FORBIDDEN for part in parts):
        raise ValueError("Forbidden archive path")
    if any(part.startswith(".") for part in parts):
        if name not in ALLOWED_HIDDEN_PATHS or is_directory != (name == ".well-known"):
            raise ValueError("Forbidden hidden archive path")
    if not is_directory:
        # Reapply the reviewed publication policy to every file on disk,
        # not just to files initially selected by the builder.
        from build_netlify_public import relative_path_allowed, RELEASE_METADATA_PATH
        rel = Path(name)
        if rel != RELEASE_METADATA_PATH and not relative_path_allowed(rel):
            raise ValueError("Unapproved public archive file")

def digest(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(block)
    return result.hexdigest()

def inventory(root: Path):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Invalid public root")
    files = {}
    total = 0
    entries = 0
    for p in sorted(root.rglob("*")):
        entries += 1
        if entries > MAX_FILES:
            raise ValueError("Public inventory too large")
        name = p.relative_to(root).as_posix()
        if any(ord(ch) < 32 or ord(ch) == 127 or ch == "\\" for ch in name):
            raise ValueError("Invalid archive path")
        st = p.lstat()
        check_public_path(name, stat.S_ISDIR(st.st_mode))
        if stat.S_ISDIR(st.st_mode):
            continue
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise ValueError("Non-regular or linked public file")
        total += st.st_size
        if total > MAX_BYTES:
            raise ValueError("Public archive too large")
        with p.open("rb") as src:
            files[name] = (st.st_size, digest(src))
    if not files or "index.html" not in files:
        raise ValueError("Public entry point missing")
    return files

def verify_archive(archive: Path, expected):
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size > MAX_BYTES:
        raise ValueError("Invalid archive")
    seen = set()
    with tarfile.open(archive, "r:") as tar:
        for member in tar:
            name = member.name
            if not member.isfile() or member.issparse() or name in seen or name not in expected:
                raise ValueError("Unexpected archive member")
            size, sha = expected[name]
            if member.size != size:
                raise ValueError("Archive size mismatch")
            with tar.extractfile(member) as stream:
                if digest(stream) != sha:
                    raise ValueError("Archive content mismatch")
            seen.add(name)
    if seen != set(expected):
        raise ValueError("Incomplete archive")

def create(root: Path, archive: Path):
    expected = inventory(root)
    if archive.resolve().is_relative_to(root.resolve()) or archive.exists() or archive.is_symlink():
        raise ValueError("Archive output must be new and outside public tree")
    try:
        with archive.open("xb") as output:
            with tarfile.open(fileobj=output, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for name,(size,_) in expected.items():
                    info = tarfile.TarInfo(name)
                    info.size = size
                    info.mode = 0o644
                    info.mtime = 0
                    with (root / name).open("rb") as src:
                        tar.addfile(info, src)
        verify_archive(archive, expected)
        if inventory(root) != expected:
            raise ValueError("Public tree changed during packaging")
    except BaseException:
        archive.unlink(missing_ok=True)
        raise

class Tests(unittest.TestCase):
    def test_archive_deterministic_and_hidden_public_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"_site"; root.mkdir()
            (root/"index.html").write_bytes(b"synthetic")
            (root/".well-known").mkdir()
            (root/".well-known/security.txt").write_bytes(b"fixture")
            (root/".nojekyll").touch()
            a=Path(tmp)/"a.tar"; b=Path(tmp)/"b.tar"
            create(root,a); create(root,b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            expected=inventory(root)
            (root/"index.html").write_bytes(b"different")
            with self.assertRaises(ValueError): verify_archive(a,inventory(root))
            verify_archive(a,expected)
            self.assertFalse((root/"a.tar").exists())

    def test_reject_nonpublic_links_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"_site"; root.mkdir()
            (root/"index.html").touch()
            bad=root/".env"; bad.touch()
            with self.assertRaises(ValueError): inventory(root)
            bad.unlink()
            bad=root/"linked"; bad.symlink_to(root/"index.html")
            with self.assertRaises(ValueError): inventory(root)
            bad.unlink()
            with self.assertRaises(ValueError): create(root,root/"out.tar")

    def test_nested_technical_paths_are_excluded_by_builder_and_archive(self):
        from build_netlify_public import relative_path_allowed
        for folder in ("scripts", "tests", "docs", "tools", "SUPABASE", ".git"):
            rel=Path("projets")/"projet-nova"/folder/"fixture.mjs"
            self.assertFalse(relative_path_allowed(rel), str(rel))
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/"_site"; root.mkdir()
                (root/"index.html").touch()
                bad=root/rel; bad.parent.mkdir(parents=True); bad.touch()
                with self.assertRaises(ValueError): inventory(root)
        self.assertTrue(relative_path_allowed(Path("projets/projet-nova/assets/nova-civic-integrity.js")))
        self.assertTrue(relative_path_allowed(Path("projets/projet-nova/official/reference/corpus.md")))

    def test_reject_unapproved_public_files_and_hidden_paths(self):
        bad_paths = (
            "assets/.well-known/security.txt",
            "assets/.nojekyll",
            ".well-known/extra.json",
            ".well-known/security.txt/fixture.html",
            "assets/private-export.csv",
            "assets/source.js.map",
            "assets/backup.zip",
            "_headers",
            "_redirects",
            "projets/projet-nova/data/unreviewed.json",
            "projets/sinjira/romans/unreviewed.pdf",
        )
        for name in bad_paths:
            with self.subTest(path=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "_site"; root.mkdir()
                (root / "index.html").touch()
                bad = root / name
                bad.parent.mkdir(parents=True, exist_ok=True)
                bad.touch()
                with self.assertRaises(ValueError):
                    inventory(root)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "_site"; root.mkdir()
            for name in ("index.html", ".nojekyll", ".well-known/security.txt",
                         ".well-known/release.json", "assets/js/site.js"):
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.touch()
            self.assertEqual(len(inventory(root)), 5)

    def test_reject_extra_missing_traversal_duplicate_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            import io
            root=Path(tmp)/"_site"; root.mkdir()
            (root/"index.html").write_bytes(b"x")
            expected=inventory(root)
            a=Path(tmp)/"a.tar"
            for names in [[],["index.html","extra"],["../index.html"],["index.html","index.html"]]:
                with tarfile.open(a,"w") as tar:
                    for name in names:
                        info=tarfile.TarInfo(name);info.size=1
                        tar.addfile(info,io.BytesIO(b"x"))
                with self.assertRaises(ValueError): verify_archive(a,expected)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["create","self-test"])
    parser.add_argument("root",nargs="?",type=Path)
    parser.add_argument("archive",nargs="?",type=Path)
    args=parser.parse_args()
    if args.action=="self-test":
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if args.root is None or args.archive is None: parser.error("root and archive required")
    create(args.root,args.archive)
    print("PASS: verified deterministic public Pages TAR")
    return 0
if __name__=="__main__": raise SystemExit(main())
