#!/usr/bin/env python3
"""Parcours navigateur complet sans soumission au backend Nova 40."""
import os
from playwright.sync_api import expect, sync_playwright
BROWSER=os.environ.get("BROWSER","chromium")
URL="http://127.0.0.1:4173/projets/projet-nova/consultation-40.html"
def check(ok,msg):
    if not ok:raise AssertionError(f"{BROWSER}: {msg}")
with sync_playwright() as p:
    browser=getattr(p,BROWSER).launch()
    page=browser.new_page(viewport={"width":390,"height":844},locale="fr-CA")
    try:
        calls=[]
        page.on("request",lambda req:calls.append(req.url) if "nova-consultation40-submit" in req.url else None)
        response=page.goto(URL,wait_until="domcontentloaded",timeout=30000)
        check(response is not None and response.status==200,"page de consultation absente")
        page.locator("#sondage-start").wait_for()
        check(page.locator("#sondage-start").is_disabled(),"âge et consentement devraient verrouiller le début")
        page.locator("#sondage-age").check()
        check(page.locator("#sondage-start").is_disabled(),"le consentement séparé reste requis")
        page.locator("#sondage-consent").check()
        expect(page.locator("#sondage-start")).to_be_enabled(timeout=10000)
        page.locator("#sondage-start").click()
        check(page.locator("#sondage-position").inner_text().startswith("Question 1 sur 40"),"début non séquentiel")
        check(page.locator("#sondage-next").is_disabled(),"question sans réponse ne doit pas passer")
        page.locator("input[value=pour]").check()
        page.locator("#sondage-next").click()
        check("Question 2 sur 40" in page.locator("#sondage-position").inner_text(),"progression cassée")
        page.locator("#sondage-back").click()
        check(page.locator("input[value=pour]").is_checked(),"réponse perdue au retour")
        page.locator("#sondage-next").click()
        for n in range(2,41):
            check(f"Question {n} sur 40" in page.locator("#sondage-position").inner_text(),f"question {n} absente")
            page.locator("input[value=contre]" if n%2==0 else "input[value=sans_opinion]").check()
            page.locator("#sondage-next").click()
        check(page.locator("#sondage-finish").is_visible(),"récapitulatif final absent")
        check(page.locator("#sondage-submit").is_disabled(),"collecte doit rester inactive")
        check(not calls,"des réponses politiques ont été transmises")
        page.locator("#sondage-review").click()
        check(page.locator("#sondage-questionnaire").is_visible(),"relecture impossible")
        print(f"OK {BROWSER}: 40 questions, consentement 18+, retour, aucune collecte")
    finally:
        browser.close()
