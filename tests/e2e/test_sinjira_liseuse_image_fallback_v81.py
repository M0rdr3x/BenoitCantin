#!/usr/bin/env python3
"""V81 : page illustrée réelle (PDF fictif) en texte adaptable — Chromium et WebKit.

Tests sans compte, sans réseau externe et sans roman réel. Les gestes sont
émis par le navigateur de test, pas par un iPhone/Android physique.
"""
import argparse
from playwright.sync_api import sync_playwright

from test_sinjira_liseuse_mobile_v54 import serve_fixture, swipe
from test_sinjira_liseuse_real_page_v57 import install_isolation, snapshot


def run(playwright, engine, url):
    browser = getattr(playwright, engine).launch()
    try:
        context = browser.new_context(
            viewport={"width":390,"height":844}, is_mobile=True,has_touch=True,
            device_scale_factor=2,locale="fr-CA",service_workers="block",
            reduced_motion="reduce"
        )
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        blocked = install_isolation(page, image_only_pages=(4,))
        page.goto(url, wait_until="load")
        page.wait_for_function("""()=>{
          const t=document.querySelector('#reader-text');
          const v=document.querySelector('#reader-viewer');
          return !document.querySelector('#reader-content').hidden &&
            !t.hidden && v.dataset.readerLayout==='screens' &&
            t.textContent.includes('LIVRE DE TEST · Page 3');
        }""",timeout=15000)
        assert snapshot(page)["page"] == 3
        assert page.locator("#reader-image-fallback").is_hidden()

        # La page 4 fictive ne comporte AUCUN texte extractible :
        # elle doit montrer la vraie surface PDF et quitter la pagination.
        page.locator("#reader-page").fill("4")
        page.locator("#reader-page").dispatch_event("change")
        page.wait_for_function("""()=>{
          const v=document.querySelector('#reader-viewer');
          return document.querySelector('#reader-page').value==='4' &&
            document.querySelector('#reader-text').hidden &&
            !document.querySelector('#reader-canvas').hidden &&
            !document.querySelector('#reader-image-fallback').hidden &&
            v.dataset.readerLayout==='scroll';
        }""",timeout=10000)
        assert page.locator("#reader-image-fallback").get_attribute("role")=="status"
        assert page.locator("#reader-mode").get_attribute("aria-pressed")=="false", (
            "V81 ne doit PAS changer la préférence texte",
            page.locator("#reader-mode").get_attribute("aria-pressed")
        )
        assert page.locator("#reader-text").text_content()==""
        illustrated = snapshot(page)
        assert illustrated["page"] == 4 and illustrated["textHidden"]

        # Le geste gauche doit encore passer la page PDF suivante.
        left = swipe(page, -130)
        page.wait_for_function("""()=>{
          const v=document.querySelector('#reader-viewer');
          const t=document.querySelector('#reader-text');
          return document.querySelector('#reader-page').value==='5' &&
            !t.hidden && t.textContent.includes('LIVRE DE TEST · Page 5') &&
            document.querySelector('#reader-image-fallback').hidden &&
            document.querySelector('#reader-canvas').hidden &&
            v.dataset.readerLayout==='screens';
        }""",timeout=10000)
        assert snapshot(page)["page"] == 5
        assert left["page"] == 5, left

        # Revenir à la page illustrée, puis geste droite vers le texte :
        # les deux directions fonctionnent pendant ce basculement automatique.
        page.locator("#reader-page").fill("4")
        page.locator("#reader-page").dispatch_event("change")
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='4' &&
          !document.querySelector('#reader-canvas').hidden &&
          document.querySelector('#reader-viewer').dataset.readerLayout==='scroll'""")
        swipe(page, 130)
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='3' &&
          !document.querySelector('#reader-text').hidden &&
          document.querySelector('#reader-viewer').dataset.readerLayout==='screens'""")
        assert page.locator("#reader-image-fallback").is_hidden()

        # Choix utilisateur : PDF manuel doit rester PDF, y compris sur
        # une page normale et une page illustrée (pas de retour forcé).
        page.locator("#reader-mode").click()
        page.wait_for_function("""()=>document.querySelector('#reader-text').hidden &&
          !document.querySelector('#reader-canvas').hidden""")
        page.locator("#reader-page").fill("4")
        page.locator("#reader-page").dispatch_event("change")
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='4' &&
          !document.querySelector('#reader-canvas').hidden""")
        assert page.locator("#reader-image-fallback").is_hidden()
        page.locator("#reader-page").fill("5")
        page.locator("#reader-page").dispatch_event("change")
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='5' &&
          !document.querySelector('#reader-canvas').hidden""")
        assert page.locator("#reader-text").is_hidden()
        assert page.locator("#reader-image-fallback").is_hidden()
        assert not errors, errors
        assert not blocked, blocked
        print(f"PASS {engine} V81: illustration auto-PDF, gauche/droite, "
              "retour texte reflow et choix PDF explicite, sans Supabase")
        context.close()
    finally:
        browser.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--browser", choices=("chromium","webkit"), required=True)
    args=parser.parse_args()
    with serve_fixture() as fixture:
        origin=fixture.split("/tests/e2e/fixtures/")[0]
        with sync_playwright() as p:
            run(p,args.browser,origin+"/compte/liseuse.html?edition=demo")


if __name__=="__main__":
    main()
