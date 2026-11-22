#!/usr/bin/env python3
"""Contrat UX Codex SINJIRA : honnêteté, structure, responsive, CSP stricte.

Cette suite vérifie uniquement les parcours publics, sans compte ni backend.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
CODEX = ROOT / "projets/sinjira/codex/index.html"
CSS = ROOT / "assets/css/codex-ux-v1.css"
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173").rstrip("/")
BROWSER = os.environ.get("BROWSER", "chromium").lower()
WIDTHS = (240, 320, 390, 768, 1440)
NEXT = (
    "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/",
    "/projets/sinjira/registre/",
)
CSP = (
    "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'"
)
DESCRIPTION = (
    "Codex SINJIRA™ en préparation : futures fiches de personnages, lieux, factions "
    "et événements avec sources et protection contre les divulgâcheurs."
)


def check_sources() -> str:
    html = CODEX.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert html.count(DESCRIPTION) == 4, "métadonnées de disponibilité divergentes"
    assert "Codex vivant de SINJIRA™" not in html
    assert '<body class="project-page codex-ux-page"' in html
    assert 'href="/assets/css/codex-ux-v1.css?v=1.0.0"' in html
    assert html.count('src="/assets/icons/sinjira-officiel-20261120.png"') == 2
    assert (ROOT / "assets/icons/sinjira-officiel-20261120.png").is_file()
    assert "aucune fiche publique consultable" in html
    assert "aucune fiche" in html.lower()
    assert "Méthode prévue · non publiée" in html
    assert 'class="v24-badge live"' not in html
    assert not re.search(r'\b(?:style|onclick|onload|onerror)\s*=', html, re.I)
    assert '<h1 id="codex-title">' in html
    assert 'aria-labelledby="codex-method-title"' in html
    assert 'aria-labelledby="codex-next-title"' in html

    # Régression des blocs : une fermeture de div superflue cassait la
    # structure de la page et pouvait déplacer l'état vide hors du conteneur.
    main = html.split('<main id="contenu"', 1)[1].split("</main>", 1)[0]
    assert len(re.findall(r"<section(?:\s|>)", main)) == 3
    assert len(re.findall(r"</section>", main)) == 3
    assert len(re.findall(r"<div(?:\s|>)", main)) == len(re.findall(r"</div>", main))
    assert main.count('<article class="v24-panel">') == 3
    assert main.count('class="codex-next-links"') == 1

    for link in NEXT:
        assert f'href="{link}"' in html, link
        assert (ROOT / link.lstrip("/") / "index.html").is_file(), link
    for fragment in (
        "min-height:52px", ":focus-visible",
        "@media(max-width:900px)", "@media(max-width:600px)",
        "prefers-reduced-motion:reduce",
    ):
        assert fragment in css, fragment
    print("OK statique : statut véridique, DOM équilibré, visuel officiel, 3 liens existants")
    return html


def check_browser(browser, html: str, width: int, js: bool) -> None:
    ctx = browser.new_context(
        viewport={"width": width, "height": 800},
        java_script_enabled=js,
        service_workers="block",
        reduced_motion="reduce",
    )
    try:
        if js:
            ctx.route(
                re.compile(r"/projets/sinjira/codex/(?:index\.html)?(?:\?.*)?$"),
                lambda route: route.fulfill(
                    status=200,
                    body=html,
                    headers={"content-type": "text/html; charset=utf-8",
                             "content-security-policy": CSP},
                ),
            )
        page = ctx.new_page()
        res = page.goto(BASE + "/projets/sinjira/codex/", wait_until="domcontentloaded", timeout=30000)
        assert res and res.status == 200, (BROWSER, width, "Codex indisponible")
        assert page.locator("main h1").count() == 1
        assert page.locator("main h1").is_visible()
        assert page.locator("main > section").count() == 3, (BROWSER, width, "sections mal imbriquées")
        assert page.locator("main aside.codex-method-panel").count() == 1
        assert page.locator("main .codex-method-list dt").count() == 4
        assert page.locator("main .codex-method-list dd").count() == 4
        assert page.locator("main .codex-topic-grid article").count() == 3
        assert "aucune fiche publique consultable" in page.locator("main").inner_text()
        assert "Les champs ci-dessous décrivent" in page.locator("main").inner_text()
        assert page.locator("main .v24-badge.live").count() == 0
        assert page.locator("main form, main input").count() == 0

        links = page.locator("main nav.codex-next-links a")
        assert links.count() == len(NEXT)
        for link, href in zip(links.all(), NEXT):
            assert link.get_attribute("href") == href
            rect = link.bounding_box()
            assert rect and rect["height"] >= 44, (BROWSER, width, "tactile insuffisant", rect)
            assert rect["x"] >= -2 and rect["x"] + rect["width"] <= width + 2, (
                BROWSER, width, "lien hors écran", href, rect
            )

        for selector in ("main .v24-shell", "main .codex-method-panel", "main .codex-next-panel"):
            for item in page.locator(selector).all():
                rect = item.bounding_box()
                assert rect and rect["x"] >= -2 and rect["x"] + rect["width"] <= width + 2, (
                    BROWSER, width, selector, rect
                )
        full_width = page.evaluate(
            "() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)"
        )
        assert full_width <= width + 2, (BROWSER, width, "défilement horizontal", full_width)
        for image in page.locator(".site-header .brand img, .site-footer .footer-brand img").all():
            image.scroll_into_view_if_needed()
            assert image.evaluate("(img) => img.complete && img.naturalWidth > 0"), (
                BROWSER, width, "logo SINJIRA non chargé"
            )

        if width == 390:
            link = links.nth(1)
            link.focus()
            assert page.evaluate(
                "() => document.activeElement?.getAttribute('href') === '/projets/sinjira/jeux/'"
            ), (BROWSER, "lien non focalisable")
            page.keyboard.press("Enter")
            page.wait_for_url(re.compile(r"/projets/sinjira/jeux/(?:index\.html)?$"), timeout=15000)
            assert urlsplit(page.url).path.startswith("/projets/sinjira/jeux/")
        print(f"OK {BROWSER}: Codex {width}px JS={'CSP' if js else 'désactivé'}")
    finally:
        ctx.close()


def main() -> None:
    if BROWSER not in ("chromium", "firefox", "webkit"):
        raise ValueError("Navigateur non reconnu")
    html = check_sources()
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        try:
            for js in (False, True):
                for width in WIDTHS:
                    check_browser(browser, html, width, js)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
