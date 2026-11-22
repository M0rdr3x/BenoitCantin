#!/usr/bin/env python3
"""À propos — SINJIRA prioritaire, canaux honnêtes, ergonomie PC et mobile.

Recette locale sans collecte de données : Chromium, Firefox et WebKit.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173").rstrip("/")
BROWSER = os.environ.get("BROWSER", "chromium").lower()
WIDTHS = (240, 320, 390, 768, 1440)
CSP = (
    "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'"
)


def validate_contract() -> str:
    html = (ROOT / "a-propos.html").read_text("utf-8")
    css = (ROOT / "assets/css/about-contact-responsive-v1.css").read_text("utf-8")
    assert 'class="about-ux-page"' in html
    assert 'href="/assets/css/about-contact-responsive-v1.css?v=1.0.0"' in html
    assert html.count('<h1>') == 1
    assert 'class="container about-content-grid"' in html
    assert 'class="container cta-panel about-contact-panel"' in html
    assert 'aria-label="Canaux de contact disponibles"' in html
    assert 'mailto:sinjiraofficiel@gmail.com' in html
    assert 'href="/contact.html">Choisir un contact</a>' in html
    assert 'Le formulaire personnel du portail est actuellement désactivé.' in html
    assert 'SINJIRA™ est l’univers principal' in html
    assert 'Projet Nova conserve son espace séparé' in html
    assert 'href="/projets/projet-nova/"' not in html
    assert '>Me contacter<' not in html
    assert '<form' not in html.lower()
    assert not re.search(r'\b(?:style|onclick|onerror|onload)\s*=', html, re.I)
    assert ':focus-visible' in css
    assert '@media(max-width:560px)' in css.replace(" ", "")
    assert 'prefers-reduced-motion' in css
    assert 'min-height:48px' in css.replace(" ", "")
    print("OK : À propos sans faux formulaire, canaux officiels, navigation claire")
    return html


def verify(browser, html: str, width: int, js_enabled: bool) -> None:
    context = browser.new_context(
        viewport={"width": width, "height": 760},
        java_script_enabled=js_enabled,
        reduced_motion="reduce",
        service_workers="block",
    )
    try:
        if js_enabled:
            context.route(
                re.compile(r"/a-propos\.html(?:\?.*)?$"),
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
        response = page.goto(BASE + "/a-propos.html", wait_until="domcontentloaded", timeout=30_000)
        assert response and response.status == 200, (BROWSER, width, "page indisponible")
        assert page.get_by_role("heading", level=1, name="Benoit Cantin.").count() == 1
        assert page.locator("main article.about-unknown").count() == 0
        assert page.locator("main .about-content-grid > article").count() == 2
        assert "SINJIRA™ est l’univers principal" in page.locator("main").inner_text()
        assert page.locator("main form").count() == 0
        assert page.locator('main a[href="/projets/projet-nova/"]').count() == 0

        actions = page.locator(".about-contact-actions a")
        assert actions.count() == 2
        assert actions.nth(0).get_attribute("href") == "mailto:sinjiraofficiel@gmail.com"
        assert actions.nth(1).get_attribute("href") == "/contact.html"
        for el in [page.locator(".about-contact-panel")] + actions.all():
            rect = el.bounding_box()
            assert rect is not None, (BROWSER, width, "action masquée")
            assert rect["x"] >= -2 and rect["x"] + rect["width"] <= width + 2, (
                BROWSER, width, "débordement action", rect
            )
        for action in actions.all():
            assert action.bounding_box()["height"] >= 44, (BROWSER, width, "cible tactile trop petite")

        columns = page.locator(".about-content-grid").evaluate(
            "(node) => getComputedStyle(node).gridTemplateColumns.split(' ').length"
        )
        assert columns == (2 if width > 1050 else 1), (BROWSER, width, "colonnes non adaptées", columns)
        doc_width = page.evaluate(
            "() => Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)"
        )
        assert doc_width <= width + 2, (BROWSER, width, "débordement horizontal", doc_width)

        if width == 390:
            actions.nth(1).focus()
            assert page.evaluate(
                'document.activeElement?.getAttribute("href")==="/contact.html"'
            ), (BROWSER, "le lien Contact n'accepte pas le focus")
            page.keyboard.press("Enter")
            page.wait_for_url(re.compile(r"/contact\.html$"), timeout=10_000)
            assert urlsplit(page.url).path == "/contact.html", (BROWSER, "navigation clavier")
        print(f"OK {BROWSER}: {width}px, JS={'actif+CSP' if js_enabled else 'désactivé'}")
    finally:
        context.close()


def main() -> None:
    if BROWSER not in ("chromium", "firefox", "webkit"):
        raise ValueError("Moteur navigateur non autorisé")
    html = validate_contract()
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        try:
            for js_enabled in (False, True):
                for width in WIDTHS:
                    verify(browser, html, width, js_enabled)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
