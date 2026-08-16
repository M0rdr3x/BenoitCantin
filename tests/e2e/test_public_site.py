#!/usr/bin/env python3
import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER_NAME = os.environ.get("BROWSER", "chromium").strip().lower()
SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
PUBLIC_ROUTES = [
    "",
    "a-propos.html",
    "contact.html",
    "projets/sinjira/",
    "projets/sinjira/registre/",
    "projets/projet-nova/",
    "projets/sinjira/jeux/",
    "projets/sinjira/jeux/fracture-du-reseau-mere/",
]
EXPECTED_DOORS = {
    "/projets/sinjira/",
    "/projets/sinjira/registre/",
    "/projets/projet-nova/",
}


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def register_error_capture(page, target):
    page.on("pageerror", lambda error: target.append(f"pageerror: {error}"))


def run() -> None:
    assert_true(BROWSER_NAME in SUPPORTED_BROWSERS, f"Navigateur Playwright inconnu: {BROWSER_NAME}")

    with sync_playwright() as p:
        browser_type = getattr(p, BROWSER_NAME)
        browser = browser_type.launch()

        context = browser.new_context(
            locale="fr-CA",
            viewport={"width": 1440, "height": 1000},
            reduced_motion="reduce",
        )
        page = context.new_page()
        page_errors = []
        register_error_capture(page, page_errors)

        for route in PUBLIC_ROUTES:
            url = urljoin(BASE_URL, route)
            response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            assert_true(response is not None, f"Aucune réponse navigateur pour {url}")
            assert_true(response.status < 400, f"HTTP {response.status} pour {url}")
            assert_true(page.locator("main").count() >= 1, f"Repère main absent: {url}")
            assert_true(page.locator("h1").count() >= 1, f"H1 absent: {url}")
            assert_true(bool(page.title().strip()), f"Titre absent: {url}")

        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_function(
            "document.querySelector('link[data-sinjira-browser-compat]') !== null",
            timeout=10_000,
        )
        compat_href = page.locator("link[data-sinjira-browser-compat]").get_attribute("href") or ""
        assert_true("browser-compat-v24-4-22.css" in compat_href, "Couche CSS de compatibilité non chargée")

        runtime_version = page.evaluate("window.__SINJIRA_RUNTIME__ && window.__SINJIRA_RUNTIME__.version")
        assert_true(runtime_version == "24.4.22", f"Runtime public inattendu: {runtime_version!r}")

        cards = page.locator("a.home-project")
        assert_true(cards.count() == 3, f"Accueil: 3 portes attendues, trouvé {cards.count()}")
        hrefs = {cards.nth(i).get_attribute("href") for i in range(cards.count())}
        assert_true(hrefs == EXPECTED_DOORS, f"Accueil: portes inattendues: {hrefs}")
        home_text = page.locator("main").inner_text().lower()
        for retired_name in ("lumina", "futurax", "chroniques de l’ombre", "chroniques de l'ombre"):
            assert_true(retired_name not in home_text, f"Accueil: univers secondaire remis au premier plan: {retired_name}")

        assert_true(
            page.evaluate("CSS && CSS.supports && CSS.supports('display', 'grid')"),
            f"{BROWSER_NAME}: CSS Grid indisponible dans le moteur testé",
        )

        mobile = browser.new_context(
            locale="fr-CA",
            viewport={"width": 390, "height": 844},
            has_touch=True,
            reduced_motion="reduce",
        )
        mobile_page = mobile.new_page()
        mobile_errors = []
        register_error_capture(mobile_page, mobile_errors)
        response = mobile_page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: accueil mobile inaccessible")

        overflow = mobile_page.evaluate(
            "document.documentElement.scrollWidth <= Math.ceil(window.innerWidth) + 2"
        )
        assert_true(overflow, f"{BROWSER_NAME}: débordement horizontal détecté en 390 px")

        toggle = mobile_page.locator("[data-menu-toggle]")
        assert_true(toggle.count() == 1, f"{BROWSER_NAME}: bouton de menu mobile absent")
        toggle.click()
        assert_true(toggle.get_attribute("aria-expanded") == "true", f"{BROWSER_NAME}: menu mobile n’annonce pas son état ouvert")
        nav_class = mobile_page.locator("[data-main-nav]").get_attribute("class") or ""
        assert_true("open" in nav_class.split(), f"{BROWSER_NAME}: menu mobile ne s’ouvre pas")
        toggle.click()
        assert_true(toggle.get_attribute("aria-expanded") == "false", f"{BROWSER_NAME}: menu mobile ne se referme pas")
        mobile.close()

        # Une page privée peut être servie statiquement, mais ne doit jamais embarquer
        # l’identité de connexion du propriétaire ni être indexable sans session.
        page.goto(urljoin(BASE_URL, "compte/"), wait_until="domcontentloaded", timeout=30_000)
        html = page.content().lower()
        assert_true("kingtyrano@gmail.com" not in html, "Adresse propriétaire embarquée dans la page compte")
        robots = page.locator('meta[name="robots"]')
        assert_true(
            robots.count() == 1 and "noindex" in (robots.get_attribute("content") or "").lower(),
            "Page compte non protégée contre l’indexation",
        )

        all_errors = page_errors + mobile_errors
        assert_true(not all_errors, f"{BROWSER_NAME}: erreurs JavaScript navigateur: " + " | ".join(all_errors[:5]))
        context.close()
        browser.close()
        print(
            f"OK E2E {BROWSER_NAME}: {len(PUBLIC_ROUTES)} routes publiques, "
            f"accueil desktop/mobile, compatibilité CSS/runtime et frontière compte vérifiés sur {BASE_URL}"
        )


if __name__ == "__main__":
    run()
