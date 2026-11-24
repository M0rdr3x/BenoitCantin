#!/usr/bin/env python3
"""Page Merci : indication honnête de réception et actions tactiles PC/mobile.

Tests navigateur sur un serveur statique local, sans formulaire ni accès privé.
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
CSP = (
    "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'"
)


def static_contract() -> str:
    html = (ROOT / "merci.html").read_text("utf-8")
    css = (ROOT / "assets/css/merci-ux-v1.css").read_text("utf-8")
    assert 'name="robots" content="noindex,nofollow,noarchive"' in html
    assert '<body class="merci-ux-page"' in html
    assert '/assets/css/merci-ux-v1.css?v=1.0.0' in html
    assert 'aria-label="Liens utiles après votre démarche"' in html
    assert "ne confirme donc pas qu’un message a été envoyé ou reçu" in html
    assert "Votre message a été transmis" not in html
    assert "Transmission reçue" not in html
    assert "<form" not in html.lower()
    assert not re.search(r'\b(?:onclick|onload|onerror|style)\s*=', html, re.I)
    assert not re.search(r'<script\b(?![^>]*\bsrc=)', html, re.I)
    assert ':focus-visible' in css and '@media(max-width:640px)' in css
    assert 'min-height:48px' in css
    print("OK : aucune fausse confirmation, aucune collecte et aucun style/script inline")
    return html


def check_page(browser, html: str, width: int, js_enabled: bool) -> None:
    context = browser.new_context(
        viewport={"width": width, "height": 760},
        java_script_enabled=js_enabled,
        reduced_motion="reduce",
        service_workers="block",
    )
    try:
        if js_enabled:
            context.route(
                re.compile(r"/merci\.html(?:\?.*)?$"),
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
        url = BASE + "/merci.html"
        if width == 390:
            url += "?statut=envoye&message=exemple"
        response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        assert response and response.status == 200, (BROWSER, width, "page inaccessible")
        assert page.locator("main#contenu").count() == 1
        assert page.get_by_role("heading", name="Merci de votre visite.").count() == 1
        assert page.locator("main form").count() == 0
        assert page.locator("main .merci-intro").count() == 1
        assert "ne confirme donc pas" in page.locator("main .merci-intro").inner_text()
        assert "a été transmis" not in page.locator("main").inner_text()
        actions = page.locator("main nav.merci-actions a")
        assert actions.count() == 3, (BROWSER, width, "nombre d'actions")
        expected = ("/projets/sinjira/", "/contact.html", "/")
        assert tuple(actions.nth(i).get_attribute("href") for i in range(3)) == expected
        for item in [page.locator("main .merci-card")] + actions.all():
            rect = item.bounding_box()
            assert rect, (BROWSER, width, "élément masqué")
            assert rect["x"] >= -2 and rect["x"] + rect["width"] <= width + 2, (
                BROWSER, width, "débordement horizontal", rect
            )
        for action in actions.all():
            assert action.bounding_box()["height"] >= 44, (BROWSER, width, "cible tactile")
        if width == 390 and js_enabled:
            actions.nth(1).click()
            assert urlsplit(page.url).path == "/contact.html", (
                BROWSER, width, "lien contact erroné", page.url
            )
        print(f"OK {BROWSER}: {width}px, JS={'actif sous CSP' if js_enabled else 'désactivé'}")
    finally:
        context.close()


def main():
    if BROWSER not in ("chromium", "firefox", "webkit"):
        raise ValueError("Moteur non autorisé")
    html = static_contract()
    with sync_playwright() as p:
        browser = getattr(p, BROWSER).launch()
        try:
            for js_enabled in (False, True):
                for width in WIDTHS:
                    check_page(browser, html, width, js_enabled)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
