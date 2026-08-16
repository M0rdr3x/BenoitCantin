#!/usr/bin/env python3
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
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


def run() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(locale="fr-CA", viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page_errors = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        for route in PUBLIC_ROUTES:
            url = urljoin(BASE_URL, route)
            response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            assert_true(response is not None, f"Aucune réponse navigateur pour {url}")
            assert_true(response.status < 400, f"HTTP {response.status} pour {url}")
            assert_true(page.locator("main").count() >= 1, f"Repère main absent: {url}")
            assert_true(page.locator("h1").count() >= 1, f"H1 absent: {url}")
            assert_true(bool(page.title().strip()), f"Titre absent: {url}")

        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        cards = page.locator("a.home-project")
        assert_true(cards.count() == 3, f"Accueil: 3 portes attendues, trouvé {cards.count()}")
        hrefs = {cards.nth(i).get_attribute("href") for i in range(cards.count())}
        assert_true(hrefs == EXPECTED_DOORS, f"Accueil: portes inattendues: {hrefs}")
        home_text = page.locator("main").inner_text().lower()
        for retired_name in ("lumina", "futurax", "chroniques de l’ombre", "chroniques de l'ombre"):
            assert_true(retired_name not in home_text, f"Accueil: univers secondaire remis au premier plan: {retired_name}")

        mobile = browser.new_context(locale="fr-CA", viewport={"width": 390, "height": 844}, is_mobile=True)
        mobile_page = mobile.new_page()
        response = mobile_page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        assert_true(response is not None and response.status < 400, "Accueil mobile inaccessible")
        toggle = mobile_page.locator("[data-menu-toggle]")
        assert_true(toggle.count() == 1, "Bouton de menu mobile absent")
        toggle.click()
        assert_true(toggle.get_attribute("aria-expanded") == "true", "Menu mobile n’annonce pas son état ouvert")
        assert_true("open" in (mobile_page.locator("[data-main-nav]").get_attribute("class") or ""), "Menu mobile ne s’ouvre pas")
        mobile.close()

        # Une page privée peut être servie statiquement, mais ne doit jamais embarquer
        # l’identité de connexion du propriétaire ni être indexable sans session.
        page.goto(urljoin(BASE_URL, "compte/"), wait_until="domcontentloaded", timeout=30_000)
        html = page.content().lower()
        assert_true("kingtyrano@gmail.com" not in html, "Adresse propriétaire embarquée dans la page compte")
        robots = page.locator('meta[name="robots"]')
        assert_true(robots.count() == 1 and "noindex" in (robots.get_attribute("content") or "").lower(), "Page compte non protégée contre l’indexation")

        assert_true(not page_errors, "Erreurs JavaScript navigateur: " + " | ".join(page_errors[:5]))
        context.close()
        browser.close()
        print(f"OK E2E navigateur: {len(PUBLIC_ROUTES)} routes publiques, accueil desktop/mobile et frontière compte vérifiés sur {BASE_URL}")


if __name__ == "__main__":
    run()
