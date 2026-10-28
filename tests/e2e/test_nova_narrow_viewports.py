#!/usr/bin/env python3
"""Projet Nova : qualification petits écrans sur l'artefact public isolé.

Vérifie l'accueil général, l'accueil Nova, les 40/64 questions, la Boussole
et les résultats à 320, 360 et 768 pixels sur chaque moteur Playwright.
N'envoie aucune opinion; aucune connexion à la production.
"""
from __future__ import annotations

import os
from playwright.sync_api import sync_playwright

ROOT = "http://127.0.0.1:4173"
BROWSER = os.getenv("BROWSER", "chromium")
WIDTHS = (320, 360, 768)
PATHS = (
    "/", "/projets/projet-nova/", "/projets/projet-nova/consultation-40.html",
    "/projets/projet-nova/sondage.html",
    "/projets/projet-nova/boussole-electorale.html",
    "/projets/projet-nova/resultats-sondages.html",
)


def check(condition, message):
    if not condition:
        raise AssertionError(f"{BROWSER}: {message}")


def check_width(page, label):
    metrics = page.evaluate("""() => ({
        viewport: innerWidth,
        document: document.documentElement.scrollWidth,
        body: document.body.scrollWidth,
        offenders: [...document.querySelectorAll('body *')]
          .map(el => ({name: el.tagName.toLowerCase(), id: el.id,
                        right: Math.round(el.getBoundingClientRect().right)}))
          .filter(el => el.right > innerWidth + 4).slice(0, 8)
    })""")
    check(metrics["document"] <= metrics["viewport"] + 2,
          f"{label}: débordement horizontal {metrics}")


def check_links(page, selectors, label):
    for selector, expected in selectors:
        item = page.locator(selector)
        check(item.count() == 1, f"{label}: lien absent/dupliqué {selector}")
        check(item.get_attribute("href") == expected,
              f"{label}: URL inattendue pour {selector}")
        check(item.is_visible(), f"{label}: lien non visible {selector}")


def main():
    check(BROWSER in {"chromium", "firefox", "webkit"}, "navigateur inconnu")
    with sync_playwright() as pw:
        browser = getattr(pw, BROWSER).launch()
        try:
            for width in WIDTHS:
                page = browser.new_page(
                    viewport={"width": width, "height": 720},
                    locale="fr-CA",
                    reduced_motion="reduce",
                    service_workers="block",
                )
                posts = []
                page.on("request", lambda r: posts.append(r.url)
                        if r.method == "POST" else None)
                try:
                    for path in PATHS:
                        response = page.goto(ROOT + path, wait_until="domcontentloaded",
                                             timeout=30000)
                        check(response is not None and response.status in (200, 304),
                              f"{width}px {path}: HTTP absent ({response.status if response else 'aucun'})")
                        if path == "/":
                            check_links(page, (
                                ("#home-sondage-40", "/projets/projet-nova/consultation-40.html"),
                                ("#home-sondage-64", "/projets/projet-nova/sondage.html"),
                                ("#home-sondages-resultats", "/projets/projet-nova/resultats-sondages.html"),
                            ), "accueil principal")
                        elif path == "/projets/projet-nova/":
                            check_links(page, (
                                ("#nova-survey-directory-40", "consultation-40.html"),
                                ("#nova-survey-directory-64", "sondage.html"),
                                ("#nova-survey-directory-compass", "boussole-electorale.html"),
                            ), "accueil Nova")
                        elif path.endswith(("consultation-40.html", "sondage.html")):
                            page.locator('#sondage-start[data-ready="true"]').wait_for(
                                state="visible", timeout=25000)
                            check(page.locator("#sondage-start").is_disabled(),
                                  f"{width}px {path}: participation sans accord")
                            if width == 320:
                                page.locator("#sondage-age").check()
                                page.locator("#sondage-consent").check()
                                page.locator("#sondage-start").click()
                                page.locator("#sondage-choices input[type=radio]").first.wait_for(
                                    state="attached", timeout=5000)
                                check(page.locator("#sondage-questionnaire").is_visible(),
                                      f"{width}px {path}: question non affichée")
                        elif path.endswith("boussole-electorale.html"):
                            page.wait_for_function(
                                "() => !document.querySelector('#compass-start').disabled",
                                timeout=25000)
                            if width == 320:
                                page.locator("#compass-start").click()
                                page.locator("#compass-question-stage input[type=radio]").first.wait_for(
                                    state="attached", timeout=5000)
                        check_width(page, f"{width}px {path}")
                    check(not posts, f"{width}px: opinions transmises par POST : {posts}")
                    print(f"PASS Nova {BROWSER}: 6 routes, viewport {width}px, 0 POST")
                finally:
                    page.close()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
