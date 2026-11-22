#!/usr/bin/env python3
"""Contrats UX réels du sous-menu public SINJIRA, sans accès à un compte.

Exécution: BASE_URL=http://127.0.0.1:4173/ BROWSER=chromium python ...
"""
from __future__ import annotations

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/")
ENGINE = os.environ.get("BROWSER", "chromium")
PAGES = (
    "/projets/sinjira/",
    "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/",
)
WIDTHS = (240, 320, 390, 768, 1440)
DESTINATIONS = (
    "/projets/sinjira/",
    "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/",
    "/projets/sinjira/registre/",
    "/projets/sinjira/communaute/",
    "/projets/sinjira/monde-parallele/",
    "/projets/sinjira/codex/",
)


def test_sources() -> None:
    script = ROOT / "assets/js/sinjira-universe-nav-v2.js"
    style = ROOT / "assets/css/sinjira-universe-nav-v2.css"
    assert script.is_file() and style.is_file(), "Ressources manquantes"
    for page in PAGES:
        source = ROOT / page.lstrip("/") / "index.html"
        html = source.read_text(encoding="utf-8")
        assert html.count("sinjira-universe-nav-v2.css?v=2.0.0") == 1, page
        assert html.count("sinjira-universe-nav-v2.js?v=2.0.0") == 1, page
        assert 'class="universe-subnav"' in html, page
        assert 'aria-current="page"' in html, page
    assert "démo de validation de 62 pages" not in (ROOT / "projets/sinjira/index.html").read_text("utf-8")


def main() -> None:
    test_sources()
    if ENGINE not in ("chromium", "firefox", "webkit"):
        raise ValueError("Moteur navigateur non pris en charge")
    with sync_playwright() as playwright:
        browser = getattr(playwright, ENGINE).launch()
        try:
            for path in PAGES:
                for width in WIDTHS:
                    context = browser.new_context(
                        viewport={"width": width, "height": 820},
                        reduced_motion="reduce",
                    )
                    try:
                        page = context.new_page()
                        response = page.goto(BASE + path, wait_until="domcontentloaded")
                        assert response is not None and response.status == 200, (path, width)
                        nav = page.locator("nav.universe-subnav")
                        nav.wait_for()
                        page.wait_for_function(
                            "document.querySelector('nav.universe-subnav')?.hasAttribute('data-universe-controls-ready')",
                            timeout=5000,
                        )
                        strip = nav.locator(".container")
                        links = strip.locator("a")
                        assert links.count() == len(DESTINATIONS), (path, width)
                        destinations = links.evaluate_all(
                            "(elements) => elements.map(link => new URL(link.getAttribute('href'), "
                            "location.href).pathname)"
                        )
                        assert tuple(destinations) == DESTINATIONS, (path, width, destinations)
                        current = strip.locator('a[aria-current="page"]')
                        assert current.count() == 1, (path, width)
                        assert current.evaluate("(link) => new URL(link.href).pathname") == path, (
                            path, width, "rubrique active incorrecte"
                        )
                        previous = nav.locator("button.universe-scroll-button").nth(0)
                        following = nav.locator("button.universe-scroll-button").nth(1)
                        assert previous.get_attribute("aria-controls") == strip.get_attribute("id")
                        assert following.get_attribute("aria-controls") == strip.get_attribute("id")
                        metrics = strip.evaluate(
                            "(e) => ({overflow:e.scrollWidth-e.clientWidth>3,"
                            "left:e.scrollLeft,width:e.clientWidth,total:e.scrollWidth})"
                        )
                        if metrics["overflow"]:
                            assert previous.is_visible() and following.is_visible(), (path, width)
                            controls = [button for button in (following, previous) if button.is_enabled()]
                            assert controls, (path, width, metrics)
                            before = strip.evaluate("(e) => e.scrollLeft")
                            controls[0].click()
                            page.wait_for_function(
                                "([before]) => Math.abs(document.querySelector('nav.universe-subnav .container').scrollLeft-before)>5",
                                arg=[before],
                                timeout=3000,
                            )
                        else:
                            assert not previous.is_visible() and not following.is_visible(), (path, width)
                        print(f"OK {ENGINE}: {path} — {width}px")
                    finally:
                        context.close()

            # Dégradation progressive : les sept rubriques restent accessibles
            # sur les trois pages, même lorsque JavaScript est désactivé.
            context = browser.new_context(
                viewport={"width": 240, "height": 820}, java_script_enabled=False
            )
            try:
                page = context.new_page()
                for path in PAGES:
                    response = page.goto(BASE + path, wait_until="domcontentloaded")
                    assert response is not None and response.status == 200, path
                    nav = page.locator("nav.universe-subnav")
                    links = nav.locator(".container a")
                    assert links.count() == len(DESTINATIONS), path
                    destinations = links.evaluate_all(
                        "(elements) => elements.map(link => "
                        "new URL(link.getAttribute('href'), location.href).pathname)"
                    )
                    assert tuple(destinations) == DESTINATIONS, (path, destinations)
                    assert nav.locator('a[aria-current="page"]').count() == 1, path
                    assert nav.locator(".container").evaluate(
                        "(e) => getComputedStyle(e).overflowX === 'auto'"
                    ), f"Défilement horizontal natif absent sans JS : {path}"
                    print(f"OK {ENGINE}: {path} sans JS à 240px")
            finally:
                context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
