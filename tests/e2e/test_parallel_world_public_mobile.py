#!/usr/bin/env python3
"""Monde parallèle SINJIRA : parcours publics, mobile, clavier, CSS et CSP.

Les tests ne manipulent ni données de membre ni service distant.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "projets/sinjira/monde-parallele/index.html"
STYLES = ROOT / "assets/css/parallel-world-public-ux-v1.css"
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173").rstrip("/")
ENGINE = os.environ.get("BROWSER", "chromium").strip().lower()
WIDTHS = (240, 320, 390, 768, 1440)
ANCHORS = ("parallel-cycles", "parallel-pionniers", "parallel-protections")
LINKS = (
    "/compte/monde-parallele.html",
    "/projets/sinjira/registre/",
    "/confidentialite.html",
)
CSP = (
    "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'"
)


def static_contract() -> str:
    html = PAGE.read_text("utf-8")
    css = STYLES.read_text("utf-8")
    main = html.split('<main id="contenu">', 1)[1].split("</main>", 1)[0]
    assert '<body class="project-page parallel-public-ux"' in html
    assert 'href="/assets/css/parallel-world-public-ux-v1.css?v=1.0.0"' in html
    assert html.count('src="/assets/icons/sinjira-officiel-20261120.png"') == 2
    assert (ROOT / "assets/icons/sinjira-officiel-20261120.png").is_file()
    assert 'id="parallel-title"' in main
    assert 'class="parallel-jump-nav v24-shell"' in main
    assert 'aria-label="Accès rapide aux sections du Monde parallèle"' in main
    assert len(re.findall(r"<section(?:\s|>)", main)) == 5
    assert len(re.findall(r"</section>", main)) == 5
    assert len(re.findall(r"<div(?:\s|>)", main)) == len(re.findall(r"</div>", main))
    assert main.count('<section class="v24-section parallel-section"') == 3
    for anchor in ANCHORS:
        assert f'href="#{anchor}"' in main, anchor
        assert f'id="{anchor}"' in main, anchor
    assert "Accéder à mon espace (compte)" in main
    assert "Découvrir le Registre" in main
    assert "Créer mon dossier personnage" not in main
    assert 'class="v24-badge live"' not in main

    # Les principes existants de l'univers restent visibles : ne pas
    # altérer de façon involontaire la protection du compte ou des pionniers.
    for phrase in (
        "40 premiers personnages de fans approuvés",
        "Le numéro est attribué à l’approbation",
        "Chronique personnelle est privée par défaut",
        "L’IA pourra assister certaines tâches plus tard",
        "Les espaces jeunesse et adulte restent séparés",
        "Les correspondances nécessaires à l’autorisation restent côté serveur",
        "Pare-feu d’identité",
    ):
        assert phrase in main, phrase
    for path in LINKS:
        assert f'href="{path}"' in main, path
        target = ROOT / path.lstrip("/")
        assert target.is_file() if target.suffix else (target / "index.html").is_file()
    assert not re.search(r'\b(?:style|onclick|onload|onerror)\s*=', main, re.I)
    assert "<form" not in main.lower()
    assert 'min-height:52px' in css
    assert "scroll-margin-top:128px" in css
    assert ":focus-visible" in css
    assert "@media(max-width:900px)" in css
    assert "@media(max-width:600px)" in css
    assert "prefers-reduced-motion:reduce" in css
    print("OK statique : 3 ancres, liens publics, contenu préservé, CSS isolé")
    return html


def browser_check(browser, html: str, width: int, javascript: bool) -> None:
    context = browser.new_context(
        viewport={"width": width, "height": 760},
        java_script_enabled=javascript,
        service_workers="block",
        reduced_motion="reduce",
    )
    try:
        if javascript:
            context.route(
                re.compile(r"/projets/sinjira/monde-parallele/(?:index\.html)?(?:\?.*)?$"),
                lambda route: route.fulfill(
                    status=200, body=html,
                    headers={
                        "content-type": "text/html; charset=utf-8",
                        "content-security-policy": CSP,
                    },
                ),
            )
        page = context.new_page()
        response = page.goto(
            BASE + "/projets/sinjira/monde-parallele/",
            wait_until="domcontentloaded", timeout=30000,
        )
        assert response and response.status == 200
        assert page.locator("main h1").count() == 1
        assert page.locator("main h1").is_visible()
        assert page.locator("main > section").count() == 5
        assert page.locator("main > nav.parallel-jump-nav").count() == 1
        assert page.locator("main .parallel-section").count() == 3

        jumps = page.locator("main .parallel-jump-nav a")
        assert jumps.count() == len(ANCHORS)
        for jump, anchor in zip(jumps.all(), ANCHORS):
            assert jump.get_attribute("href") == "#" + anchor
            assert page.locator("#" + anchor).count() == 1
            bounds = jump.bounding_box()
            assert bounds and bounds["height"] >= 44, (ENGINE, width, "lien tactile trop court")
            assert bounds["x"] >= -2 and bounds["x"] + bounds["width"] <= width + 2, (
                ENGINE, width, "lien de section hors écran", bounds,
            )

        actions = page.locator("main .parallel-hero-actions a, main .parallel-next-links a")
        assert actions.count() == 5
        for action in actions.all():
            box = action.bounding_box()
            assert box and box["height"] >= 44, (ENGINE, width, "bouton trop petit", box)
            assert box["x"] >= -2 and box["x"] + box["width"] <= width + 2, (
                ENGINE, width, "bouton hors écran", box,
            )
        for selector in ("main .v24-shell", "main .v24-panel"):
            for element in page.locator(selector).all():
                box = element.bounding_box()
                assert box and box["x"] >= -2 and box["x"] + box["width"] <= width + 2, (
                    ENGINE, width, "panneau hors écran", selector, box
                )
        doc_width = page.evaluate(
            "() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)"
        )
        assert doc_width <= width + 2, (ENGINE, width, "débordement horizontal", doc_width)

        for logo in page.locator(".site-header .brand img, .site-footer .footer-brand img").all():
            logo.scroll_into_view_if_needed()
            assert logo.evaluate("(img) => img.complete && img.naturalWidth > 0"), (
                ENGINE, width, "logo officiel non chargé"
            )

        if width == 390:
            link = jumps.nth(1)
            link.focus()
            assert page.evaluate(
                "() => document.activeElement?.getAttribute('href') === '#parallel-pionniers'"
            ), (ENGINE, "navigation clavier impossible")
            page.keyboard.press("Enter")
            assert urlsplit(page.url).fragment == "parallel-pionniers"
            assert page.locator("#parallel-pionniers").is_visible()
        else:
            jumps.first.click()
            assert urlsplit(page.url).fragment == "parallel-cycles"

        print(f"OK {ENGINE}: {width}px JS={'CSP' if javascript else 'désactivé'}")
    finally:
        context.close()


def main() -> None:
    if ENGINE not in ("chromium", "firefox", "webkit"):
        raise ValueError("Navigateur non reconnu")
    html = static_contract()
    with sync_playwright() as p:
        browser = getattr(p, ENGINE).launch()
        try:
            for js in (False, True):
                for width in WIDTHS:
                    browser_check(browser, html, width, js)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
