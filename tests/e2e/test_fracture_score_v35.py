#!/usr/bin/env python3
"""Playwright — feuille de score Fracture, sur le site construit localement.
Aucun utilisateur, identité, connexion ni appel Supabase. Trois navigateurs.
"""
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/")
BROWSER = os.environ.get("BROWSER", "chromium")
ROUTE = "projets/sinjira/jeux/fracture-du-reseau-mere/feuille-de-score.html"


def check(condition, message):
    if not condition:
        raise AssertionError(f"{BROWSER}: {message}")


def run():
    check(BROWSER in {"chromium", "firefox", "webkit"}, "navigateur inconnu")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        context = browser.new_context(locale="fr-CA", viewport={"width": 1280, "height": 900})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.goto(urljoin(BASE_URL, ROUTE), wait_until="domcontentloaded", timeout=30000)
        check(response is not None and response.status < 400, "route calculateur introuvable")
        page.wait_for_function(
            "() => document.querySelectorAll('#fracture-rounds-body tr').length===10",
            timeout=10000)
        check("3 sièges" in page.locator("#fracture-score-rules").inner_text(), "calcul des sièges")
        check("6 cartes" in page.locator("#fracture-score-rules").inner_text(), "2N cartes au centre")
        check(page.locator("#fracture-final-panel").is_hidden(), "accusation affichée avant 10 rondes")

        first = page.locator("#fracture-rounds-body tr").first
        first.locator("input[data-camp=resistance]").fill("1")
        first.locator("input[data-camp=reseau]").fill("2")
        check("Total impossible" in page.locator("#fracture-score-status").inner_text(),
              "score irréalisable accepté")
        first.locator("input[data-camp=resistance]").fill("4")
        for row in page.locator("#fracture-rounds-body tr").all()[1:]:
            row.locator("input[data-camp=resistance]").fill("3")
            row.locator("input[data-camp=reseau]").fill("3")
        check(page.locator("#fracture-final-panel").is_visible(),
              "accusation non affichée après 10 rondes")
        page.locator("#fracture-correct").fill("2")
        page.locator("#fracture-incorrect").fill("1")
        check(page.locator("#fracture-total-r").inner_text() == "31", "total Résistance")
        check(page.locator("#fracture-total-m").inner_text() == "29", "total Réseau-Mère")
        check(page.locator("#fracture-final-r").inner_text() == "37", "bonus Résistance")
        check(page.locator("#fracture-final-m").inner_text() == "32", "bonus Réseau-Mère")
        check("Camp gagnant : Résistance" in page.locator("#fracture-conclusion").inner_text(),
              "résultat final")
        check(page.evaluate(
            "() => !Object.keys(localStorage).some(k => k.startsWith('fracture-score'))"),
            "stockage de scores inattendu")

        # Une correction invalide après un résultat complet ne doit laisser
        # aucun ancien chiffre visible ni permettre de nouvelles accusations.
        first.locator("input[data-camp=resistance]").fill("1")
        for name in ("progress","total-r","total-m","wins-r","wins-m","bonus-r","bonus-m","final-r","final-m"):
            check(page.locator("#fracture-"+name).inner_text()=="—", "ancien résultat visible : "+name)
        check(page.locator("#fracture-final-panel").is_hidden(), "accusations visibles malgré une ronde invalide")
        first.locator("input[data-camp=resistance]").fill("4")
        check(page.locator("#fracture-final-panel").is_visible(), "accusations non restaurées")
        check(page.locator("#fracture-final-r").inner_text()=="37", "résultat non recalculé")
        page.locator("#fracture-incorrect").fill("2")
        check(page.locator("#fracture-final-panel").is_visible(), "impossible de corriger les accusations")
        check(page.locator("#fracture-bonus-r").inner_text()=="—", "ancien bonus visible")
        page.locator("#fracture-incorrect").fill("1")
        check(page.locator("#fracture-final-r").inner_text()=="37", "bonus non recalculé")

        # Le format Express ne peut être activé qu'à partir de 13 humains.
        page.locator("#fracture-humans").fill("13")
        check(page.locator("#fracture-express").is_enabled(), "Express inaccessible à 13")
        page.locator("#fracture-express").check()
        page.once("dialog", lambda dialog: dialog.accept())
        page.locator("#fracture-score-config button[type=submit]").click()
        page.wait_for_function(
            "() => document.querySelectorAll('#fracture-rounds-body tr').length===6",
            timeout=10000)
        check("26 cartes" in page.locator("#fracture-score-rules").inner_text(),
              "26 cartes au centre pour 13 sièges")
        check("52 accusations" in page.locator("#fracture-score-rules").inner_text(),
              "seuls les humains déposent des accusations")
        check(page.locator("#fracture-final-panel").is_hidden(), "ancien score persistant")
        check(not errors, f"erreurs JavaScript : {errors[:3]}")
        context.close()

        mobile = browser.new_context(locale="fr-CA", viewport={"width": 390, "height": 844},
                                     has_touch=True)
        mobile_page = mobile.new_page()
        mobile_errors = []
        mobile_page.on("pageerror", lambda error: mobile_errors.append(str(error)))
        result = mobile_page.goto(urljoin(BASE_URL, ROUTE),
                                  wait_until="domcontentloaded", timeout=30000)
        check(result is not None and result.status < 400, "route mobile introuvable")
        mobile_page.wait_for_function(
            "() => document.querySelectorAll('#fracture-rounds-body tr').length===10",
            timeout=10000)
        check(mobile_page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth+2"),
            "débordement horizontal mobile")
        check(mobile_page.locator("#fracture-score-config").is_visible(),
              "contrôles mobile invisibles")
        for width, zoom in ((240,"100%"),(320,"200%"),(390,"100%"),(768,"100%"),(1440,"100%")):
            mobile_page.set_viewport_size({"width":width,"height":844})
            mobile_page.evaluate("(zoom)=>document.documentElement.style.fontSize=zoom",zoom)
            geometry=mobile_page.evaluate("""() => {
              const wraps=[...document.querySelectorAll('.fracture-score-table-wrap')];
              const controls=[...document.querySelectorAll('#fracture-rounds-body input,#fracture-humans,.fracture-score-actions button')];
              return {page:document.documentElement.scrollWidth<=innerWidth+2,
                tables:wraps.every(e=>e.scrollWidth<=e.clientWidth+2),
                controls:controls.every(e=>{const r=e.getBoundingClientRect();return r.left>=-2&&r.right<=innerWidth+2&&r.height>=47.5})};
            }""")
            check(all(geometry.values()), f"saisie hors écran {width}px / {zoom}: {geometry}")
        check(not mobile_errors, f"erreurs JavaScript mobile : {mobile_errors[:3]}")
        mobile.close()
        browser.close()
        print(f"OK score Fracture {BROWSER}: 3 joueurs, 13 Express, bonus, mobilité, confidentialité.")


if __name__ == "__main__":
    run()
