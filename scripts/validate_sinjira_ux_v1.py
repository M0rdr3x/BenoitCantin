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
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "assets/css/site-ux-sinjira-v1.css"
SITE_JS = ROOT / "assets/js/site.js"
EXPECTED = (
    "/", "/projets/sinjira/", "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/", "/projets/sinjira/registre/",
    "/projets/sinjira/communaute/", "/compte/",
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
        self.stylesheets = []
        self.navs = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "nav" and "data-main-nav" in attributes:
            self.in_navigation += 1
            self.navs += 1
        elif tag == "a" and self.in_navigation:
            self.links.append(attributes.get("href"))
        elif tag == "link" and "stylesheet" in (attributes.get("rel") or "").lower().split():
            self.stylesheets.append(attributes.get("href") or "")

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


def is_approved_ux_stylesheet(href: str, page: str) -> bool:
    """Vérifie une URL CSS locale, avec chemin absolu ou relatif et cache versionné."""
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        return False
    if not re.fullmatch(r"v=[0-9]+(?:\.[0-9]+)*", parsed.query):
        return False
    return urljoin("/" + page, parsed.path) == "/assets/css/site-ux-sinjira-v1.css"


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
        # Accepter une nouvelle version de cache sans relâcher le chemin exact
        # du CSS ni la vérification d'un vrai élément <link rel=stylesheet>.
        if not any(is_approved_ux_stylesheet(href, relative)
                   for href in parser.stylesheets):
            problems.append(f"{relative}: feuille de style adaptée absente")
        boot = '/assets/js/sinjira-nav-boot-v2.js?v=2.0.0'
        if relative == "projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html":
            # Garde V44 : mode Web désactivé, liste fermée à deux scripts.
            # L'ajout d'un troisième script contournerait une protection volontaire.
            if boot in text:
                problems.append(f"{relative}: boot non approuvé sur mode Web suspendu")
            continue
        if text.count(boot) != 1:
            problems.append(f"{relative}: préchargement du menu absent ou dupliqué")
        else:
            head = text.split("</head>", 1)[0]
            if boot not in head:
                problems.append(f"{relative}: préchargement du menu en dehors du head")
            elif head.find(boot) > head.find("site-ux-sinjira-v1.css"):
                problems.append(f"{relative}: préchargement du menu après le CSS (risque CLS)")
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
            '.site-footer .footer-col a', 'min-height:44px',
            ':focus-visible', 'prefers-reduced-motion:reduce',
            'scroll-behavior:auto!important',
        ):
            if token not in css:
                problems.append("CSS ergonomique: protection manquante " + token)
        for token in (
            '.sinjira-account-nav-frame.is-scrollable',
            '.sinjira-account-nav-arrow',
            '.account-nav [hidden]',
        ):
            if token not in css:
                problems.append("Navigation horizontale du compte: CSS absent " + token)
        for token in (
            "Rubriques précédentes du compte",
            "Rubriques suivantes du compte",
            "accountScroll.scrollTo(",
            "revealCurrentTab()",
            "data-sinjira-account-scroll-ready",
        ):
            if token not in js:
                problems.append("Navigation horizontale du compte: JS absent " + token)
        # Un contrat sur toutes les pages équipées évite la dérive de cache
        # à mesure que le compte SINJIRA évolue.
        account_nav_pages = 0
        account_ux_pages = 0
        for account_page in sorted((ROOT / "compte").glob("*.html")):
            page = account_page.read_text("utf-8")
            if 'data-sinjira-ux="v1"' not in page:
                continue
            account_ux_pages += 1
            # Toutes les pages équipées utilisent le même runtime, y compris
            # les formulaires et les pages sans ruban horizontal.
            scripts = re.findall(
                r"""<script\b[^>]*\bsrc=["'][^"']*/site\.js\?v=([^"']+)["'][^>]*>""",
                page, re.I,
            )
            if scripts != ["24.4.105"]:
                rel = account_page.relative_to(ROOT)
                problems.append(f"{rel}: version site.js incorrecte ou dupliquée: {scripts}")
            if "account-nav-scroll" not in page:
                continue
            account_nav_pages += 1
            for version in (
                "site-ux-sinjira-v1.css?v=1.0.1",
                "site.js?v=24.4.105",
            ):
                if page.count(version) != 1:
                    rel = account_page.relative_to(ROOT)
                    problems.append(f"{rel}: ressource de navigation absente ou dupliquée: {version}")
        if account_ux_pages < 44:
            problems.append(f"Compte: couverture UX suspecte ({account_ux_pages}/44)")
        if account_nav_pages < 33:
            problems.append(f"Compte: couverture des menus suspecte ({account_nav_pages}/33)")
        if "data-sinjira-nav-ready" not in js:
            problems.append("Menu JavaScript: activation progressive absente")
        boot_path = ROOT / "assets/js/sinjira-nav-boot-v2.js"
        if not boot_path.is_file():
            problems.append("Script de préchargement SINJIRA absent")
        else:
            boot_js = boot_path.read_text("utf-8")
            for token in ("data-sinjira-nav-ready", "data-sinjira-nav-initialized", "DOMContentLoaded", "addEventListener('error'"):
                if token not in boot_js:
                    problems.append("Script de préchargement incomplet : " + token)
        if "data-sinjira-nav-initialized" not in js:
            problems.append("Menu JavaScript: accusé d'initialisation absent")
        if "html:not([data-sinjira-nav-ready])" not in css or "position:static" not in css:
            problems.append("Menu mobile: navigation sans JavaScript non prévue")
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
    print(f"OK : {count} pages, navigation 7 destinations, contrôle mobile/tablette, "
          "raccourcis et accessibilité statique conformes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
