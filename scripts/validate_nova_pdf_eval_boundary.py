#!/usr/bin/env python3
"""Gate the local-only NOVA viewer, fail closed until reviewed vendoring."""
from __future__ import annotations
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from validate_pdfjs_vendored_runtime import verify_state

VIEWER=Path("projets/projet-nova/visionneuse.html")
MODULE=Path("projets/projet-nova/assets/nova-pdf-viewer.mjs")
DOCUMENTS=Path("projets/projet-nova/assets/documents.js")
EXPECTED_SCRIPTS=["assets/documents.js","script.js?v=26.1.0","assets/nova-pdf-viewer.mjs"]
FILES={"resume":"01_Resume_Officiel_1_Page_Projet_Nova.pdf","depliant":"02_Depliant_Public_4_Pages_Projet_Nova.pdf","livre-court":"03_Livre_Nova_Version_Courte.pdf","livre-complet":"04_Livre_Nova_Complet.pdf","manifeste":"05_Manifeste_Officiel_Projet_Nova.pdf","faq-citoyenne":"06_FAQ_Citoyenne_Officielle_Projet_Nova.pdf","programme":"07_Programme_Electoral_Complet_Projet_Nova.pdf","code-conduite":"08_Code_de_Conduite_Gouvernance_Nova.pdf","dossier-presse":"09_Dossier_de_Presse_Projet_Nova.pdf","charte-visuelle":"11_Charte_Visuelle_Projet_Nova.pdf","resume-executif":"12_Resume_Executif_Officiel_Systeme_Nova.pdf"}

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts=[]
        self.inline=False
    def handle_starttag(self,tag,attrs):
        if tag=="script":
            a=dict(attrs)
            if len(a)!=len(attrs) or not a.get("src"):
                self.inline=True
            self.scripts.append(a.get("src"))

def validate(source,module,documents,enabled=False):
    p=Scripts()
    p.feed(source)
    p.close()
    if p.inline or p.scripts!=EXPECTED_SCRIPTS or "cdnjs.cloudflare.com" in source:
        raise ValueError("Unexpected viewer script")
    flag="true" if enabled else "false"
    if module.count(f"const RUNTIME_ENABLED = {flag};")!=1:
        raise ValueError("Runtime activation does not match verified publication")
    if re.search(r"https?://|//cdnjs|pdfjsLib|\.innerHTML\b|\.outerHTML\b|insertAdjacentHTML",module):
        raise ValueError("Unreviewed viewer execution or HTML sink")
    for token in ("Object.hasOwn(PUBLIC_FILES,d.id)", "d.path !== 'documents/' + d.file",
                  "url.origin !== location.origin","enableXfa:false","useWasm:false","isEvalSupported:false",
                  "worker.port instanceof Worker","width*height>10000000",
                  "engine.version!=='6.5.438'","await import('./pdfjs-6.5.438/build/pdf.mjs')"):
        if module.count(token)!=1:
            raise ValueError("Viewer security invariant absent")
    raw=re.fullmatch(r"window\.NOVA_DOCUMENTS\s*=\s*(\[.*\]);\s*",documents,re.S)
    policy=re.search(r"const PUBLIC_FILES = Object\.freeze\((\{.*?\})\);",module,re.S)
    if not raw or not policy or json.loads(policy[1])!=FILES:
        raise ValueError("Unexpected document policy")
    entries=json.loads(raw[1])
    if len(entries)!=len(FILES) or {d["id"]:d["file"] for d in entries}!=FILES:
        raise ValueError("Public document catalog changed")
    if any(d["path"]!="documents/"+d["file"] or d["format"]!="PDF" for d in entries):
        raise ValueError("Unreviewed document path")

class Tests(unittest.TestCase):
    def test_mutations(self):
        root=Path(__file__).resolve().parents[1]
        source,module,docs=( (root/p).read_text("utf-8") for p in (VIEWER,MODULE,DOCUMENTS))
        validate(source,module,docs)
        for replacement in (
            ("const RUNTIME_ENABLED = false;","const RUNTIME_ENABLED = true;"),
            ("enableXfa:false","enableXfa:true"),("useWasm:false","useWasm:true"),
            ("Object.hasOwn(PUBLIC_FILES,d.id)","true"),("url.origin !== location.origin","false"),
            ("width*height>10000000","false"),("engine.version!=='6.5.438'","false"),
            ("pages.replaceChildren(holder)","pages.innerHTML='unsafe'"),
        ):
            with self.subTest(replacement=replacement),self.assertRaises(ValueError):
                validate(source,module.replace(*replacement),docs)
        with self.assertRaises(ValueError):
            validate(source+'<script src="https://example.invalid/a.js"></script>',module,docs)
        with self.assertRaises(ValueError):
            validate(source,module,docs.replace("documents/01_","../01_",1))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--root",type=Path)
    a=p.parse_args()
    if a.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    if a.root is None: p.error("Build root required")
    records=verify_state(a.root)
    validate(*((a.root/path).read_text("utf-8") for path in (VIEWER,MODULE,DOCUMENTS)),enabled=bool(records))
    print("PASS: no legacy CDN; exact local public PDF catalog; runtime state verified.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
