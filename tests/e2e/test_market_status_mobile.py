#!/usr/bin/env python3
"""Marché SINJIRA : statut honnête, parcours public et UX tactile 240–1440px.

Vérifie que l'interface annonce bien les fonctionnalités fermées par les flags.
Aucun paiement, compte ni requête privée n'est réalisé.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HTML_PATH = ROOT / "projets/sinjira/marche/index.html"
CSS_PATH = ROOT / "assets/css/market-status-responsive-v1.css"
FLAGS_PATH = ROOT / "assets/js/v24-feature-flags.js"
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173").rstrip("/")
ENGINE = os.environ.get("BROWSER", "chromium").lower()
WIDTHS = (240, 320, 390, 768, 1440)
DESTINATIONS = (
    "/projets/sinjira/",
    "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/",
)
DESCRIPTION = (
    "Marché SINJIRA™ en préparation : annonces, dons, ventes et paiements "
    "actuellement désactivés. Découvrez les conditions prévues avant son ouverture."
)
CSP = (
    "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'"
)


def validate_contract() -> str:
    html = HTML_PATH.read_text("utf-8")
    css = CSS_PATH.read_text("utf-8")
    flags = FLAGS_PATH.read_text("utf-8")
    # Changer un flag requiert de réviser la communication publique,
    # pas de laisser un statut obsolète après lancement du Marché.
    assert re.search(r"(?m)^\s*market:\s*false\s*,", flags), "Marché activé: vérifier les annonces publiques"
    assert re.search(r"(?m)^\s*marketPayments:\s*false\s*,", flags), "Paiements activés: réviser les mentions"
    assert html.count(DESCRIPTION) == 4, "Metadonnées SEO/social divergentes"
    assert '<body class="project-page market-ux-page"' in html
    assert 'href="/assets/css/market-status-responsive-v1.css?v=1.0.0"' in html
    assert 'data-v24-market-feed' in html
    assert html.count('data-v24-market-feed') == 1
    assert "le service n’est pas encore ouvert" in html
    assert "annonces, dons, ventes et paiements sont désactivés" in html
    assert 'Fonctionnalité non disponible' in html
    assert 'Fonctionnement prévu après activation' in html
    assert 'Aucune annonce n’est publiée pour le moment' in html
    assert not re.search(r'\b(?:style|onclick|onload|onerror)\s*=', html, re.I)
    assert "<form" not in html.lower(), "Aucun formulaire d'achat/vente ne doit être simulé"
    assert 'class="v24-badge live"' not in html
    assert html.count('src="/assets/icons/sinjira-officiel-20261120.png"') == 2
    assert (ROOT / "assets/icons/sinjira-officiel-20261120.png").is_file()
    for path in DESTINATIONS:
        assert f'href="{path}"' in html
        assert (ROOT / path.lstrip("/") / "index.html").is_file(), path
    for rule in (
        "min-height:52px", ":focus-visible",
        "@media(max-width:900px)", "@media(max-width:600px)",
        "prefers-reduced-motion:reduce",
    ):
        assert rule in css, rule
    print("OK contrat : Marché inactif et communiqué, 3 liens publics, pas de faux achat")
    return html


def validate_browser(browser, html: str, width: int, javascript: bool) -> None:
    context = browser.new_context(
        viewport={"width": width, "height": 800},
        java_script_enabled=javascript,
        service_workers="block",
        reduced_motion="reduce",
    )
    try:
        if javascript:
            context.route(
                re.compile(r"/projets/sinjira/marche/(?:index\.html)?(?:\?.*)?$"),
                lambda route: route.fulfill(
                    status=200, body=html,
                    headers={
                        "content-type": "text/html; charset=utf-8",
                        "content-security-policy": CSP,
                    },
                ),
            )
        page = context.new_page()
        market_reads = []
        page.on(
            "request",
            lambda req: market_reads.append(req.url)
            if "/rest/v1/market_listings" in req.url else None,
        )
        response = page.goto(
            BASE + "/projets/sinjira/marche/",
            wait_until="domcontentloaded", timeout=30000,
        )
        assert response and response.status == 200
        assert page.locator("main h1").count() == 1
        assert page.locator("main h1").is_visible()
        assert page.locator("main > section").count() == 4
        assert page.locator("main .market-status-panel").count() == 1
        assert page.locator("main .market-plans article").count() == 2
        assert page.locator("main [data-v24-market-feed]").count() == 1
        assert "le service n’est pas encore ouvert" in page.locator("main").inner_text()
        assert "Aucune annonce n’est publiée" in page.locator("main").inner_text()
        assert page.locator("main form, main input, main button").count() == 0

        links = page.locator("main .market-next-links a")
        assert links.count() == len(DESTINATIONS)
        for link, href in zip(links.all(), DESTINATIONS):
            assert link.get_attribute("href") == href, (ENGINE, href)
            bounds = link.bounding_box()
            assert bounds and bounds["height"] >= 44, (ENGINE, width, "Cible tactile", bounds)
            assert bounds["x"] >= -2 and bounds["x"] + bounds["width"] <= width + 2, (
                ENGINE, width, "Lien hors écran", href, bounds,
            )
        for selector in ("main .v24-shell", "main .market-status-panel", "main .market-plans article"):
            for element in page.locator(selector).all():
                rect = element.bounding_box()
                assert rect and rect["x"] >= -2 and rect["x"] + rect["width"] <= width + 2, (
                    ENGINE, width, selector, rect,
                )
        doc_width = page.evaluate(
            "() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)"
        )
        assert doc_width <= width + 2, (ENGINE, width, "Défilement horizontal", doc_width)
        for logo in page.locator(".site-header .brand img, .site-footer .footer-brand img").all():
            logo.scroll_into_view_if_needed()
            assert logo.evaluate("(img) => img.complete && img.naturalWidth > 0"), (
                ENGINE, width, "Image officielle indisponible",
            )
        if width == 390:
            link = links.nth(2)
            link.focus()
            assert page.evaluate(
                "() => document.activeElement?.getAttribute('href') === '/projets/sinjira/jeux/'"
            ), (ENGINE, "Focus clavier non fonctionnel")
            page.keyboard.press("Enter")
            page.wait_for_url(re.compile(r"/projets/sinjira/jeux/(?:index\.html)?$"), timeout=15000)
            assert urlsplit(page.url).path.startswith("/projets/sinjira/jeux/")
        assert not market_reads, (ENGINE, width, "Appel au marché fermé", market_reads)
        print(f"OK {ENGINE}: {width}px JS={'CSP' if javascript else 'désactivé'}")
    finally:
        context.close()


def main() -> None:
    if ENGINE not in ("chromium", "firefox", "webkit"):
        raise ValueError("Navigateur non reconnu")
    html = validate_contract()
    with sync_playwright() as playwright:
        browser = getattr(playwright, ENGINE).launch()
        try:
            for javascript in (False, True):
                for width in WIDTHS:
                    validate_browser(browser, html, width, javascript)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
