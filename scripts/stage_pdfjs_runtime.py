#!/usr/bin/env python3
"""Prepare the reviewed, minimal PDF.js runtime in a disposable directory only."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import tempfile
import unittest
import zipfile
from verify_pdfjs_release_candidate import SIZE, VERSION, DIGEST, verify

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_COUNT = 198
RUNTIME_BYTES = 6015955
RUNTIME_SHA = "745e8bc0d9399eb6154009683cfae7ab4ab70d0d7966811f58efa75e533d466b"
EXACT = {
    "LICENSE", "build/pdf.mjs", "build/pdf.worker.mjs",
    "web/cmaps/LICENSE",
    "web/standard_fonts/LICENSE_FOXIT", "web/standard_fonts/LICENSE_LIBERATION",
    "web/iccs/CGATS001Compat-v2-micro.icc", "web/iccs/LICENSE",
    "web/wasm/jbig2_nowasm_fallback.js", "web/wasm/openjpeg_nowasm_fallback.js",
    "web/wasm/LICENSE_JBIG2", "web/wasm/LICENSE_OPENJPEG",
    "web/wasm/LICENSE_PDFJS_JBIG2", "web/wasm/LICENSE_PDFJS_OPENJPEG",
    "web/wasm/LICENSE_PDFJS_QCMS", "web/wasm/LICENSE_QCMS",
}
MODULE_HASHES = {
    "build/pdf.mjs": "49f16195d418122d8f91a41da3361667fc7d34405d186860e1bb8af4683d6006",
    "build/pdf.worker.mjs": "8336aabf764cb08c818555a2fd2545e4fed10837146de927564875c93b3c4f83",
}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def allowed(name):
    path = PurePosixPath(name)
    if path.is_absolute() or str(path) != name or any(x in ("", ".", "..") for x in name.split("/")):
        return False
    return (name in EXACT or (str(path.parent) == "web/cmaps" and path.suffix == ".bcmap")
            or (str(path.parent) == "web/standard_fonts" and path.suffix in (".pfb", ".ttf")))

def inventory_bytes(records):
    return (json.dumps(records, sort_keys=True, separators=(",", ":")) + "\n").encode()

def select(inventory):
    records = sorted((x for x in inventory["files"] if allowed(x["path"])),key=lambda x:x["path"])
    names = {x["path"]:x for x in records}
    if not EXACT <= names.keys() or len(records) != len(names) or len(records) != RUNTIME_COUNT:
        raise ValueError("Runtime file selection changed")
    if sum(x["bytes"] for x in records) != RUNTIME_BYTES or digest(inventory_bytes(records)) != RUNTIME_SHA:
        raise ValueError("Unreviewed runtime inventory")
    if any(names[path]["sha256"] != expected for path,expected in MODULE_HASHES.items()):
        raise ValueError("Reviewed module changed")
    return records

def check_tree(root, records):
    expected = {x["path"]:x for x in records}
    directories = {str(parent) for name in expected for parent in PurePosixPath(name).parents if str(parent)!="."}
    seen, seen_dirs = set(), set()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Invalid runtime directory")
    for path in root.rglob("*"):
        name = path.relative_to(root).as_posix()
        st = path.lstat()
        if stat.S_ISDIR(st.st_mode):
            if name not in directories:
                raise ValueError("Unexpected runtime directory")
            seen_dirs.add(name)
            continue
        if name not in expected or not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise ValueError("Unexpected runtime file")
        record = expected[name]
        if st.st_size != record["bytes"]:
            raise ValueError("Runtime size mismatch")
        with path.open("rb") as stream:
            data = stream.read(record["bytes"]+1)
        if len(data) != record["bytes"] or digest(data) != record["sha256"]:
            raise ValueError("Runtime digest mismatch")
        seen.add(name)
    if seen != expected.keys() or seen_dirs != directories:
        raise ValueError("Incomplete runtime directory")

def stage(archive, destination):
    if destination.exists() or destination.is_symlink() or not destination.parent.is_dir() or destination.parent.is_symlink():
        raise ValueError("Fresh runtime destination required")
    resolved = destination.resolve()
    if resolved == ROOT or ROOT in resolved.parents or resolved in ROOT.parents:
        raise ValueError("Candidate must remain outside repository")
    st = archive.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_size != SIZE:
        raise ValueError("Invalid source archive")
    with archive.open("rb") as stream:
        payload=stream.read(SIZE+1)
    records=select(verify(payload))
    destination.mkdir(mode=0o700)
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        for item in records:
            data=z.read(item["path"])
            if len(data)!=item["bytes"] or digest(data)!=item["sha256"]:
                raise ValueError("Runtime member changed")
            target=destination/item["path"]
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open("xb") as out:
                out.write(data)
    check_tree(destination,records)
    print("PASS: minimal PDF.js runtime",len(records),"files",RUNTIME_BYTES,"bytes; no WASM, maps or PDF sandbox")
    return records

class Tests(unittest.TestCase):
    def test_selection(self):
        for name in ("build/pdf.mjs","build/pdf.worker.mjs","web/cmaps/a.bcmap","web/standard_fonts/font.ttf","web/wasm/jbig2_nowasm_fallback.js","LICENSE"):
            self.assertTrue(allowed(name))
        for name in ("build/pdf.sandbox.mjs","build/pdf.renderer.mjs","build/pdf.mjs.map","web/wasm/quickjs-eval.js","web/wasm/openjpeg.wasm","web/viewer.html","web/cmaps/sub/a.bcmap","../LICENSE","/LICENSE","web//cmaps/a.bcmap"):
            self.assertFalse(allowed(name))
        with self.assertRaises(ValueError):
            select({"files":[]})
    def test_tree_mutations(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            path=root/"build"
            path.mkdir()
            file=path/"pdf.mjs"
            file.write_bytes(b"test")
            records=[{"path":"build/pdf.mjs","bytes":4,"sha256":digest(b"test")}]
            check_tree(root,records)
            file.write_bytes(b"evil")
            with self.assertRaises(ValueError): check_tree(root,records)
            file.write_bytes(b"test")
            (root/"unexpected").mkdir()
            with self.assertRaises(ValueError): check_tree(root,records)
            (root/"unexpected").rmdir()
            link=root/"alias"
            link.symlink_to(file)
            with self.assertRaises(ValueError): check_tree(root,records)
            link.unlink()
            file.unlink()
            with self.assertRaises(ValueError): check_tree(root,records)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--archive",type=Path)
    p.add_argument("--destination",type=Path)
    p.add_argument("--receipt",type=Path)
    args=p.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if not all((args.archive,args.destination,args.receipt)):
        p.error("Archive, fresh destination and receipt required")
    try:
        receipt=args.receipt.resolve()
        destination=args.destination.resolve()
        if ROOT in receipt.parents or destination in receipt.parents or receipt==destination:
            raise ValueError("Receipt must remain outside repository and runtime")
        records=stage(args.archive,args.destination)
        with args.receipt.open("x",encoding="utf-8") as out:
            json.dump({"status":"candidate-not-approved","version":VERSION,"archive_sha256":DIGEST,
                       "runtime_inventory_sha256":RUNTIME_SHA,"files":records},out,indent=2,sort_keys=True)
            out.write("\n")
    except (ValueError,OSError,KeyError,TypeError,zipfile.BadZipFile,RuntimeError,NotImplementedError):
        print("FAIL: minimal runtime rejected")
        return 1
    return 0

if __name__=="__main__":
    raise SystemExit(main())
