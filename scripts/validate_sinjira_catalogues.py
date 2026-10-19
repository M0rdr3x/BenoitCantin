#!/usr/bin/env python3
"""Contrat public des trois catalogues SINJIRA — sans réseau ni données privées."""
from __future__ import annotations

import argparse
import hashlib
import re
from shutil import copyfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.benoitcantin.com"
ROUTES = {
    "romans": "/projets/sinjira/romans/",
    "jeux": "/projets/sinjira/jeux/",
    "logiciels": "/projets/sinjira/logiciels/",
}
PAGES = {
    "accueil": "projets/sinjira/index.html",
    **{kind: f"projets/sinjira/{kind}/index.html" for kind in ROUTES},
}
SOFTWARE_TARGETS = (
    "/compte/",
    "/compte/bibliotheque.html",
    "/projets/sinjira/registre/",
    "/projets/sinjira/codex/",
)

# Empreintes des 3 visuels transmis : interdit un remplacement silencieux
# d'affiche sous un nom valide. WebP = adaptation de livraison sans recadrage.
BANNERS = {
    "romans": {
        "path": "assets/media/sinjira-romans-banniere-2026.webp",
        "width": "1672", "height": "941",
        "sha256": "2a4c521e7b23474c34a10b56a401e576e8a8482195013b91028ae701d4745c09",
    },
    "jeux": {
        "path": "assets/media/sinjira-jeux-banniere-2026.webp",
        "width": "1916", "height": "821",
        "sha256": "731413d350a6f92772525098dc91315bd4741ea1735d6bbdb178b117ec668a22",
    },
    "logiciels": {
        "path": "assets/media/sinjira-logiciels-banniere-2026.webp",
        "width": "2048", "height": "768",
        "sha256": "3d5667a9ceadf993e1ec43dc381d6af5b82c6a614590dbe50bed8500d7464c3c",
    },
}


class PageLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nav_depth = 0
        self.main_nav_depth = 0
        self.nav_links: list[tuple[str, str | None]] = []
        self.main_nav_links: list[tuple[str, str | None]] = []
        self.links: list[tuple[str, dict[str, str]]] = []
        self.images: list[dict[str, str]] = []
        self.canonicals: list[str] = []
        self.titles: list[str] = []
        self.current_title = False
        self.lang: str | None = None
        self.main_count = 0
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "html":
            self.lang = data.get("lang")
        if tag == "nav" and "universe-subnav" in (data.get("class") or ""):
            self.nav_depth += 1
        if tag == "nav" and "main-nav" in (data.get("class") or ""):
            self.main_nav_depth += 1
        if tag == "a" and data.get("href"):
            url = data["href"]
            self.links.append((url, {k: v or "" for k, v in attrs}))
            if self.nav_depth:
                self.nav_links.append((url, data.get("aria-current")))
            if self.main_nav_depth:
                self.main_nav_links.append((url, data.get("aria-current")))
        if tag == "img":
            self.images.append({k: v or "" for k, v in attrs})
        if tag == "link" and data.get("rel") == "canonical":
            self.canonicals.append(data.get("href") or "")
        if tag == "main":
            self.main_count += 1
    def handle_endtag(self, tag: str) -> None:
        if tag == "nav" and self.nav_depth:
            self.nav_depth -= 1
        if tag == "nav" and self.main_nav_depth:
            self.main_nav_depth -= 1

def resolve_local(page: Path, href: str, root: Path) -> Path | None:
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or not parts.path:
        return None
    path = (root / parts.path.lstrip("/")) if parts.path.startswith("/") else (page.parent / parts.path)
    if parts.path.endswith("/"):
        path = path / "index.html"
    return path.resolve()

def inspect_banners(root: Path) -> list[str]:
    errors: list[str] = []
    homepage = root / PAGES["accueil"]
    for kind, manifest in BANNERS.items():
        image_path = root / manifest["path"]
        image_url = "/" + manifest["path"]
        if not image_path.is_file() or image_path.is_symlink():
            errors.append(f"Bannière {kind} absente : {image_url}")
            continue
        data = image_path.read_bytes()
        if (len(data) > 350_000 or len(data) < 40_000
                or data[:4] != b"RIFF" or data[8:12] != b"WEBP"):
            errors.append(f"Bannière {kind} non optimisée ou WebP invalide")
        if hashlib.sha256(data).hexdigest() != manifest["sha256"]:
            errors.append(f"Bannière {kind} différente du visuel officiel approuvé")

        for cat, html_file in ((kind, root / PAGES[kind]), ("accueil", homepage)):
            if not html_file.is_file():
                errors.append(f"Page de bannière manquante : {cat}")
                continue
            parser = PageLinks()
            parser.feed(html_file.read_text("utf-8"))
            candidates = [img for img in parser.images if img.get("src") == image_url]
            if len(candidates) != 1:
                errors.append(f"Bannière {kind} absente ou dupliquée : {cat}")
                continue
            img = candidates[0]
            if img.get("width") != manifest["width"] or img.get("height") != manifest["height"]:
                errors.append(f"Dimensions naturelles incorrectes : {cat}/{kind}")
            if cat != "accueil":
                if not img.get("alt", "").strip():
                    errors.append(f"Alternative textuelle vide : {kind}")
                if "sinjira-category-poster--banner" not in html_file.read_text("utf-8"):
                    errors.append(f"Cadre panoramique manquant : {kind}")
            elif "sinjira-portal-art" not in img.get("class", ""):
                errors.append(f"Miniature de portail incorrecte : {kind}")
    css = root / "projets/sinjira/sinjira.css"
    if css.is_file():
        rules = css.read_text("utf-8")
        if (".sinjira-category-poster.sinjira-category-poster--banner img" not in rules
                or "object-fit:contain" not in rules
                or "height:auto" not in rules
                or "@media (max-width:640px)" not in rules):
            errors.append("Bannières : affichage intégral ou adaptation mobile non prouvé")
    return errors



def inspect_software_anchor_navigation(css: str) -> list[str]:
    """Prouver deux offsets d'ancrage accessibles sous les menus sticky.

    La vraie visibilité est testée séparément sur les trois navigateurs.
    """
    selectors = (
        r"\.sinjira-software-page\s+#outils,\s*"
        r"\.sinjira-software-page\s+#avenir\s*"
        r"\{\s*scroll-margin-top:\s*(\d+)px\s*\}"
    )
    offsets = [int(value) for value in re.findall(selectors, css)]
    main_offsets = [
        int(value) for value in re.findall(
            r"\.sinjira-software-page\s+#contenu\s*"
            r"\{\s*scroll-margin-top:\s*(\d+)px\s*\}", css
        )
    ]
    problems: list[str] = []
    if len(offsets) != 2 or min(offsets, default=0) < 165:
        problems.append("Ancres Logiciels : titres masqués par menus fixes")
    if len(main_offsets) != 2 or min(main_offsets, default=0) < 78:
        problems.append("Lien Aller au contenu : décalage du bandeau absent")
    if "@media(max-width:650px)" not in css:
        problems.append("Ancres Logiciels : aucun ajustement mobile")
    return problems


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return ["Racine de site absente"]
    for category, path in PAGES.items():
        file = root / path
        if not file.is_file():
            errors.append("Page absente : " + path)
            continue
        parser = PageLinks()
        parser.feed(file.read_text("utf-8"))
        expected_canonical = BASE + (
            "/projets/sinjira/" if category == "accueil" else ROUTES[category]
        )
        if parser.canonicals != [expected_canonical]:
            errors.append(f"Canonique incorrect ou dupliqué : {category}")
        if parser.lang != "fr-CA" or parser.main_count != 1:
            errors.append(f"Structure accessible ou langue incorrecte : {category}")
        # Les deux menus ont un rôle différent : le sous-menu désigne
        # une seule page courante; le menu principal indique uniquement
        # le parent SINJIRA sur une fiche de catégorie.
        links = [(url, state) for url, state in parser.nav_links]
        selected_subnav = [(url, state) for url, state in links
                           if state == "page"]
        selected_main = [(url, state) for url, state in parser.main_nav_links
                         if state in {"page", "location"}]
        expected_main = ("page" if category == "accueil" else "location")
        if selected_main != [("/projets/sinjira/", expected_main)]:
            errors.append(
                f"Menu principal SINJIRA : position courante incorrecte ({category})"
            )
        if len(selected_subnav) != 1:
            errors.append(
                f"Sous-menu SINJIRA : une seule page courante attendue ({category})"
            )
        expected_subnav = ((root / PAGES[category]).resolve())
        for url, state in selected_subnav:
            if resolve_local(file, url, root) != expected_subnav:
                errors.append(
                    f"Sous-menu SINJIRA : mauvaise page sélectionnée ({category})"
                )
        for kind, route in ROUTES.items():
            variants = {route, route + "index.html", kind + "/", "../" + kind + "/index.html"}
            matching = [(url, state) for url, state in links
                        if url == route or (resolve_local(file, url, root) ==
                                            (root / route.lstrip("/") / "index.html").resolve())]
            if len(matching) != 1:
                errors.append(f"Lien de catalogue {kind} absent ou dupliqué : {category}")
            elif category == kind and matching[0][1] != "page":
                errors.append(f"Section courante non identifiée : {kind}")
            elif category != kind and matching[0][1] == "page":
                errors.append(f"Fausse section courante : {category}/{kind}")
        if category == "logiciels":
            if any("download" in attrs for _, attrs in parser.links):
                errors.append("Téléchargement logiciel non annoncé présent")
            for target in SOFTWARE_TARGETS:
                if not any(url == target for url, _ in parser.links):
                    errors.append("Lien logiciel réel absent : " + target)
                if not resolve_local(file, target, root).is_file():
                    errors.append("Cible de service logiciel inexistante : " + target)
            html = file.read_text("utf-8")
            for label in ("Aucun téléchargement de logiciel autonome", "Selon vos droits"):
                if label not in html:
                    errors.append("Statut du logiciel ou des droits insuffisamment clair : " + label)
    sitemap = root / "sitemap.xml"
    if not sitemap.is_file() or (BASE + ROUTES["logiciels"]) not in sitemap.read_text("utf-8"):
        errors.append("Logiciels absent du plan XML")
    library = root / "compte/bibliotheque.html"
    if not library.is_file():
        errors.append("Bibliothèque des membres introuvable")
    else:
        for route in ROUTES.values():
            if f'href="{route}"' not in library.read_text("utf-8"):
                errors.append("Raccourci bibliothèque absent : " + route)
    css = root / "projets/sinjira/sinjira.css"
    if not css.is_file():
        errors.append("Feuille de style SINJIRA absente")
    else:
        rules = css.read_text("utf-8")
        if "@media(max-width:700px)" not in rules:
            errors.append("Style mobile Logiciels absent")
        errors.extend(inspect_software_anchor_navigation(rules))
    errors.extend(inspect_banners(root))
    return errors

def self_test() -> None:
    # Un cas négatif prouve que la navigation n'est pas seulement décorative.
    with TemporaryDirectory() as folder:
        test_root = Path(folder)
        assert any("Page absente" in err for err in validate(test_root))
    # Vérifier les fichiers de la vraie livraison puis simuler une suppression
    # et une permutation des deux affiches : ces changements doivent échouer.
    with TemporaryDirectory() as folder:
        root = Path(folder)
        for rel in PAGES.values():
            to = root / rel
            to.parent.mkdir(parents=True, exist_ok=True)
            copyfile(ROOT / rel, to)
        stylesheet = root / "projets/sinjira/sinjira.css"
        stylesheet.parent.mkdir(parents=True, exist_ok=True)
        copyfile(ROOT / "projets/sinjira/sinjira.css", stylesheet)
        for entry in BANNERS.values():
            to = root / entry["path"]
            to.parent.mkdir(parents=True, exist_ok=True)
            copyfile(ROOT / entry["path"], to)
        assert not inspect_banners(root), inspect_banners(root)
        styles = stylesheet.read_text("utf-8")
        assert not inspect_software_anchor_navigation(styles)
        for altered in (
            styles.replace("scroll-margin-top:178px", "scroll-margin-top:0px"),
            styles.replace("scroll-margin-top:170px", "scroll-margin-top:60px"),
            styles.replace(".sinjira-software-page #avenir", ".fausse-ancre"),
            styles.replace("scroll-margin-top:94px", "scroll-margin-top:0px"),
        ):
            assert inspect_software_anchor_navigation(altered), (
                "Régression d'ancre fixe non détectée"
            )
        banner = root / BANNERS["jeux"]["path"]
        banner.unlink()
        assert any("Bannière jeux absente" in e for e in inspect_banners(root)), (
            "Fichier de bannière manquant non détecté"
        )
        copyfile(ROOT / BANNERS["jeux"]["path"], banner)
        page = root / PAGES["logiciels"]
        page.write_text(page.read_text("utf-8").replace(
            "/assets/media/sinjira-logiciels-banniere-2026.webp",
            "/assets/media/sinjira-romans-banniere-2026.webp"
        ), "utf-8")
        assert any("Bannière logiciels absente ou dupliquée" in e
                   for e in inspect_banners(root)), (
            "Affiche placée dans la mauvaise catégorie non détectée"
        )
    # Cas négatifs de sémantique aria-current : une page de catalogue
    # ne doit jamais prétendre être l'accueil du site ni désigner deux
    # catégories simultanément.
    with TemporaryDirectory() as folder:
        test_root = Path(folder)
        rel = PAGES["romans"]
        destination = test_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        text = (ROOT / rel).read_text("utf-8")
        destination.write_text(text.replace(
            'aria-current="location" href="/projets/sinjira/"',
            'aria-current="page" href="/projets/sinjira/"', 1
        ), "utf-8")
        # Le parseur détecte cette incohérence même sans disposer des
        # médias et autres pages nécessaires à un test intégral.
        violations = validate(test_root)
        assert any(
            "Menu principal SINJIRA : position courante incorrecte (romans)"
            in violation for violation in violations
        ), "Erreur aria-current de l'onglet Romans non détectée"
        # Un deuxième aria-current=page dans la sous-navigation doit aussi
        # être rejeté indépendamment de l'inventaire public des pages.
        destination.write_text(text.replace(
            'href="../jeux/index.html"',
            'aria-current="page" href="../jeux/index.html"', 1
        ), "utf-8")
        violations = validate(test_root)
        assert any(
            "Sous-menu SINJIRA : une seule page courante attendue (romans)"
            in violation for violation in violations
        ), "Double page active non détectée"

    # Le véritable projet est la fixture positive afin de contrôler les liens réels.
    problems = validate(ROOT)
    if problems:
        raise AssertionError("\n".join(problems))
    print("OK autotests : page absente rejetée et 3 catalogues réels conformes")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if args.self_test and not errors:
        self_test()
    for error in errors:
        print("ERREUR : " + error)
    if errors:
        return 1
    print("OK : 3 catalogues, liens croisés, sitemap, services et mobile contrôlés")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
