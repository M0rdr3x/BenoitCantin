#!/usr/bin/env python3
"""V82 — une extraction PDF défaillante doit laisser voir le vrai livre.

Page HTML réelle et PDF synthétique; aucun compte, roman privé ou Supabase.
Chromium/WebKit simulés, non réception d'appareils physiques.
"""
import argparse
from playwright.sync_api import sync_playwright

from test_sinjira_liseuse_mobile_v54 import serve_fixture, swipe
from test_sinjira_liseuse_real_page_v57 import install_isolation, snapshot


def run(playwright, engine, url):
    browser=getattr(playwright,engine).launch()
    try:
        context=browser.new_context(
            viewport={"width":390,"height":844},is_mobile=True,has_touch=True,
            device_scale_factor=2,locale="fr-CA",service_workers="block",
            reduced_motion="reduce"
        )
        page=context.new_page()
        js_errors=[]
        page.on("pageerror",lambda err:js_errors.append(str(err)))
        rejected=install_isolation(page,text_error_pages=(4,))
        page.goto(url,wait_until="load")
        page.wait_for_function("""()=>{
          const v=document.querySelector('#reader-viewer');
          const t=document.querySelector('#reader-text');
          return !document.querySelector('#reader-content').hidden &&
            v.dataset.readerLayout==='screens' && !t.hidden &&
            t.textContent.includes('LIVRE DE TEST · Page 3');
        }""",timeout=15000)
        assert snapshot(page)["page"]==3
        assert page.locator("#reader-image-fallback").is_hidden()

        # Une erreur getTextContent() n'est PAS un échec de render(). Le
        # lecteur affiche le canevas sans perdre la préférence de mode texte.
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
        assert page.locator("#reader-mode").get_attribute("aria-pressed")=="false"
        assert page.locator("#reader-error").is_hidden()
        assert page.locator("#reader-image-fallback").get_attribute("role")=="status"
        assert "PDF s'affiche automatiquement" in page.locator(
            "#reader-image-fallback").inner_text()
        assert page.locator("#reader-text").text_content()==""

        # Un balayage gauche recompose la page suivante, sans laisser la
        # moindre exception de la page 4 bloquer la file de rendus.
        left=swipe(page,-130)
        page.wait_for_function("""()=>{
          const v=document.querySelector('#reader-viewer');
          const t=document.querySelector('#reader-text');
          return document.querySelector('#reader-page').value==='5' &&
            !t.hidden && t.textContent.includes('LIVRE DE TEST · Page 5') &&
            document.querySelector('#reader-image-fallback').hidden &&
            document.querySelector('#reader-canvas').hidden &&
            v.dataset.readerLayout==='screens';
        }""",timeout=10000)
        assert left["page"]==5,left

        # Retour manuel sur la page 4 et swipe droite : reprise page 3.
        page.locator("#reader-page").fill("4")
        page.locator("#reader-page").dispatch_event("change")
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='4' &&
          !document.querySelector('#reader-canvas').hidden &&
          document.querySelector('#reader-viewer').dataset.readerLayout==='scroll'""")
        swipe(page,130)
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='3' &&
          !document.querySelector('#reader-text').hidden &&
          document.querySelector('#reader-viewer').dataset.readerLayout==='screens'""")
        assert page.locator("#reader-image-fallback").is_hidden()
        assert not js_errors,js_errors
        assert not rejected,rejected
        print(f"PASS {engine} V82: erreur d'extraction -> PDF visible; "
              "swipes gauche/droite et reflow repris; sans accès privé")
        context.close()
    finally:
        browser.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--browser",choices=("chromium","webkit"),required=True)
    args=parser.parse_args()
    with serve_fixture() as fixture:
        origin=fixture.split("/tests/e2e/fixtures/")[0]
        with sync_playwright() as playwright:
            run(playwright,args.browser,origin+"/compte/liseuse.html?edition=demo")


if __name__=="__main__":
    main()
