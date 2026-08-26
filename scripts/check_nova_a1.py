#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets" / "projet-nova"
errors: list[str] = []

if not NOVA.is_dir():
    errors.append("dossier projets/projet-nova absent")

# Manifeste documentaire JSON.
for rel in ["data/documents.json", "data/documents-word-only.json", "documents.json", "documents-word-only.json"]:
    p = NOVA / rel
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{rel}: JSON invalide: {exc}")
        continue
    for slug, item in data.items():
        pdf = item.get("pdf")
        if pdf and not (NOVA / pdf).is_file():
            errors.append(f"{rel}: {slug} référence un PDF absent: {pdf}")

# Aucun formulaire externe public ni ancien mécanisme de préadhésion.
for p in NOVA.glob("*.html"):
    text = p.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    if "formspree.io" in low or "formsubmit.co" in low:
        errors.append(f"{p.name}: fournisseur de formulaire externe encore actif/référencé")
    if "10_formulaire_soutien_preadhesion_projet_nova.pdf" in low:
        errors.append(f"{p.name}: référence à l'ancien PDF de préadhésion")

# documents.js ne doit pas référencer un fichier inexistant.
docjs = NOVA / "assets" / "documents.js"
if docjs.is_file():
    text = docjs.read_text(encoding="utf-8", errors="replace")
    for path in re.findall(r'"path"\s*:\s*"([^"]+)"', text):
        if not (NOVA / path).is_file():
            errors.append(f"assets/documents.js: fichier absent: {path}")

# Liens / ressources locaux dans les HTML de premier niveau.
attr_re = re.compile(r'(?:href|src)=["\']([^"\'#]+)["\']', re.I)
for p in NOVA.glob("*.html"):
    text = p.read_text(encoding="utf-8", errors="replace")
    for raw in attr_re.findall(text):
        if raw.startswith(("http://", "https://", "mailto:", "tel:", "data:", "javascript:")):
            continue
        path = urlsplit(raw).path
        if not path or path.startswith("/"):
            continue
        target = (p.parent / path).resolve()
        # Le lien ../../index.html et les actifs du portail vivent hors NOVA mais dans ROOT.
        try:
            target.relative_to(ROOT)
        except ValueError:
            errors.append(f"{p.name}: chemin sortant invalide: {raw}")
            continue
        if not target.exists():
            errors.append(f"{p.name}: cible locale absente: {raw}")

# Canonique de l'accueil Nova et fichiers de gouvernance A1.
index = NOVA / "index.html"
if index.is_file() and "https://www.benoitcantin.com/projets/projet-nova/" not in index.read_text(encoding="utf-8"):
    errors.append("index.html: URL canonique Nova absente")
for rel in ["SECURITY.md", "DOCUMENT_CONTROL.md", "STATUT_A1.md"]:
    if not (NOVA / rel).is_file():
        errors.append(f"gouvernance A1 absente: {rel}")

if errors:
    print("NOVA A1 — FAIL")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("NOVA A1 — PASS")
