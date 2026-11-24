#!/usr/bin/env python3
"""Recette navigateur SINJIRA Roman IV : mobile, ordinateur, clavier et mode sans JS.

Les éditions PDF/EPUB sont volontairement hors ligne. Le test ne contacte
aucun compte, service privé ou stockage de manuscrit.
"""
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER = os.environ.get("BROWSER", "chromium").lower().strip()
ROMAN_PATH = "projets/sinjira/romans/les-cicatrices-du-salut/"
WIDTHS = (320, 360, 390, 430, 768, 1024, 1440)


def require(value, message):
    if not value:
        raise AssertionError(f"{BROWSER}: {message}")


def inspect(page, width):
    page.set_viewport_size({"width": width, "height": 850})
    response = page.goto(urljoin(BASE_URL, ROMAN_PATH), wait_until="domcontentloaded",
                         timeout=30_000)
    require(response is not None and response.status < 400,
            f"Roman IV introuvable à {width}px")
    page.wait_for_function(
        "() => document.documentElement.hasAttribute('data-sinjira-nav-initialized')",
        timeout=15_000,
    )
    geometry = page.evaluate("""() => {
      const checks = ['.sinjira-roman-iv-panel', '.sinjira-roman-iv-actions .btn',
                      '.sinjira-novel-iv-facts > div'];
      const nodes = checks.flatMap(s => [...document.querySelectorAll(s)]);
      return {
        overflow: document.documentElement.scrollWidth > innerWidth + 2,
        protruding: nodes.some(node => {
          const box = node.getBoundingClientRect();
          return box.left < -2 || box.right > innerWidth + 2;
        }),
        buttons: [...document.querySelectorAll('.sinjira-roman-iv-actions .btn')]
          .map(node => node.getBoundingClientRect().height),
        nav: getComputedStyle(document.querySelector('[data-main-nav]')).display,
        logo: document.querySelector('.site-header .brand img')?.getAttribute('src'),
        forbiddenLinks: [...document.querySelectorAll('a[href]')]
          .filter(a => /\.(pdf|epub)([?#]|$)/i.test(a.getAttribute('href') || '')).length,
        heading: document.querySelector('h1')?.textContent?.trim() || '',
        facts: [...document.querySelectorAll('.sinjira-novel-iv-facts > div')]
          .map(node => node.textContent.trim()),
        touch: getComputedStyle(document.querySelector('.sinjira-roman-iv-actions .btn')).minHeight,
      };
    }""")
    require(not geometry["overflow"], f"défilement horizontal à {width}px: {geometry}")
    require(not geometry["protruding"], f"élément hors écran à {width}px: {geometry}")
    require(geometry["forbiddenLinks"] == 0, f"document privé exposé à {width}px")
    require(geometry["logo"] == "/assets/icons/sinjira-officiel-20261120.png",
            f"identité visuelle incorrecte à {width}px")
    require(geometry["heading"] == "Les Cicatrices du Salut", f"titre incorrect à {width}px")
    require(len(geometry["facts"]) == 3 and "55 pages" in geometry["facts"][0]
            and "494 pages" in geometry["facts"][1]
            and "EPUB" in geometry["facts"][2],
            f"versions du roman mal expliquées à {width}px")
    require(len(geometry["buttons"]) >= 2 and min(geometry["buttons"]) >= 44,
            f"boutons trop petits à {width}px: {geometry}")
    require(page.locator('link[href^="/assets/css/site-ux-sinjira-v1.css?v="]').count() == 1,
            f"CSS UX absent à {width}px")

    toggle = page.locator("[data-menu-toggle]")
    nav = page.locator("[data-main-nav]")
    if width <= 1020:
        require(toggle.is_visible(), f"menu mobile invisible à {width}px")
        require(nav.is_hidden(), f"menu mobile ouvert sans action à {width}px")
        toggle.click()
        require(toggle.get_attribute("aria-expanded") == "true",
                f"état ARIA du menu invalide à {width}px")
        require(nav.is_visible(), f"menu mobile non déployé à {width}px")
        page.keyboard.press("Escape")
        require(toggle.get_attribute("aria-expanded") == "false" and nav.is_hidden(),
                f"fermeture par Échap défectueuse à {width}px")
        require(page.evaluate("() => document.activeElement?.hasAttribute('data-menu-toggle')"),
                f"focus non rendu au menu à {width}px")
    else:
        require(nav.is_visible(), f"menu ordinateur invisible à {width}px")


def run():
    require(BROWSER in {"chromium", "firefox", "webkit"}, "navigateur invalide")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        try:
            context = browser.new_context(
                locale="fr-CA", viewport={"width": 390, "height": 850},
                reduced_motion="reduce", service_workers="block",
            )
            try:
                page = context.new_page()
                for width in WIDTHS:
                    inspect(page, width)
            finally:
                context.close()

            no_js = browser.new_context(
                locale="fr-CA", viewport={"width": 390, "height": 850},
                java_script_enabled=False, reduced_motion="reduce",
            )
            try:
                page = no_js.new_page()
                response = page.goto(urljoin(BASE_URL, ROMAN_PATH),
                                     wait_until="domcontentloaded", timeout=30_000)
                require(response is not None and response.status < 400,
                        "fiche indisponible sans JS")
                nav = page.locator("[data-main-nav]")
                require(nav.is_visible(), "liens du menu perdus si JavaScript est bloqué")
                paths = tuple(nav.locator("a").evaluate_all(
                    "(links) => links.map(a => new URL(a.href).pathname)"
                ))
                require(paths == (
                    "/", "/projets/sinjira/", "/projets/sinjira/romans/",
                    "/projets/sinjira/jeux/", "/projets/sinjira/registre/",
                    "/projets/sinjira/communaute/", "/compte/",
                ), f"destinations de secours incomplètes ou mal ordonnées : {paths}")
                require(not page.evaluate(
                    "() => document.documentElement.scrollWidth > innerWidth + 2"),
                    "débordement lorsque JavaScript est désactivé")
            finally:
                no_js.close()
            print(f"OK {BROWSER}: Roman IV, 7 largeurs 320–1440 px, clavier, menu et mode sans JS")
        finally:
            browser.close()


if __name__ == "__main__":
    run()
