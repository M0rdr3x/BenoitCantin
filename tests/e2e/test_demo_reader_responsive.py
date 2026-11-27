#!/usr/bin/env python3
"""Recette du retrait de l'ancienne démo : PC, cellulaire et sécurité des liens.

Les PDF de validation ne sont pas encore publiés : aucun lecteur intégré ne
doit essayer de charger le fichier périmé. Les droits privés sont inchangés.
"""
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER = os.environ.get("BROWSER", "chromium").strip().lower()
VIEWPORTS = (240, 320, 390, 430, 540, 700, 768, 1280)
PAGE = "projets/sinjira/romans/lire-demo.html"
OLD_DOCUMENT = "SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"


def check(ok, message):
    if not ok:
        raise AssertionError(f"{BROWSER}: {message}")


def run():
    check(BROWSER in ("chromium", "firefox", "webkit"), "moteur non autorisé")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        context = browser.new_context(
            locale="fr-CA", viewport={"width": 390, "height": 844},
            reduced_motion="reduce", service_workers="block",
        )
        page = context.new_page()
        try:
            for width in VIEWPORTS:
                page.set_viewport_size({"width": width, "height": 844})
                response = page.goto(urljoin(BASE_URL, PAGE),
                                     wait_until="domcontentloaded", timeout=30_000)
                check(response is not None and response.status < 400,
                      f"page de retrait inaccessible à {width} px")
                page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                state = page.evaluate("""() => {
                    const actions=[...document.querySelectorAll('.sinjira-release-actions .btn')];
                    const logo=document.querySelector('.site-header .brand img');
                    const cover=document.querySelector('.sinjira-release-cover img');
                    const wrap=document.querySelector('.sinjira-release-layout');
                    return {
                        overflow:document.documentElement.scrollWidth>innerWidth+2,
                        width:innerWidth, layout:getComputedStyle(wrap).gridTemplateColumns,
                        layoutDisplay:getComputedStyle(wrap).display,
                        stylesheet:[...document.querySelectorAll('link[rel="stylesheet"]')]
                          .some(el=>el.getAttribute('href')?.startsWith('/assets/css/sinjira-demo-release-v1.css')),
                        targets:actions.map(el=>el.getBoundingClientRect().height),
                        offscreen:actions.some(el=>{
                            const r=el.getBoundingClientRect();
                            return r.left<-1||r.right>innerWidth+1;
                        }),
                        logo:logo?.getAttribute('src'), cover:!!cover,
                        coverSource:cover?.getAttribute('src'),
                        coverLazy:cover?.loading === 'lazy' && cover?.decoding === 'async',
                        coverSources:cover?.getAttribute('srcset') || '',
                        cardFirst:wrap.firstElementChild?.classList.contains('sinjira-release-card'),
                        cardTop:wrap.querySelector('.sinjira-release-card').getBoundingClientRect().top,
                        cardBottom:wrap.querySelector('.sinjira-release-card').getBoundingClientRect().bottom,
                        coverTop:cover?.getBoundingClientRect().top,
                        mainFocusable:document.querySelector('main')?.getAttribute('tabindex') === '-1',
                        oldLinks:document.querySelectorAll('a[href*=".pdf"],iframe[data-pdf-reader]').length,
                        h1:document.querySelector('h1')?.textContent||'',
                        status:document.querySelector('main')?.textContent||''
                    };
                }""")
                check(state["stylesheet"] and state["layoutDisplay"] == "grid",
                      f"CSS responsive SINJIRA absent ou inactif à {width} px : {state}")
                check(not state["overflow"], f"débordement à {width} px : {state}")
                check(not state["offscreen"], f"bouton hors écran à {width} px : {state}")
                check(len(state["targets"]) >= 2 and all(h >= 44 for h in state["targets"]),
                      f"cibles tactiles trop petites à {width} px : {state}")
                check(state["logo"] == "/assets/icons/sinjira-officiel-20261120.png",
                      f"logo SINJIRA incohérent à {width} px")
                check(state["cover"], f"couverture absente à {width} px")
                check(state["coverSource"] == "/assets/media/sinjira-livre-1-cover-480.webp"
                      and "768w" in state["coverSources"] and state["coverLazy"],
                      f"couverture adaptative ou différée absente à {width}px")
                check(state["cardFirst"] and state["mainFocusable"],
                      f"ordre de lecture ou cible du lien d’évitement incorrecte à {width}px")
                if width <= 700:
                    check(state["coverTop"] >= state["cardBottom"] - 2,
                          f"couverture avant le statut éditorial à {width}px")
                check(state["oldLinks"] == 0, f"ancien document encore lié à {width} px")
                check("démo précédente a été retirée" in state["h1"],
                      f"retour utilisateur non explicite à {width} px")
                check("62 pages" in state["status"] and "chapitres 1 et 2" in state["status"],
                      f"nouvelle version de validation mal décrite à {width} px")
                check("pas encore hébergées" in state["status"],
                      f"nouvelle démo annoncée à tort comme publiée à {width} px")
            print(f"OK {BROWSER}: retrait explicite, identité, absence de PDF périmé et ergonomie 240-1280 px et CSS externe")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    run()
