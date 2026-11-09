#!/usr/bin/env python3
"""Vérification automatisée du clavier et des repères de focus de la Boussole.

Parcours LOCAL uniquement : aucune donnée politique n'est envoyée, aucun
bulletin n'est créé, et ceci ne remplace pas un audit WCAG manuel indépendant.
"""
from __future__ import annotations

import json
import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER_NAME = os.environ.get("BROWSER", "chromium").strip().lower()
BROWSERS = {"chromium", "firefox", "webkit"}


def assert_focus(page, selector, message):
    active = page.evaluate(
        """selector => document.activeElement === document.querySelector(selector)""",
        selector,
    )
    assert active, message


def assert_focus_in_viewport(page, label):
    """Détecte un focus hors écran; ne détecte pas tous les recouvrements CSS."""
    measure = page.evaluate(
        """() => {
          const el = document.activeElement;
          if (!el || !el.isConnected) return {in_viewport:false, reason:"no_active_element"};
          const r = el.getBoundingClientRect();
          const st = getComputedStyle(el);
          return {
            in_viewport: r.width > 0 && r.height > 0 &&
              r.right > 0 && r.bottom > 0 &&
              r.left < innerWidth && r.top < innerHeight &&
              st.visibility !== "hidden" && st.display !== "none",
            x:r.x,y:r.y,width:r.width,height:r.height,
            viewport_width:innerWidth,viewport_height:innerHeight
          };
        }"""
    )
    assert measure["in_viewport"], label + ": focus hors écran / invisible: " + repr(measure)


def focused_outline(page):
    return page.evaluate(
        """() => {
            const style = getComputedStyle(document.activeElement);
            return {style:style.outlineStyle, width:parseFloat(style.outlineWidth),
                    color:style.outlineColor};
        }"""
    )


def run_view(browser, width, height):
    context = browser.new_context(
        viewport={"width": width, "height": height},
        locale="fr-CA",
        reduced_motion="reduce",
        service_workers="block",
    )
    forbidden_writes = []

    def no_write(route):
        if route.request.method != "GET":
            forbidden_writes.append(route.request.method)
            route.abort()
        else:
            route.continue_()

    context.route("**/*", no_write)
    page = context.new_page()
    url = urljoin(BASE_URL, "projets/projet-nova/boussole-electorale.html")
    response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
    assert response is not None and response.status == 200, "Page locale indisponible"
    page.locator("#compass-start").wait_for(state="visible")
    page.wait_for_function("() => !document.querySelector('#compass-start').disabled")
    css_link = page.locator('link[href*="assets/boussole-electorale.css"]').get_attribute("href")
    assert css_link == "assets/boussole-electorale.css?v=3.6.12", "Style de focus non versionné"
    assert page.locator("#compass-status").get_attribute("role") == "status"
    assert page.locator("#compass-status").get_attribute("aria-live") == "polite"
    assert page.locator("#compass-results").is_hidden()

    page.locator("#compass-start").focus()
    page.keyboard.press("Enter")
    assert page.locator("#compass-stepper").is_visible()
    assert page.locator("#compass-question-stage fieldset").get_attribute("data-question-id") == "q01"
    assert_focus(page, "[data-compass-question-focus]", "Focus question Q01 manquant")
    assert_focus_in_viewport(page, "Question Q01")
    assert page.locator("#compass-progress-track").get_attribute("aria-valuemax") == "64"
    assert page.locator("#compass-progress-track").get_attribute("aria-valuenow") == "1"

    # Depuis le titre focalisé, Tab doit atteindre un vrai contrôle radio.
    page.keyboard.press("Tab")
    assert page.evaluate(
        """() => document.activeElement?.matches(
            '#compass-question-stage input[type="radio"]')"""
    ), "Radio inaccessible au clavier"
    page.keyboard.press("Space")
    assert page.locator("#compass-next").is_enabled()
    assert "enregistrée localement" in page.locator("#compass-status").inner_text()

    page.keyboard.press("Tab")
    assert_focus(page, "#compass-question-stage [data-importance]", "Select importance inaccessible")
    assert_focus_in_viewport(page, "Sélecteur importance")
    outline = focused_outline(page)
    assert outline["style"] != "none" and outline["width"] >= 3, (
        "Repère de focus sur l'importance absent: " + repr(outline)
    )
    page.keyboard.press("ArrowDown")
    assert page.locator("#compass-question-stage [data-importance]").input_value() == "forte"

    # À Q01, le bouton Précédent est désactivé et doit être ignoré par Tab.
    page.keyboard.press("Tab")
    assert_focus(page, "#compass-next", "Suivant non accessible au clavier à Q01")
    assert_focus_in_viewport(page, "Suivant Q01")
    outline = focused_outline(page)
    assert outline["style"] != "none" and outline["width"] >= 3, "Suivant sans focus visible"
    page.keyboard.press("Enter")
    assert page.locator("#compass-question-stage fieldset").get_attribute("data-question-id") == "q02"
    assert_focus(page, "[data-compass-question-focus]", "Focus question Q02 manquant")
    assert_focus_in_viewport(page, "Question Q02")
    assert page.locator("#compass-progress-track").get_attribute("aria-valuenow") == "2"

    page.keyboard.press("Tab")
    page.keyboard.press("Space")
    assert page.locator("#compass-next").is_enabled()
    page.keyboard.press("Tab")  # importance
    page.keyboard.press("Tab")  # précédent
    assert_focus(page, "#compass-prev", "Précédent inaccessible à Q02")
    assert_focus_in_viewport(page, "Précédent Q02")
    page.keyboard.press("Tab")  # suivant
    page.keyboard.press("Tab")  # profil partiel
    assert_focus(page, "#compass-preview", "Profil partiel inaccessible au clavier")
    assert_focus_in_viewport(page, "Profil partiel")
    page.keyboard.press("Enter")
    assert not page.locator("#compass-results").is_hidden(), "Profil non affiché"
    assert_focus(page, "#compass-results-title", "Le titre des résultats ne reçoit pas le focus")
    assert_focus_in_viewport(page, "Titre du résultat")
    outline = focused_outline(page)
    assert outline["style"] != "none" and outline["width"] >= 3, "Résultats sans focus visible"
    assert page.locator("#compass-results-grid .compass-result-card").count() == 16
    assert page.locator("#compass-radar svg[role='img']").count() == 1

    page.locator("#compass-reset").focus()
    page.keyboard.press("Enter")
    assert page.locator("#compass-results").is_hidden()
    assert page.locator("#compass-start-panel").is_visible()
    assert_focus(page, "#compass-start", "Recommencer ne rend pas le focus au départ")
    assert_focus_in_viewport(page, "Retour au départ")
    assert page.locator("#compass-stepper").is_hidden()
    assert page.locator("#compass-start").is_enabled()
    assert page.evaluate(
        """() => getComputedStyle(
          document.getElementById('compass-progress-bar')).transitionDuration"""
    ) in ("0s", "0s, 0s"), "Mouvement réduit ignoré"
    assert not forbidden_writes, "Tentative de requête d'écriture: " + repr(forbidden_writes)
    print(json.dumps({
        "browser": BROWSER_NAME, "viewport": width, "keyboard_focus": "passed",
        "questions_checked": 2, "result_cards": 16,
        "political_network_writes": len(forbidden_writes),
        "geometric_viewport_focus_checks": 8,
        "manual_wcag_certified": False,
    }, ensure_ascii=False))
    context.close()


def main():
    assert BROWSER_NAME in BROWSERS, "Moteur navigateur non autorisé"
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER_NAME).launch()
        try:
            for width, height in [(1440, 900), (390, 844)]:
                run_view(browser, width, height)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
