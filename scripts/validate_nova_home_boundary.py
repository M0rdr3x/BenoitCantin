#!/usr/bin/env python3
"""Empêche la réapparition de NOVA sur l'accueil public après son retrait.

Contrôle des liens/ressources HTML (sans requêtes réseau et sans besoin
de publier le sous-site NOVA). Les manifestes et contrôles documentaires
historiques restent vérifiés séparément par check_nova_a1.py.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"
BLOCKED = ("/projets/projet-nova", "/assets/media/nova-logo.webp")


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for attr, value in attrs:
            if value is None:
                continue
            if attr.lower() in {"href", "src", "poster", "action", "formaction"}:
                self.urls.append(value)
            elif attr.lower() == "srcset":
                self.urls.extend(piece.strip().split()[0] for piece in value.split(",") if piece.strip())


def check_home(html: str) -> list[str]:
    parser = References()
    parser.feed(html)
    parser.close()
    errors: list[str] = []
    links = [unquote(value).lower().split("?", 1)[0].split("#", 1)[0]
             for value in parser.urls]
    if not any(value.endswith("/projets/sinjira/") for value in links):
        errors.append("accueil: lien principal SINJIRA absent")
    for value in links:
        if any(value.startswith(item) or item in value for item in BLOCKED):
            errors.append("accueil: chemin public du projet NOVA retiré encore référencé")
            break
    return errors


def self_test() -> None:
    safe = '<a href="/projets/sinjira/">SINJIRA</a>'
    assert check_home(safe) == []
    assert check_home('<!-- <a href="/projets/projet-nova/">ancien</a> -->' + safe) == []
    malicious = (
        '<a href="/projets/projet-nova/">Nova</a>',
        '<a href="/projets/projet-nova">Nova</a>',
        '<a href="/projets/%70rojet-nova/">Nova</a>',
        '<img src="/assets/media/nova-logo.webp">',
        '<img srcset="/assets/media/nova-logo.webp 1x">',
        '<a href="https://benoitcantin.com/projets/projet-nova/">Nova</a>',
        '<form action="/projets/projet-nova/index.html"></form>',
        '<video poster="/assets/media/nova-logo.webp"></video>',
        '<a href="/PROJETS/PROJET-NOVA/">Nova</a>',
        '<a href="/projets/sinjira/"><img src="/assets/media/nova-logo.webp"></a>',
    )
    for idx, case in enumerate(malicious, 1):
        errors = check_home(safe + case)
        assert any("NOVA retiré" in error for error in errors), f"Régression NOVA #{idx}"
    assert check_home('<a href="/">Accueil</a>'), "L'accès SINJIRA absent doit échouer"
    print(f"OK : {len(malicious)} réintroductions publiques NOVA refusées; SINJIRA obligatoire.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not HOME.is_file() or HOME.is_symlink():
        print("ÉCHEC: accueil public absent ou lien symbolique")
        return 1
    try:
        html = HOME.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError):
        print("ÉCHEC: accueil public illisible")
        return 1
    errors = check_home(html)
    for error in errors:
        print("ÉCHEC: " + error)
    if errors:
        return 1
    print("OK : page d'accueil centrée sur SINJIRA, sans ressource ni lien NOVA retiré.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
