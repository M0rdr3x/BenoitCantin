#!/usr/bin/env python3
"""Vérifier l'ergonomie du menu SINJIRA sur les pages publiques et du compte.

Ne lit aucun secret ni contenu privé : analyse seulement les ressources Git.
Les pages Nova historiques, les immersions sans menu et les redirections
ne doivent pas être modifiées pour se conformer à ce contrat.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets/css/site-ux-sinjira-v1.css"
SITE_JS = ROOT / "assets/js/site.js"
EXPECTED = (
    "/", "/projets/sinjira/", "/projets/sinjira/romans/",
    "/projets/sinjira/registre/", "/projets/sinjira/communaute/", "/compte/",
)
REQUIRED = (
    "index.html", "compte/index.html", "compte/connexion.html",
    "compte/inscription.html", "compte/mes-lectures.html",
    "compte/communaute.html", "compte/securite.html",
    "projets/sinjira/index.html", "projets/sinjira/romans/index.html",
    "projets/sinjira/registre/index.html", "projets/sinjira/jeux/index.html",
    "projets/sinjira/communaute/index.html",
)


class NavLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_navigation = 0
        self.links = []
        self.navs = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "nav" and "data-main-nav" in attributes:
            self.in_navigation += 1
            self.navs += 1
        elif tag == "a" and self.in_navigation:
            self.links.append(attributes.get("href"))

    def handle_endtag(self, tag):
        if tag == "nav" and self.in_navigation:
            self.in_navigation -= 1


def candidate_pages():
    pages = [
        ROOT / "index.html",
        ROOT / "a-propos.html",
        ROOT / "contact.html",
    ]
    pages += list(ROOT.glob("compte/**/*.html"))
    pages += list(ROOT.glob("projets/sinjira/**/*.html"))
    pages += [
        ROOT / name for name in (
            "confidentialite.html", "avis-legal.html",
            "gouvernance-vie-privee.html", "transparence-ia.html",
            "univers.html", "404.html", "merci.html", "offline.html",
        )
    ]
    return sorted(set(pages))


def check():
    problems = []
    count = 0
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            problems.append(f"Fichier critique introuvable : {rel}")
    for path in candidate_pages():
        if not path.is_file():
            continue
        text = path.read_text("utf-8", errors="replace")
        parser = NavLinks()
        parser.feed(text)
        if not parser.navs:
            # Lecture immersive et stubs de redirection sans menu global.
            continue
        relative = str(path.relative_to(ROOT))
        count += 1
        if parser.navs != 1 or tuple(parser.links) != EXPECTED:
            problems.append(f"{relative}: destinations du menu non homogènes: {parser.links}")
        if 'data-sinjira-ux="v1"' not in text:
            problems.append(f"{relative}: configuration de l'interface mobile absente")
        if "/assets/css/site-ux-sinjira-v1.css?v=1.0.0" not in text:
            problems.append(f"{relative}: feuille de style adaptée absente")
        if "Projet Nova" in text[text.find("data-main-nav"):text.find("</nav>", text.find("data-main-nav"))]:
            problems.append(f"{relative}: ancien lien Nova toujours présent dans le menu")
    if count < 50:
        problems.append(f"Seulement {count} pages équipées; couverture suspecte")
    home = (ROOT / "index.html").read_text("utf-8")
    if len(re.findall(r"<link\b[^>]*rel=[\"']stylesheet[\"']", home, re.I)) > 8:
        problems.append("Budget styles de l'accueil dépassé")
    dashboard = (ROOT / "compte/index.html").read_text("utf-8")
    for href in (
        "mes-lectures.html", "bibliotheque.html", "messages.html",
        "notifications.html", "mon-personnage.html",
    ):
        if not re.search(r'<a href="' + re.escape(href) + r'">', dashboard):
            problems.append(f"Compte: action rapide absente: {href}")
    if 'aria-labelledby="account-quick-title"' not in dashboard:
        problems.append("Compte: raccourcis sans titre accessible")
    if not CSS.is_file() or not SITE_JS.is_file():
        problems.append("Couche CSS/JS SINJIRA introuvable")
    else:
        css = CSS.read_text("utf-8")
        js = SITE_JS.read_text("utf-8")
        for token in (
            '@media(max-width:1020px)', 'max-height:calc(100dvh - 74px)',
            '.main-nav.open', 'min-height:48px',
            '.account-nav-scroll', '.account-quick-actions',
            ':focus-visible', 'prefers-reduced-motion:reduce',
        ):
            if token not in css:
                problems.append("CSS ergonomique: protection manquante " + token)
        if "(min-width: 1021px)" not in js or "focusin" not in js:
            problems.append("Menu JavaScript: tablette ou sortie du focus non traitée")
    return count, problems


def main():
    count, problems = check()
    if problems:
        print(f"ÉCHEC ergonomie SINJIRA ({count} pages, {len(problems)} erreur(s))")
        for problem in problems:
            print("- " + problem)
        return 1
    print(f"OK : {count} pages, navigation 6 destinations, contrôle mobile/tablette, "
          "raccourcis et accessibilité statique conformes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
