#!/usr/bin/env python3
"""Recette du véritable accueil SINJIRA, sans session ni service externe.

Vérifie l'ergonomie PC/mobile, le logo officiel, le menu au clavier,
et le repli de la navigation lorsque JavaScript est désactivé.
"""
import os
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER = os.environ.get("BROWSER", "chromium").strip().lower()
WIDTHS = (320, 390, 420, 600, 768, 1020, 1024, 1440)
LOGO = "/assets/icons/sinjira-officiel-20261120.png"
NAV_PATHS = (
    "/", "/projets/sinjira/", "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/", "/projets/sinjira/registre/",
    "/projets/sinjira/communaute/", "/compte/",
)


def verify(condition, message):
    if not condition:
        raise AssertionError(f"{BROWSER}: {message}")


def geometry(page):
    return page.evaluate("""() => {
      const box = element => {
        const b = element.getBoundingClientRect();
        return {left:b.left,right:b.right,top:b.top,bottom:b.bottom,
                width:b.width,height:b.height};
      };
      const orbit=document.querySelector('.home-sinjira-cosmos .sinjira-orbit');
      const cosmos=document.querySelector('.home-sinjira-cosmos');
      const label=document.querySelector('.home-sinjira-cosmos .cosmos-label');
      const note=document.querySelector('.home-sinjira-note');
      const cards=[...document.querySelectorAll('.home-project')];
      return {
        width:innerWidth,
        overflow:document.documentElement.scrollWidth > innerWidth + 2,
        logo:orbit?.querySelector('img')?.getAttribute('src'),
        orbit:box(orbit),cosmos:box(cosmos),label:box(label),
        children:[...orbit.children].map(box),
        noteMargin:parseFloat(getComputedStyle(note).marginTop),
        cards:cards.map(box)
      };
    }""")


def test_home(page):
    response = page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)
    verify(response is not None and response.status < 400, "accueil local inaccessible")
    page.wait_for_function(
        "() => document.documentElement.hasAttribute('data-sinjira-nav-initialized')",
        timeout=12_000,
    )
    nav = page.locator("[data-main-nav]")
    toggle = page.locator("[data-menu-toggle]")
    verify(tuple(nav.locator("a").evaluate_all(
        "(links) => links.map(a => new URL(a.href).pathname)"
    )) == NAV_PATHS, "menu principal incomplet ou mal ordonné")
    verify(page.locator(".home-project").count() == 4,
           "les quatre accès directs SINJIRA doivent rester présents")

    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 760})
        state = geometry(page)
        verify(not state["overflow"], f"débordement horizontal à {width}px : {state}")
        verify(state["logo"] == LOGO, "logo officiel du cercle remplacé")
        verify(state["orbit"]["left"] >= -2 and state["orbit"]["right"] <= width + 2,
               f"cercle hors écran à {width}px : {state}")
        verify(abs((state["label"]["left"] + state["label"]["right"]) / 2
                   - (state["cosmos"]["left"] + state["cosmos"]["right"]) / 2) <= 3,
               f"légende du cercle non centrée à {width}px : {state}")
        verify(state["noteMargin"] >= 12,
               f"espacement du texte d'aide supprimé à {width}px : {state}")
        # Le contexte navigateur demande explicitement la réduction du mouvement.
        verify(page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
               == "auto", f"défilement animé malgré la préférence de mouvement à {width}px")
        if width <= 600:
            targets = page.locator(".site-footer .footer-col a")
            verify(targets.count() >= 5, "liens de pied de page manquants")
            short_targets = targets.evaluate_all(
                "(links) => links.filter(a => a.getBoundingClientRect().height < 43.5)"
                ".map(a => a.textContent.trim())"
            )
            verify(not short_targets,
                   f"liens difficiles à toucher à {width}px : {short_targets}")
        for child in state["children"]:
            verify(child["left"] >= state["orbit"]["left"] - 3 and
                   child["right"] <= state["orbit"]["right"] + 3 and
                   child["top"] >= state["orbit"]["top"] - 3 and
                   child["bottom"] <= state["orbit"]["bottom"] + 3,
                   f"contenu du cercle tronqué ou débordant à {width}px : {state}")
        for card in state["cards"]:
            verify(card["left"] >= -2 and card["right"] <= width + 2,
                   f"carte de rubrique débordante à {width}px : {state}")

        if width <= 1020:
            verify(toggle.is_visible() and not nav.is_visible(),
                   f"menu mobile non replié à {width}px")
            toggle.click()
            verify(nav.is_visible() and toggle.get_attribute("aria-expanded") == "true",
                   f"menu impossible à ouvrir à {width}px")
            page.keyboard.press("Escape")
            verify(not nav.is_visible() and
                   toggle.get_attribute("aria-expanded") == "false",
                   f"Échap ne ferme pas le menu à {width}px")
            verify(toggle.evaluate("(el) => document.activeElement === el"),
                   f"focus non restauré sur la commande à {width}px")
        else:
            verify(nav.is_visible() and not toggle.is_visible(),
                   f"menu bureau incorrect à {width}px")

    verify(page.locator(".home-cosmos a.sinjira-orbit").get_attribute("href")
           == "/projets/sinjira/", "destination officielle SINJIRA incorrecte")



def test_short_mobile_menu(page):
    """Le dernier lien reste atteignable au clavier sur petits écrans/paysage."""
    nav = page.locator("[data-main-nav]")
    toggle = page.locator("[data-menu-toggle]")
    for width, height in ((240, 420), (320, 340), (390, 360)):
        page.set_viewport_size({"width": width, "height": height})
        verify(toggle.is_visible() and nav.is_hidden(),
               f"menu compact non replié à {width}x{height}")
        toggle.focus()
        toggle.press("Enter")
        verify(nav.is_visible() and toggle.get_attribute("aria-expanded") == "true",
               f"menu compact impossible à ouvrir à {width}x{height}")
        # Firefox peut transférer le focus au moment de l'activation du
        # bouton. Repartir de sa position explicite plutôt que supposer
        # que le focus demeure inchangé après la touche Entrée.
        toggle.focus()
        verify(toggle.evaluate("(el) => document.activeElement === el"),
               f"focus perdu sur le bouton à {width}x{height}")
        for index, expected in enumerate(NAV_PATHS):
            page.keyboard.press("Tab")
            focused = page.evaluate("""() => {
              const link = document.activeElement;
              if (!link || !link.matches('[data-main-nav] a')) return null;
              return new URL(link.href).pathname;
            }""")
            verify(focused == expected,
                   f"parcours clavier incomplet à {width}x{height}, lien "
                   f"{index + 1}/7 : attendu {expected}, obtenu {focused}")
        last = nav.locator("a").last
        verify(last.evaluate("(a) => document.activeElement === a"),
               f"lien Compte non atteignable au clavier à {width}x{height}")
        page.wait_for_function("""() => {
          const nav = document.querySelector('[data-main-nav]');
          const last = nav?.querySelector('a:last-of-type');
          if (!nav || !last) return false;
          const menu = nav.getBoundingClientRect();
          const link = last.getBoundingClientRect();
          return link.top >= menu.top - 2 && link.bottom <= menu.bottom + 2;
        }""", timeout=5_000)
        dimensions = nav.evaluate("""el => ({
          scrollable: getComputedStyle(el).overflowY === 'auto' &&
                      el.scrollHeight > el.clientHeight,
          lastHeight: el.querySelector('a:last-of-type').getBoundingClientRect().height,
          scrollTop: el.scrollTop
        })""")
        verify(dimensions["scrollable"] and dimensions["lastHeight"] >= 47.5
               and dimensions["scrollTop"] > 0,
               f"dernier lien inaccessible dans le menu défilant à {width}x{height}: {dimensions}")
        page.keyboard.press("Escape")
        verify(nav.is_hidden() and toggle.get_attribute("aria-expanded") == "false"
               and toggle.evaluate("(el) => document.activeElement === el"),
               f"menu compact non refermé au clavier à {width}x{height}")


def test_without_javascript(browser):
    context = browser.new_context(
        java_script_enabled=False, service_workers="block", locale="fr-CA",
        reduced_motion="reduce", viewport={"width": 320, "height": 760},
    )
    try:
        page = context.new_page()
        response = page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)
        verify(response is not None and response.status < 400,
               "accueil sans JavaScript inaccessible")
        nav = page.locator("[data-main-nav]")
        for width in (320, 768, 1024):
            page.set_viewport_size({"width": width, "height": 760})
            verify(nav.is_visible(), f"liens inaccessibles sans JS à {width}px")
            verify(tuple(nav.locator("a").evaluate_all(
                "(links) => links.map(a => new URL(a.href).pathname)"
            )) == NAV_PATHS,
                   f"navigation de repli incomplète à {width}px")
            state = page.evaluate("""() => ({
              overflow:document.documentElement.scrollWidth > innerWidth + 2,
              left:document.querySelector('[data-main-nav]').getBoundingClientRect().left,
              right:document.querySelector('[data-main-nav]').getBoundingClientRect().right
            })""")
            verify(not state["overflow"] and state["left"] >= -2
                   and state["right"] <= width + 2,
                   f"navigation sans JS hors écran à {width}px : {state}")
    finally:
        context.close()


def run():
    verify(BROWSER in {"chromium", "firefox", "webkit"}, "navigateur inconnu")
    verify((urlparse(BASE).hostname or "") in {"localhost", "127.0.0.1"},
           "la recette responsive ne doit tester que le site local")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        try:
            context = browser.new_context(
                locale="fr-CA", viewport={"width": 390, "height": 760},
                reduced_motion="reduce", service_workers="block",
            )
            try:
                page = context.new_page()
                test_home(page)
                test_short_mobile_menu(page)
            finally:
                context.close()
            test_without_javascript(browser)
        finally:
            browser.close()
    print(f"OK {BROWSER}: accueil SINJIRA, 8 largeurs, clavier, mobile et sans JS")


if __name__ == "__main__":
    run()
