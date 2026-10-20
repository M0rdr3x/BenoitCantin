#!/usr/bin/env python3
"""Parcours navigateur : opinion référendaire non officielle, 40 questions et aucune collecte."""
import os
from playwright.sync_api import expect, sync_playwright

BROWSER = os.environ.get("BROWSER", "chromium")
URL = "http://127.0.0.1:4173/projets/projet-nova/consultation-40.html"

def check(ok, message):
    if not ok:
        raise AssertionError(f"{BROWSER}: {message}")

with sync_playwright() as p:
    browser = getattr(p, BROWSER).launch()
    page = browser.new_page(viewport={"width": 390, "height": 844}, locale="fr-CA")
    try:
        calls = []
        page.on("request", lambda req: calls.append(req.url)
                if "nova-consultation40-submit" in req.url else None)
        response = page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        check(response is not None and response.status == 200, "page de consultation absente")
        check("non officiel" in page.locator("#sondage-introduction").inner_text(),
              "statut consultatif et non officiel absent")
        check("Une fois une contribution agrégée" in page.locator("#sondage-privacy-warning").inner_text(),
              "avis sur la limite de retrait absent")
        check(page.locator("#sondage-start").is_disabled(), "verrou 18+ et consentement absent")
        page.locator("#sondage-age").check()
        check(page.locator("#sondage-start").is_disabled(), "consentement distinct absent")
        page.locator("#sondage-consent").check()
        expect(page.locator("#sondage-start")).to_be_enabled(timeout=10000)
        page.locator("#sondage-start").click()
        check(page.locator("#sondage-position").inner_text().startswith("Question 1 sur 40"),
              "première question manquante")
        check("Québec" in page.locator("#sondage-question-heading").inner_text(),
              "question référendaire initiale absente")
        check(page.locator("#sondage-next").is_disabled(), "réponse vide franchit une étape")
        page.locator("input[value=pour]").check()
        page.locator("#sondage-next").click()
        check("Question 2 sur 40" in page.locator("#sondage-position").inner_text(),
              "progression cassée")
        page.locator("#sondage-back").click()
        check(page.locator("input[value=pour]").is_checked(), "réponse perdue après retour")
        page.locator("#sondage-next").click()
        for n in range(2, 41):
            check(f"Question {n} sur 40" in page.locator("#sondage-position").inner_text(),
                  f"question {n} absente")
            page.locator("input[value=contre]" if n % 2 == 0
                         else "input[value=sans_opinion]").check()
            page.locator("#sondage-next").click()
        check(page.locator("#sondage-finish").is_visible(), "récapitulatif final absent")
        check(page.locator("#sondage-review-list li").count() == 40,
              "40 réponses du récapitulatif absentes")
        check(page.locator("#sondage-submit").is_disabled(), "collecte doit rester inactive")
        check(not calls, "des réponses ont été transmises")
        page.locator("#sondage-review-list li").first.locator("button").click()
        check(page.locator("#sondage-position").inner_text().startswith("Question 1 sur 40"),
              "édition directe d'une réponse impossible")
        check(page.locator("input[value=pour]").is_checked(), "valeur de révision perdue")
        page.locator("input[value=contre]").check()
        page.locator("#sondage-next").click()
        check(page.locator("#sondage-finish").is_visible(), "retour au récapitulatif absent")
        check("Votre choix : Contre" in page.locator("#sondage-review-list li").first.inner_text(),
              "révision non reflétée dans le récapitulatif")
        page.locator("#sondage-review").click()
        check(page.locator("#sondage-questionnaire").is_visible(), "relecture complète impossible")
        check(page.locator("input[value=contre]").is_checked(),
              "réponse modifiée perdue à la relecture")
        page.once("dialog", lambda dialog: dialog.accept())
        page.locator("#sondage-reset-question").click()
        check(page.locator("#sondage-introduction").is_visible(),
              "effacement et retour au début impossibles")
        check(not page.locator("#sondage-age").is_checked(),
              "confirmation d'âge conservée après effacement")
        check(not page.locator("#sondage-consent").is_checked(),
              "consentement conservé après effacement")
        check(page.locator("#sondage-start").is_disabled(), "démarrage non verrouillé après effacement")
        page.locator("#sondage-age").check()
        page.locator("#sondage-consent").check()
        page.locator("#sondage-start").click()
        check(page.locator("#sondage-next").is_disabled(),
              "réponses conservées après l'effacement demandé")
        check(not page.locator("input[value=contre]").is_checked(),
              "opinion personnelle encore présente après effacement")
        check(not calls, "un envoi politique s'est déclenché en aperçu")
        print(f"OK {BROWSER}: 40 questions 18+, navigation, révision, effacement et collecte fermée")
    finally:
        browser.close()
