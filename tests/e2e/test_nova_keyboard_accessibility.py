#!/usr/bin/env python3
"""Nova : accès clavier aux deux sondages et à la Boussole depuis l'artefact Web.

Exécution : BROWSER=chromium|firefox|webkit python tests/e2e/test_nova_keyboard_accessibility.py
Le serveur local doit servir le paquet public _site sur le port 4173.
Aucune collecte ni opinion réelle n'est transmise.
"""
from __future__ import annotations

import os
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4173/projets/projet-nova/"
BROWSER = os.environ.get("BROWSER", "chromium")


def check(ok, message):
    if not ok:
        raise AssertionError(f"{BROWSER}: {message}")


def response_labels(page, selector):
    return page.locator(selector).evaluate_all("""elements => elements.every(input => {
      const label = input.closest('label');
      return label && label.textContent && label.textContent.trim().length > 0;
    })""")


def survey(browser, filename, count):
    page = browser.new_page(locale="fr-CA", viewport={"width": 390, "height": 844},
                            reduced_motion="reduce")
    posted = []
    page.on("request", lambda request: posted.append(request.url)
            if request.method == "POST" else None)
    try:
        res = page.goto(BASE + filename, wait_until="domcontentloaded", timeout=30_000)
        check(res is not None and res.status in (200, 304),
              f"{filename}: page absente")
        # Ne pas cocher des cases avant l'initialisation asynchrone du corpus
        # (manifestes + SHA-256), surtout avec WebKit et cache froid.
        page.locator('#sondage-start[data-ready="true"]').wait_for(
            state="visible", timeout=25_000)
        check(page.locator("#sondage-start").is_disabled(),
              f"{filename}: démarrage sans attestation ni accord")
        for field in ("#sondage-age", "#sondage-consent"):
            page.locator(field).focus()
            page.keyboard.press("Space")
            check(page.locator(field).is_checked(),
                  f"{filename}: case {field} inopérante au clavier")
        page.wait_for_function(
            "() => !document.querySelector('#sondage-start').disabled",
            timeout=25_000)
        page.locator("#sondage-start").focus()
        page.keyboard.press("Enter")
        check(page.locator("#sondage-questionnaire").is_visible(),
              f"{filename}: démarrage par Entrée impossible")
        heading = page.locator("#sondage-question-heading")
        check(heading.inner_text().strip() != "",
              f"{filename}: intitulé de question absent")
        group = page.locator("#sondage-choices")
        check(group.get_attribute("role") == "radiogroup" and
              group.get_attribute("aria-labelledby") == "sondage-question-heading",
              f"{filename}: groupe de réponses sans nom accessible")
        radios = page.locator("#sondage-choices input[type=radio]")
        check(radios.count() >= 3 and response_labels(page, "#sondage-choices input[type=radio]"),
              f"{filename}: réponses sans libellés accessibles")
        check(page.locator("#sondage-next").is_disabled(),
              f"{filename}: avancer sans réponse")
        # Le focus sur la légende est volontairement programmatique. Tab doit
        # atteindre un contrôle de réponse, y compris dans WebKit mobile.
        check(heading.locator("[data-sondage-question-focus]").evaluate("el => el === document.activeElement"),
              f"{filename}: focus non transmis à la nouvelle question")
        page.keyboard.press("Tab")
        check(radios.first.evaluate("el => el === document.activeElement"),
              f"{filename}: premier choix inaccessible par Tab")
        page.keyboard.press("Space")
        check(radios.first.is_checked() and page.locator("#sondage-next").is_enabled(),
              f"{filename}: choix ou progression impossible avec Espace")
        page.locator("#sondage-next").focus()
        page.keyboard.press("Enter")
        check("Question 2 sur " + str(count) in page.locator("#sondage-position").inner_text(),
              f"{filename}: progression par Entrée impossible")
        page.wait_for_function("""() => {
            const title=document.querySelector('[data-sondage-question-focus]');
            return title && document.activeElement===title;
        }""", timeout=5_000)
        check(heading.locator("[data-sondage-question-focus]").evaluate("el => el === document.activeElement"),
              f"{filename}: focus non déplacé après navigation")
        check(not posted, f"{filename}: transmission réseau pendant parcours clavier")
        print(f"PASS accessibilité clavier {filename}: consentement, noms, réponse, progression, 0 POST")
    finally:
        page.close()


def compass(browser):
    page = browser.new_page(locale="fr-CA", viewport={"width": 390, "height": 844},
                            reduced_motion="reduce")
    posted = []
    page.on("request", lambda request: posted.append(request.url)
            if request.method == "POST" else None)
    try:
        res = page.goto(BASE + "boussole-electorale.html",
                        wait_until="domcontentloaded", timeout=30_000)
        check(res is not None and res.status in (200, 304), "Boussole : page absente")
        page.locator("#compass-start").wait_for(state="visible", timeout=25_000)
        page.wait_for_function(
            "() => !document.querySelector('#compass-start').disabled",
            timeout=25_000)
        page.locator("#compass-start").focus()
        page.keyboard.press("Enter")
        fieldset = page.locator("#compass-question-stage fieldset")
        check(fieldset.count() == 1, "Boussole : question non affichée au clavier")
        check(fieldset.locator("legend").count() == 1,
              "Boussole : légende native absente")
        group = fieldset.locator('[role="radiogroup"]')
        check(group.get_attribute("aria-labelledby") == "compass-question-title",
              "Boussole : nom du groupe de choix incorrect")
        radios = fieldset.locator('input[type="radio"]')
        check(radios.count() == 8 and response_labels(page,
              '#compass-question-stage input[type="radio"]'),
              "Boussole : huit réponses sans libellé accessible")
        heading = fieldset.locator("[data-compass-question-focus]")
        check(heading.evaluate("el => el === document.activeElement"),
              "Boussole : focus initial inaccessible")
        check(page.locator("#compass-next").is_disabled(),
              "Boussole : avancer sans réponse")
        page.keyboard.press("Tab")
        check(radios.first.evaluate("el => el === document.activeElement"),
              "Boussole : première réponse inaccessible par Tab")
        page.keyboard.press("Space")
        check(radios.first.is_checked() and page.locator("#compass-next").is_enabled(),
              "Boussole : réponse clavier non enregistrée")
        page.locator("#compass-next").focus()
        page.keyboard.press("Enter")
        check("Question 2 sur 64" in page.locator("#compass-progress-text").inner_text(),
              "Boussole : progression au clavier impossible")
        check(page.locator("[data-compass-question-focus]").evaluate(
              "el => el === document.activeElement"),
              "Boussole : focus non déplacé vers la question suivante")
        check(not posted, "Boussole : transmission réseau pendant navigation clavier")
        print("PASS accessibilité clavier Boussole : noms, réponse, progression, 0 POST")
    finally:
        page.close()


def main():
    check(BROWSER in ("chromium", "firefox", "webkit"), "navigateur invalide")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        try:
            survey(browser, "consultation-40.html", 40)
            survey(browser, "sondage.html", 64)
            compass(browser)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
