#!/usr/bin/env python3
"""Parcours réel 18+ Projet Nova, Chromium/Firefox/WebKit, aucun envoi live."""
import os
from playwright.sync_api import sync_playwright

BROWSER = os.environ.get("BROWSER", "chromium")
URL = "http://127.0.0.1:4173/projets/projet-nova/sondage.html"


def require(condition, message):
    if not condition:
        raise AssertionError(f"{BROWSER}: {message}")


def main():
    require(BROWSER in {"chromium", "firefox", "webkit"}, "moteur non autorisé")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        page = browser.new_page(
            locale="fr-CA", viewport={"width": 390, "height": 844},
            reduced_motion="reduce",
        )
        sent = []
        page.on("request", lambda request:
                sent.append(request.url) if request.method == "POST" else None)
        try:
            response = page.goto(URL, wait_until="domcontentloaded", timeout=30_000)
            require(response is not None and response.status in (200, 304),
                    "page de sondage non disponible localement")
            page.wait_for_function(
                "() => !document.getElementById('sondage-start').disabled || "
                "document.querySelector('#sondage-introduction [role=alert]')",
                timeout=10_000,
            ) if False else None
            # Les réponses ne doivent être saisissables qu'une fois le
            # manifeste chargé et les deux cases vérifiées.
            page.locator("#sondage-age").check()
            page.locator("#sondage-consent").uncheck()
            require(page.locator("#sondage-start").is_disabled(),
                    "Consentement non exigé avant démarrage")
            page.locator("#sondage-age").uncheck()
            page.locator("#sondage-consent").check()
            require(page.locator("#sondage-start").is_disabled(),
                    "Contrôle 18 ans contournable")
            page.locator("#sondage-age").check()
            page.locator("#sondage-start").wait_for(state="attached")
            page.wait_for_function(
                "() => !document.getElementById('sondage-start').disabled",
                timeout=15_000,
            )
            page.locator("#sondage-start").click()
            require(not page.locator("#sondage-questionnaire").is_hidden(),
                    "Première question non affichée")
            require(page.locator("#sondage-choices input[type=radio]").count() == 8,
                    "Échelle -3..+3 et Sans opinion non disponible")
            page.locator("#sondage-choices input[value='1']").check()
            page.locator("#sondage-next").click()
            require("Question 2 sur 64" in page.locator("#sondage-position").inner_text(),
                    "Progression de la question 2 incorrecte")
            page.locator("#sondage-choices input[value='skip']").check()
            page.locator("#sondage-back").click()
            require(page.locator("#sondage-choices input[value='1']").is_checked(),
                    "Retour à la question 1 : choix perdu")
            page.locator("#sondage-next").click()
            require(page.locator("#sondage-choices input[value='skip']").is_checked(),
                    "Retour à la question 2 : Sans opinion perdu")
            page.locator("#sondage-next").click()
            for position in range(3, 65):
                require(
                    f"Question {position} sur 64" in page.locator("#sondage-position").inner_text(),
                    f"Question {position} non présentée individuellement",
                )
                page.locator("#sondage-choices input[value='skip']").check()
                page.locator("#sondage-next").click()
            require(not page.locator("#sondage-finish").is_hidden(),
                    "Écran final absent après 64 questions")
            require(page.locator("#sondage-submit").is_disabled(),
                    "Envoi politique non approuvé activé par erreur")
            require("non ouverte" in page.locator("#sondage-submit-status").inner_text(),
                    "État réel de la collecte masqué")
            require(sent == [], f"Une réponse a quitté le navigateur : {sent}")
            page.locator("#sondage-review").click()
            require(not page.locator("#sondage-questionnaire").is_hidden(),
                    "Relecture des questions impossible")
            require(page.locator("#sondage-choices input[value='skip']").is_checked(),
                    "Dernière réponse perdue en relecture")
            require(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
                    "Débordement horizontal en 390 px")
            page.set_viewport_size({"width": 1440, "height": 900})
            require(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
                    "Débordement horizontal sur ordinateur")
            print(f"OK {BROWSER}: Nova 18+, consentement, 64 questions, "
                  "relecture, aucun POST et collecte désactivée")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
