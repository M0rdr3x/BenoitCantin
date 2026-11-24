#!/usr/bin/env python3
"""Parcours de la bibliothèque SINJIRA, sans session ni service privé."""
from __future__ import annotations

import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER_NAME = os.environ.get("BROWSER", "chromium").lower()
TARGETS = ("livre-1", "precommande", "livre-2", "roman-4", "commentaires")
WIDTHS = (240, 320, 390, 768, 1024, 1440)


def check(condition, message):
    if not condition:
        raise AssertionError(f"{BROWSER_NAME}: {message}")


def main():
    check(BROWSER_NAME in ("chromium", "firefox", "webkit"), "navigateur non reconnu")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER_NAME).launch()
        try:
            for width in WIDTHS:
                context = browser.new_context(
                    locale="fr-CA",
                    viewport={"width": width, "height": 760},
                    reduced_motion="reduce",
                    java_script_enabled=False,
                    service_workers="block",
                )
                try:
                    page = context.new_page()
                    response = page.goto(
                        urljoin(BASE_URL, "projets/sinjira/romans/"),
                        wait_until="domcontentloaded",
                        timeout=30_000,
                    )
                    check(response is not None and response.status < 400,
                          f"bibliothèque absente à {width}px")
                    nav = page.locator("nav.sinjira-romans-jump-nav")
                    check(nav.count() == 1, "sommaire de lecture absent")
                    check(nav.get_attribute("aria-label") == "Accès rapide aux romans",
                          "sommaire sans nom accessible")
                    links = nav.locator("a")
                    check(links.count() == len(TARGETS), "sommaire incomplet")
                    for index, target in enumerate(TARGETS):
                        link = links.nth(index)
                        check(link.get_attribute("href") == "#" + target,
                              f"cible erronée pour {target}")
                        check(page.locator(f"section#{target}").count() == 1,
                              f"destination manquante : {target}")
                        check(link.bounding_box()["height"] >= 44,
                              f"cible tactile trop petite : {target} à {width}px")
                    dimensions = page.evaluate("""() => ({
                        body: document.documentElement.scrollWidth,
                        viewport: innerWidth,
                        navScroll: document.querySelector('.sinjira-romans-jump-nav .container').scrollWidth,
                        navVisible: document.querySelector('.sinjira-romans-jump-nav .container').clientWidth
                    })""")
                    check(dimensions["body"] <= dimensions["viewport"] + 2,
                          f"débordement horizontal global à {width}px : {dimensions}")
                    if width <= 390:
                        check(dimensions["navScroll"] > dimensions["navVisible"],
                              f"sommaire mobile non défilable à {width}px")
                    nav.locator('a[href="#roman-4"]').click()
                    check(page.evaluate("location.hash") == "#roman-4",
                          f"ancre Roman IV non fonctionnelle à {width}px")
                    top = page.locator("#roman-4").evaluate(
                        "(el) => el.getBoundingClientRect().top"
                    )
                    check(top >= 60, f"titre Roman IV masqué après navigation : {top}px")
                finally:
                    context.close()
        finally:
            browser.close()
    print(f"OK {BROWSER_NAME}: sommaire Romans, 6 largeurs, clavier/tactile et sans JS")


if __name__ == "__main__":
    main()
