#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

KEY_PAGES = {
    "index.html": "Accueil",
    "a-propos.html": "À propos",
    "contact.html": None,
    "transparence-ia.html": None,
    "projets/sinjira/index.html": "SINJIRA™",
}

EXPECTED_LABELS = ("Accueil", "SINJIRA™", "Projet Nova", "À propos", "Compte")
FORBIDDEN_GLOBAL_LABELS = (">Registre</a>", ">Contact</a>")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def extract_main_nav(html: str) -> str:
    start = html.find('<nav class="main-nav" data-main-nav')
    if start < 0:
        raise ValueError("navigation principale absente")
    end = html.find("</nav>", start)
    if end < 0:
        raise ValueError("fermeture navigation principale absente")
    return html[start:end + len("</nav>")]


def validate(errors: list[str], contents: dict[str, str]) -> None:
    site_js = contents["assets/js/site.js"]

    for marker in (
        "function normalizePortalNavigation()",
        "Accueil</a>",
        "SINJIRA™</a>",
        "Projet Nova</a>",
        "À propos</a>",
        'class="nav-cta" href="/compte/" data-sinjira-session-nav>Compte</a>',
        "path.indexOf('/projets/projet-nova') === 0",
        "path === '/compte'",
        "path === '/app'",
        "path === '/admin'",
    ):
        if marker not in site_js:
            errors.append(f"runtime navigation incomplet: {marker}")

    for path, active_label in KEY_PAGES.items():
        try:
            nav = extract_main_nav(contents[path])
        except ValueError as exc:
            errors.append(f"{path}: {exc}")
            continue

        for label in EXPECTED_LABELS:
            if f">{label}</a>" not in nav:
                errors.append(f"{path}: lien global manquant: {label}")

        for marker in FORBIDDEN_GLOBAL_LABELS:
            if marker in nav:
                errors.append(f"{path}: lien déplacé encore présent dans le menu global: {marker}")

        if nav.count("<a") != 5:
            errors.append(f"{path}: le menu global doit contenir exactement 5 liens")

        if "site.js?v=24.4.23" not in contents[path]:
            errors.append(f"{path}: version de cache navigation publique obsolète")

        if 'href="/compte/" data-sinjira-session-nav' not in nav:
            errors.append(f"{path}: Compte doit rester pilotable par la session")

        if active_label and f'aria-current="page" href="' not in nav:
            errors.append(f"{path}: lien actif attendu pour {active_label}")

    home = contents["index.html"]
    for marker in (
        'href="/projets/sinjira/registre/"',
        "Registre des Consciences",
        "Créer mon personnage",
    ):
        if marker not in home:
            errors.append(f"Accueil: accès direct Registre perdu: {marker}")

    sinjira = contents["projets/sinjira/index.html"]
    for marker in (
        'class="universe-subnav"',
        'href="registre/">Registre</a>',
        'href="/contact.html">Contact</a>',
        'href="/transparence-ia.html">Transparence IA</a>',
    ):
        if marker not in sinjira:
            errors.append(f"SINJIRA: navigation secondaire/footer incomplet: {marker}")

    contact = contents["contact.html"]
    if 'id="contact-general"' not in contact:
        errors.append("Contact: formulaire principal perdu")
    if 'href="/contact.html"' not in contact:
        errors.append("Contact: auto-lien/footer de contact absent")


def self_test(contents: dict[str, str]) -> None:
    mutations = [
        ("Registre remis dans le menu global", "index.html", ">SINJIRA™</a>", ">SINJIRA™</a><a href="/projets/sinjira/registre/">Registre</a>"),
        ("Compte retiré", "a-propos.html", 'href="/compte/" data-sinjira-session-nav>Compte</a>', 'href="/compte/">Compte retiré</a>'),
        ("Registre accueil retiré", "index.html", "Créer mon personnage", "Accès retiré"),
        ("normalisation runtime retirée", "assets/js/site.js", "function normalizePortalNavigation()", "function navigationRetiree()"),
        ("sous-nav SINJIRA retirée", "projets/sinjira/index.html", 'href="registre/">Registre</a>', 'href="registre/">Entrée retirée</a>'),
    ]
    detected = 0
    for name, path, old, new in mutations:
        mutated = dict(contents)
        if old not in mutated[path]:
            raise ValueError(f"auto-test invalide, marqueur absent: {name}")
        mutated[path] = mutated[path].replace(old, new, 1)
        errors: list[str] = []
        validate(errors, mutated)
        if errors:
            detected += 1
        else:
            raise ValueError(f"auto-test: dérive non détectée: {name}")
    print(f"OK navigation publique auto-test: {detected}/{len(mutations)} dérives détectées")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    paths = ["assets/js/site.js", *KEY_PAGES.keys()]
    contents = {path: read(path) for path in paths}

    if args.self_test:
        self_test(contents)
        return 0

    errors: list[str] = []
    validate(errors, contents)
    if errors:
        print(f"ECHEC navigation publique: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print("OK navigation publique V25: 5 liens globaux, Compte conservé, Registre dans SINJIRA et Contact accessible hors menu principal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
