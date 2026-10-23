#!/usr/bin/env python3
"""Contrôle de l'ancienne fiche joueur : seule la redirection sûre subsiste."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "projets/sinjira/jeux/fracture-du-reseau-mere/fiche-joueur.html"
RULES = ROOT / "projets/sinjira/jeux/fracture-du-reseau-mere/regles.html"
MAIN_BLOB_SHA = "6398fb058eb938569623219d994ec7e3c8bbab67"


def validate_page(html: str) -> list[str]:
    errors = []
    for item in (
        '<meta name="robots" content="noindex,nofollow,noarchive">',
        '<meta http-equiv="refresh" content="0; url=regles.html">',
        'href="https://www.benoitcantin.com/projets/sinjira/jeux/fracture-du-reseau-mere/regles.html"',
        '<a class="btn btn-primary" href="regles.html">',
    ):
        if item not in html:
            errors.append("Ancienne fiche joueur : redirection ou noindex absent: " + item)
    if re.search(r'<form\b|data-novel-comments|data-reader-controls', html, re.IGNORECASE):
        errors.append("Ancienne fiche joueur : fonctionnalité active inattendue")
    return errors


def main() -> list[str]:
    errors = []
    if not PAGE.is_file() or not RULES.is_file():
        return ["Ancienne fiche ou règles officielles absentes"]
    raw = PAGE.read_bytes()
    observed = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    if observed != MAIN_BLOB_SHA:
        errors.append("La redirection héritée ne correspond plus au blob validé de main.")
    errors.extend(validate_page(raw.decode("utf-8")))
    return errors


def self_test() -> list[str]:
    errors = []
    page = PAGE.read_text(encoding="utf-8")
    if validate_page(page):
        errors.append("Auto-test positif de la redirection de main invalide")
    changed = page.replace('content="0; url=regles.html"', 'content="0; url=/compte/"')
    if not validate_page(changed):
        errors.append("Le test n'a pas détecté la redirection dangereuse")
    changed = page.replace('noindex,nofollow,noarchive', 'index,follow')
    if not validate_page(changed):
        errors.append("Le test n'a pas détecté le référencement de la fiche obsolète")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    issues = self_test() if args.self_test else main()
    for issue in issues:
        print("ECHEC:", issue)
    if issues:
        raise SystemExit(1)
    print("OK : fiche héritée = blob exact de main, redirection vers règles, non indexable.")
