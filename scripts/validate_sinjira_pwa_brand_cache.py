#!/usr/bin/env python3
"""Vérifier la mise à jour du cache visuel SINJIRA sans toucher aux données privées."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "sw.js").read_text("utf-8")
errors = []
cache = re.search(r"const CACHE='([^']+)'", source)
if not cache or not re.search(r"-public-(?:[6-9]|[1-9][0-9]+)$",cache.group(1)):
    errors.append("Le cache public n'a pas été renouvelé pour la nouvelle identité.")
for asset in (
    "/assets/icons/sinjira-favicon.png",
    "/assets/css/home-sinjira-only-v1.css",
    "/assets/css/site-ux-sinjira-v1.css",
):
    if f"'{asset}'" not in source:
        errors.append(f"Actif de marque non précaché : {asset}")
    if not (ROOT / asset.lstrip("/")).is_file():
        errors.append(f"Actif inexistant : {asset}")
for forbidden in (
    "/assets/media/sinjira-emblem.webp",
    "/assets/media/nova-logo.webp",
    "'/projets/projet-nova/'",
):
    if forbidden in source:
        errors.append(f"Ressource non essentielle conservée dans le cache public : {forbidden}")
for security_guard in (
    "const privatePath=", "cache:'no-store'", "if(privatePath||r.headers.has('Authorization')",
    "const PUBLIC_DOCUMENTS=", "const PUBLIC_ASSET=",
    "isPublicDocument", "if(u.search)", "resp.redirected",
    "resp.status!==200", "'Set-Cookie'",
    "r.headers.has('Authorization')", "r.headers.has('Range')",
    "keys.filter(k=>k.startsWith('benoitcantin-')", "const liveAsset=",
):
    if security_guard not in source:
        errors.append(f"Protection de cache privée ou réseau absente : {security_guard}")
if errors:
    print("ÉCHEC cache SINJIRA :")
    for error in errors:
        print("- " + error)
    raise SystemExit(1)
print("OK : cache renouvelé, nouvelle marque précachée et données privées hors cache.")
