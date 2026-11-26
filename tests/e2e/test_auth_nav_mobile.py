#!/usr/bin/env python3
"""Navigation Auth PC/mobile : liens visibles, clavier et repli sans JS.

Ne contacte ni Supabase ni les API de session ; tout script hors navigation
est neutralisé. Pages HTML et CSS réellement servis par le dépôt.
"""
import os
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
ENGINE = os.environ.get("BROWSER", "chromium").strip().lower()
PAGES = (
    "compte/connexion.html", "compte/inscription.html",
    "compte/mot-de-passe-oublie.html", "compte/reinitialiser-mot-de-passe.html",
)
WIDTHS = (240, 280, 320, 390, 540, 680, 768, 1440)


def check(condition, reason):
    if not condition:
        raise AssertionError(f"{ENGINE}: {reason}")


def snapshot(page):
    return page.evaluate("""() => {
      const nav=document.querySelector('.universe-subnav');
      const track=nav?.querySelector('.container');
      const active=track?.querySelector('a[aria-current="page"]');
      const box=track?.getBoundingClientRect();
      const a=active?.getBoundingClientRect();
      const arrows=[...(nav?.querySelectorAll('.sinjira-auth-nav-arrow')||[])];
      const visible=!!a && !!box && a.right>box.left+1 && a.left<box.right-1;
      const entire=!!a && !!box && a.left>=box.left-3 && a.right<=box.right+3;
      return {
        docOverflow:document.documentElement.scrollWidth>innerWidth+2,
        width:innerWidth, ready:nav?.hasAttribute('data-sinjira-auth-nav-ready'),
        equipped:nav?.classList.contains('is-scrollable'),
        scrollWidth:track?.scrollWidth||0, clientWidth:track?.clientWidth||0,
        scrollLeft:track?.scrollLeft||0, id:track?.id,
        count:arrows.length,
        current:!!active, currentVisible:visible, currentEntire:entire,
        currentWidth:a?.width||0,
        buttons:arrows.map(b=>{
          const r=b.getBoundingClientRect();
          return {hidden:b.hidden, displayed:getComputedStyle(b).display!=='none',
                  disabled:b.disabled, width:r.width,height:r.height,
                  label:b.getAttribute('aria-label'), target:b.getAttribute('aria-controls')};
        })
      };
    }""")


def active_is_visible(page):
    return page.evaluate("""() => {
      const n=document.querySelector('.universe-subnav .container');
      const active=n?.querySelector('a[aria-current="page"]');
      if(!active) return true;
      const b=n.getBoundingClientRect();
      const r=active.getBoundingClientRect();
      return r.right>b.left+1 && r.left<b.right-1 &&
        (r.width>b.width-4 || (r.left>=b.left-3 && r.right<=b.right+3));
    }""")


def run():
    check(ENGINE in {"chromium", "firefox", "webkit"}, "moteur inconnu")
    check((urlparse(BASE).hostname or "").lower() in {"localhost", "127.0.0.1"},
          "seul un site local est autorisé")
    with sync_playwright() as p:
        browser=getattr(p, ENGINE).launch()
        try:
            context=browser.new_context(
                viewport={"width":320,"height":800},locale="fr-CA",
                reduced_motion="reduce",service_workers="block")
            try:
                def route_script(route):
                    url=urlparse(route.request.url).path
                    if url == "/assets/js/sinjira-auth-nav-v1.js":
                        return route.continue_()
                    return route.fulfill(status=200,content_type="text/javascript",
                                         body="/* Scripts privés neutralisés. */")
                context.route("**/assets/js/**",route_script)
                context.route("**/*.supabase.co/**",lambda route:route.abort())
                page=context.new_page()
                for path in PAGES:
                    response=page.goto(urljoin(BASE,path),wait_until="domcontentloaded",
                                       timeout=30_000)
                    check(response is not None and response.status<400,
                          f"page absente {path}")
                    page.wait_for_function("""() =>
                      !!document.querySelector('.universe-subnav[data-sinjira-auth-nav-ready]')
                    """, timeout=12_000)
                    for width in WIDTHS:
                        page.set_viewport_size({"width":width,"height":800})
                        page.wait_for_timeout(80)
                        # WebKit diffère parfois l'observation de layout. Ne
                        # vérifier les flèches qu'après synchronisation.
                        page.wait_for_function("""() => {
                          const nav=document.querySelector('.universe-subnav');
                          const track=nav?.querySelector('.container');
                          return nav && track && (!nav.classList.contains('is-scrollable') ||
                            track.scrollWidth>track.clientWidth+2);
                        }""",timeout=5_000)
                        state=snapshot(page)
                        check(not state["docOverflow"],
                              f"débordement global {path} {width}px: {state}")
                        check(state["ready"] and state["count"]==2,
                              f"navigation non initialisée {path}: {state}")
                        expected=width<=680 and state["scrollWidth"]>state["clientWidth"]+2
                        if expected:
                            check(state["equipped"] and all(
                                  not b["hidden"] and b["displayed"]
                                  and b["width"]>=44 and b["height"]>=44
                                  and b["label"] and b["target"]==state["id"]
                                  for b in state["buttons"]),
                                  f"flèches non accessibles {path} {width}px: {state}")
                            page.wait_for_function("""() => {
                              const n=document.querySelector('.universe-subnav .container');
                              const a=n?.querySelector('a[aria-current="page"]');
                              if(!a)return true;
                              const r=a.getBoundingClientRect(),b=n.getBoundingClientRect();
                              return r.right>b.left+1 && r.left<b.right-1 &&
                                (r.width>b.width-4 || (r.left>=b.left-3 && r.right<=b.right+3));
                            }""", timeout=5_000)
                            check(active_is_visible(page),
                                  f"onglet actif non visible {path} {width}px")
                        else:
                            check(all(not b["displayed"] for b in state["buttons"]),
                                  f"flèches inutiles visibles {path} {width}px: {state}")
                    page.set_viewport_size({"width":320,"height":800})
                    page.wait_for_function("""() => {
                      const n=document.querySelector('.universe-subnav');
                      const t=n?.querySelector('.container');
                      return n?.classList.contains('is-scrollable') &&
                        t.scrollWidth>t.clientWidth+2;
                    }""",timeout=5_000)
                    track=page.locator(".universe-subnav .container")
                    prev=page.get_by_role("button",name="Liens précédents de connexion")
                    nxt=page.get_by_role("button",name="Liens suivants de connexion")
                    track.evaluate("(el)=>{el.scrollLeft=0}")
                    page.wait_for_function("""() => {
                      const n=document.querySelector('.universe-subnav .container');
                      const b=document.querySelector('.sinjira-auth-nav-arrow');
                      return n && b && n.scrollLeft<=2 && b.disabled;
                    }""",timeout=5_000)
                    # Un changement de hauteur ne doit pas recentrer le lien actif.
                    page.set_viewport_size({"width":320,"height":600})
                    page.evaluate("() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                    check(snapshot(page)["scrollLeft"]<=2,
                          f"recentrage non sollicité après changement de hauteur {path}: {snapshot(page)}")
                    nxt.focus()
                    nxt.press("Enter")
                    page.wait_for_function("""() => {
                      const n=document.querySelector('.universe-subnav .container');
                      const b=document.querySelector('.sinjira-auth-nav-arrow');
                      return n && b && n.scrollLeft>20 && !b.disabled;
                    }""",timeout=5_000)
                    prev.click()
                    page.wait_for_function("""() => {
                      const n=document.querySelector('.universe-subnav .container');
                      const b=document.querySelector('.sinjira-auth-nav-arrow');
                      return n && b && n.scrollLeft<=2 && b.disabled;
                    }""",timeout=5_000)
                fallback=browser.new_context(java_script_enabled=False,
                  viewport={"width":320,"height":800})
                try:
                    p2=fallback.new_page()
                    p2.goto(urljoin(BASE,PAGES[0]),wait_until="load")
                    # WebKit sans JS peut appliquer les feuilles de style après
                    # DOMContentLoaded : vérifier après la disposition flex réelle.
                    p2.wait_for_function("""() => {
                      const el=document.querySelector('.universe-subnav .container');
                      return el && getComputedStyle(el).display==='flex' &&
                        el.scrollWidth>el.clientWidth+2;
                    }""",timeout=5_000)
                    check(p2.evaluate("""() => {
                      const nav=document.querySelector('.universe-subnav');
                      const el=nav?.querySelector('.container');
                      return !!el && !nav.hasAttribute('data-sinjira-auth-nav-ready') &&
                        nav.querySelectorAll('.sinjira-auth-nav-arrow').length===0 &&
                        el.scrollWidth>el.clientWidth+2 &&
                        document.documentElement.scrollWidth<=innerWidth+2;
                    }"""),"repli sans JavaScript non défilable")
                finally:
                    fallback.close()
            finally:
                context.close()
        finally:
            browser.close()
    print(f"OK {ENGINE}: 4 sous-menus Auth, 8 résolutions, clavier et repli sans JS")


if __name__=="__main__":
    run()
