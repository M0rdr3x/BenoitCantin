#!/usr/bin/env python3
"""Contrôles statiques de la liseuse SINJIRA et des catégories de bibliothèque.

Test de garde-fous : les essais fonctionnels doivent aussi vérifier l'authentification
avec des comptes de test autorisé/non autorisé avant publication.
"""
from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class HtmlInfo(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.script_paths: set[str] = set()
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = dict(attrs)
        if d.get("id"):
            self.ids.add(str(d["id"]))
        if tag == "a" and d.get("href"):
            self.links.append(str(d["href"]))
        if tag == "script" and d.get("src"):
            self.script_paths.add(str(d["src"]).split("?", 1)[0])

def html(path: str) -> HtmlInfo:
    obj = HtmlInfo()
    obj.feed((ROOT / path).read_text("utf-8"))
    return obj

def validate() -> list[str]:
    problems: list[str] = []
    pages = {
        "compte/bibliotheque.html": "Vue d’ensemble",
        "compte/bibliotheque-romans.html": "Romans",
        "compte/bibliotheque-jeux.html": "Jeux",
        "compte/bibliotheque-ressources.html": "Ressources",
    }
    for path in pages:
        if not (ROOT / path).is_file():
            problems.append(f"Page absente: {path}")
            continue
        obj = html(path)
        for target in pages:
            name = target.rsplit("/", 1)[-1]
            if name not in [link.split("#", 1)[0].split("?", 1)[0] for link in obj.links]:
                problems.append(f"Catégorie sans navigation {name}: {path}")
        if path != "compte/bibliotheque.html":
            content=(ROOT / path).read_text("utf-8")
            if "noindex,nofollow,noarchive" not in content:
                problems.append(f"Référencement privé non bloqué: {path}")
    if not (ROOT / "compte/liseuse.html").is_file():
        return problems + ["Page de liseuse absente"]
    ui=html("compte/liseuse.html")
    expected_ids = (
        "reader-chapters","reader-theme","reader-size","reader-zoom",
        "reader-previous","reader-next","reader-page","reader-range","reader-percent",
        "reader-bar","reader-canvas","reader-text","reader-viewer",
        "reader-loading","reader-content","reader-status","reader-total",
        "reader-error","reader-native-demo","reader-demo-link","reader-download-demo",
        "reader-edition","reader-privacy","reader-mode","reader-chapter-label",
    )
    for element in expected_ids:
        if element not in ui.ids:
            problems.append(f"Contrôle liseuse absent : #{element}")
    if "/assets/js/sinjira-liseuse-v26.js" not in ui.script_paths:
        problems.append("Liseuse non branchée au contrôleur JavaScript")
    reader=(ROOT / "assets/js/sinjira-liseuse-v26.js").read_text("utf-8")
    required = (
        "requireUser(", "get-novel-file-url", "functions.invoke(",
        "new Uint8Array(await response.arrayBuffer())",
        "state.pdf.numPages", "reader-chapters", "reader-text",
        "reader-theme", "reader-page", "sinjira_reader_library",
        "localStorage", "SIGNED_ORIGIN", "isFull", "referrerPolicy:'no-referrer'",
    )
    for needle in required:
        if needle not in reader:
            problems.append(f"Mécanisme liseuse absent : {needle}")
    forbidden = (
        "SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf",
        "537dbe86dad08c288d5f559707b888257c40ea6aadb89b5abfbbf9789e1825a6",
        "getPublicUrl(", ".from('user_entitlements').insert(",
        ".from('user_entitlements').upsert(",
    )
    for part in forbidden:
        if part in reader:
            problems.append("Fichier intégral ou privilège exposé en JavaScript : " + part[:35])
    for path in ("compte/liseuse.html", "compte/bibliotheque.html",
                 "compte/bibliotheque-romans.html",
                 "projets/sinjira/romans/index.html"):
        content=(ROOT / path).read_text("utf-8")
        if "liseuse.html?edition=integrale" not in content:
            problems.append(f"Pas de lien vers la lecture privée : {path}")
    if "get-novel-file-url" in (ROOT / "assets/js/sinjira-library-hub-v26.js").read_text("utf-8"):
        problems.append("La page de bibliothèque ne doit pas signer d'URL privée")
    return problems

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    problems=validate()
    if problems:
        for problem in problems:
            print("ÉCHEC : "+problem)
        return 1
    print("OK : navigation séparée, liseuse, session privée, progression et absence de contenu intégral public")
    if args.self_test:
        print("OK : vérification de garde-fous terminée")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
