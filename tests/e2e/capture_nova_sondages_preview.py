#!/usr/bin/env python3
"""Aperçu Nova en captures PNG privées au run CI, jamais publié sur Pages.

Aucun compte, aucun vote réel, aucune API distante. Navigateur local uniquement.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4173"
CAPTURES = (
    ("/", "#sondages-nova", "01-accueil-benoitcantin.png"),
    ("/projets/projet-nova/", "#consultations", "02-accueil-projet-nova.png"),
    ("/projets/projet-nova/consultation-40.html", "#sondage-introduction", "03-sondage-referendaire-40.png"),
    ("/projets/projet-nova/sondage.html", "#sondage-introduction", "04-sondage-citoyen-64.png"),
    ("/projets/projet-nova/resultats-sondages.html", "#results-state", "05-resultats-publics.png"),
)
ICON = "nova-sondage-icone.webp"


def capture(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    seen: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1280, "height": 900},
            locale="fr-CA",
            device_scale_factor=1,
        )
        try:
            page.on("request", lambda request: seen.append(request.url)
                    if "nova-survey-submit" in request.url
                    or "nova-consultation40-submit" in request.url else None)
            for route, selector, filename in CAPTURES:
                response = page.goto(BASE + route, wait_until="domcontentloaded", timeout=30000)
                if response is None or response.status != 200:
                    raise AssertionError(f"Page de préparation absente: {route}")
                element = page.locator(selector)
                element.wait_for(state="visible", timeout=15000)
                if route == "/":
                    image = element.locator("img[src*='nova-sondage-icone.webp']")
                    if image.count() != 1:
                        raise AssertionError("Icône du sondage absente du portail")
                    image.evaluate("(image) => image.decode()")
                    if image.evaluate("(image) => image.naturalWidth") != 256:
                        raise AssertionError("Icône Nova chargée avec une taille inattendue")
                if route == "/projets/projet-nova/":
                    icons = element.locator("img[src*='nova-sondage-icone.webp']")
                    if icons.count() != 2:
                        raise AssertionError("Deux cartes de consultation avec icône attendues")
                    for icon in icons.all():
                        icon.evaluate("(image) => image.decode()")
                        if icon.evaluate("(image) => image.naturalWidth") != 256:
                            raise AssertionError("Icône du sondage 40/64 non chargée")
                if route.endswith("consultation-40.html") or route.endswith("sondage.html"):
                    if not page.locator("#sondage-start").is_disabled():
                        raise AssertionError("Questionnaire sans attestation 18+ ou consentement")
                    if not page.locator("#sondage-introduction").is_visible():
                        raise AssertionError("Introduction au sondage invisible")
                if route.endswith("resultats-sondages.html"):
                    page.locator("#results-question-list li").first.wait_for(timeout=15000)
                    if page.locator("#results-question-list li").count() != 40:
                        raise AssertionError("Résultats : 40 formulations non affichées")
                    if "Aucun résultat publié" not in element.inner_text():
                        raise AssertionError("Résultats de démonstration faussement annoncés")
                    if page.locator(".nova-results-bar-item").count():
                        raise AssertionError("Chiffres fictifs visibles dans les résultats")
                element.screenshot(path=str(output / filename), animations="disabled", timeout=15000)
                print(f"APERÇU vérifié : {filename}")
            if seen:
                raise AssertionError("Requête de collecte des opinions lors des captures")
        finally:
            browser.close()
    (output / "LISEZ-MOI.txt").write_text(
        "PROJET NOVA — APERÇUS DE PRÉPRODUCTION, NON PUBLIÉS\n"
        "Cette archive contient cinq captures d'interfaces locales de test.\n"
        "Ce ne sont pas des captures du site www.benoitcantin.com en production.\n"
        "Aucune réponse réelle n'a été soumise ou enregistrée.\n"
        "Les deux consultations sont non représentatives ; le sondage\n"
        "référendaire de 40 questions n'est pas un référendum officiel.\n"
        f"Commit GitHub : {os.environ.get('GITHUB_SHA', 'local')}\n"
        f"Run de validation : {os.environ.get('GITHUB_RUN_ID', 'local')}\n"
        "Publication bloquée tant que GitHub Pages #450 n'est pas résolu.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    capture(args.output)


if __name__ == "__main__":
    main()
