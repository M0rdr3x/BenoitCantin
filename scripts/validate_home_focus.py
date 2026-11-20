#!/usr/bin/env python3
"""Contrat de l'accueil personnel : SINJIRA est l'unique projet mis en avant.

Les pages Nova historiques demeurent disponibles dans le dépôt pour archivage;
leur présence dans le projet ne doit plus être requise sur la page d'accueil.
"""
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"
STYLE = ROOT / "assets/css/home-sinjira-only-v1.css"

FEATURE_LINKS = {
    "/projets/sinjira/romans/",
    "/projets/sinjira/registre/",
    "/projets/sinjira/jeux/",
    "/projets/sinjira/communaute/",
}


class HomeStructure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.project_circles = []
        self.feature_cards = []
        self.navigation = []
        self.images = []
        self.css = []
        self._cosmos = 0
        self._stack = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        classes = set(data.get("class", "").split())
        if tag == "div" and "home-cosmos" in classes:
            self._cosmos += 1
        if tag == "a" and self._cosmos and "sinjira-orbit" in classes:
            self.project_circles.append(data.get("href"))
        if tag == "a" and "home-project" in classes:
            self.feature_cards.append(data.get("href"))
        if tag == "a":
            self.navigation.append(data.get("href"))
        if tag == "img":
            self.images.append(data.get("src"))
        if tag == "link" and data.get("rel") == "stylesheet":
            self.css.append(data.get("href"))
        # HTMLParser n'est pas un parseur de DOM complet; les sections de
        # l'orbite sont contrôlées directement par une sous-chaîne plus bas.


def main() -> int:
    errors = []
    if not HOME.is_file() or not STYLE.is_file():
        print("ECHEC: accueil ou feuille de style SINJIRA manquants.")
        return 1

    home = HOME.read_text("utf-8")
    css = STYLE.read_text("utf-8")
    parser = HomeStructure()
    parser.feed(home)

    if 'class="home-page home-sinjira-only"' not in home:
        errors.append("Classe d'isolation de la nouvelle page manquante.")
    if parser.project_circles != ["/projets/sinjira/"]:
        errors.append("Le cercle doit contenir un seul lien, vers SINJIRA.")
    if len(parser.feature_cards) != 4 or set(parser.feature_cards) != FEATURE_LINKS:
        errors.append("Les 4 services SINJIRA doivent figurer sous le cercle.")
    if "nova" in home.casefold() or "boussole" in home.casefold():
        errors.append("Aucune présentation Nova/boussole ne doit rester sur l'accueil.")
    if any((url or "").startswith("/projets/projet-nova") for url in parser.navigation):
        errors.append("Un lien Nova est encore affiché sur l'accueil.")
    if not any("home-sinjira-only-v1.css" in href for href in parser.css):
        errors.append("Styles SINJIRA de l'accueil absents.")
    if "/assets/media/sinjira-emblem.webp" not in parser.images:
        errors.append("Emblème SINJIRA officiel absent du cercle.")
    for key in (".home-sinjira-cosmos", ".sinjira-orbit", "@media(max-width:700px)",
                ":focus-visible", "prefers-reduced-motion"):
        if key not in css:
            errors.append(f"Ergonomie/accessibilité CSS manquante: {key}")
    if ".home-sinjira-only" not in css:
        errors.append("CSS global non isolé sous home-sinjira-only.")

    if errors:
        print("ECHEC accueil SINJIRA: " + str(len(errors)) + " problème(s)")
        for error in errors:
            print("- " + error)
        return 1
    print("OK: SINJIRA seul dans le cercle, 4 services associés, aucune porte Nova, styles mobile et clavier.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
