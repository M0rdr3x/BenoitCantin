#!/usr/bin/env python3
"""Univers SINJIRA : un seul projet principal, six parcours, zéro débordement.

Contrôles locaux PC/mobile et clavier, sans compte ni données privées.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173").rstrip("/")
BROWSER = os.environ.get("BROWSER", "chromium")
WIDTHS = (240, 320, 390, 768, 1440)
DESTINATIONS = (
    "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/",
    "/projets/sinjira/registre/",
    "/projets/sinjira/communaute/",
    "/projets/sinjira/monde-parallele/",
    "/projets/sinjira/codex/",
)
CSP = (
    "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'"
)


def static_contract() -> str:
    html = (ROOT / "univers.html").read_text("utf-8")
    css = (ROOT / "assets/css/univers-sinjira-only-v1.css").read_text("utf-8")
    assert 'class="univers-sinjira-page"' in html
    assert 'href="/assets/css/univers-sinjira-only-v1.css?v=1.0.0"' in html
    assert html.count('class="univers-main-project"') == 1
    assert html.count('src="/assets/icons/sinjira-officiel-20261120.png"') == 1
    assert (ROOT / "assets/icons/sinjira-officiel-20261120.png").is_file()
    assert "Projet Nova" not in html
    assert "Trois portes" not in html and "trois portes" not in html
    assert "sinjira-emblem.webp" not in html
    assert "Un seul univers à l’honneur" in html
    assert html.count('class="univers-path-link"') == 6
    for path in DESTINATIONS:
        assert f'href="{path}"' in html, path
        assert (ROOT / path.lstrip("/") / "index.html").is_file(), path
    assert 'aria-labelledby="parcours-sinjira-title"' in html
    assert 'aria-label="Rubriques de SINJIRA"' in html
    assert not re.search(r'\b(?:style|onclick|onerror|onload)\s*=', html, re.I)
    assert ':focus-visible' in css and "prefers-reduced-motion" in css
    assert "@media(max-width:520px)" in css
    print("OK: un seul cercle officiel, six destinations existantes et aucun Nova en vitrine")
    return html


def test_view(browser, html: str, width: int, js_enabled: bool) -> None:
    context = browser.new_context(
        viewport={"width": width, "height": 760},
        java_script_enabled=js_enabled,
        reduced_motion="reduce",
        service_workers="block",
    )
    try:
        if js_enabled:
            context.route(
                re.compile(r"/univers\.html(?:\?.*)?$"),
                lambda route: route.fulfill(
                    status=200,
                    body=html,
                    headers={
                        "content-type": "text/html; charset=utf-8",
                        "content-security-policy": CSP,
                    },
                ),
            )
        page = context.new_page()
        response = page.goto(BASE + "/univers.html", wait_until="domcontentloaded", timeout=30_000)
        assert response and response.status == 200, (BROWSER, width, "page manquante")
        assert page.locator("main#contenu").count() == 1
        assert page.get_by_role("heading", level=1).count() == 1
        assert "SINJIRA" in page.locator("main h1").inner_text()
        assert "Projet Nova" not in page.locator("main").inner_text()
        hub = page.locator("main a.univers-main-project")
        assert hub.count() == 1 and hub.get_attribute("href") == "/projets/sinjira/"
        image = hub.locator("img")
        assert image.get_attribute("src") == "/assets/icons/sinjira-officiel-20261120.png"
        image.wait_for(state="visible", timeout=10_000)
        assert page.evaluate(
            """() => {
                const i = document.querySelector('main .univers-main-project img');
                return i.complete && i.naturalWidth > 0;
            }"""
        ), (BROWSER, width, "logo officiel absent ou non chargé")
        routes = page.locator("nav[aria-label='Rubriques de SINJIRA'] a.univers-path-link")
        assert routes.count() == 6, (BROWSER, width, routes.count())
        assert tuple(routes.nth(i).get_attribute("href") for i in range(6)) == DESTINATIONS
        for item in [hub] + routes.all():
            b = item.bounding_box()
            assert b, (BROWSER, width, "lien masqué")
            assert b["height"] >= 44, (BROWSER, width, "cible tactile", b)
            assert b["x"] >= -2 and b["x"] + b["width"] <= width + 2, (
                BROWSER, width, "action débordante", b
            )
        doc_width = page.evaluate(
            "() => Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)"
        )
        assert doc_width <= width + 2, (BROWSER, width, "débordement horizontal", doc_width)

        # Les parcours fonctionnent même sans JavaScript.
        if width == 390:
            route = routes.first
            route.focus()
            assert page.evaluate(
                """() => document.activeElement &&
                document.activeElement.getAttribute('href') === '/projets/sinjira/romans/'"""
            ), (BROWSER, width, "focus clavier perdu")
            page.keyboard.press("Enter")
            page.wait_for_url(re.compile(r"/projets/sinjira/romans/?$"), timeout=10_000)
            assert urlsplit(page.url).path == "/projets/sinjira/romans/", (
                BROWSER, width, "lien non fonctionnel", page.url
            )
        print(f"OK {BROWSER} : {width}px, JS={'CSP stricte' if js_enabled else 'désactivé'}")
    finally:
        context.close()


def main() -> None:
    if BROWSER not in ("chromium", "firefox", "webkit"):
        raise ValueError("Moteur navigateur non autorisé")
    html = static_contract()
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        try:
            for enabled in (False, True):
                for width in WIDTHS:
                    test_view(browser, html, width, enabled)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
