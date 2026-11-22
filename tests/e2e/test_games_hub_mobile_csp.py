#!/usr/bin/env python3
"""Hub Jeux SINJIRA : navigation rapide, clavier, CSP stricte, PC/mobile."""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PATH = "/projets/sinjira/jeux/"
FOLDER = ROOT / PATH.lstrip("/")
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173").rstrip("/")
ENGINE = os.environ.get("BROWSER", "chromium").lower()
WIDTHS = (240, 320, 390, 768, 1440)
GAME_ANCHORS = ("#jeu-fracture", "#jeu-resistance")
ACTION_HREFS = (
    "fracture-du-reseau-mere/index.html",
    "fracture-du-reseau-mere/regles.html",
    "fracture-du-reseau-mere/feuille-de-score.html",
    "reseau-mere-resistance/index.html",
)
CSP = (
    "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'"
)


def validate_static() -> str:
    html = (FOLDER / "index.html").read_text("utf-8")
    css = (FOLDER / "games-hub-ux-v1.css").read_text("utf-8")
    assert 'class="project-page games-page games-hub-ux"' in html
    assert 'href="games-hub-ux-v1.css?v=1.0.0"' in html
    assert html.count('class="games-quick-links"') == 1
    assert "aria-label=\"Choisir un jeu\"" in html
    for href in GAME_ANCHORS:
        assert f'href="{href}"' in html
        assert f'id="{href[1:]}"' in html
    assert 'aria-labelledby="titre-jeu-fracture"' in html
    assert 'aria-labelledby="titre-jeu-resistance"' in html
    assert 'id="titre-jeu-fracture"' in html
    assert 'id="titre-jeu-resistance"' in html
    for target in ACTION_HREFS:
        assert f'href="{target}"' in html, target
        assert (FOLDER / target).is_file(), target
    assert not re.search(r'\b(?:style|onclick|onerror|onload)\s*=', html, re.I)
    assert ':focus-visible' in css
    assert 'scroll-margin-top:135px' in css
    assert 'min-height:52px' in css
    assert '@media(max-width:560px)' in css
    assert 'prefers-reduced-motion:reduce' in css
    for cover in (
        "sinjira-jeux.webp", "sinjira-fracture-deduction-simplifiee-couverture.webp",
        "sinjira-reseau-mere-resistance-officiel.webp",
    ):
        assert (ROOT / "assets/media" / cover).is_file()
    print("OK statique : 2 liens internes, 4 liens de jeu et CSS externe compatible CSP")
    return html


def check_browser(browser, html: str, width: int, javascript: bool) -> None:
    ctx = browser.new_context(
        viewport={"width": width, "height": 760},
        java_script_enabled=javascript,
        reduced_motion="reduce",
        service_workers="block",
    )
    try:
        if javascript:
            ctx.route(
                re.compile(r"/projets/sinjira/jeux/(?:index\.html)?(?:\?.*)?$"),
                lambda route: route.fulfill(
                    status=200,
                    body=html,
                    headers={"content-type": "text/html; charset=utf-8", "content-security-policy": CSP},
                ),
            )
        page = ctx.new_page()
        response = page.goto(BASE + PATH, wait_until="domcontentloaded", timeout=30000)
        assert response and response.status == 200
        h1 = page.locator("main h1")
        assert h1.count() == 1, (
            ENGINE, width, "titre H1 absent du DOM", page.url,
            page.locator("main").count(), page.title()
        )
        assert h1.is_visible(), (
            ENGINE, width, "titre H1 masqué", page.url,
            h1.evaluate("(el) => ({display:getComputedStyle(el).display, rect:el.getBoundingClientRect().toJSON()})")
        )
        assert page.locator("main article.game-selection-card").count() == 2
        assert page.locator("main .games-quick-links a").count() == 2
        assert page.locator("main .game-card-actions a").count() == 4

        # Toutes les cibles doivent rester dans la zone visible du viewport :
        # les colonnes du jeu ne créent pas de défilement horizontal global.
        links = page.locator("main .games-quick-links a, main .game-card-actions a")
        assert links.count() == 6
        for link in links.all():
            box = link.bounding_box()
            assert box and box["height"] >= 44, (ENGINE, width, "zone tactile trop petite", box)
            assert box["x"] >= -2 and box["x"] + box["width"] <= width + 2, (
                ENGINE, width, "débordement de lien", box
            )
        for selector in (".game-selection-card--fracture", ".game-selection-card--refuge"):
            box = page.locator(selector).bounding_box()
            assert box and box["x"] >= -2 and box["x"] + box["width"] <= width + 2, (
                ENGINE, width, selector, box
            )
        document_width = page.evaluate(
            "() => Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)"
        )
        assert document_width <= width + 2, (ENGINE, width, "scroll horizontal global", document_width)

        # Les visuels officiels sont réellement chargés sur la page.
        for image in page.locator("main img").all():
            image.scroll_into_view_if_needed()
            assert image.evaluate("(el) => el.complete && el.naturalWidth > 0"), (
                ENGINE, width, "image inaccessible", image.get_attribute("src")
            )

        for href in GAME_ANCHORS:
            target = page.locator(href)
            assert target.count() == 1
            assert target.get_attribute("aria-labelledby"), (ENGINE, href)
        if width == 390:
            anchor = page.locator('main .games-quick-links a[href="#jeu-resistance"]')
            anchor.focus()
            assert page.evaluate(
                "() => document.activeElement?.getAttribute('href') === '#jeu-resistance'"
            ), (ENGINE, "focus clavier absent")
            page.keyboard.press("Enter")
            assert urlsplit(page.url).fragment == "jeu-resistance", (ENGINE, "ancre clavier", page.url)
            assert page.locator("#jeu-resistance").is_visible()

            # La navigation concrète fonctionne vers une page de jeu publique,
            # sans démarrer de moteur privé ni de session.
            page.locator('main .game-card-actions a[href="fracture-du-reseau-mere/regles.html"]').click()
            page.wait_for_url(re.compile(r"/jeux/fracture-du-reseau-mere/regles\.html$"), timeout=15000)
            assert urlsplit(page.url).path.endswith("/jeux/fracture-du-reseau-mere/regles.html")
        print(f"OK {ENGINE}: {width}px JS={'CSP' if javascript else 'désactivé'}")
    finally:
        ctx.close()


def main() -> None:
    if ENGINE not in ("chromium", "firefox", "webkit"):
        raise ValueError("Navigateur non reconnu")
    html = validate_static()
    with sync_playwright() as playwright:
        browser = getattr(playwright, ENGINE).launch()
        try:
            for javascript in (False, True):
                for width in WIDTHS:
                    check_browser(browser, html, width, javascript)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
