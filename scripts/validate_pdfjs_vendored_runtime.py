#!/usr/bin/env python3
"""Offline publication gate: allow only the reviewed complete PDF.js tree."""
from __future__ import annotations
import hashlib
from pathlib import Path
import re
import stat
import tempfile
import unittest
from stage_pdfjs_runtime import RUNTIME_COUNT, RUNTIME_BYTES, allowed, select, check_tree

RUNTIME=Path("projets/projet-nova/assets/pdfjs-6.5.438")
MODULE=Path("projets/projet-nova/assets/nova-pdf-viewer.mjs")

def runtime_path_allowed(rel):
    try:
        name=rel.relative_to(RUNTIME).as_posix()
    except ValueError:
        return False
    return allowed(name)

def verify_tree(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Missing verified runtime")
    records=[]
    total=0
    for path in sorted(root.rglob("*")):
        st=path.lstat()
        if stat.S_ISDIR(st.st_mode):
            continue
        name=path.relative_to(root).as_posix()
        if (not allowed(name) or not stat.S_ISREG(st.st_mode) or st.st_nlink!=1
                or len(records)>=RUNTIME_COUNT or not 0<st.st_size<=RUNTIME_BYTES
                or total+st.st_size>RUNTIME_BYTES):
            raise ValueError("Unexpected runtime member")
        with path.open("rb") as stream:
            data=stream.read(st.st_size+1)
        if len(data)!=st.st_size:
            raise ValueError("Runtime member size changed")
        total+=len(data)
        records.append({"path":name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    records=select({"files":records})
    check_tree(root,records)
    return records

def verify_state(root):
    module=root/MODULE
    runtime=root/RUNTIME
    if module.is_symlink() or not module.is_file():
        raise ValueError("Missing viewer module")
    for relative in (MODULE,RUNTIME):
        for parent in relative.parents:
            if (root/parent).is_symlink():
                raise ValueError("Symbolic viewer ancestor")
    if module.stat().st_size>65536:
        raise ValueError("Oversized viewer module")
    source=module.read_text("utf-8")
    flags=re.findall(r"(?m)^const RUNTIME_ENABLED = (true|false);$",source)
    if len(flags)!=1 or source.count("RUNTIME_ENABLED =")!=1:
        raise ValueError("Ambiguous runtime activation")
    if flags==["false"]:
        if runtime.exists() or runtime.is_symlink():
            raise ValueError("Disabled runtime must not be published")
        return []
    return verify_tree(runtime)

def publication_errors(root):
    try:
        verify_state(root)
    except (OSError,ValueError,TypeError,KeyError):
        return ["PDF.js: état de publication ou inventaire cryptographique non conforme."]
    return []

class Tests(unittest.TestCase):
    def test_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            module=root/MODULE
            module.parent.mkdir(parents=True)
            module.write_text("const RUNTIME_ENABLED = false;\n")
            self.assertEqual(verify_state(root),[])
            module.write_text("const RUNTIME_ENABLED = true;\n")
            self.assertTrue(publication_errors(root))
            runtime=root/RUNTIME
            runtime.mkdir()
            (runtime/"unknown.js").write_text("test")
            self.assertTrue(publication_errors(root))
            module.write_text("const RUNTIME_ENABLED = false;\n")
            self.assertTrue(publication_errors(root))
            self.assertFalse(runtime_path_allowed(RUNTIME/"build/pdf.sandbox.mjs"))
            self.assertFalse(runtime_path_allowed(RUNTIME/"web/wasm/quickjs-eval.js"))
            self.assertTrue(runtime_path_allowed(RUNTIME/"web/cmaps/LICENSE"))
            self.assertTrue(runtime_path_allowed(RUNTIME/"web/cmaps/test.bcmap"))

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--root",type=Path)
    a=p.parse_args()
    if a.self_test:
        raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1)
    if a.root is None:
        p.error("Root required")
    errors=publication_errors(a.root)
    if errors:
        print(errors[0])
        raise SystemExit(1)
    print("PASS: exact PDF.js publication state and runtime inventory.")
