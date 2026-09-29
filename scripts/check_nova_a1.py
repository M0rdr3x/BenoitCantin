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

DOCUMENT_MANIFESTS = [
    "data/documents.json",
    "data/documents-word-only.json",
    "documents.json",
    "documents-word-only.json",
]

for rel in DOCUMENT_MANIFESTS:
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

manifest_path = NOVA / "data" / "sources.json"
try:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
except Exception as exc:
    manifest = {}
    errors.append(f"data/sources.json invalide ou absent: {exc}")

required_docs = {"corpus", "statuts", "programme"}
document_ids = set((manifest.get("documents") or {}).keys())
if not required_docs.issubset(document_ids):
    errors.append("data/sources.json: corpus/statuts/programme requis")

for doc_id, doc in (manifest.get("documents") or {}).items():
    parts = doc.get("parts") or []
    if not parts:
        errors.append(f"référence {doc_id}: aucune source")
    for part in parts:
        raw = part.get("path", "")
        expected = part.get("sha256", "")
        source = (NOVA / raw).resolve()
        try:
            source.relative_to(ROOT)
        except ValueError:
            errors.append(f"référence {doc_id}: chemin source hors dépôt: {raw}")
            continue
        if not source.is_file():
            errors.append(f"référence {doc_id}: source absente: {raw}")
            continue
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            errors.append(f"référence {doc_id}: SHA-256 invalide: {raw}")
        elif actual != expected:
            errors.append(f"référence {doc_id}: empreinte différente: {raw}")

for p in list(NOVA.rglob("*.html")) + list(NOVA.rglob("*.js")):
    if "node_modules" in p.parts or "vendor" in p.parts:
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    if "formspree.io" in low or "formsubmit.co" in low:
        errors.append(f"{p.relative_to(NOVA)}: fournisseur de formulaire externe encore référencé")
    if "10_formulaire_soutien_preadhesion_projet_nova.pdf" in low:
        errors.append(f"{p.relative_to(NOVA)}: référence à l'ancien PDF de préadhésion")

# Les identifiants de chantier ne doivent pas être exposés dans la couche publique active.
version_re = re.compile(r"\bA[12](?:\.\d+)?\b", re.I)
for p in NOVA.glob("*.html"):
    text = p.read_text(encoding="utf-8", errors="replace")
    public_markup = re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.I | re.S)
    public_markup = re.sub(r"<style\b[^>]*>.*?</style>", "", public_markup, flags=re.I | re.S)
    if version_re.search(public_markup):
        errors.append(f"{p.name}: numéro de version de chantier visible dans l'interface publique")

# La bibliothèque, les manifestes, les références et les fichiers de gouvernance
# servis dans le sous-site ne doivent eux-mêmes contenir aucun numéro de chantier.
active_public_files = [
    NOVA / "assets" / "documents.js",
    NOVA / "data" / "documents.json",
    NOVA / "data" / "documents-word-only.json",
    NOVA / "documents.json",
    NOVA / "documents-word-only.json",
    NOVA / "data" / "sources.json",
    NOVA / "document.html",
    NOVA / "README.md",
    NOVA / "DOCUMENT_CONTROL.md",
    NOVA / "SECURITY.md",
]
active_public_files.extend(sorted((NOVA / "official" / "reference").glob("*.md")))
for p in active_public_files:
    if not p.is_file():
        errors.append(f"source publique active absente: {p.relative_to(NOVA)}")
        continue
    if version_re.search(p.read_text(encoding="utf-8", errors="replace")):
        errors.append(f"{p.relative_to(NOVA)}: numéro de version de chantier exposé dans une source publique active")

# Les anciens points d'entrée versionnés sont conservés par l'historique Git,
# mais ne doivent plus être servis par le site actif.
legacy_public_paths = [
    NOVA / "document-a1.html",
    NOVA / "STATUT_A1.md",
    NOVA / "data" / "a1-sources.json",
    NOVA / "official" / "a1",
]
for p in legacy_public_paths:
    if p.exists():
        errors.append(f"ancien chemin versionné encore servi: {p.relative_to(NOVA)}")

docjs = NOVA / "assets" / "documents.js"
if docjs.is_file():
    text = docjs.read_text(encoding="utf-8", errors="replace")
    for path in re.findall(r'"path"\s*:\s*"([^"]+)"', text):
        if not (NOVA / path).is_file():
            errors.append(f"assets/documents.js: fichier absent: {path}")

attr_re = re.compile(r'(?:href|src)=["\']([^"\'#]+)["\']', re.I)
for p in NOVA.glob("*.html"):
    text = p.read_text(encoding="utf-8", errors="replace")
    is_redirect = bool(re.search(r'<meta\b[^>]*http-equiv=["\']refresh["\'][^>]*>', text, flags=re.I))
    if is_redirect:
        robots = re.search(
            r'<meta\b(?=[^>]*name=["\']robots["\'])(?=[^>]*content=["\']([^"\']*)["\'])[^>]*>',
            text,
            flags=re.I,
        )
        robots_value = robots.group(1).lower() if robots else ""
        if "noindex" not in robots_value:
            errors.append(f"{p.name}: redirection publique sans noindex")
    else:
        if 'portal-return-benoit' not in text:
            errors.append(f"{p.name}: fallback de navigation globale vers Benoit Cantin absent")
        main_count = len(re.findall(r"<main\b", text, flags=re.I))
        h1_count = len(re.findall(r"<h1\b", text, flags=re.I))
        if main_count != 1:
            errors.append(f"{p.name}: exactement un <main> attendu, trouvé {main_count}")
        if h1_count != 1:
            errors.append(f"{p.name}: exactement un H1 attendu, trouvé {h1_count}")
        if not re.search(r'<main\b(?=[^>]*id=["\']contenu["\'])[^>]*>', text, flags=re.I):
            errors.append(f"{p.name}: landmark principal #contenu absent")
        if not re.search(
            r'<a\b(?=[^>]*class=["\'][^"\']*\bskip-link\b[^"\']*["\'])(?=[^>]*href=["\']#contenu["\'])[^>]*>',
            text,
            flags=re.I,
        ):
            errors.append(f"{p.name}: lien d’évitement vers #contenu absent")
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

required_pages = {
    "index.html": "https://www.benoitcantin.com/projets/projet-nova/",
    "documents.html": "document.html?doc=corpus",
    "programme.html": "document.html?doc=programme",
    "constitution.html": "document.html?doc=corpus",
    "code-conduite.html": "document.html?doc=statuts",
    "registre-conformite.html": "document.html?doc=corpus",
    "finances.html": "document.html?doc=finances",
    "document.html": "data/sources.json",
}
for rel, needle in required_pages.items():
    f = NOVA / rel
    if not f.is_file():
        errors.append(f"page publique absente: {rel}")
        continue
    text = f.read_text(encoding="utf-8", errors="replace")
    if needle not in text:
        errors.append(f"{rel}: marqueur public absent: {needle}")

constitution = NOVA / "constitution.html"
if constitution.is_file() and "noindex" in constitution.read_text(encoding="utf-8", errors="replace").lower():
    errors.append("constitution.html: la page constitutionnelle publique ne doit pas être noindex")

nova_runtime = NOVA / "script.js"
if not nova_runtime.is_file():
    errors.append("script.js Nova absent")
else:
    runtime_text = nova_runtime.read_text(encoding="utf-8", errors="replace")
    for marker in (
        "data-portal-global-nav",
        "Navigation générale du portail",
        "Navigation de Projet Nova",
        "/projets/sinjira/",
        "/projets/projet-nova/",
        "/a-propos.html",
        "/compte/",
        "/assets/js/v19-session.js?v=25.0.0",
    ):
        if marker not in runtime_text:
            errors.append(f"script.js Nova: navigation globale incomplète: {marker}")

portal_css = NOVA / "assets" / "portal-return.css"
if not portal_css.is_file():
    errors.append("assets/portal-return.css absent")
else:
    portal_css_text = portal_css.read_text(encoding="utf-8", errors="replace")
    for marker in (".portal-global-nav", ".portal-global-links", ".portal-global-account"):
        if marker not in portal_css_text:
            errors.append(f"portal-return.css: style navigation globale absent: {marker}")


# Cache public Nova — toute page active utilisant les assets principaux doit rester sur V25.
for page in NOVA.glob("*.html"):
    page_text = page.read_text(encoding="utf-8", errors="replace")
    is_redirect = bool(re.search(r'<meta\\b[^>]*http-equiv=["\\']refresh["\\'][^>]*>', page_text, flags=re.I))
    if is_redirect:
        continue
    for asset in ("styles.css", "script.js"):
        versions = re.findall(rf'{re.escape(asset)}\\?v=([^"\\'\\s<>]+)', page_text, flags=re.I)
        for version in versions:
            if version != "25":
                errors.append(f"{page.name}: cache Nova obsolète pour {asset}: {version}")

# Visionneuse PDF — contrat CSP, indexation et cohérence publique.
viewer = NOVA / "visionneuse.html"
if not viewer.is_file():
    errors.append("visionneuse.html absente")
else:
    viewer_text = viewer.read_text(encoding="utf-8", errors="replace")
    viewer_low = viewer_text.lower()
    if "cdnjs.cloudflare.com" in viewer_low:
        errors.append("visionneuse.html: CDN cdnjs interdit par la CSP publique")
    for marker in (
        "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js",
        "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js",
        'styles.css?v=25',
        'script.js?v=25',
        'data-ai-transparency',
        '/assets/js/site-personality-v25.js?v=25.0.0',
    ):
        if marker not in viewer_text:
            errors.append(f"visionneuse.html: contrat public absent: {marker}")
    robots_match = re.search(
        r'<meta\\b(?=[^>]*name=["\\']robots["\\'])(?=[^>]*content=["\\']([^"\\']*)["\\'])[^>]*>',
        viewer_text,
        flags=re.I,
    )
    robots_value = robots_match.group(1).lower() if robots_match else ""
    if "noindex" not in robots_value:
        errors.append("visionneuse.html: page utilitaire dynamique sans noindex")

netlify = ROOT / "netlify.toml"
if not netlify.is_file():
    errors.append("netlify.toml absent")
else:
    netlify_text = netlify.read_text(encoding="utf-8", errors="replace")
    if "https://cdn.jsdelivr.net" not in netlify_text:
        errors.append("netlify.toml: cdn.jsdelivr.net absent de la CSP alors que la visionneuse PDF l’utilise")

for rel in ["SECURITY.md", "DOCUMENT_CONTROL.md"]:
    if not (NOVA / rel).is_file():
        errors.append(f"gouvernance documentaire absente: {rel}")

if errors:
    print("PROJET NOVA — FAIL")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("PROJET NOVA — PASS")