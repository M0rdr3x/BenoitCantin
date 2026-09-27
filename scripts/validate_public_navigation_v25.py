#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

KEY_PAGES = {
    "index.html": "Accueil",
    "a-propos.html": "À propos",
    "contact.html": None,
    "transparence-ia.html": None,
    "confidentialite.html": None,
    "gouvernance-vie-privee.html": None,
    "avis-legal.html": None,
    "404.html": None,
    "projets/sinjira/index.html": "SINJIRA™",
    "projets/sinjira/romans/index.html": "SINJIRA™",
    "projets/sinjira/jeux/index.html": "SINJIRA™",
    "projets/sinjira/registre/index.html": "SINJIRA™",
    "projets/sinjira/communaute/index.html": "SINJIRA™",
    "projets/sinjira/monde-parallele/index.html": "SINJIRA™",
    "projets/sinjira/codex/index.html": "SINJIRA™",
    "projets/sinjira/romans/lire-demo.html": "SINJIRA™",
    "projets/sinjira/romans/le-sang-du-sauveur/index.html": "SINJIRA™",
    "projets/sinjira/jeux/fracture-du-reseau-mere/index.html": "SINJIRA™",
}

INFO_FOOTER_PAGES = (
    "index.html",
    "a-propos.html",
    "contact.html",
    "transparence-ia.html",
    "confidentialite.html",
    "gouvernance-vie-privee.html",
    "avis-legal.html",
    "404.html",
)

INFO_FOOTER_LINKS = (
    ("/a-propos.html", "À propos"),
    ("/contact.html", "Contact"),
    ("/transparence-ia.html", "Transparence IA"),
    ("/confidentialite.html", "Confidentialité"),
    ("/gouvernance-vie-privee.html", "Gouvernance vie privée"),
    ("/avis-legal.html", "Avis légal"),
)

SINJIRA_FOOTER_PAGES = (
    "projets/sinjira/index.html",
    "projets/sinjira/romans/index.html",
    "projets/sinjira/jeux/index.html",
    "projets/sinjira/registre/index.html",
    "projets/sinjira/communaute/index.html",
    "projets/sinjira/monde-parallele/index.html",
    "projets/sinjira/codex/index.html",
    "projets/sinjira/romans/lire-demo.html",
    "projets/sinjira/romans/le-sang-du-sauveur/index.html",
    "projets/sinjira/jeux/fracture-du-reseau-mere/index.html",
)

SINJIRA_FOOTER_LINKS = (
    ("/projets/sinjira/", "Vue d’ensemble"),
    ("/projets/sinjira/romans/", "Romans"),
    ("/projets/sinjira/jeux/", "Jeux"),
    ("/projets/sinjira/registre/", "Registre"),
    ("/projets/sinjira/communaute/", "Communauté"),
    ("/projets/sinjira/monde-parallele/", "Monde parallèle"),
    ("/projets/sinjira/codex/", "Codex"),
    ("/compte/", "Compte SINJIRA™"),
    *INFO_FOOTER_LINKS,
)

EXPECTED_LABELS = ("Accueil", "SINJIRA™", "Projet Nova", "À propos", "Compte")
FORBIDDEN_GLOBAL_LABELS = (">Registre</a>", ">Contact</a>")

SINJIRA_SUBNAV_ACTIVE = {
    "projets/sinjira/index.html": "Vue d’ensemble",
    "projets/sinjira/romans/index.html": "Romans",
    "projets/sinjira/jeux/index.html": "Jeux",
    "projets/sinjira/registre/index.html": "Registre",
    "projets/sinjira/communaute/index.html": "Communauté",
    "projets/sinjira/monde-parallele/index.html": "Monde parallèle",
    "projets/sinjira/codex/index.html": "Codex",
}

COMMON_PUBLIC_CSS_VERSION = "25.0.0"
COMMON_PORTAL_CSS_ASSETS = ("site.css", "v24-platform.css", "v19-pro.css")
COMMON_SINJIRA_CSS_ASSETS = ("site.css", "sinjira.css", "v24-platform.css", "v19-pro.css")

SINJIRA_SUBNAV_LINKS = (
    ("/projets/sinjira/", "Vue d’ensemble"),
    ("/projets/sinjira/romans/", "Romans"),
    ("/projets/sinjira/jeux/", "Jeux"),
    ("/projets/sinjira/registre/", "Registre"),
    ("/projets/sinjira/communaute/", "Communauté"),
    ("/projets/sinjira/monde-parallele/", "Monde parallèle"),
    ("/projets/sinjira/codex/", "Codex"),
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def extract_main_nav(html: str) -> str:
    cursor = 0
    while True:
        start = html.find("<nav", cursor)
        if start < 0:
            raise ValueError("navigation principale absente")
        open_end = html.find(">", start)
        if open_end < 0:
            raise ValueError("ouverture navigation principale invalide")
        opening = html[start:open_end + 1]
        if 'class="main-nav"' in opening and "data-main-nav" in opening:
            end = html.find("</nav>", open_end)
            if end < 0:
                raise ValueError("fermeture navigation principale absente")
            return html[start:end + len("</nav>")]
        cursor = open_end + 1


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
        "toggle.setAttribute('aria-controls', nav.id)",
        "toggle.setAttribute('aria-label', 'Fermer le menu')",
        "toggle.setAttribute('aria-label', 'Ouvrir le menu')",
        "event.key === 'Escape'",
        "closeMainNavigation(true)",
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
        if '/assets/js/v19-session.js?v=25.0.0' not in contents[path]:
            errors.append(f"{path}: runtime session public SINJIRA absent ou obsolète")

        if 'id="navigation-principale"' not in nav:
            errors.append(f"{path}: navigation principale sans id accessible")
        if 'aria-controls="navigation-principale"' not in contents[path]:
            errors.append(f"{path}: bouton menu sans aria-controls")
        if 'class="skip-link"' not in contents[path] or 'href="#contenu"' not in contents[path]:
            errors.append(f"{path}: lien d’évitement vers le contenu absent")
        if 'id="contenu"' not in contents[path]:
            errors.append(f"{path}: cible principale #contenu absente")

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

    for path, active_label in SINJIRA_SUBNAV_ACTIVE.items():
        html = contents[path]
        if html.count("universe-subnav") != 1:
            errors.append(f"{path}: une seule sous-navigation SINJIRA est autorisée")
        subnav_start = html.find('<nav class="universe-subnav"')
        subnav_end = html.find("</nav>", subnav_start) if subnav_start >= 0 else -1
        if subnav_start < 0 or subnav_end < 0:
            errors.append(f"{path}: sous-navigation SINJIRA absente")
            continue
        subnav = html[subnav_start:subnav_end + len("</nav>")]
        if 'aria-label="Navigation de SINJIRA™"' not in subnav:
            errors.append(f"{path}: sous-navigation SINJIRA sans libellé accessible")
        if subnav.count("<a") != len(SINJIRA_SUBNAV_LINKS):
            errors.append(f"{path}: sous-navigation SINJIRA doit contenir {len(SINJIRA_SUBNAV_LINKS)} liens")
        for href, label in SINJIRA_SUBNAV_LINKS:
            if f'href="{href}"' not in subnav or f">{label}</a>" not in subnav:
                errors.append(f"{path}: lien sous-navigation manquant: {label}")
        if f'aria-current="page" href="' not in subnav or f">{active_label}</a>" not in subnav:
            errors.append(f"{path}: section active de sous-navigation absente: {active_label}")

    registry = contents["projets/sinjira/registre/index.html"]
    direct_fields = re.findall(
        r'<div class="field"><label(?:\s+for="([^"]+)")?>(.*?)</label><(input|select|textarea)\b([^>]*)>',
        registry,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if len(direct_fields) != 25:
        errors.append(f"Registre: 25 champs directs étiquetés attendus, trouvé {len(direct_fields)}")
    for label_for, label_html, tag_name, attrs in direct_fields:
        id_match = re.search(r'\bid="([^"]+)"', attrs, flags=re.IGNORECASE)
        control_id = id_match.group(1) if id_match else ""
        label_text = re.sub(r"<[^>]+>", "", label_html).strip()
        if not label_for or not control_id or label_for != control_id:
            errors.append(
                f"Registre: association label/champ invalide pour {label_text or tag_name}"
            )

    sinjira = contents["projets/sinjira/index.html"]
    for marker in (
        'href="/contact.html">Contact</a>',
        'href="/transparence-ia.html">Transparence IA</a>',
    ):
        if marker not in sinjira:
            errors.append(f"SINJIRA: footer portail incomplet: {marker}")

    contact = contents["contact.html"]
    if 'id="contact-general"' not in contact:
        errors.append("Contact: formulaire principal perdu")
    if 'href="/contact.html"' not in contact:
        errors.append("Contact: auto-lien/footer de contact absent")

    for path in INFO_FOOTER_PAGES:
        html = contents[path]
        if f"site.css?v={COMMON_PUBLIC_CSS_VERSION}" not in html:
            errors.append(f"{path}: version commune de site.css incohérente")
        for asset in COMMON_PORTAL_CSS_ASSETS[1:]:
            if asset in html and f"{asset}?v={COMMON_PUBLIC_CSS_VERSION}" not in html:
                errors.append(f"{path}: version commune de {asset} incohérente")
        footer_at = html.find('<footer class="site-footer"')
        if footer_at < 0:
            errors.append(f"{path}: footer public absent")
            continue
        footer = html[footer_at:]
        for href, label in INFO_FOOTER_LINKS:
            if f'href="{href}"' not in footer or f">{label}</a>" not in footer:
                errors.append(f"{path}: lien footer manquant: {label}")
        if "site.js?v=24.4.23" not in html:
            errors.append(f"{path}: runtime public footer/navigation obsolète")

    for path in SINJIRA_FOOTER_PAGES:
        html = contents[path]
        if f"site.css?v={COMMON_PUBLIC_CSS_VERSION}" not in html:
            errors.append(f"{path}: version commune de site.css incohérente")
        for asset in COMMON_SINJIRA_CSS_ASSETS[1:]:
            if asset in html and f"{asset}?v={COMMON_PUBLIC_CSS_VERSION}" not in html:
                errors.append(f"{path}: version commune de {asset} incohérente")
        footer_at = html.find('<footer class="site-footer"')
        if footer_at < 0:
            errors.append(f"{path}: footer SINJIRA absent")
            continue
        footer = html[footer_at:]
        if '<div class="footer-grid">' not in footer:
            errors.append(f"{path}: structure footer SINJIRA incomplète")
        if "Univers original de Benoit Cantin." not in footer:
            errors.append(f"{path}: signature footer SINJIRA absente")
        for href, label in SINJIRA_FOOTER_LINKS:
            if f'href="{href}"' not in footer or f">{label}</a>" not in footer:
                errors.append(f"{path}: lien footer SINJIRA manquant: {label}")


def self_test(contents: dict[str, str]) -> None:
    mutations = [
        ("Registre remis dans le menu global", "index.html", ">SINJIRA™</a>", '>SINJIRA™</a><a href="/projets/sinjira/registre/">Registre</a>'),
        ("Compte retiré", "a-propos.html", 'href="/compte/" data-sinjira-session-nav>Compte</a>', 'href="/compte/">Compte retiré</a>'),
        ("Registre accueil retiré", "index.html", "Créer mon personnage", "Accès retiré"),
        ("normalisation runtime retirée", "assets/js/site.js", "function normalizePortalNavigation()", "function navigationRetiree()"),
        ("sous-nav SINJIRA retirée", "projets/sinjira/index.html", 'href="/projets/sinjira/registre/">Registre</a>', 'href="/projets/sinjira/registre-retire/">Registre</a>'),
        ("sous-nav Communauté retirée", "projets/sinjira/communaute/index.html", 'href="/projets/sinjira/monde-parallele/">Monde parallèle</a>', 'href="/projets/sinjira/monde-parallele-retire/">Monde parallèle</a>'),
        ("sous-nav Romans dupliquée", "projets/sinjira/romans/index.html", '</nav><main id="contenu">', '</nav><nav class="universe-subnav"></nav><main id="contenu">'),
        ("footer transparence retiré", "contact.html", 'href="/transparence-ia.html">Transparence IA</a>', 'href="/transparence-ia-retiree.html">Transparence retirée</a>'),
        ("aria-controls retiré", "index.html", 'aria-controls="navigation-principale"', 'aria-controls="navigation-retiree"'),
        ("fermeture Escape retirée", "assets/js/site.js", "event.key === 'Escape'", "event.key === 'F1'"),
        ("gouvernance footer accueil retirée", "index.html", 'href="/gouvernance-vie-privee.html">Gouvernance vie privée</a>', 'href="/gouvernance-retiree.html">Gouvernance retirée</a>'),
        ("libellé fermeture menu retiré", "assets/js/site.js", "toggle.setAttribute('aria-label', 'Fermer le menu')", "toggle.setAttribute('aria-label', 'Menu')"),
        ("ancien menu confidentialité réintroduit", "confidentialite.html", '<a href="/projets/projet-nova/">Projet Nova</a>', '<a href="/projets/sinjira/registre/">Registre</a><a href="/projets/projet-nova/">Projet Nova</a>'),
        ("Codex sans menu global", "projets/sinjira/codex/index.html", 'id="navigation-principale" data-main-nav', 'id="navigation-codex"'),
        ("gouvernance footer Codex retirée", "projets/sinjira/codex/index.html", 'href="/gouvernance-vie-privee.html">Gouvernance vie privée</a>', 'href="/gouvernance-retiree.html">Gouvernance retirée</a>'),
        ("lien d’évitement Codex retiré", "projets/sinjira/codex/index.html", 'class="skip-link" href="#contenu"', 'class="skip-link" href="#contenu-retire"'),
        ("label Registre désassocié", "projets/sinjira/registre/index.html", 'label for="registry-appearance-build"', 'label'),
        ("cache CSS Codex rétrogradé", "projets/sinjira/codex/index.html", 'site.css?v=25.0.0', 'site.css?v=24.0'),
        ("cache CSS À propos rétrogradé", "a-propos.html", 'site.css?v=25.0.0', 'site.css?v=24.4.12'),
        ("runtime session Codex retiré", "projets/sinjira/codex/index.html", '/assets/js/v19-session.js?v=25.0.0', '/assets/js/v19-session-retire.js?v=25.0.0'),
        ("Compte 404 retiré", "404.html", 'href="/compte/" data-sinjira-session-nav>Compte</a>', 'href="/contact.html">Contact</a>'),
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

    paths = ["assets/js/site.js", *KEY_PAGES.keys(), *[p for p in INFO_FOOTER_PAGES if p not in KEY_PAGES]]
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
