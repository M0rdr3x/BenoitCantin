#!/usr/bin/env python3
"""Navigation des pages juridiques SINJIRA : 240–1440px, clavier, sans JS/CSP.

Aucune donnée privée ni formulaire n'est manipulé.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173").rstrip("/")
BROWSER = os.environ.get("BROWSER", "chromium").strip().lower()
WIDTHS = (240, 320, 390, 768, 1440)
PAGES = {
    "confidentialite.html": ("Confidentialité.", 13),
    "gouvernance-vie-privee.html": ("Gouvernance de la vie privée.", 9),
    "avis-legal.html": ("Avis légal.", 10),
}
CSP = (
    "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
    "style-src 'self'; style-src-attr 'none'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'"
)


def validate_static() -> dict[str, str]:
    css = (ROOT / "assets/css/legal-page-navigation-v1.css").read_text("utf-8")
    for fragment in (
        "min-height:54px", "min-height:48px", ":focus-visible",
        "max-width:600px", "scroll-margin-top:105px",
    ):
        assert fragment in css, f"CSS du sommaire incomplet : {fragment}"
    pages = {}
    for filename, (title, count) in PAGES.items():
        html = (ROOT / filename).read_text("utf-8")
        main = html.split('<main id="contenu">', 1)[1].split("</main>", 1)[0]
        assert '<body class="legal-ux-page"' in html, filename
        assert '/assets/css/legal-page-navigation-v1.css?v=1.0.0' in html
        assert html.count('<details class="legal-ux-toc">') == 1
        assert html.count('<summary>Accès rapide aux ') == 1
        assert f"Accès rapide aux {count} sections" in main
        assert re.search(rf"<h1>{re.escape(title)}</h1>", main), filename
        assert len(re.findall(r'<h2 id="section-[^"]+">', main)) == count
        ids = re.findall(r'<h2 id="([^"]+)">([^<]+)</h2>', main)
        links = re.findall(r'<li><a href="#([^"]+)">([^<]+)</a></li>', main)
        assert len(ids) == len(links) == count
        assert [(id_, heading) for id_, heading in ids] == links, filename
        assert len(set(id_ for id_, _ in ids)) == count
        assert not re.search(r'\b(?:style|onclick|onload|onerror)\s*=', main, re.I)
        assert not re.search(r'<script\b', main, re.I)
        assert '<form' not in main.lower()
        pages[filename] = html
    print("OK contrat : 3 pages, 32 ancres correctes, aucun JS ou formulaire ajouté")
    return pages


def browser_page(browser, filename: str, html: str, width: int, js: bool) -> None:
    context = browser.new_context(
        viewport={"width": width, "height": 760},
        java_script_enabled=js,
        reduced_motion="reduce",
        service_workers="block",
    )
    try:
        if js:
            context.route(
                re.compile(r"/" + re.escape(filename) + r"(?:\?.*)?$"),
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
        response = page.goto(BASE + "/" + filename, wait_until="domcontentloaded", timeout=30000)
        assert response is not None and response.status == 200, (BROWSER, filename, width)
        title, expected = PAGES[filename]
        assert page.get_by_role("heading", level=1, name=title).count() == 1

        details = page.locator("main details.legal-ux-toc")
        summary = details.locator("summary")
        assert details.count() == 1
        assert not details.evaluate("(node) => node.open")
        assert summary.is_visible()
        rect = summary.bounding_box()
        assert rect and rect["height"] >= 44, (BROWSER, filename, width, "Sommaire petit")
        summary.click()
        assert details.evaluate("(node) => node.open"), (BROWSER, filename, width, "Sommaire inerte")

        links = details.locator("nav ol a")
        assert links.count() == expected, (BROWSER, filename, width, links.count())
        assert page.locator("main article h2[id]").count() == expected
        for link in links.all():
            box = link.bounding_box()
            assert box and box["height"] >= 44, (BROWSER, filename, width, "Cible tactile")
            assert box["x"] >= -2 and box["x"] + box["width"] <= width + 2, (
                BROWSER, filename, width, "Lien débordant", box
            )
            target = link.get_attribute("href")
            assert target and target.startswith("#section-")
            assert page.locator(target).count() == 1, (BROWSER, filename, target)

        document_width = page.evaluate(
            "() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)"
        )
        assert document_width <= width + 2, (
            BROWSER, filename, width, "Débordement horizontal", document_width
        )
        chosen = links.last if width == 390 else links.first
        target = chosen.get_attribute("href")
        if width == 390:
            chosen.focus()
            assert page.evaluate(
                "(href) => document.activeElement?.getAttribute('href') === href", target
            ), (BROWSER, filename, "Focus clavier perdu")
            page.keyboard.press("Enter")
        else:
            chosen.click()
        assert unquote(urlsplit(page.url).fragment) == target[1:], (
            BROWSER, filename, width, "Navigation d'ancre incorrecte", page.url
        )
        assert page.locator(target).is_visible()
        assert page.locator(target).evaluate(
            "(node) => getComputedStyle(node).scrollMarginTop !== '0px'"
        )
        print(f"OK {BROWSER}: {filename}, {width}px, JS={'CSP' if js else 'non'}")
    finally:
        context.close()


def main() -> None:
    if BROWSER not in ("chromium", "firefox", "webkit"):
        raise ValueError("Navigateur non pris en charge")
    pages = validate_static()
    with sync_playwright() as p:
        browser = getattr(p, BROWSER).launch()
        try:
            for js in (False, True):
                for filename, html in pages.items():
                    for width in WIDTHS:
                        browser_page(browser, filename, html, width, js)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
