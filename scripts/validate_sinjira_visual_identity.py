#!/usr/bin/env python3
"""Identité SINJIRA : aucun pictogramme cible et logos légers cohérents.

On ne remplace pas les couvertures de livres, les illustrations de jeu ou
les images du Registre : seules les marques/icônes globales sont concernées.
"""
from pathlib import Path
import base64
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "assets/icons/sinjira-favicon.png"
OFFICIAL = ROOT / "assets/icons/sinjira-officiel-20261120.png"
HOME = ROOT / "index.html"
SVG = ROOT / "assets/icons/sinjira.svg"
SMALL_BRAND_PAGES = [
    "projets/sinjira/index.html",
    "projets/sinjira/romans/index.html",
    "projets/sinjira/registre/index.html",
    "projets/sinjira/jeux/index.html",
    "projets/sinjira/communaute/index.html",
    "projets/sinjira/codex/index.html",
    "projets/sinjira/marche/index.html",
    "compte/index.html",
    "compte/bibliotheque.html",
    "compte/liseuse.html",
]


def validate() -> list[str]:
    problems = []
    data = LOGO.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        problems.append("Logo officiel SINJIRA : le fichier n'est pas un PNG valide.")
    elif len(data) < 1000 or len(data) > 125_000:
        problems.append("Logo SINJIRA : dimensions binaires/poids incohérents.")
    else:
        width, height = struct.unpack(">II", data[16:24])
        if min(width, height) < 128 or max(width, height) > 512:
            problems.append(f"Logo SINJIRA : résolution inattendue {width} x {height}.")

    html = HOME.read_text("utf-8")
    orbit = re.search(r'<a\s+class="sinjira-orbit"[^>]*>[\s\S]*?</a>', html)
    if not orbit or 'src="/assets/icons/sinjira-officiel-20261120.png"' not in orbit.group(0):
        problems.append("L'accueil n'utilise pas le logo SINJIRA dans son cercle central.")
    if not OFFICIAL.exists() or OFFICIAL.read_bytes() != data:
        problems.append("L'icône officielle versionnée diverge de la marque globale.")
    if 'src="/assets/icons/sinjira.svg"' in html:
        problems.append("La cible SVG historique est toujours montrée sur l'accueil.")

    svg = SVG.read_text("utf-8")
    if "<image" not in svg or "data:image/png;base64," not in svg:
        problems.append("Le SVG historique ne reprend pas la vraie marque.")
    if "Anneaux concentriques" in svg or "M64 12v104M12 64h104" in svg:
        problems.append("Le dessin en cible est toujours présent dans le SVG.")
    if '<title id="sinjira-brand-title">Emblème SINJIRA</title>' not in svg:
        problems.append("Le SVG n'a pas de nom accessible.")
    embedded = re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', svg)
    if embedded:
        try:
            if base64.b64decode(embedded.group(1), validate=True) != data:
                problems.append("Le SVG ne contient pas le logo PNG source exact.")
        except ValueError:
            problems.append("Le SVG contient des données PNG invalides.")

    # Toutes les pages SINJIRA et les écrans du compte doivent désormais
    # afficher la même icône compacte lorsqu'il s'agit du logo de marque.
    # Le fichier haute définition reste archivé mais ne doit plus être
    # téléchargé comme une petite icône de 47–58 pixels.
    for folder in (ROOT / "projets/sinjira", ROOT / "compte"):
        for page in folder.rglob("*.html"):
            text = page.read_text("utf-8")
            if "sinjira-emblem.webp" in text:
                problems.append(f"{page.relative_to(ROOT)} : ancienne image de marque lourde.")

    for relative in SMALL_BRAND_PAGES:
        file = ROOT / relative
        if not file.is_file():
            problems.append(f"Page SINJIRA manquante : {relative}")
            continue
        text = file.read_text("utf-8")
        if "sinjira-emblem.webp" in text:
            problems.append(f"{relative} : image de marque trop lourde encore chargée.")
        if "/assets/icons/sinjira-favicon.png" not in text:
            problems.append(f"{relative} : logo harmonisé absent.")
    return problems


def main():
    errors = validate()
    if errors:
        print(f"ÉCHEC identité SINJIRA : {len(errors)} erreur(s).")
        for error in errors:
            print("- " + error)
        return 1
    print("OK : centre SINJIRA sans cible, SVG harmonisé et 10 pages utilisant le logo léger.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
