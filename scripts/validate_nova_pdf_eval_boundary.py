#!/usr/bin/env python3
"""Temporary defensive control for the legacy PDF.js viewer until upgrade."""
from __future__ import annotations
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

VIEWER = Path("projets/projet-nova/visionneuse.html")
CALL = "pdfjsLib.getDocument({url:d.path, isEvalSupported:false, enableXfa:false, disableAutoFetch:false, disableStream:false})"

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside = False
        self.parts = []
        self.inline = []
    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.inside = "src" not in dict(attrs)
            self.parts = []
    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == "script":
            if self.inside:
                self.inline.append("".join(self.parts))
            self.inside = False

def validate(source):
    parser = Scripts()
    parser.feed(source)
    parser.close()
    inline = "\n".join(parser.inline)
    if inline.count(CALL) != 1 or len(re.findall(r"\bgetDocument\s*\(",inline)) != 1:
        raise ValueError("Legacy PDF loading must explicitly disable evaluation and XFA")
    if re.search(r"\bisEvalSupported\s*:\s*(?!false\b)",inline):
        raise ValueError("Unsafe PDF evaluation option")
    if re.search(r"\benableXfa\s*:\s*(?!false\b)",inline):
        raise ValueError("Unsafe XFA option")

class Tests(unittest.TestCase):
    def test_contract(self):
        source = "<script>pdf=await "+CALL+".promise;</script>"
        validate(source)
        for changed in (
            source.replace("isEvalSupported:false, ",""),
            source.replace("isEvalSupported:false","isEvalSupported:true"),
            source.replace("enableXfa:false","enableXfa:true"),
            source.replace("enableXfa:false, ",""),
            source + "<script>pdfjsLib.getDocument({url:d.path})</script>",
            "<!--"+source+"-->",
        ):
            with self.assertRaises(ValueError):
                validate(changed)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--root",type=Path)
    args=p.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if args.root is None:
        p.error("Build root required")
    validate((args.root/VIEWER).read_text(encoding="utf-8"))
    print("PASS: legacy PDF viewer evaluation and XFA explicitly disabled.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
