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
                        assert strip.locator("a").count() >= 4, (path, width)
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

            # Dégradation progressive : les liens restent accessibles sans JavaScript.
            context = browser.new_context(
                viewport={"width": 240, "height": 820}, java_script_enabled=False
            )
            try:
                page = context.new_page()
                response = page.goto(BASE + PAGES[0], wait_until="domcontentloaded")
                assert response is not None and response.status == 200
                nav = page.locator("nav.universe-subnav")
                assert nav.locator("a").count() >= 7
                assert nav.locator(".container").evaluate(
                    "(e) => getComputedStyle(e).overflowX === 'auto'"
                ), "Défilement horizontal natif absent sans JS"
                print(f"OK {ENGINE}: navigation utilisable sans JS à 240px")
            finally:
                context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
