#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER_NAME = os.environ.get("BROWSER", "chromium").strip().lower()
SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
LITERATURE_ROUTE = "projets/sinjira/romans/"
READER_ROUTE = "projets/sinjira/romans/lire-demo.html"
DEMO_ROUTE = "projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"
DEMO_BASENAME = "SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"
FULL_BASENAME = "SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf"
CANONICAL = "https://www.benoitcantin.com/projets/sinjira/romans/"
READER_CANONICAL = "https://www.benoitcantin.com/projets/sinjira/romans/lire-demo.html"
BOOK_NAME = "SINJIRA™ — Livre I : La Cendre du Jugement"
READER_WORK_NAME = f"{BOOK_NAME} — Démo officielle"
COVER_URL = "https://www.benoitcantin.com/assets/media/sinjira-livre-1-cover.webp"
COVER_ALT = "Couverture de SINJIRA™ — Livre I : La Cendre du Jugement"


def assert_true(value, message: str) -> None:
    if not value:
        raise AssertionError(message)


def collect_page_errors(page, target: list[str]) -> None:
    page.on("pageerror", lambda error: target.append(f"pageerror: {error}"))


def block_embedded_pdf(context) -> None:
    # Le contrat du lecteur est testé sans dépendre du moteur PDF natif de Chromium/Firefox/WebKit.
    # La disponibilité HTTP du PDF est vérifiée séparément par une requête HEAD.
    context.route(
        f"**/{DEMO_BASENAME}",
        lambda route: route.fulfill(status=204, content_type="application/pdf", body=""),
    )


def json_ld_graph(page) -> list[dict]:
    nodes: list[dict] = []
    scripts = page.locator('script[type="application/ld+json"]')
    for index in range(scripts.count()):
        raw = scripts.nth(index).text_content() or ""
        if not raw.strip():
            continue
        payload = json.loads(raw)
        if isinstance(payload, dict) and isinstance(payload.get("@graph"), list):
            nodes.extend(node for node in payload["@graph"] if isinstance(node, dict))
        elif isinstance(payload, dict):
            nodes.append(payload)
    return nodes


def assert_no_full_edition_link(page, label: str) -> None:
    hrefs = page.locator("a[href]").evaluate_all("els => els.map(el => el.getAttribute('href') || '')")
    for href in hrefs:
        clean = href.split("#", 1)[0].split("?", 1)[0]
        assert_true(
            not clean.endswith(FULL_BASENAME),
            f"{BROWSER_NAME}: édition intégrale exposée par un lien public ({label}): {href}",
        )


def assert_no_horizontal_overflow(page, label: str) -> None:
    fits = page.evaluate("document.documentElement.scrollWidth <= Math.ceil(window.innerWidth) + 2")
    assert_true(fits, f"{BROWSER_NAME}: débordement horizontal en 390 px sur {label}")


def run() -> None:
    assert_true(BROWSER_NAME in SUPPORTED_BROWSERS, f"Navigateur Playwright inconnu: {BROWSER_NAME}")

    with sync_playwright() as p:
        browser = getattr(p, BROWSER_NAME).launch()
        context = browser.new_context(
            locale="fr-CA",
            viewport={"width": 1440, "height": 1000},
            reduced_motion="reduce",
        )
        block_embedded_pdf(context)
        page = context.new_page()
        errors: list[str] = []
        collect_page_errors(page, errors)

        literature_url = urljoin(BASE_URL, LITERATURE_ROUTE)
        response = page.goto(literature_url, wait_until="domcontentloaded", timeout=30_000)
        assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: page Littérature inaccessible")
        assert_true(page.locator("main#contenu").count() == 1, f"{BROWSER_NAME}: main Littérature absent")
        assert_true(page.locator("h1").inner_text().strip() == "Littérature.", f"{BROWSER_NAME}: H1 Littérature inattendu")
        assert_true(
            page.locator('link[rel="canonical"]').get_attribute("href") == CANONICAL,
            f"{BROWSER_NAME}: canonical Littérature incorrecte",
        )
        assert_true(
            page.locator('meta[property="og:url"]').get_attribute("content") == CANONICAL,
            f"{BROWSER_NAME}: og:url Littérature incorrect",
        )
        assert_true(
            page.locator('meta[name="twitter:card"]').get_attribute("content") == "summary_large_image",
            f"{BROWSER_NAME}: Twitter Card Littérature absente",
        )
        assert_true(page.locator('nav[aria-label="Navigation principale"]').count() == 1, f"{BROWSER_NAME}: navigation Littérature non nommée")
        assert_true("83 pages" in page.locator("main").inner_text(), f"{BROWSER_NAME}: pagination de la démo absente de la fiche")

        graph = json_ld_graph(page)
        books = [node for node in graph if node.get("@type") == "Book"]
        assert_true(len(books) == 1, f"{BROWSER_NAME}: provenance JSON-LD Book absente ou dupliquée")
        book = books[0]
        assert_true(book.get("name") == BOOK_NAME, f"{BROWSER_NAME}: nom JSON-LD du Livre I incorrect")
        assert_true(book.get("inLanguage") == "fr-CA", f"{BROWSER_NAME}: langue JSON-LD du Livre I incorrecte")
        demo_part = book.get("hasPart") or {}
        assert_true(demo_part.get("isAccessibleForFree") is True, f"{BROWSER_NAME}: gratuité de la démo non déclarée")
        assert_true(demo_part.get("url") == READER_CANONICAL, f"{BROWSER_NAME}: URL JSON-LD de la démo incorrecte")

        demo_links = page.locator(f'a[href="../documents/{DEMO_BASENAME}"]')
        assert_true(demo_links.count() >= 1, f"{BROWSER_NAME}: lien de téléchargement PDF stable absent")
        download_link = page.locator(f'a[download="{DEMO_BASENAME}"]')
        assert_true(download_link.count() == 1, f"{BROWSER_NAME}: téléchargement PDF nommé absent ou dupliqué")
        assert_true(download_link.get_attribute("type") == "application/pdf", f"{BROWSER_NAME}: type PDF du téléchargement absent")
        assert_no_full_edition_link(page, "Littérature")

        pdf_head = context.request.head(urljoin(BASE_URL, DEMO_ROUTE), timeout=30_000)
        assert_true(pdf_head.status < 400, f"{BROWSER_NAME}: PDF démo public inaccessible (HTTP {pdf_head.status})")

        reader_url = urljoin(BASE_URL, READER_ROUTE)
        response = page.goto(reader_url, wait_until="domcontentloaded", timeout=30_000)
        assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: lecteur démo inaccessible")
        assert_true(page.locator("main#lecteur").count() == 1, f"{BROWSER_NAME}: main lecteur absent")
        assert_true(page.locator('a.skip-link[href="#lecteur"]').count() == 1, f"{BROWSER_NAME}: lien d’évitement lecteur absent")
        assert_true(
            page.locator('link[rel="canonical"]').get_attribute("href") == READER_CANONICAL,
            f"{BROWSER_NAME}: canonical lecteur incorrecte",
        )
        assert_true(
            page.locator('meta[name="twitter:image"]').get_attribute("content") == COVER_URL,
            f"{BROWSER_NAME}: image Twitter du lecteur incorrecte",
        )
        assert_true(
            page.locator('meta[name="twitter:image:alt"]').get_attribute("content") == COVER_ALT,
            f"{BROWSER_NAME}: alternative de l’image Twitter du lecteur absente ou incorrecte",
        )

        reader_graph = json_ld_graph(page)
        reader_works = [
            node for node in reader_graph
            if node.get("@type") == "CreativeWork" and node.get("@id") == f"{READER_CANONICAL}#demo"
        ]
        assert_true(len(reader_works) == 1, f"{BROWSER_NAME}: JSON-LD de la démo lecteur absent ou dupliqué")
        reader_work = reader_works[0]
        assert_true(reader_work.get("name") == READER_WORK_NAME, f"{BROWSER_NAME}: nom JSON-LD du lecteur incorrect")
        assert_true(reader_work.get("url") == READER_CANONICAL, f"{BROWSER_NAME}: URL JSON-LD du lecteur incorrecte")
        assert_true(reader_work.get("inLanguage") == "fr-CA", f"{BROWSER_NAME}: langue JSON-LD du lecteur incorrecte")
        assert_true(reader_work.get("isAccessibleForFree") is True, f"{BROWSER_NAME}: gratuité JSON-LD du lecteur absente")
        author = reader_work.get("author") or {}
        assert_true(author.get("@type") == "Person" and author.get("name") == "Benoit Cantin", f"{BROWSER_NAME}: auteur JSON-LD du lecteur incorrect")
        parent_book = reader_work.get("isPartOf") or {}
        assert_true(parent_book.get("@type") == "Book", f"{BROWSER_NAME}: rattachement JSON-LD du lecteur au Livre I absent")
        assert_true(parent_book.get("name") == BOOK_NAME, f"{BROWSER_NAME}: Livre I parent JSON-LD incorrect")
        assert_true(parent_book.get("url") == CANONICAL, f"{BROWSER_NAME}: URL du Livre I parent incorrecte")
        assert_true(FULL_BASENAME not in page.content(), f"{BROWSER_NAME}: nom du fichier intégral exposé dans le lecteur")

        assert_true(page.locator('input[data-reader-page-number][aria-label="Numéro de page"]').count() == 1, f"{BROWSER_NAME}: champ de page lecteur non nommé")
        assert_true(page.locator("input[data-reader-page-number]").get_attribute("max") == "83", f"{BROWSER_NAME}: maximum du lecteur différent de 83")
        assert_true(page.locator('[data-reader-resume][aria-live="polite"]').count() == 1, f"{BROWSER_NAME}: reprise lecteur non annoncée aux aides techniques")
        frame = page.locator("iframe[data-pdf-reader]")
        assert_true(frame.count() == 1, f"{BROWSER_NAME}: iframe du lecteur absente")
        assert_true(DEMO_BASENAME in (frame.get_attribute("src") or ""), f"{BROWSER_NAME}: iframe ne pointe plus vers la démo stable")
        assert_true("83 pages" in page.locator("main").inner_text(), f"{BROWSER_NAME}: lecteur ne décrit plus la démo 83 pages")
        assert_no_full_edition_link(page, "lecteur")

        mobile = browser.new_context(
            locale="fr-CA",
            viewport={"width": 390, "height": 844},
            has_touch=True,
            reduced_motion="reduce",
        )
        block_embedded_pdf(mobile)
        mobile_page = mobile.new_page()
        mobile_errors: list[str] = []
        collect_page_errors(mobile_page, mobile_errors)

        for route, label in ((LITERATURE_ROUTE, "Littérature"), (READER_ROUTE, "lecteur démo")):
            response = mobile_page.goto(urljoin(BASE_URL, route), wait_until="domcontentloaded", timeout=30_000)
            assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: {label} inaccessible sur mobile")
            assert_no_horizontal_overflow(mobile_page, label)

        assert_true(mobile_page.locator("iframe[data-pdf-reader]").count() == 1, f"{BROWSER_NAME}: iframe lecteur mobile absente")
        assert_true(mobile_page.locator('a[download="SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"]').count() == 1, f"{BROWSER_NAME}: téléchargement lecteur mobile absent")

        assert_true(not errors, f"{BROWSER_NAME}: erreurs JavaScript Littérature: " + " | ".join(errors[:5]))
        assert_true(not mobile_errors, f"{BROWSER_NAME}: erreurs JavaScript Littérature mobile: " + " | ".join(mobile_errors[:5]))

        mobile.close()
        context.close()
        browser.close()
        print(f"OK littérature {BROWSER_NAME}: fiche, SEO, lecteur 83 pages, frontière intégrale et mobile vérifiés.")


if __name__ == "__main__":
    run()
