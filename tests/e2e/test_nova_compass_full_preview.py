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
            page.evaluate("""() => {
                window.__novaDetachedCompass = document.querySelector(
                    '#compass-question-stage fieldset');
            }""")
            page.locator("#compass-next").click()
            require("Question 2 sur 64" in page.locator("#compass-progress-text").inner_text(),
                    "navigation vers la question 2 impossible")
            page.locator("#compass-prev").click()
            require(page.locator('#compass-question-stage input[value="skip"]').is_checked(),
                    "l'option Sans opinion a été oubliée")
            page.locator("#compass-reset").click()
            # Une ancienne fermeture "change" demeure sur le fieldset détaché.
            # Même après avoir commencé une nouvelle visite, elle ne peut plus
            # recréer de score/importance ni activer Suivant.
            stale = page.evaluate("""() => {
                document.querySelector("#compass-start").click();
                const fieldset=window.__novaDetachedCompass;
                delete window.__novaDetachedCompass;
                const oldRadio=fieldset.querySelector('input[type="radio"][value="3"]');
                const oldWeight=fieldset.querySelector("[data-importance]");
                oldRadio.dispatchEvent(new Event("change",{bubbles:true}));
                oldWeight.value="forte";
                oldWeight.dispatchEvent(new Event("change",{bubbles:true}));
                const next=document.querySelector("#compass-next");
                const progress=document.querySelector("#compass-progress-text").textContent;
                const ok=next.disabled && progress.includes("0 réponse") &&
                    !document.querySelector("#compass-question-stage input:checked");
                document.querySelector("#compass-reset").click();
                return {ok,progress};
            }""")
            require(stale["ok"], "Réponse/importance ressuscitée par un ancien champ: "+repr(stale))

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
            # La présentation finale doit être stable : un ancien événement
            # « Suivant » ne doit pas recréer 16 cartes ni changer le partage.
            frozen = page.evaluate("""() => {
                const next=document.querySelector("#compass-next");
                const cards=document.querySelector("#compass-results-grid");
                const originalCard=cards.firstElementChild;
                const originalCopy=document.querySelector("#compass-copy-result").onclick;
                const originalStatus=document.querySelector("#compass-status").textContent;
                next.dispatchEvent(new Event("click",{bubbles:true}));
                return next.disabled && !document.querySelector("#compass-results").hidden &&
                    cards.firstElementChild===originalCard &&
                    document.querySelector("#compass-copy-result").onclick===originalCopy &&
                    document.querySelector("#compass-status").textContent===originalStatus;
            }""")
            require(frozen,"Résultat dupliqué par une ancienne commande Suivant")

            # Modifier les réponses APRÈS l'affichage du profil doit retirer
            # immédiatement le résultat et toutes ses possibilités de partage.
            page.locator("#compass-prev").click()
            earlier = page.evaluate("""() => ({
                question:document.querySelector("#compass-progress-text").textContent,
                noResult:document.querySelector("#compass-results").hidden &&
                  document.querySelector("#compass-results-grid").children.length===0 &&
                  document.querySelector("#compass-summary").textContent==="" &&
                  document.querySelector("#compass-copy-result").onclick===null &&
                  document.querySelector("#compass-share-email").getAttribute("href")==="mailto:",
                stageVisible:!document.querySelector("#compass-stepper").hidden
            })""")
            require(earlier["noResult"] and earlier["stageVisible"] and
                    "Question 63 sur 64" in earlier["question"],
                    "Revenir aux réponses conserve un ancien profil: "+repr(earlier))
            page.locator("#compass-next").click()
            require("Question 64 sur 64" in page.locator("#compass-progress-text").inner_text(),
                    "Retour à la dernière question après modification impossible")
            page.locator("#compass-next").click()
            require(not page.locator("#compass-results").is_hidden(),
                    "Profil non recalculable après navigation arrière/avant")
            page.locator('#compass-question-stage input[value="3"]').check()
            stale = page.evaluate("""() => {
                const status=document.querySelector("#compass-status").textContent;
                return document.querySelector("#compass-results").hidden &&
                  document.querySelector("#compass-summary").textContent==="" &&
                  document.querySelector("#compass-copy-result").onclick===null &&
                  document.querySelector("#compass-share-native").onclick===null &&
                  document.querySelector("#compass-share-email").getAttribute("href")==="mailto:" &&
                  document.querySelector("#compass-results-grid").children.length===0 &&
                  status.includes("Ancien résultat retiré");
            }""")
            require(stale,"Un changement direct conserve un résultat/partage périmé")
            page.locator("#compass-next").click()
            require(not page.locator("#compass-results").is_hidden() and
                    page.locator("#compass-results-grid .compass-result-card").count() == 16,
                    "Profil corrigé non recalculé après la 64e question")
            # Corriger seulement la pondération de la question finale :
            # Next doit être réactivé après purge du profil périmé.
            page.locator("#compass-question-stage [data-importance]").select_option("forte")
            require(page.locator("#compass-results").is_hidden() and
                    not page.locator("#compass-next").is_disabled() and
                    page.locator("#compass-results-grid").locator("*").count() == 0 and
                    page.locator("#compass-copy-result").evaluate("(el) => el.onclick===null"),
                    "Changement de pondération : ancien profil encore exposé ou recalcul désactivé")
            page.locator("#compass-next").click()
            require(not page.locator("#compass-results").is_hidden() and
                    page.locator("#compass-next").is_disabled(),
                    "Pondération ajustée : résultat impossible à recalculer ou commande encore active")

            # Les callbacks de partage retiennent le résumé et doivent
            # également disparaître après reset, pas seulement les cartes SVG.
            require(page.evaluate("""() =>
                typeof document.querySelector("#compass-share-native").onclick === "function" &&
                typeof document.querySelector("#compass-copy-result").onclick === "function" &&
                typeof document.querySelector("#compass-email-recipient").oninput === "function"
            """), "partage local non configuré après résultats")
            # Rejet asynchrone du presse-papiers et partage natif terminé
            # APRÈS reset : pas de copie de secours, pas de statut restauré.
            delayed = page.evaluate("""async () => {
                let rejectClipboard;
                let resolveShare;
                let manualCopy = 0;
                Object.defineProperty(navigator, "clipboard", {
                    configurable:true,
                    value:{writeText:()=>new Promise((_resolve,reject)=>{
                        rejectClipboard=reject;
                    })}
                });
                Object.defineProperty(navigator, "share", {
                    configurable:true,
                    value:()=>new Promise(resolve=>{resolveShare=resolve;})
                });
                const originalCreate = document.createElement.bind(document);
                document.createElement = function(tag, ...rest) {
                    if(tag.toLowerCase()==="textarea") manualCopy++;
                    return originalCreate(tag, ...rest);
                };
                document.querySelector("#compass-copy-result").click();
                document.querySelector("#compass-share-native").click();
                if(typeof rejectClipboard!=="function" || typeof resolveShare!=="function") {
                    return {ok:false,reason:"promesses non créées"};
                }
                document.querySelector("#compass-reset").click();
                rejectClipboard(Error("Copie refusée après reset"));
                resolveShare();
                await new Promise(resolve=>setTimeout(resolve,0));
                return {
                    ok:manualCopy===0 &&
                        document.querySelector("#compass-status").textContent.includes("réinitialisé") &&
                        document.querySelector("#compass-copy-result").onclick===null &&
                        document.querySelector("#compass-share-native").onclick===null &&
                        document.querySelector("#compass-share-email").getAttribute("href")==="mailto:",
                    manualCopy,
                    status:document.querySelector("#compass-status").textContent
                };
            }""")
            require(delayed["ok"], "Partage tardif après purge: " + repr(delayed))
            require(page.locator("#compass-results").is_hidden()
                    and page.locator("#compass-results-grid .compass-result-card").count() == 0
                    and page.locator("#compass-start").is_visible(),
                    "le résultat subsiste après réinitialisation")
            require(page.locator("#compass-progress-track").get_attribute("aria-valuenow") == "0"
                    and page.locator("#compass-progress-track").get_attribute("aria-valuetext")
                    == "Questionnaire non commencé"
                    and "non commencé" in page.locator("#compass-progress-text").inner_text(),
                    "Retour à l'introduction : progression et accessibilité encore à question 1")

            require(page.evaluate("""() => {
                const input = document.querySelector("#compass-email-recipient");
                input.value = "autre@example.test";
                input.dispatchEvent(new Event("input",{bubbles:true}));
                return document.querySelector("#compass-share-native").onclick === null &&
                    document.querySelector("#compass-copy-result").onclick === null &&
                    input.oninput === null &&
                    document.querySelector("#compass-share-email").getAttribute("href") === "mailto:" &&
                    document.querySelector("#compass-summary").textContent === "" &&
                    document.querySelector("#compass-radar").children.length === 0;
            }"""), "profil conservé dans les callbacks de partage après reset")

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

            # Une réponse n'implique pas une dimension calculable : ne pas
            # proposer au partage un profil dépourvu de scores.
            none = page.evaluate("""() => {
                document.querySelector("#compass-start").click();
                for (let step = 1; step <= 64; step++) {
                    const radio = document.querySelector(
                        '#compass-question-stage input[type="radio"][value="' +
                        (step === 1 ? "2" : "skip") + '"]'
                    );
                    if (!radio) return {ok:false,step};
                    radio.click();
                    document.querySelector("#compass-next").click();
                }
                const share = document.querySelector("#compass-share-card");
                return {
                    ok: !document.querySelector("#compass-results").hidden &&
                        document.querySelector("#compass-summary").textContent.includes(
                            "Aucune dimension calculable") &&
                        share.hidden && getComputedStyle(share).display === "none" &&
                        document.querySelector("#compass-copy-result").onclick === null &&
                        document.querySelector("#compass-share-native").onclick === null
                };
            }""")
            require(none["ok"], "profil fantôme partageable avec une seule réponse: " + repr(none))
            page.locator("#compass-reset").click()

            # Profil PARTIEL : trois dimensions adjacentes à deux réponses
            # chacune. Les treize autres restent non calculées, sans faux
            # marqueur neutre, sans polygone traversant leurs positions.
            partial = page.evaluate("""() => {
                document.querySelector("#compass-start").click();
                const answered = new Set([1,2,5,6,9,10]);
                for (let step = 1; step <= 64; step++) {
                    const radio = document.querySelector(
                        '#compass-question-stage input[type="radio"][value="' +
                        (answered.has(step) ? '2' : 'skip') + '"]'
                    );
                    const next = document.querySelector("#compass-next");
                    if (!radio || !next) return {ok:false,step,reason:"question manquante"};
                    radio.click();
                    next.click();
                }
                const cards = [...document.querySelectorAll(
                    "#compass-results-grid .compass-result-card")];
                const chart = document.querySelector("#compass-radar svg");
                return {
                    ok: !document.querySelector("#compass-results").hidden &&
                        cards.length === 16 &&
                        cards.filter(card => card.querySelector(
                            ".compass-axis-track i")).length === 3 &&
                        document.querySelectorAll("#compass-radar text").length === 16 &&
                        document.querySelectorAll(
                            "#compass-radar .compass-radar-point").length === 3 &&
                        document.querySelectorAll(
                            "#compass-radar .compass-radar-segment").length === 2 &&
                        document.querySelectorAll("#compass-radar polygon").length === 0 &&
                        chart?.querySelector("desc")?.textContent.includes(
                            "3 dimensions calculées sur 16") &&
                        document.querySelector("#compass-summary").textContent.includes(
                            "Profil partiel"),
                    charts: !!chart, step:64
                };
            }""")
            require(partial["ok"], "carte partielle trompeuse: " + repr(partial))
            page.locator("#compass-reset").click()

            # Cas frontière méthodologique : 32/64 réponses, mais uniquement
            # sur les huit premiers axes. Il ne s'agit pas d'un profil 16/16.
            half = page.evaluate("""() => {
                document.querySelector("#compass-start").click();
                for (let step = 1; step <= 64; step++) {
                    const radio = document.querySelector(
                        '#compass-question-stage input[type="radio"][value="' +
                        (step <= 32 ? "2" : "skip") + '"]'
                    );
                    if (!radio) return {ok:false,step};
                    radio.click();
                    document.querySelector("#compass-next").click();
                }
                const text = document.querySelector("#compass-summary").textContent;
                const cards = [...document.querySelectorAll(
                    "#compass-results-grid .compass-result-card")];
                const calculated = cards.filter(card =>
                    card.querySelector(".compass-result-head strong")?.textContent.trim() !== "—");
                return {
                    ok: !document.querySelector("#compass-results").hidden &&
                        text.includes("Profil partiel") &&
                        text.includes("8/16 dimensions calculables") &&
                        cards.length === 16 && calculated.length === 8 &&
                        !document.querySelector("#compass-share-card").hidden,
                    step:64, calculated:calculated.length, summary:text
                };
            }""")
            require(half["ok"], "32 réponses sur 8 axes présentées comme 16 axes: " + repr(half))
            page.locator("#compass-reset").click()
            require(not submitted, "POST interdit détecté pendant la Boussole")
            print(f"PASS {BROWSER}: 64 questions, 16 scores neutres à zéro, "
                  "couverture 4/4, Sans opinion distinct, réinitialisation, zéro POST")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
