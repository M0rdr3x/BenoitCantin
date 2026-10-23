#!/usr/bin/env python3
"""Réconciliation contrôlée des hubs SINJIRA et du contrat privé Livre I.

Seul le contenu HTML public et sa navigation sont contrôlés; le document
intégral ne doit pas être ajouté ou activé par ce validateur.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SINJIRA = ROOT / "projets/sinjira/index.html"
ROMANS = ROOT / "projets/sinjira/romans/index.html"
CONTRACT = ROOT / "projets/sinjira/codex/livre-i-delivery-contract.json"
REQUIRED_FOOTER = (
    "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/",
    "/projets/sinjira/registre/",
    "/projets/sinjira/communaute/",
    "/projets/sinjira/monde-parallele/",
    "/projets/sinjira/codex/",
    "/a-propos.html",
    "/contact.html",
    "/transparence-ia.html",
    "/confidentialite.html",
    "/gouvernance-vie-privee.html",
    "/avis-legal.html",
)


def check_hub(name: str, html: str, *, demo_pages: int, full_pages: int) -> list[str]:
    errors: list[str] = []
    if not re.search(r'<footer\b[^>]*>.*?</footer>', html, re.S | re.I):
        return [f"{name}: pied de page absent"]
    footer = re.search(r'<footer\b[^>]*>(.*?)</footer>', html, re.S | re.I).group(1)
    for target in REQUIRED_FOOTER:
        if f'href="{target}"' not in footer:
            errors.append(f"{name}: lien de navigation/footer absent: {target}")
    if html.count("<footer") != 1:
        errors.append(f"{name}: footer dupliqué")
    for marker in (
        'id="navigation-principale"',
        "data-main-nav",
        "data-menu-toggle",
        'aria-controls="navigation-principale"',
        'href="/compte/"',
    ):
        if marker not in html:
            errors.append(f"{name}: navigation accessible incomplète: {marker}")
    if f"{demo_pages} pages" not in html:
        errors.append(f"{name}: démo incompatible avec le contrat de {demo_pages} pages")
    if f"{full_pages} pages" not in html:
        errors.append(f"{name}: intégrale incompatible avec le contrat de {full_pages} pages")
    if name == "accueil SINJIRA":
        seo = (
            'hreflang="fr-CA"', 'hreflang="x-default"',
            'property="og:locale" content="fr_CA"',
            'name="twitter:card" content="summary_large_image"',
            'name="twitter:image:alt"',
            '"@type":"CreativeWorkSeries"',
            'src="../../assets/js/site.js?v=24.4.100"',
        )
        for marker in seo:
            if marker not in html:
                errors.append(f"{name}: métadonnées du portail manquantes: {marker}")
    else:
        scripts = re.findall(
            r'<script\s+type="application/ld\+json"\s*>(.*?)</script>', html, re.S
        )
        if not scripts:
            errors.append("Romans: données structurées Book absentes")
        else:
            try:
                doc = json.loads(scripts[0])
                graph = doc.get("@graph", [])
                book = next((x for x in graph if x.get("@type") == "Book"), None)
                if not book or book.get("numberOfPages") != full_pages:
                    errors.append("Romans: nombre de pages Book hors contrat")
                if not book or f"{demo_pages} pages" != book.get("hasPart", {}).get("pagination"):
                    errors.append("Romans: pagination démo Book hors contrat")
            except (ValueError, TypeError, AttributeError):
                errors.append("Romans: JSON-LD Book invalide")
    return errors


def validate() -> list[str]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    demo = contract.get("demo", {}).get("pages")
    full = contract.get("full_edition", {}).get("pages")
    errors: list[str] = []
    if contract.get("publication_state") != "not_activated" or not contract.get("human_gate_required"):
        errors.append("Livre I: diffusion privée activée sans décision humaine explicite")
    edition = contract.get("full_edition", {})
    if edition.get("public_static_url_allowed") is not False:
        errors.append("Livre I: URL publique de l'intégrale interdite")
    if edition.get("public_repository_allowed") is not False:
        errors.append("Livre I: publication de l'intégrale dans Git interdite")
    if edition.get("delivery") != "authenticated_private_storage_only":
        errors.append("Livre I: remise privée authentifiée obligatoire")
    if not isinstance(demo, int) or not isinstance(full, int):
        return errors + ["Contrat Livre I: nombres de pages absents"]
    errors.extend(check_hub(
        "accueil SINJIRA", SINJIRA.read_text(encoding="utf-8"),
        demo_pages=demo, full_pages=full
    ))
    errors.extend(check_hub(
        "romans", ROMANS.read_text(encoding="utf-8"),
        demo_pages=demo, full_pages=full
    ))
    return errors


def self_test() -> list[str]:
    errors: list[str] = []
    home = SINJIRA.read_text(encoding="utf-8")
    novels = ROMANS.read_text(encoding="utf-8")
    if check_hub("accueil SINJIRA", home, demo_pages=84, full_pages=1027):
        errors.append("Le contrôle positif de l'accueil échoue")
    if check_hub("romans", novels, demo_pages=84, full_pages=1027):
        errors.append("Le contrôle positif de la bibliothèque échoue")
    weakened = home.replace('href="/projets/sinjira/codex/"', 'href="/ancien-codex/"', 1)
    if not any("codex" in error for error in check_hub(
        "accueil SINJIRA", weakened, demo_pages=84, full_pages=1027
    )):
        errors.append("Test négatif Codex non détecté")
    stale = novels.replace('"numberOfPages":1027', '"numberOfPages":520', 1)
    if not any("Book hors contrat" in error for error in check_hub(
        "romans", stale, demo_pages=84, full_pages=1027
    )):
        errors.append("Test négatif du JSON-LD ancien non détecté")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args()
    problems = self_test() if options.self_test else validate()
    for p in problems:
        print("ECHEC:", p)
    if problems:
        raise SystemExit(1)
    print("OK: SEO et navigation SINJIRA préservés, Livre I privé hors publication.")
