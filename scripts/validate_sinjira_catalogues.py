#!/usr/bin/env python3
"""Contrat public des trois catalogues SINJIRA — sans réseau ni données privées."""
from __future__ import annotations

import argparse
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

class PageLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nav_depth = 0
        self.nav_links: list[tuple[str, str | None]] = []
        self.links: list[tuple[str, dict[str, str]]] = []
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
        if tag == "a" and data.get("href"):
            url = data["href"]
            self.links.append((url, {k: v or "" for k, v in attrs}))
            if self.nav_depth:
                self.nav_links.append((url, data.get("aria-current")))
        if tag == "link" and data.get("rel") == "canonical":
            self.canonicals.append(data.get("href") or "")
        if tag == "main":
            self.main_count += 1
    def handle_endtag(self, tag: str) -> None:
        if tag == "nav" and self.nav_depth:
            self.nav_depth -= 1

def resolve_local(page: Path, href: str, root: Path) -> Path | None:
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or not parts.path:
        return None
    path = (root / parts.path.lstrip("/")) if parts.path.startswith("/") else (page.parent / parts.path)
    if parts.path.endswith("/"):
        path = path / "index.html"
    return path.resolve()

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
        links = [(url, state) for url, state in parser.nav_links]
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
    if not css.is_file() or "@media(max-width:700px)" not in css.read_text("utf-8"):
        errors.append("Style mobile Logiciels absent")
    return errors

def self_test() -> None:
    # Un cas négatif prouve que la navigation n'est pas seulement décorative.
    with TemporaryDirectory() as folder:
        test_root = Path(folder)
        assert any("Page absente" in err for err in validate(test_root))
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
