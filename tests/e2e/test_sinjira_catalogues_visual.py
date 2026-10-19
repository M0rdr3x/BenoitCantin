#!/usr/bin/env python3
"""Preuve visuelle locale, sans identifiants ni déploiement, des trois catalogues.

Ce test s'exécute même quand la PR globale reste DRAFT : les autres
parcours authentifiés et le workflow de publication restent fermés.
"""
from __future__ import annotations

import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:4173/"
BROWSER = os.environ.get("BROWSER", "chromium")
CATEGORIES = {
    "romans": (1672, 941),
    "jeux": (1916, 821),
    "logiciels": (2048, 768),
}


def require(condition: bool, explanation: str) -> None:
    if not condition:
        raise AssertionError(f"{BROWSER}: {explanation}")


def image_loaded(page, selector: str, width: int, height: int) -> None:
    page.locator(selector).scroll_into_view_if_needed()
    page.wait_for_function(
        """([selector, w, h]) => {
            const img = document.querySelector(selector);
            return img && img.complete && img.naturalWidth === w
                && img.naturalHeight === h;
        }""",
        arg=[selector, width, height],
        timeout=15_000,
    )


def proportions(page, selector: str, category: str, viewport: int) -> None:
    dimensions = page.locator(selector).evaluate(
        """img => {
            const box = img.getBoundingClientRect();
            return {
                displayedWidth: box.width,
                displayedHeight: box.height,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                fit: getComputedStyle(img).objectFit,
                overflow: document.documentElement.scrollWidth - innerWidth
            };
        }"""
    )
    expected_height = (
        dimensions["displayedWidth"] * dimensions["naturalHeight"]
        / dimensions["naturalWidth"]
    )
    require(
        dimensions["displayedWidth"] > 250
        and abs(dimensions["displayedHeight"] - expected_height) < 3
        and dimensions["fit"] == "contain",
        f"{category}: image déformée ou rognée sur {viewport}px {dimensions}",
    )
    require(
        dimensions["overflow"] <= 2,
        f"{category}: débordement horizontal {viewport}px "
        f"{dimensions['overflow']}px",
    )




def mobile_current_category_visible(page) -> None:
    """La catégorie sélectionnée doit être visible sans sauter le héros.

    Le menu horizontal peut dépasser la largeur d'un téléphone, mais la
    page courante doit rester lisible à son chargement et après rotation.
    """
    for category in CATEGORIES:
        page.set_viewport_size({"width": 390, "height": 844})
        response = page.goto(
            urljoin(BASE_URL, f"projets/sinjira/{category}/"),
            wait_until="load", timeout=30_000,
        )
        require(response is not None and response.status in (200, 304),
                f"{category}: HTTP inattendu à 390 px : "
                f"{response.status if response else 'sans réponse'}")
        current = page.locator(".universe-subnav a[aria-current='page']")
        require(current.count() == 1,
                f"{category}: catégorie courante introuvable")
        def state():
            return current.evaluate("""element => {
                const bar = element.closest('.universe-subnav').querySelector('.container');
                const area = bar.getBoundingClientRect();
                const selected = element.getBoundingClientRect();
                return {
                    left: selected.left, right: selected.right,
                    boundaryLeft: area.left, boundaryRight: area.right,
                    scrollLeft: bar.scrollLeft, scrollWidth: bar.scrollWidth,
                    width: bar.clientWidth, pageY: scrollY
                };
            }""")
        page.wait_for_function("""() => {
            const item = document.querySelector('.universe-subnav [aria-current="page"]');
            const bar = item?.closest('.universe-subnav')?.querySelector('.container');
            if (!item || !bar) return false;
            const rect = item.getBoundingClientRect(), area = bar.getBoundingClientRect();
            return rect.left >= area.left - 2 && rect.right <= area.right + 2;
        }""", timeout=5_000)
        initial = state()
        require(
            initial["left"] >= initial["boundaryLeft"] - 2
            and initial["right"] <= initial["boundaryRight"] + 2,
            f"{category}: onglet actif caché en mobile : {initial}",
        )
        require(initial["pageY"] < 3,
                f"{category}: l'ajustement horizontal a sauté le héros : {initial}")
        if category == "logiciels":
            require(initial["scrollLeft"] > 2 and
                    initial["scrollWidth"] > initial["width"],
                    f"Logiciels : onglet courant hors champ non corrigé : {initial}")
            # Simuler une rotation après une manipulation du ruban :
            # seule la nouvelle largeur est responsable du recalage.
            page.evaluate("""() => {
                document.querySelector('.universe-subnav .container').scrollLeft = 0;
            }""")
            page.set_viewport_size({"width": 420, "height": 844})
            page.wait_for_function("""() => {
                const nav = document.querySelector('.universe-subnav .container');
                const selected = nav.querySelector('[aria-current="page"]').getBoundingClientRect();
                const rect = nav.getBoundingClientRect();
                return selected.left >= rect.left - 2 && selected.right <= rect.right + 2;
            }""", timeout=5_000)
            rotated = state()
            require(rotated["pageY"] < 3,
                    f"Logiciels : rotation provoque un défilement vertical : {rotated}")
    page.set_viewport_size({"width": 1440, "height": 960})


def software_anchor_navigation(page) -> None:
    """Les boutons #outils/#avenir doivent laisser les titres visibles.

    La barre principale et le sous-menu SINJIRA restent sticky :
    sur un petit écran, un fragment HTML sans scroll-margin masque le
    titre de la section qu'il était censé ouvrir.
    """
    for viewport in (1440, 390):
        page.set_viewport_size({"width": viewport, "height": 844})
        for fragment in ("outils", "avenir"):
            response = page.goto(
                urljoin(BASE_URL, "projets/sinjira/logiciels/"),
                wait_until="domcontentloaded",
                timeout=30_000,
            )
            require(response is not None and response.status == 200,
                    f"Logiciels: HTTP non 200 sur {viewport}px")
            page.locator(
                f'.hero-actions a[href="#{fragment}"]'
            ).click()
            page.wait_for_function(
                "(value) => location.hash === value",
                arg=f"#{fragment}",
                timeout=5_000,
            )
            # Le test utilise le positionnement réel des deux barres,
            # pas seulement une comparaison de chaînes dans le CSS.
            geometry = page.locator(f"#{fragment}").evaluate(
                """target => {
                    const nav = document.querySelector('.universe-subnav');
                    const header = document.querySelector('.site-header');
                    const rect = target.getBoundingClientRect();
                    return {
                        top: rect.top,
                        headerBottom: header.getBoundingClientRect().bottom,
                        navBottom: nav.getBoundingClientRect().bottom,
                        margin: parseFloat(getComputedStyle(target).scrollMarginTop),
                        headingVisible: !!target.querySelector('h2')
                    };
                }"""
            )
            require(
                geometry["margin"] >= 165 and geometry["headingVisible"],
                f"Logiciels #{fragment}: décalage d'ancre absent "
                f"({viewport}px, {geometry})",
            )
            require(
                geometry["top"] >= max(
                    geometry["headerBottom"], geometry["navBottom"]
                ) - 2,
                f"Logiciels #{fragment}: section masquée par les menus "
                f"({viewport}px, {geometry})",
            )
    page.set_viewport_size({"width": 1440, "height": 960})


def main() -> None:
    require(BROWSER in {"chromium", "firefox", "webkit"}, "moteur inconnu")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        page = browser.new_page(
            viewport={"width": 1440, "height": 960},
            locale="fr-CA",
            reduced_motion="reduce",
        )
        try:
            for category, (width, height) in CATEGORIES.items():
                response = page.goto(
                    urljoin(BASE_URL, f"projets/sinjira/{category}/"),
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                require(
                    response is not None and response.status == 200,
                    f"{category}: réponse HTTP non 200",
                )
                src = f"/assets/media/sinjira-{category}-banniere-2026.webp"
                selector = (
                    ".sinjira-category-poster--banner "
                    + f'img[src="{src}"]'
                )
                require(page.locator(selector).count() == 1,
                        f"{category}: bannière officielle introuvable")
                image_loaded(page, selector, width, height)
                nav = page.locator(
                    'nav.main-nav a[href="/projets/sinjira/"]'
                )
                current = page.locator(
                    'nav.universe-subnav a[aria-current="page"]'
                )
                require(
                    nav.count() == 1
                    and nav.get_attribute("aria-current") == "location",
                    f"{category}: page parente faussement sélectionnée",
                )
                require(current.count() == 1, f"{category}: plusieurs pages actives")
                current_url = urljoin(
                    page.url, current.get_attribute("href") or ""
                ).rstrip("/").removesuffix("/index.html")
                require(
                    current_url == page.url.rstrip("/"),
                    f"{category}: sous-navigation sélectionne une autre page",
                )
                for viewport in (1440, 390):
                    page.set_viewport_size(
                        {"width": viewport, "height": 844}
                    )
                    proportions(page, selector, category, viewport)
                page.set_viewport_size({"width": 1440, "height": 960})

            mobile_current_category_visible(page)
            software_anchor_navigation(page)

            response = page.goto(
                urljoin(BASE_URL, "projets/sinjira/"),
                wait_until="domcontentloaded",
                timeout=30_000,
            )
            require(response is not None and response.status == 200,
                    "portail SINJIRA inaccessible")
            for category, (width, height) in CATEGORIES.items():
                selector = (
                    f'a.v24-portal-card[href="{category}/"] '
                    f'img.sinjira-portal-art'
                )
                require(page.locator(selector).count() == 1,
                        f"{category}: affiche absente de l'accueil")
                image_loaded(page, selector, width, height)
                require(
                    page.locator(selector).evaluate(
                        "img => getComputedStyle(img).objectFit"
                    ) == "contain",
                    f"{category}: miniature d'accueil recadrée",
                )
            print(
                f"OK {BROWSER}: 3 catalogues + portail, bannières "
                "décodées, ratios naturels, 390px, onglet actif visible, navigation ARIA et ancres visibles"
            )
        finally:
            browser.close()


if __name__ == "__main__":
    main()
