#!/usr/bin/env python3
"""Récupération mobile/PC sans JavaScript ni gestionnaire inline, sous CSP stricte.

Tests passifs : site local uniquement, aucune authentification ni donnée privée.
"""
from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/")
ENGINE = os.environ.get("BROWSER", "chromium")
WIDTHS = (240, 320, 390, 768, 1440)
STRICT_CSP = (
    "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'"
)


def static_contracts():
    offline = (ROOT / "offline.html").read_text("utf-8")
    not_found = (ROOT / "404.html").read_text("utf-8")
    aliases = ROOT / "assets/js/sinjira-404-aliases-v1.js"
    css = (ROOT / "assets/css/site-ux-sinjira-v1.css").read_text("utf-8")

    assert '<a class="btn btn-primary" href="">Réessayer la connexion</a>' in offline
    assert "onclick=" not in offline and "style=" not in offline
    assert 'class="site-recovery-page site-offline-page"' in offline
    assert 'class="site-recovery-page site-not-found-page"' in not_found
    assert "style=" not in not_found and "<script>(" not in not_found
    assert not_found.count('sinjira-404-aliases-v1.js?v=1.0.0') == 1
    assert aliases.is_file()
    text = aliases.read_text("utf-8")
    assert "location.replace(aliases[p]+location.search+location.hash)" in text
    assert "if(aliases[p])" in text
    assert ".site-recovery-page .hero-actions .btn" in css
    print("OK: HTML/CSS/JS sans handlers inline sur les pages de récupération")


def verify_layout(page, label, width):
    assert page.locator("main .recovery-card").count() == 1, (label, width)
    assert page.locator("h1").count() == 1, (label, width)
    for link in page.locator(".recovery-card .hero-actions a").all():
        bounds = link.bounding_box()
        assert bounds, (label, width, "lien invisible")
        assert bounds["height"] >= 44, (label, width, bounds)
        assert bounds["x"] >= -2 and bounds["x"] + bounds["width"] <= width + 2, (
            label, width, "action débordante", bounds
        )


def retry_offline(browser, js_enabled):
    context = browser.new_context(
        viewport={"width": 240, "height": 760},
        java_script_enabled=js_enabled,
        reduced_motion="reduce",
    )
    try:
        page = context.new_page()
        counter = {"total": 0}
        offline = (ROOT / "offline.html").read_text("utf-8")
        def serve_recovery(route):
            counter["total"] += 1
            if counter["total"] == 1:
                route.fulfill(
                    status=200, body=offline,
                    headers={
                        "content-type": "text/html; charset=utf-8",
                        "content-security-policy": STRICT_CSP,
                    },
                )
            else:
                route.fulfill(
                    status=200,
                    content_type="text/html; charset=utf-8",
                    body="<html lang='fr'><title>Reprise</title>"
                         "<main><h1>Connexion rétablie</h1></main></html>",
                )
        page.route("**/temoin-connexion/", serve_recovery)
        page.goto(BASE + "/temoin-connexion/", wait_until="domcontentloaded")
        page.get_by_role("link", name="Réessayer la connexion").click()
        page.get_by_role("heading", name="Connexion rétablie").wait_for()
        assert counter["total"] == 2, counter
        assert page.url == BASE + "/temoin-connexion/"
        print(f"OK {ENGINE}: reprise réseau au même URL (JavaScript {'actif' if js_enabled else 'désactivé'})")
    finally:
        context.close()


def legacy_alias(browser):
    context = browser.new_context(viewport={"width": 320, "height": 760})
    try:
        page = context.new_page()
        html = (ROOT / "404.html").read_text("utf-8")
        def respond_404(route):
            route.fulfill(
                status=404,
                body=html,
                headers={
                    "content-type": "text/html; charset=utf-8",
                    "content-security-policy": STRICT_CSP,
                },
            )
        page.route("**/sinjira?*", respond_404)
        page.goto(BASE + "/sinjira?source=historique#univers", wait_until="domcontentloaded")
        expected = BASE + "/projets/sinjira/?source=historique#univers"
        page.wait_for_url(expected, timeout=8000)
        print(f"OK {ENGINE}: ancienne adresse redirigée sous CSP stricte")
    finally:
        context.close()


def main():
    if ENGINE not in ("chromium", "firefox", "webkit"):
        raise ValueError("Moteur non pris en charge")
    static_contracts()
    with sync_playwright() as playwright:
        browser = getattr(playwright, ENGINE).launch()
        try:
            for width in WIDTHS:
                for route in ("/404.html", "/offline.html"):
                    context = browser.new_context(
                        viewport={"width": width, "height": 760},
                        java_script_enabled=False,
                        reduced_motion="reduce",
                    )
                    try:
                        page = context.new_page()
                        response = page.goto(BASE + route, wait_until="domcontentloaded")
                        assert response and response.status == 200, (route, width)
                        verify_layout(page, route, width)
                        print(f"OK {ENGINE}: {route} {width}px sans JS")
                    finally:
                        context.close()
            retry_offline(browser, js_enabled=False)
            retry_offline(browser, js_enabled=True)
            legacy_alias(browser)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
