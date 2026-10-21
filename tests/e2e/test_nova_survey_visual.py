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
            require("Cette case ne constitue pas un consentement à une future collecte." in
                    page.locator("label:has(#sondage-consent)").inner_text(),
                    "La démonstration exige un nouvel accord de collecte pour une future activation")
            require(page.locator("#sondage-form").get_attribute("autocomplete") == "off",
                    "Autocomplétion du questionnaire non désactivée")
            require(page.locator("#sondage-consent").get_attribute("autocomplete") == "off",
                    "Autocomplétion de l'accord de démonstration non désactivée")
            # Les réponses ne doivent être saisissables qu'une fois le
            # manifeste chargé et les deux cases vérifiées.
            require("Une fois une contribution agrégée" in page.locator("#sondage-privacy-warning").inner_text(),
                    "Avertissement de retrait des agrégats absent")
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
            require(page.locator("#sondage-choices input[type=radio]").first.get_attribute("autocomplete") == "off",
                    "Le navigateur ne doit pas mémoriser automatiquement les choix politiques")
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
            require(page.locator("#sondage-review-list li").count() == 64,
                    "Récapitulatif des 64 choix absent")
            require("Votre choix : Plutôt d’accord" in
                    page.locator("#sondage-review-list li").first.inner_text(),
                    "Première réponse non affichée")
            require("Sans opinion" in page.locator("#sondage-review-list li").last.inner_text(),
                    "La réponse Sans opinion n'apparaît pas dans le récapitulatif")
            require(page.locator("#sondage-submit").is_disabled(),
                    "Envoi politique non approuvé activé par erreur")
            require("non ouverte" in page.locator("#sondage-submit-status").inner_text(),
                    "État réel de la collecte masqué")
            require(sent == [], f"Une réponse a quitté le navigateur : {sent}")
            page.locator("#sondage-review-list li").first.locator("button").click()
            require("Question 1 sur 64" in page.locator("#sondage-position").inner_text(),
                    "Modification directe impossible")
            require(page.locator("#sondage-choices input[value='1']").is_checked(),
                    "Réponse originale perdue")
            page.locator("#sondage-choices input[value='-2']").check()
            page.locator("#sondage-next").click()
            require(not page.locator("#sondage-finish").is_hidden(),
                    "Retour au récapitulatif impossible après correction")
            require("Votre choix : En désaccord" in
                    page.locator("#sondage-review-list li").first.inner_text(),
                    "Réponse corrigée non reflétée")
            require("Sans opinion" in page.locator("#sondage-review-list li").last.inner_text(),
                    "Dernière réponse perdue pendant la correction")
            page.locator("#sondage-review").click()
            require(not page.locator("#sondage-questionnaire").is_hidden(),
                    "Relecture des questions impossible")
            require("Question 1 sur 64" in page.locator("#sondage-position").inner_text(),
                    "La relecture ne démarre pas à la première question")
            require(page.locator("#sondage-choices input[value='-2']").is_checked(),
                    "Réponse corrigée perdue")
            require(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
                    "Débordement horizontal en 390 px")
            page.once("dialog", lambda dialog: dialog.accept())
            page.locator("#sondage-reset-question").click()
            require(not page.locator("#sondage-introduction").is_hidden(),
                    "Retour au consentement après effacement impossible")
            require(not page.locator("#sondage-age").is_checked(),
                    "Attestation 18 ans non réinitialisée")
            require(not page.locator("#sondage-consent").is_checked(),
                    "Consentement non réinitialisé")
            require(page.locator("#sondage-start").is_disabled(),
                    "Démarrage encore autorisé après retrait du consentement")
            page.locator("#sondage-age").check()
            page.locator("#sondage-consent").check()
            page.locator("#sondage-start").click()
            require(page.locator("#sondage-next").is_disabled(),
                    "Des opinions sont restées dans la mémoire après effacement")
            require(not page.locator("#sondage-choices input[value='1']").is_checked(),
                    "Ancienne réponse retrouvée après purge")
            require(sent == [], f"Des réponses ont été envoyées malgré la collecte fermée : {sent}")
            page.locator("#sondage-choices input[value='1']").check()
            page.goto("http://127.0.0.1:4173/projets/projet-nova/", wait_until="domcontentloaded")
            page.go_back(wait_until="domcontentloaded")
            require(not page.locator("#sondage-introduction").is_hidden(),
                    "Retour historique : le sondage ne revient pas à l'introduction")
            require(not page.locator("#sondage-age").is_checked()
                    and not page.locator("#sondage-consent").is_checked(),
                    "Retour historique : attestation 18+ ou accord de démonstration conservé")
            require(page.locator("#sondage-start").is_disabled(),
                    "Retour historique : démarrage sans nouvelle attestation")
            page.reload(wait_until="domcontentloaded")
            require(not page.locator("#sondage-introduction").is_hidden()
                    and not page.locator("#sondage-age").is_checked()
                    and not page.locator("#sondage-consent").is_checked(),
                    "Rechargement : confirmation d'âge ou accord restauré")
            require(page.locator("#sondage-start").is_disabled(),
                    "Rechargement : questionnaire lancé sans attestation")
            require(sent == [], "Historique/rechargement : requête de collecte non autorisée")
            page.set_viewport_size({"width": 1440, "height": 900})
            require(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
                    "Débordement horizontal sur ordinateur")
            print(f"OK {BROWSER}: Nova 18+, consentement, 64 questions, "
                  "relecture, aucun POST et collecte désactivée")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
