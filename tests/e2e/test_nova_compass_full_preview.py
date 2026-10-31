#!/usr/bin/env python3
"""Parcours complet de la Boussole en prévisualisation locale, sans aucun envoi.

Exécution: BROWSER=chromium|firefox|webkit python tests/e2e/test_nova_compass_full_preview.py
Le serveur HTTP doit être disponible sur 127.0.0.1:4173.
"""
from __future__ import annotations

import os
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:4173/projets/projet-nova/boussole-electorale.html"
BROWSER = os.environ.get("BROWSER", "chromium")


def require(condition, message):
    if not condition:
        raise AssertionError(f"{BROWSER}: {message}")


def main():
    require(BROWSER in {"chromium", "firefox", "webkit"}, "navigateur non autorisé")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        context = browser.new_context(
            locale="fr-CA",
            viewport={"width": 390, "height": 844},
            reduced_motion="reduce",
        )
        page = context.new_page()
        submitted = []
        page.on("request", lambda request: submitted.append(request.url)
                if request.method == "POST" else None)
        try:
            response = page.goto(URL, wait_until="domcontentloaded", timeout=30_000)
            require(response is not None and response.status == 200,
                    "page de la Boussole absente de la prévisualisation")
            page.locator("#compass-start").wait_for(state="visible", timeout=25_000)
            page.locator("#compass-start").click()
            require(page.locator("#compass-question-stage fieldset").count() == 1,
                    "la première question ne s'affiche pas")

            # Sans opinion n'est pas neutre et doit survivre à un aller-retour.
            page.locator('#compass-question-stage input[type="radio"][value="skip"]').check()
            page.locator("#compass-next").click()
            require("Question 2 sur 64" in page.locator("#compass-progress-text").inner_text(),
                    "navigation vers la question 2 impossible")
            page.locator("#compass-prev").click()
            require(page.locator('#compass-question-stage input[value="skip"]').is_checked(),
                    "l'option Sans opinion a été oubliée")
            page.locator("#compass-reset").click()

            # 64 réponses neutres explicites doivent produire 16 vrais scores 0,
            # pas 16 scores inconnus, et une couverture 100 % sur chaque dimension.
            neutral = page.evaluate("""() => {
                document.querySelector("#compass-start").click();
                for (let step = 1; step <= 64; step++) {
                    const fieldset = document.querySelector("#compass-question-stage fieldset");
                    const heading = fieldset?.querySelector(".compass-question-counter")?.textContent || "";
                    const radio = fieldset?.querySelector('input[type="radio"][value="0"]');
                    const next = document.querySelector("#compass-next");
                    if (!heading.includes("Question " + step + " sur 64") || !radio || !next ||
                        !document.querySelector("#compass-results").hidden)
                        return {ok:false,step,reason:"étape ou commande manquante"};
                    radio.click();
                    if (next.disabled)
                        return {ok:false,step,reason:"bouton Suivant inactif"};
                    next.click();
                }
                const cards = [...document.querySelectorAll("#compass-results-grid .compass-result-card")];
                const checks = cards.map(card => ({
                    score: card.querySelector(".compass-result-head strong")?.textContent?.trim(),
                    coverage: card.querySelector(".compass-result-meta")?.textContent?.trim()
                }));
                return {
                    ok: !document.querySelector("#compass-results").hidden &&
                        checks.length === 16 &&
                        checks.every(c => c.score === "0" &&
                            c.coverage.includes("4/4 réponses (100 %)")) &&
                        document.querySelector("#compass-summary").textContent.includes("100 %"),
                    step:64, dimensionCount:checks.length, checks
                };
            }""")
            require(neutral["ok"], "profil neutre incomplet: " + repr(neutral))
            require(not submitted, "une opinion politique a été transmise pendant le test")

            page.locator("#compass-reset").click()
            require(page.locator("#compass-results").is_hidden()
                    and page.locator("#compass-results-grid .compass-result-card").count() == 0
                    and page.locator("#compass-start").is_visible(),
                    "le résultat subsiste après réinitialisation")

            # 64 choix « Sans opinion » ne doivent pas fabriquer de scores.
            skipped = page.evaluate("""() => {
                document.querySelector("#compass-start").click();
                for (let step = 1; step <= 64; step++) {
                    const radio = document.querySelector(
                        '#compass-question-stage input[type="radio"][value="skip"]'
                    );
                    const next = document.querySelector("#compass-next");
                    if (!radio || !next) return {ok:false,step};
                    radio.click();
                    next.click();
                }
                return {
                    ok: document.querySelector("#compass-results").hidden &&
                        document.querySelectorAll("#compass-results-grid .compass-result-card").length === 0 &&
                        document.querySelector("#compass-status").textContent.includes("au moins une"),
                    step:64
                };
            }""")
            require(skipped["ok"], "64 choix Sans opinion ont produit un faux profil: " + repr(skipped))
            page.locator("#compass-reset").click()
            require(not submitted, "POST interdit détecté pendant la Boussole")
            print(f"PASS {BROWSER}: 64 questions, 16 scores neutres à zéro, "
                  "couverture 4/4, Sans opinion distinct, réinitialisation, zéro POST")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
