#!/usr/bin/env python3
"""Vérification locale de la navigation horizontale du compte SINJIRA.

Le test utilise le véritable HTML, CSS et le script de navigation du site.
Les modules d'authentification et les réseaux privés sont neutralisés.
"""
import os
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
ENGINE = os.environ.get("BROWSER", "chromium").strip().lower()
PAGES = ("compte/index.html", "compte/bibliotheque.html",
         "compte/mes-lectures.html", "compte/securite.html", "compte/profil.html")
WIDTHS = (320, 390, 600, 768, 1020, 1024, 1440)


def check(value, message):
    if not value:
        raise AssertionError(f"{ENGINE}: {message}")


def snapshot(page):
    return page.evaluate("""() => {
      const frame = document.querySelector('.sinjira-account-nav-frame');
      const scroll = frame?.querySelector('.account-nav-scroll');
      const arrows = frame?.querySelectorAll('.sinjira-account-nav-arrow') || [];
      const current = scroll?.querySelector('a[aria-current="page"]');
      const rect = current?.getBoundingClientRect();
      const region = scroll?.getBoundingClientRect();
      const admin = scroll?.querySelector('[data-admin-nav]');
      return {
        documentOverflow: document.documentElement.scrollWidth > innerWidth + 2,
        count: arrows.length, width:innerWidth,
        scrollWidth:scroll?.scrollWidth||0, clientWidth:scroll?.clientWidth||0,
        scrollLeft:scroll?.scrollLeft||0,
        scrollbar:scroll ? getComputedStyle(scroll).overflowX : 'missing',
        equipped:!!frame?.classList.contains('is-scrollable'),
        buttons:[...arrows].map(button=>({
          hidden:button.hidden,displayed:getComputedStyle(button).display!=='none',disabled:button.disabled,
          height:button.getBoundingClientRect().height,
          width:button.getBoundingClientRect().width,
          label:button.getAttribute('aria-label'),
          target:button.getAttribute('aria-controls')
        })),
        scrollId:scroll?.id,
        currentVisible:!!rect && !!region &&
          rect.left >= region.left - 3 && rect.right <= region.right + 3,
        adminHidden:!admin || getComputedStyle(admin).display==='none',
        focused:document.activeElement?.getAttribute('aria-label')
      };
    }""")


def run():
    check(ENGINE in {"chromium", "firefox", "webkit"}, "moteur inconnu")
    check((urlparse(BASE).hostname or "").lower() in {"localhost", "127.0.0.1"},
          "seul un site de test local est autorisé")
    with sync_playwright() as playwright:
        browser = getattr(playwright, ENGINE).launch()
        try:
            context = browser.new_context(
                viewport={"width":320,"height":800},locale="fr-CA",
                reduced_motion="reduce",service_workers="block")
            try:
                def local_scripts_only(route):
                    path = urlparse(route.request.url).path
                    if path in ("/assets/js/site.js", "/assets/js/sinjira-nav-boot-v2.js"):
                        return route.continue_()
                    return route.fulfill(status=200,content_type="text/javascript",
                                         body="/* Authentification neutralisée : test local. */")
                context.route("**/assets/js/**",local_scripts_only)
                context.route("**/*.supabase.co/**",lambda route: route.abort())
                page = context.new_page()
                for path in PAGES:
                    response=page.goto(urljoin(BASE,path),wait_until="domcontentloaded",
                                       timeout=30_000)
                    check(response is not None and response.status<400,
                          f"page non disponible : {path}")
                    page.locator(".sinjira-account-nav-frame").wait_for(timeout=12_000)
                    for width in WIDTHS:
                        page.set_viewport_size({"width":width,"height":800})
                        page.wait_for_timeout(60)
                        state=snapshot(page)
                        check(not state["documentOverflow"],
                              f"débordement global {path} à {width}px : {state}")
                        check(state["count"]==2 and state["adminHidden"],
                              f"commandes ou attribut hidden incorrects {path} : {state}")
                        if width<=1020:
                            check(state["equipped"] and state["scrollWidth"]>state["clientWidth"],
                                  f"défilement absent {path} à {width}px : {state}")
                            check(all(not b["hidden"] and b["height"]>=44 and b["width"]>=44
                                      and b["label"] and b["target"]==state["scrollId"]
                                      for b in state["buttons"]),
                                  f"boutons non accessibles {path} à {width}px : {state}")
                            check(state["currentVisible"],
                                  f"rubrique active hors de la zone visible {path} {width}: {state}")
                        else:
                            check(all(not b["displayed"] for b in state["buttons"]),
                                  f"commandes mobiles visibles sur PC {path} {width}: {state}")

                    # Le sens de lecture et les contrôles restent utilisables au clavier.
                    page.set_viewport_size({"width":390,"height":800})
                    region=page.locator(".account-nav-scroll")
                    next_button=page.get_by_role("button",name="Rubriques suivantes du compte")
                    previous_button=page.get_by_role("button",name="Rubriques précédentes du compte")
                    region.evaluate("(el) => el.scrollLeft=0")
                    page.wait_for_function("""() => {
                      const x=document.querySelector('.account-nav-scroll');
                      return x.scrollLeft<=2;
                    }""")
                    check(previous_button.is_disabled(),
                          f"flèche précédente disponible au bord gauche : {path}")
                    next_button.focus()
                    next_button.press("Enter")
                    page.wait_for_function("""() => {
                      const x=document.querySelector('.account-nav-scroll');
                      return x.scrollLeft>20;
                    }""")
                    page.wait_for_function("""() => {
                      const button=document.querySelector('.sinjira-account-nav-arrow');
                      return button && !button.disabled;
                    }""")
                    check(previous_button.is_enabled(),
                          f"la flèche précédente n'est pas réactivée : {path}")
                    previous_button.click()
                    page.wait_for_function("""() => {
                      const x=document.querySelector('.account-nav-scroll');
                      return x.scrollLeft<=2;
                    }""")
                # Si JS ne fonctionne pas, les liens originaux restent défilables.
                nojs=browser.new_context(java_script_enabled=False,
                                         viewport={"width":320,"height":720})
                try:
                    fallback=nojs.new_page()
                    fallback.goto(urljoin(BASE,"compte/index.html"),
                                  wait_until="domcontentloaded",timeout=30_000)
                    check(fallback.locator(".sinjira-account-nav-frame").count()==0,
                          "le repli sans JS est altéré")
                    check(fallback.evaluate("""() => {
                      const el=document.querySelector('.account-nav-scroll');
                      return !!el && el.scrollWidth>el.clientWidth &&
                        document.documentElement.scrollWidth <= innerWidth + 2;
                    }"""), "navigation sans JavaScript non défilable")
                finally:
                    nojs.close()
            finally:
                context.close()
        finally:
            browser.close()
    print(f"OK {ENGINE}: 5 pages du compte, 7 tailles, clavier, onglet actif et repli sans JS")


if __name__=="__main__":
    run()
