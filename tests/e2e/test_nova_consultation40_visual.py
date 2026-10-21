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
        homepage = page.goto("http://127.0.0.1:4173/projets/projet-nova/",
                             wait_until="domcontentloaded", timeout=30000)
        check(homepage is not None and homepage.status == 200,
              "accueil Projet Nova inaccessible")
        check(page.locator("#consultations").is_visible(),
              "annuaire des consultations invisible depuis l'accueil")
        icons = page.locator(".nova-survey-directory-icon-link img")
        check(icons.count() == 2, "Icônes des deux cartes de sondage absentes")
        for icon in icons.all():
            expect(icon).to_have_js_property("naturalWidth", 256, timeout=15000)
        check(page.locator(".nova-survey-directory-icon-link").first.get_attribute("href") == "consultation-40.html",
              "L'icône du sondage référendaire ne donne pas accès aux 40 questions")
        check(page.locator(".nova-survey-directory-icon-link").nth(1).get_attribute("href") == "sondage.html",
              "L'icône du sondage citoyen ne donne pas accès aux 64 propositions")
        check(page.locator("#nova-survey-directory-40").get_attribute("href") == "consultation-40.html",
              "lien 40 questions incorrect")
        check(page.locator("#nova-survey-directory-64").get_attribute("href") == "sondage.html",
              "lien 64 propositions incorrect")
        check("collecte fermée" in page.locator("#consultations").inner_text().lower(),
              "état réel de la collecte non affiché")
        check(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
              "débordement horizontal sur l'accueil mobile")
        page.locator("#nova-survey-directory-40").click()
        page.wait_for_url("**/consultation-40.html", timeout=15000)
        response = page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        check(response is not None and response.status == 200, "page de consultation absente")
        check("non officiel" in page.locator("#sondage-introduction").inner_text(),
              "statut consultatif et non officiel absent")
        check("Une fois une contribution agrégée" in page.locator("#sondage-privacy-warning").inner_text(),
              "avis sur la limite de retrait absent")
        check(page.locator("#sondage-start").is_disabled(), "verrou 18+ et accord de démonstration absent")
        check("Cette case ne constitue pas un consentement à une future collecte." in
              page.locator("label:has(#sondage-consent)").inner_text(),
              "l'accord de démonstration doit être séparé d'un consentement futur")
        check(page.locator("#sondage-form").get_attribute("autocomplete") == "off",
              "persistance navigateur du formulaire non désactivée")
        check(page.locator("#sondage-consent").get_attribute("autocomplete") == "off",
              "restauration automatique de l'accord de démonstration non désactivée")
        page.locator("#sondage-age").check()
        check(page.locator("#sondage-start").is_disabled(), "consentement distinct absent")
        page.locator("#sondage-consent").check()
        expect(page.locator("#sondage-start")).to_be_enabled(timeout=10000)
        page.locator("#sondage-start").click()
        check(page.locator("#sondage-position").inner_text().startswith("Question 1 sur 40"),
              "première question manquante")
        check(page.locator("input[name='nova40-response']").first.get_attribute("autocomplete") == "off",
              "réponses politiques exposées à l'autocomplétion du navigateur")
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
        page.locator("input[value=pour]").check()
        page.goto("http://127.0.0.1:4173/projets/projet-nova/", wait_until="domcontentloaded")
        page.go_back(wait_until="domcontentloaded")
        check(page.locator("#sondage-introduction").is_visible(),
              "retour historique : la consultation doit redémarrer à l'introduction")
        check(not page.locator("#sondage-age").is_checked()
              and not page.locator("#sondage-consent").is_checked(),
              "retour historique : attestation 18+ ou accord de démonstration conservé")
        check(page.locator("#sondage-start").is_disabled(),
              "retour historique : démarrage encore autorisé")
        page.reload(wait_until="domcontentloaded")
        check(page.locator("#sondage-introduction").is_visible()
              and not page.locator("#sondage-age").is_checked()
              and not page.locator("#sondage-consent").is_checked(),
              "rechargement : préférences politiques ou consentement restaurés")
        check(page.locator("#sondage-start").is_disabled(),
              "rechargement : démarrage autorisé sans nouvelle attestation")
        check(not calls, "rechargement ou historique ont déclenché une transmission")
        print(f"OK {BROWSER}: 40 questions 18+, historique, rechargement, révision, purge et collecte fermée")
    finally:
        browser.close()
