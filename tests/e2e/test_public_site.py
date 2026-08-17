#!/usr/bin/env python3
import os
from urllib.parse import urljoin, urlparse

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
AUTH_ROUTES = [
    "compte/connexion.html",
    "compte/inscription.html",
    "compte/mot-de-passe-oublie.html",
    "compte/reinitialiser-mot-de-passe.html",
]
EXPECTED_DOORS = {
    "/projets/sinjira/",
    "/projets/sinjira/registre/",
    "/projets/projet-nova/",
}
NOVA_ENDPOINT = "https://formspree.io/f/xkolwjdg"
PERSONAL_ENDPOINT = "https://formspree.io/f/xdenkzrv"
IS_LOCAL = (urlparse(BASE_URL).hostname or "").lower() in {"127.0.0.1", "localhost"}


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

        # Le formulaire de contact contient encore un petit runtime inline : on le
        # teste dans chaque moteur pour éviter une régression Safari/Firefox.
        page.goto(urljoin(BASE_URL, "contact.html"), wait_until="domcontentloaded", timeout=30_000)
        project = page.locator("#contact-project")
        form = page.locator("#contact-general")
        route = page.locator("#contact-route")
        project.select_option("Projet Nova")
        assert_true(form.get_attribute("action") == NOVA_ENDPOINT, f"{BROWSER_NAME}: routage Nova incorrect")
        assert_true("Projet Nova" in route.inner_text(), f"{BROWSER_NAME}: confirmation Nova absente")
        project.select_option("SINJIRA")
        assert_true(form.get_attribute("action") == PERSONAL_ENDPOINT, f"{BROWSER_NAME}: routage SINJIRA incorrect")
        assert_true("Benoit Cantin" in route.inner_text(), f"{BROWSER_NAME}: confirmation SINJIRA absente")
        contact_html = page.content().lower()
        assert_true("kingtyrano@gmail.com" not in contact_html, "Adresse privée embarquée dans le formulaire de contact")

        # Le smoke Auth détaillé est volontairement exécuté uniquement sur la copie
        # exacte du dépôt. Le déploiement GitHub Pages peut être en retard de quelques
        # secondes sur le push; mélanger ce test de version au site public créerait un
        # faux négatif de CI. Aucune soumission n'est effectuée et aucun compte n'est créé.
        if IS_LOCAL:
            for auth_route in AUTH_ROUTES:
                auth_url = urljoin(BASE_URL, auth_route)
                response = page.goto(auth_url, wait_until="domcontentloaded", timeout=30_000)
                assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: page Auth inaccessible: {auth_route}")
                assert_true(page.locator("main#main-content").count() == 1, f"{BROWSER_NAME}: main Auth accessible absent: {auth_route}")
                assert_true(page.locator("h1").count() == 1, f"{BROWSER_NAME}: H1 Auth invalide: {auth_route}")
                assert_true(page.locator('a.skip-link[href="#main-content"]').count() == 1, f"{BROWSER_NAME}: lien d'évitement Auth absent: {auth_route}")
                assert_true(page.locator('[data-account-status]').count() == 1, f"{BROWSER_NAME}: zone de statut Auth absente: {auth_route}")
                robots = page.locator('meta[name="robots"]').get_attribute("content") or ""
                assert_true("noindex" in robots.lower(), f"{BROWSER_NAME}: page Auth indexable: {auth_route}")
                assert_true(bool(page.title().strip()), f"{BROWSER_NAME}: titre Auth absent: {auth_route}")

            page.goto(urljoin(BASE_URL, "compte/inscription.html"), wait_until="domcontentloaded", timeout=30_000)
            assert_true(page.locator('input[type="password"][minlength="12"]').count() == 2, f"{BROWSER_NAME}: politique 12 caractères incohérente à l'inscription")
            page.goto(urljoin(BASE_URL, "compte/reinitialiser-mot-de-passe.html"), wait_until="domcontentloaded", timeout=30_000)
            assert_true(page.locator('input[type="password"][minlength="12"]').count() == 2, f"{BROWSER_NAME}: politique 12 caractères incohérente à la réinitialisation")

            # L’assistant V24.4.39 est testé sur la copie exacte du dépôt pour éviter
            # les faux négatifs pendant les quelques secondes de propagation Pages.
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_function("window.__SINJIRA_ASSISTANT__ && window.__SINJIRA_ASSISTANT__.version === '24.4.39'", timeout=10_000)
            assistant = page.evaluate("window.__SINJIRA_ASSISTANT__")
            assert_true(assistant.get("providerMode") == "local", f"{BROWSER_NAME}: assistant non local")
            assert_true(assistant.get("externalProviderEnabled") is False, f"{BROWSER_NAME}: fournisseur externe activé")
            assert_true(assistant.get("privacy") == "ephemeral-memory-only", f"{BROWSER_NAME}: contrat de confidentialité assistant invalide")

            assistant_toggle = page.locator(".sinjira-assistant-toggle")
            assert_true(assistant_toggle.count() == 1, f"{BROWSER_NAME}: bouton Aide IA absent")
            assistant_toggle.click()
            panel = page.locator("#sinjira-assistant-panel")
            assert_true(panel.is_visible(), f"{BROWSER_NAME}: panneau assistant ne s’ouvre pas")
            assert_true(assistant_toggle.get_attribute("aria-expanded") == "true", f"{BROWSER_NAME}: aria-expanded assistant invalide")

            question = page.locator("#sinjira-assistant-input")
            question.fill("Comment créer mon personnage ?")
            question.press("Enter")
            log_text = page.locator(".sinjira-assistant-log").inner_text().lower()
            assert_true("registre des consciences" in log_text, f"{BROWSER_NAME}: réponse Registre absente")
            assert_true(page.locator('.sinjira-assistant-link[href="/projets/sinjira/registre/"]').count() >= 1, f"{BROWSER_NAME}: lien Registre assistant absent")
            page.keyboard.press("Escape")
            assert_true(panel.is_hidden(), f"{BROWSER_NAME}: Escape ne ferme pas l’assistant")

            page.goto(urljoin(BASE_URL, "projets/projet-nova/"), wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_function("window.__SINJIRA_ASSISTANT__ && window.__SINJIRA_ASSISTANT__.version === '24.4.39'", timeout=10_000)
            assert_true(page.locator(".sinjira-assistant-toggle").count() == 1, f"{BROWSER_NAME}: assistant absent de Projet Nova")

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

        if IS_LOCAL:
            mobile_page.wait_for_function("window.__SINJIRA_ASSISTANT__ && window.__SINJIRA_ASSISTANT__.version === '24.4.39'", timeout=10_000)
            mobile_assistant = mobile_page.locator(".sinjira-assistant-toggle")
            mobile_assistant.click()
            mobile_panel = mobile_page.locator("#sinjira-assistant-panel")
            assert_true(mobile_panel.is_visible(), f"{BROWSER_NAME}: assistant mobile ne s’ouvre pas")
            assistant_overflow = mobile_page.evaluate(
                "document.documentElement.scrollWidth <= Math.ceil(window.innerWidth) + 2"
            )
            assert_true(assistant_overflow, f"{BROWSER_NAME}: assistant crée un débordement horizontal en 390 px")
            mobile_page.keyboard.press("Escape")

        mobile.close()

        # Contrôle la réponse HTML initiale de la zone privée. Certains moteurs
        # exécutent la redirection d’authentification avant que Playwright ne lise
        # le DOM; le contrat noindex doit donc être vérifié sur la réponse source.
        account_url = urljoin(BASE_URL, "compte/")
        account_response = context.request.get(account_url, timeout=30_000)
        assert_true(account_response.ok, f"{BROWSER_NAME}: page compte inaccessible")
        account_html = account_response.text().lower()
        assert_true("kingtyrano@gmail.com" not in account_html, "Adresse propriétaire embarquée dans la page compte")
        has_robots = 'name="robots"' in account_html or "name='robots'" in account_html
        assert_true(has_robots and "noindex" in account_html, "Page compte non protégée contre l’indexation")

        all_errors = page_errors + mobile_errors
        assert_true(not all_errors, f"{BROWSER_NAME}: erreurs JavaScript navigateur: " + " | ".join(all_errors[:5]))
        context.close()
        browser.close()
        auth_note = f", {len(AUTH_ROUTES)} pages Auth locales + assistant V24.4.39" if IS_LOCAL else ""
        print(
            f"OK E2E {BROWSER_NAME}: {len(PUBLIC_ROUTES)} routes publiques{auth_note}, "
            f"accueil desktop/mobile, contact, compatibilité CSS/runtime et frontière compte vérifiés sur {BASE_URL}"
        )


if __name__ == "__main__":
    run()