#!/usr/bin/env python3
"""Preuve visuelle locale, sans identifiants ni déploiement, des trois catalogues.

Ce test s'exécute même quand la PR globale reste DRAFT : les autres
parcours authentifiés et le workflow de publication restent fermés.
"""
from __future__ import annotations

import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:4173/"
BROWSER = os.environ.get("BROWSER", "chromium")
CATEGORIES = {
    "romans": (1672, 941),
    "jeux": (1916, 821),
    "logiciels": (2048, 768),
}


def require(condition: bool, explanation: str) -> None:
    if not condition:
        raise AssertionError(f"{BROWSER}: {explanation}")


def image_loaded(page, selector: str, width: int, height: int) -> None:
    page.locator(selector).scroll_into_view_if_needed()
    page.wait_for_function(
        """([selector, w, h]) => {
            const img = document.querySelector(selector);
            return img && img.complete && img.naturalWidth === w
                && img.naturalHeight === h;
        }""",
        arg=[selector, width, height],
        timeout=15_000,
    )


def proportions(page, selector: str, category: str, viewport: int) -> None:
    dimensions = page.locator(selector).evaluate(
        """img => {
            const box = img.getBoundingClientRect();
            return {
                displayedWidth: box.width,
                displayedHeight: box.height,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                fit: getComputedStyle(img).objectFit,
                overflow: document.documentElement.scrollWidth - innerWidth
            };
        }"""
    )
    expected_height = (
        dimensions["displayedWidth"] * dimensions["naturalHeight"]
        / dimensions["naturalWidth"]
    )
    require(
        dimensions["displayedWidth"] > 250
        and abs(dimensions["displayedHeight"] - expected_height) < 3
        and dimensions["fit"] == "contain",
        f"{category}: image déformée ou rognée sur {viewport}px {dimensions}",
    )
    require(
        dimensions["overflow"] <= 2,
        f"{category}: débordement horizontal {viewport}px "
        f"{dimensions['overflow']}px",
    )


def main() -> None:
    require(BROWSER in {"chromium", "firefox", "webkit"}, "moteur inconnu")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        page = browser.new_page(
            viewport={"width": 1440, "height": 960},
            locale="fr-CA",
            reduced_motion="reduce",
        )
        try:
            for category, (width, height) in CATEGORIES.items():
                response = page.goto(
                    urljoin(BASE_URL, f"projets/sinjira/{category}/"),
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                require(
                    response is not None and response.status == 200,
                    f"{category}: réponse HTTP non 200",
                )
                src = f"/assets/media/sinjira-{category}-banniere-2026.webp"
                selector = (
                    ".sinjira-category-poster--banner "
                    + f'img[src="{src}"]'
                )
                require(page.locator(selector).count() == 1,
                        f"{category}: bannière officielle introuvable")
                image_loaded(page, selector, width, height)
                nav = page.locator(
                    'nav.main-nav a[href="/projets/sinjira/"]'
                )
                current = page.locator(
                    'nav.universe-subnav a[aria-current="page"]'
                )
                require(
                    nav.count() == 1
                    and nav.get_attribute("aria-current") == "location",
                    f"{category}: page parente faussement sélectionnée",
                )
                require(current.count() == 1, f"{category}: plusieurs pages actives")
                current_url = urljoin(
                    page.url, current.get_attribute("href") or ""
                ).rstrip("/").removesuffix("/index.html")
                require(
                    current_url == page.url.rstrip("/"),
                    f"{category}: sous-navigation sélectionne une autre page",
                )
                for viewport in (1440, 390):
                    page.set_viewport_size(
                        {"width": viewport, "height": 844}
                    )
                    proportions(page, selector, category, viewport)
                page.set_viewport_size({"width": 1440, "height": 960})

            response = page.goto(
                urljoin(BASE_URL, "projets/sinjira/"),
                wait_until="domcontentloaded",
                timeout=30_000,
            )
            require(response is not None and response.status == 200,
                    "portail SINJIRA inaccessible")
            for category, (width, height) in CATEGORIES.items():
                selector = (
                    f'a.v24-portal-card[href="{category}/"] '
                    f'img.sinjira-portal-art'
                )
                require(page.locator(selector).count() == 1,
                        f"{category}: affiche absente de l'accueil")
                image_loaded(page, selector, width, height)
                require(
                    page.locator(selector).evaluate(
                        "img => getComputedStyle(img).objectFit"
                    ) == "contain",
                    f"{category}: miniature d'accueil recadrée",
                )
            print(
                f"OK {BROWSER}: 3 catalogues + portail, bannières "
                "décodées, ratios naturels, 390px, navigation ARIA"
            )
        finally:
            browser.close()


if __name__ == "__main__":
    main()
