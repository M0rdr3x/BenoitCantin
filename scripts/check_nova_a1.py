#!/usr/bin/env python3
from __future__ import annotations

import hashlib
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

# 1) Les anciens manifestes PDF doivent rester cohérents tant que les archives sont publiées.
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

# 2) Manifeste A1 et intégrité SHA-256 des sources officielles.
a1_manifest = NOVA / "data" / "a1-sources.json"
try:
    a1 = json.loads(a1_manifest.read_text(encoding="utf-8"))
except Exception as exc:
    a1 = {}
    errors.append(f"data/a1-sources.json invalide ou absent: {exc}")

required_docs = {"corpus", "statuts", "programme"}
if set((a1.get("documents") or {}).keys()) != required_docs:
    errors.append("data/a1-sources.json: corpus/statuts/programme requis")

for doc_id, doc in (a1.get("documents") or {}).items():
    parts = doc.get("parts") or []
    if not parts:
        errors.append(f"A1 {doc_id}: aucune source")
    for part in parts:
        raw = part.get("path", "")
        expected = part.get("sha256", "")
        source = (NOVA / raw).resolve()
        try:
            source.relative_to(ROOT)
        except ValueError:
            errors.append(f"A1 {doc_id}: chemin source hors dépôt: {raw}")
            continue
        if not source.is_file():
            errors.append(f"A1 {doc_id}: source absente: {raw}")
            continue
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            errors.append(f"A1 {doc_id}: SHA-256 invalide dans le manifeste: {raw}")
        elif actual != expected:
            errors.append(f"A1 {doc_id}: empreinte différente: {raw}")

# 3) Aucun fournisseur externe de formulaire politique dans le code public actif.
for p in list(NOVA.rglob("*.html")) + list(NOVA.rglob("*.js")):
    # Les bibliothèques tierces empaquetées peuvent contenir des chaînes sans être des formulaires Nova.
    if "node_modules" in p.parts or "vendor" in p.parts:
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    if "formspree.io" in low or "formsubmit.co" in low:
        errors.append(f"{p.relative_to(NOVA)}: fournisseur de formulaire externe encore référencé")
    if "10_formulaire_soutien_preadhesion_projet_nova.pdf" in low:
        errors.append(f"{p.relative_to(NOVA)}: référence à l'ancien PDF de préadhésion")

# 4) documents.js ne doit pas référencer un PDF inexistant.
docjs = NOVA / "assets" / "documents.js"
if docjs.is_file():
    text = docjs.read_text(encoding="utf-8", errors="replace")
    for path in re.findall(r'"path"\s*:\s*"([^"]+)"', text):
        if not (NOVA / path).is_file():
            errors.append(f"assets/documents.js: fichier absent: {path}")

# 5) Liens et ressources locaux dans les HTML de premier niveau.
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
        try:
            target.relative_to(ROOT)
        except ValueError:
            errors.append(f"{p.name}: chemin sortant invalide: {raw}")
            continue
        if not target.exists():
            errors.append(f"{p.name}: cible locale absente: {raw}")

# 6) Pages A1 obligatoires et liens de priorité documentaire.
required_pages = {
    "index.html": "https://www.benoitcantin.com/projets/projet-nova/",
    "documents.html": "document-a1.html?doc=corpus",
    "programme.html": "document-a1.html?doc=programme",
    "constitution.html": "document-a1.html?doc=corpus",
    "code-conduite.html": "document-a1.html?doc=statuts",
    "registre-conformite.html": "official/a1/",
    "document-a1.html": "data/a1-sources.json",
}
for rel, needle in required_pages.items():
    f = NOVA / rel
    if not f.is_file():
        errors.append(f"page A1 absente: {rel}")
        continue
    text = f.read_text(encoding="utf-8", errors="replace")
    if needle not in text:
        errors.append(f"{rel}: marqueur A1 absent: {needle}")

constitution = NOVA / "constitution.html"
if constitution.is_file() and "noindex" in constitution.read_text(encoding="utf-8", errors="replace").lower():
    errors.append("constitution.html: la page A1 publique ne doit plus être noindex")

# 7) Gouvernance documentaire minimale.
for rel in ["SECURITY.md", "DOCUMENT_CONTROL.md", "STATUT_A1.md"]:
    if not (NOVA / rel).is_file():
        errors.append(f"gouvernance A1 absente: {rel}")

if errors:
    print("NOVA A1 — FAIL")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("NOVA A1 — PASS")
