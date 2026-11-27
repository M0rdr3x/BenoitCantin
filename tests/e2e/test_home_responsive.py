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
    verify(page.locator('.home-project img[loading="lazy"][decoding="async"][fetchpriority="low"][width][height]').count() == 4,
           "images secondaires non différées ou dimensions absentes")
    verify(page.locator('.sinjira-orbit img[fetchpriority="high"]').count() == 1,
           "priorité du logo principal perdue")

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
        if width <= 700:
            verify(page.locator(".sinjira-orbit img").evaluate("(el) => getComputedStyle(el).filter") == "none",
                   f"filtre coûteux du logo mobile à {width}px")
            verify(page.locator(".site-header").evaluate("(el) => {const s=getComputedStyle(el);return (s.backdropFilter || s.webkitBackdropFilter || 'none') === 'none';}"),
                   f"flou coûteux de l’en-tête mobile à {width}px")
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
            verify(nav.evaluate("(el) => parseFloat(getComputedStyle(el).minWidth) === 0"),
                   f"largeur intrinsèque du menu non bornée à {width}px")
            verify(nav.evaluate("(el) => getComputedStyle(el).flexWrap === 'nowrap'"),
                   f"menu mobile ne doit pas créer de colonnes à {width}px")
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
    check_direct_access(page)



def check_direct_access(page):
    link = page.locator(".home-direct-access")
    target = page.locator("#univers-titre")
    verify(link.count() == 1 and link.get_attribute("href") == "#univers-titre",
           "accès direct aux rubriques absent")
    verify(link.bounding_box()["height"] >= 43.5,
           "zone tactile de l’accès direct insuffisante")
    verify(target.get_attribute("tabindex") == "-1", "titre cible non focalisable")
    link.focus()
    link.press("Enter")
    verify(urlparse(page.url).fragment == "univers-titre",
           "navigation directe vers les rubriques impossible au clavier")
    verify(page.locator(".home-project").count() == 4,
           "les quatre rubriques ne sont plus disponibles")
    verify(page.locator(".home-project").evaluate_all(
        """cards => cards.every(card => {
          const color = getComputedStyle(card).getPropertyValue('--card-glow').trim();
          const match = color.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
          if (!match) return false;
          const [r,g,b] = match.slice(1).map(Number);
          return r >= 150 && r > 1.45*g && r > 1.35*b;
        })"""),
           "palette rouge/noire des cartes non conforme")


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
            if index == 0 and nav.evaluate(
                "(el) => document.activeElement === el"
            ):
                # Firefox ajoute une étape Tab valide sur les régions de
                # défilement au clavier : NAV est une région scrollable
                # étiquetée. Les sept liens doivent rester visitables ensuite.
                verify(nav.get_attribute("aria-label") == "Navigation principale",
                       f"zone défilante sans nom accessible à {width}x{height}")
                page.keyboard.press("Tab")
            focused = page.evaluate("""() => {
              const link = document.activeElement;
              if (!link || !link.matches('[data-main-nav] a')) return null;
              return new URL(link.href).pathname;
            }""")
            if focused != expected:
                focus_state = page.evaluate("""() => {
                  const active = document.activeElement;
                  const nav = document.querySelector('[data-main-nav]');
                  const toggle = document.querySelector('[data-menu-toggle]');
                  return {
                    tag: active?.tagName || null,
                    id: active?.id || null,
                    className: String(active?.className || '').slice(0, 140),
                    href: active?.getAttribute('href') || null,
                    toggleExpanded: toggle?.getAttribute('aria-expanded'),
                    menuVisible: getComputedStyle(nav).display,
                    menuLinks: [...nav.querySelectorAll('a')].map(a => ({
                      href: a.getAttribute('href'),
                      tabIndex: a.tabIndex,
                      visible: a.getBoundingClientRect().height > 0
                    }))
                  };
                }""")
                raise AssertionError(
                    f"{BROWSER}: parcours clavier incomplet à {width}x{height}, "
                    f"lien {index + 1}/7 : attendu {expected}, obtenu {focused}. "
                    f"État public du focus : {focus_state}"
                )
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



def test_install_offer(browser):
    """iPhone : invite discrète, instructions sur demande; Android : vrai bouton d'installation."""
    iphone_ua = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                 "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                 "Mobile/15E148 Safari/604.1")
    context = browser.new_context(
        locale="fr-CA", user_agent=iphone_ua, service_workers="block",
        reduced_motion="reduce", viewport={"width": 240, "height": 420},
    )
    try:
        page = context.new_page()
        page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)
        card = page.locator(".sinjira-pwa-install[data-sinjira-pwa-install]")
        card.wait_for(state="visible", timeout=12_000)
        reveal = card.locator("[data-pwa-install-reveal]")
        details = card.locator("#sinjira-pwa-install-details")
        for width, height in ((240, 420), (320, 340), (390, 360)):
            page.set_viewport_size({"width": width, "height": height})
            verify(details.is_hidden() and reveal.get_attribute("aria-expanded") == "false",
                   f"l'invitation iOS occupe le site sans accord à {width}x{height}")
            metrics = card.evaluate("""el => {
              const b=el.getBoundingClientRect();
              const button=el.querySelector('[data-pwa-install-reveal]').getBoundingClientRect();
              return {top:b.top,bottom:b.bottom,height:b.height,buttonHeight:button.height,
                      overflow:document.documentElement.scrollWidth>innerWidth+2};
            }""")
            verify(not metrics["overflow"] and metrics["height"] <= 110
                   and metrics["buttonHeight"] >= 43.5 and metrics["top"] >= -2
                   and metrics["bottom"] <= height + 2,
                   f"invitation iOS compacte illisible à {width}x{height}: {metrics}")
            reveal.click()
            verify(details.is_visible() and reveal.get_attribute("aria-expanded") == "true",
                   f"les instructions iOS ne s'ouvrent pas à {width}x{height}")
            expanded = card.evaluate("""el => {
              const b=el.getBoundingClientRect();
              return {top:b.top,bottom:b.bottom,
                      overflow:document.documentElement.scrollWidth>innerWidth+2,
                      scrollable:el.scrollHeight>el.clientHeight};
            }""")
            verify(not expanded["overflow"] and expanded["top"] >= -2
                   and expanded["bottom"] <= height + 2,
                   f"les instructions iOS débordent à {width}x{height}: {expanded}")
            verify("Sur iPhone/iPad" in details.inner_text(),
                   "instructions manuelles Safari indisponibles")
            verify(card.locator("[data-pwa-install-action]").count() == 0,
                   "Safari affiche un bouton natif sans action disponible")
            page.keyboard.press("Escape")
            verify(details.is_hidden() and reveal.get_attribute("aria-expanded") == "false"
                   and reveal.evaluate("(el) => document.activeElement === el"),
                   f"Échap ne replie pas les instructions iOS à {width}x{height}")
        card.locator(".sinjira-pwa-install__close").click()
        verify(card.count() == 0, "la fermeture PWA n'a pas supprimé la proposition")
        page.reload(wait_until="domcontentloaded")
        page.locator('html[data-sinjira-pwa-ready="true"]').wait_for(state="attached", timeout=12_000)
        verify(page.locator(".sinjira-pwa-install[data-sinjira-pwa-install]").count() == 0,
               "une proposition refusée réapparaît dans la même session")
        page.goto(BASE.rstrip("/") + "/projets/sinjira/romans/",
                  wait_until="domcontentloaded", timeout=30_000)
        verify(page.locator(".sinjira-pwa-install[data-sinjira-pwa-install]").count() == 0,
               "la proposition PWA s'affiche sur une route non éligible")
    finally:
        context.close()

    android = browser.new_context(
        locale="fr-CA", service_workers="block",
        viewport={"width": 390, "height": 760},
    )
    try:
        page = android.new_page()
        page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)
        # Le module est injecté dynamiquement : DOMContentLoaded ne garantit
        # pas l'enregistrement de son écouteur beforeinstallprompt.
        page.locator('html[data-sinjira-pwa-ready="true"]').wait_for(state="attached", timeout=12_000)
        card = page.locator(".sinjira-pwa-install[data-sinjira-pwa-install]")
        for outcome in ("dismissed", "accepted"):
            page.evaluate("""outcome => {
              window.__testNativeInstallInvoked=false;
              const prompt=new Event('beforeinstallprompt',{cancelable:true});
              prompt.prompt=() => {window.__testNativeInstallInvoked=true; return Promise.resolve();};
              prompt.userChoice=Promise.resolve({outcome});
              window.dispatchEvent(prompt);
            }""", outcome)
            card.wait_for(state="visible", timeout=5_000)
            verify(card.locator("#sinjira-pwa-install-details").is_hidden(),
                   "l'invitation Android doit rester compacte par défaut")
            card.locator("[data-pwa-install-reveal]").click()
            card.locator("[data-pwa-install-action]").click()
            page.wait_for_function("() => window.__testNativeInstallInvoked === true", timeout=5_000)
            card.wait_for(state="detached", timeout=5_000)
    finally:
        android.close()

def test_responsive_images(browser):
    """Chaque densité conserve une image locale décodable, sans dépendance externe."""
    for width, density in ((390, 1), (1440, 3)):
        context = browser.new_context(
            viewport={"width": width, "height": 760}, device_scale_factor=density,
            locale="fr-CA", reduced_motion="reduce", service_workers="block",
        )
        try:
            page = context.new_page()
            page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)
            for name in ("registre", "jeux", "communaute"):
                image = page.locator(f'.home-project[href="/projets/sinjira/{name}/"] img')
                image.scroll_into_view_if_needed()
                page.wait_for_function(
                    """selector => {
                      const img = document.querySelector(selector);
                      return img && img.complete && img.naturalWidth > 0;
                    }""", arg=f'.home-project[href="/projets/sinjira/{name}/"] img',
                    timeout=12_000)
                current = image.evaluate("(img) => new URL(img.currentSrc).pathname")
                verify(current in (
                    f"/assets/media/sinjira-{name}-home-160.webp",
                    f"/assets/media/sinjira-{name}-home-336.webp"),
                    f"source adaptative incorrecte à {width}px DPR {density}: {current}")
                verify(image.bounding_box()["width"] <= 113,
                       f"image de carte hors format à {width}px")
        finally:
            context.close()


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
        check_direct_access(page)
        for width in (320, 768, 1024):
            page.set_viewport_size({"width": width, "height": 760})
            verify(nav.is_visible(), f"liens inaccessibles sans JS à {width}px")
            verify(page.locator("[data-menu-toggle]").is_hidden(),
                   f"commande inactive visible sans JS à {width}px")
            verify(page.locator("[data-menu-toggle]").get_attribute("hidden") is not None,
                   "commande inactive non masquée nativement")
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


def test_public_navigation_fallback(browser):
    routes = ("projets/sinjira/", "projets/sinjira/romans/",
              "projets/sinjira/jeux/", "projets/sinjira/registre/",
              "projets/sinjira/communaute/", "projets/sinjira/codex/")
    for js_enabled in (False, True):
        context = browser.new_context(
            java_script_enabled=js_enabled, service_workers="block", locale="fr-CA",
            reduced_motion="reduce", viewport={"width": 390, "height": 760},
        )
        try:
            if js_enabled:
                context.route("**/assets/js/site.js*", lambda route: route.abort())
            page = context.new_page()
            for route in routes:
                response = page.goto(BASE.rstrip("/") + "/" + route,
                                     wait_until="load", timeout=30_000)
                verify(response is not None and response.ok, f"route indisponible : {route}")
                nav = page.locator("[data-main-nav]")
                toggle = page.locator("[data-menu-toggle]")
                verify(nav.is_visible() and toggle.is_hidden(),
                       f"navigation de secours invalide : {route}, JS={js_enabled}")
                verify(toggle.get_attribute("hidden") is not None,
                       f"commande inactive non masquée nativement : {route}")
                verify(nav.locator('a[href="/compte/"]').is_visible(),
                       f"accès au compte absent : {route}")
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
            test_install_offer(browser)
            test_responsive_images(browser)
            test_without_javascript(browser)
            test_public_navigation_fallback(browser)
        finally:
            browser.close()
    print(f"OK {BROWSER}: accueil SINJIRA, 8 largeurs, clavier, mobile et sans JS")


if __name__ == "__main__":
    run()
