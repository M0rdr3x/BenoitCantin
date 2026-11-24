#!/usr/bin/env python3
"""Vérification locale de la navigation horizontale du compte SINJIRA.

Le test utilise le véritable HTML, CSS et le script de navigation du site.
Les modules d'authentification et les réseaux privés sont neutralisés.
"""
import os
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
ENGINE = os.environ.get("BROWSER", "chromium").strip().lower()
# Un échantillon transversal de rubriques actives et de sous-pages du compte.
PAGES = (
    "compte/index.html", "compte/bibliotheque.html", "compte/mes-lectures.html",
    "compte/securite.html", "compte/profil.html", "compte/communaute.html",
    "compte/licences.html", "compte/notifications.html", "compte/messages.html",
    "compte/parametres.html", "compte/mon-personnage.html", "compte/emploi.html",
    "compte/registre-personnel.html", "compte/rencontres.html",
    "compte/moderation.html", "compte/blocages.html", "compte/marche.html",
    "compte/projet.html",
)
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
        currentPresent:!!current,
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
                            # Certaines sous-pages n'ont pas de lien exact dans
                            # la barre; ne pas annoncer une rubrique différente
                            # comme la page courante.
                            if state["currentPresent"]:
                                page.wait_for_function("""() => {
                                  const scroll=document.querySelector('.account-nav-scroll');
                                  const current=scroll?.querySelector('a[aria-current="page"]');
                                  if(!current) return false;
                                  const a=current.getBoundingClientRect();
                                  const b=scroll.getBoundingClientRect();
                                  return a.left>=b.left-3 && a.right<=b.right+3;
                                }""", timeout=5_000)
                                state=snapshot(page)
                                check(state["currentVisible"],
                                      f"rubrique active hors de la zone visible {path} {width}: {state}")
                        else:
                            check(all(not b["displayed"] for b in state["buttons"]),
                                  f"commandes mobiles visibles sur PC {path} {width}: {state}")

                    # Le sens de lecture et les contrôles restent utilisables au clavier.
                    page.set_viewport_size({"width":390,"height":800})
                    # Les deux requestAnimationFrame du script de navigation
                    # se terminent après le changement de viewport sur WebKit.
                    # Attendre le layout puis réinitialiser le scroll pour
                    # tester les boutons depuis une borne contrôlée.
                    page.wait_for_timeout(250)
                    page.evaluate("""() => new Promise(resolve =>
                      requestAnimationFrame(() => requestAnimationFrame(resolve))
                    )""")
                    region=page.locator(".account-nav-scroll")
                    next_button=page.get_by_role("button",name="Rubriques suivantes du compte")
                    previous_button=page.get_by_role("button",name="Rubriques précédentes du compte")
                    region.evaluate("""(el) => {
                      el.scrollLeft = 0;
                      el.dispatchEvent(new Event('scroll'));
                    }""")
                    page.wait_for_function("""() => {
                      const x=document.querySelector('.account-nav-scroll');
                      const left=document.querySelector('.sinjira-account-nav-arrow');
                      return x && left && x.scrollLeft<=2 && left.disabled;
                    }""", timeout=5_000)
                    # Le prédicat précédent vérifie simultanément la position
                    # et la désactivation, sans fenêtre de course supplémentaire.
                    next_button.focus()
                    next_button.press("Enter")
                    page.wait_for_function("""() => {
                      const x=document.querySelector('.account-nav-scroll');
                      const left=document.querySelector('.sinjira-account-nav-arrow');
                      return x && left && x.scrollLeft>20 && !left.disabled;
                    }""", timeout=5_000)
                    check(previous_button.is_enabled(),
                          f"la flèche précédente n'est pas réactivée : {path}")
                    # Les barres du navigateur ou le clavier virtuel peuvent
                    # changer la hauteur sans changer la largeur du viewport.
                    # Le parcours manuel ne doit pas être recentré.
                    manual_scroll = region.evaluate("(el) => el.scrollLeft")
                    for height in (650, 800):
                        page.set_viewport_size({"width":390,"height":height})
                        page.evaluate("""() => new Promise(resolve =>
                          requestAnimationFrame(() => requestAnimationFrame(resolve))
                        )""")
                        page.wait_for_timeout(100)
                        after_height = region.evaluate("(el) => el.scrollLeft")
                        check(abs(after_height - manual_scroll) <= 3,
                              f"recentrage après changement de hauteur {path}: "
                              f"{manual_scroll} -> {after_height} à {height}px")
                    # WebKit peut repositionner une rubrique active après
                    # redimensionnement. Un clic doit reculer, pas forcément
                    # atteindre le début du ruban si le navigateur l'a recentré.
                    # Vérifier aussi que des clics répétés rejoignent la borne.
                    for backward_step in range(16):
                        before = region.evaluate("(el) => el.scrollLeft")
                        if before <= 2:
                            break
                        check(previous_button.is_enabled(),
                              f"flèche précédente désactivée trop tôt {path}: {snapshot(page)}")
                        try:
                            previous_button.click(timeout=2_000)
                        except PlaywrightTimeoutError as exc:
                            # WebKit peut atteindre la borne avant le clic et
                            # désactiver légitimement le bouton entre l'état
                            # observé et l'action. Ne pas confondre une telle
                            # convergence avec un blocage de navigation.
                            settled = snapshot(page)
                            if (settled["scrollLeft"] <= 2 and
                                    settled["buttons"][0]["disabled"]):
                                break
                            raise AssertionError(
                                f"{ENGINE}: bouton précédent indisponible "
                                f"avant la borne pour {path}: {settled}"
                            ) from exc
                        try:
                            page.wait_for_function("""(before) => {
                              const x=document.querySelector('.account-nav-scroll');
                              return x && x.scrollLeft < before - 1;
                            }""", arg=before, timeout=5_000)
                        except PlaywrightTimeoutError as exc:
                            raise AssertionError(
                                f"{ENGINE}: flèche précédente immobile pour {path}, "
                                f"étape {backward_step + 1}: {snapshot(page)}"
                            ) from exc
                        if region.evaluate("(el) => el.scrollLeft") <= 2:
                            break
                    else:
                        raise AssertionError(
                            f"{ENGINE}: début du menu inaccessible pour {path} "
                            f"après 16 clics : {snapshot(page)}"
                        )
                    page.wait_for_function("""() => {
                      const x=document.querySelector('.account-nav-scroll');
                      const left=document.querySelector('.sinjira-account-nav-arrow');
                      return x && left && x.scrollLeft<=2 && left.disabled;
                    }""", timeout=5_000)
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
    print(f"OK {ENGINE}: {len(PAGES)} pages du compte, 7 tailles, clavier, onglet actif et repli sans JS")


if __name__=="__main__":
    run()
