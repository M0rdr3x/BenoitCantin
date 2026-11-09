#!/usr/bin/env python3
"""Essai E2E du clavier de la Boussole Projet Nova, UNIQUEMENT en site local.

Les choix sont synthétiques, ne sont ni des votes ni un profil d'électeur.
Test dans Chromium, Firefox et WebKit, desktop et viewport mobile émulé.
Ne vaut pas audit WCAG indépendant, ni essai sur des appareils réels.
"""
from __future__ import annotations

import json
import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER_NAME = os.environ.get("BROWSER", "chromium").strip().lower()
BROWSERS = ("chromium", "firefox", "webkit")
COMPASS = "projets/projet-nova/boussole-electorale.html"


def validate_contract() -> None:
    assert BROWSER_NAME in BROWSERS, "Moteur inconnu"
    assert urlparse(BASE_URL).hostname in ("127.0.0.1", "localhost"), (
        "Ce test clavier ne peut jamais être dirigé vers le domaine public."
    )


def check_question_semantics(page, question_id: str) -> None:
    stage = page.locator("#compass-question-stage fieldset")
    assert stage.count() == 1 and stage.is_visible()
    assert stage.get_attribute("data-question-id") == question_id
    assert stage.evaluate("(e) => e.firstElementChild?.tagName === 'LEGEND'")
    legend = stage.locator("legend")
    assert legend.count() == 1 and bool(legend.inner_text().strip())
    labelled_id = legend.get_attribute("id")
    assert labelled_id, "Légende sans identifiant d'annonce"
    radiogroup = stage.locator('[role="radiogroup"]')
    assert radiogroup.count() == 1
    assert radiogroup.get_attribute("aria-labelledby") == labelled_id
    radios = radiogroup.locator('input[type="radio"]')
    assert radios.count() == 8, "Sept positions et Sans opinion doivent être accessibles"
    assert radios.evaluate_all(
        """els => els.every(x => x.closest('label')?.textContent.trim()
            && x.name && x.getAttribute('value') !== null)"""
    ), "Réponse sans libellé ou non associée à la question"
    importance = stage.locator("select[data-importance]")
    assert importance.count() == 1
    assert importance.evaluate("(e) => !!e.closest('label')?.textContent.trim()")
    focused = page.locator("#compass-question-stage [data-compass-question-focus]")
    assert focused.count() == 1
    assert focused.evaluate("(e) => document.activeElement === e")
    assert focused.evaluate(
        """e => {
          const css=getComputedStyle(e);
          return css.outlineStyle !== 'none' && parseFloat(css.outlineWidth) >= 2;
        }"""
    ), "Le repère visuel de focus de la question doit être visible"


def keyboard_activate(page, selector: str) -> None:
    control = page.locator(selector)
    control.focus()
    page.keyboard.press("Enter")


def run() -> None:
    validate_contract()
    with sync_playwright() as driver:
        browser = getattr(driver, BROWSER_NAME).launch()
        try:
            for label, width, height in (
                ("desktop", 1440, 960),
                ("mobile_emule", 390, 844),
            ):
                context = browser.new_context(
                    locale="fr-CA",
                    viewport={"width": width, "height": height},
                    reduced_motion="reduce",
                    service_workers="block",
                )
                attempted_writes = []

                def prevent_writes(route) -> None:
                    request = route.request
                    if request.method != "GET":
                        attempted_writes.append(request.method)
                        route.abort()
                    else:
                        route.continue_()

                context.route("**/*", prevent_writes)
                page = context.new_page()
                response = page.goto(urljoin(BASE_URL, COMPASS),
                                     wait_until="domcontentloaded", timeout=30_000)
                assert response is not None and response.status == 200
                page.wait_for_function(
                    "() => !!document.querySelector('#compass-start') "
                    "&& !document.querySelector('#compass-start').disabled",
                    timeout=15_000,
                )
                assert page.locator("#compass-results").is_hidden()
                keyboard_activate(page, "#compass-start")
                check_question_semantics(page, "q01")
                assert page.locator("#compass-next").is_disabled()
                progress = page.locator("#compass-progress-track")
                assert progress.get_attribute("role") == "progressbar"
                assert progress.get_attribute("aria-valuenow") == "1"
                assert progress.get_attribute("aria-valuemax") == "64"

                # Le focus automatique de la légende doit permettre d'atteindre
                # les réponses sans souris, puis d'en sélectionner une par Espace.
                page.keyboard.press("Tab")
                assert page.evaluate(
                    "() => document.activeElement.matches("
                    "'#compass-question-stage input[type=radio][value=\\\"-3\\\"]')"
                ), "Tab depuis la légende n'atteint pas la première réponse"
                page.keyboard.press("Space")
                assert page.locator(
                    '#compass-question-stage input[type="radio"][value="-3"]'
                ).is_checked()
                assert not page.locator("#compass-next").is_disabled()

                keyboard_activate(page, "#compass-next")
                check_question_semantics(page, "q02")
                assert progress.get_attribute("aria-valuenow") == "2"
                # Le saut n'est pas la neutralité : il est un choix explicite.
                skip = page.locator(
                    '#compass-question-stage input[type="radio"][value="skip"]'
                )
                skip.focus()
                page.keyboard.press("Space")
                assert skip.is_checked()
                keyboard_activate(page, "#compass-next")
                check_question_semantics(page, "q03")

                # Consulter au clavier un résultat partiel sans fabriquer
                # de score après seulement une réponse exploitable.
                keyboard_activate(page, "#compass-preview")
                assert not page.locator("#compass-results").is_hidden()
                assert page.locator("#compass-results-grid .compass-result-card").count() == 16
                assert "Aucune dimension calculable" in page.locator("#compass-summary").inner_text()
                assert page.locator("#compass-results-title").evaluate(
                    "(e) => document.activeElement === e"
                ), "Le titre des résultats doit récupérer le focus"
                assert page.locator("#compass-radar polygon").count() == 0

                keyboard_activate(page, "#compass-reset")
                assert page.locator("#compass-results").is_hidden()
                assert page.locator("#compass-stepper").is_hidden()
                assert not page.locator("#compass-start-panel").is_hidden()
                assert page.locator("#compass-start").evaluate(
                    "(e) => document.activeElement === e"
                ), "Le retour au début doit restaurer un focus logique"
                assert not attempted_writes, "Tentative réseau d'écriture interdite"
                page.reload(wait_until="domcontentloaded", timeout=30_000)
                assert page.locator("#compass-results").is_hidden()
                assert not attempted_writes, "Écriture détectée après rechargement"
                print(json.dumps({
                    "browser": BROWSER_NAME,
                    "viewport": label,
                    "keyboard_path": "q01 -> q02(skip) -> q03 -> partial -> reset",
                    "question_labels": "passed",
                    "focus": "passed",
                    "status": "passed",
                    "votes_submitted": 0,
                    "network_writes_attempted": len(attempted_writes),
                    "scope": "local_browser_only_not_WCAG_certification",
                }, ensure_ascii=False))
                context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    run()
