#!/usr/bin/env python3
"""Recette navigateur: disposition de la démo SINJIRA et ergonomie tactile.

N'envoie aucune donnée utilisateur ni aucun formulaire. Le PDF est simulé
pour vérifier la barre d'outils indépendamment du plug-in PDF du navigateur.
"""
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER = os.environ.get("BROWSER", "chromium").strip().lower()
VIEWPORTS = (320, 390, 540, 768, 1280)
DEMO = "projets/sinjira/romans/lire-demo.html"


def check(ok, message):
    if not ok:
        raise AssertionError(f"{BROWSER}: {message}")


def run():
    check(BROWSER in ("chromium", "firefox", "webkit"), "moteur non autorisé")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        context = browser.new_context(
            locale="fr-CA",
            viewport={"width": 390, "height": 844},
            reduced_motion="reduce",
            service_workers="block",
        )

        # Aucun téléchargement réel du roman ni besoin d'un lecteur PDF natif.
        context.route("**/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf*",
                      lambda route: route.fulfill(
                          status=200, content_type="application/pdf",
                          body=b"%PDF-1.4\n%%EOF\n"))
        page = context.new_page()
        try:
            for width in VIEWPORTS:
                page.set_viewport_size({"width": width, "height": 844})
                response = page.goto(urljoin(BASE_URL, DEMO),
                                     wait_until="domcontentloaded", timeout=30_000)
                check(response is not None and response.status < 400,
                      f"lecteur démo HTTP invalide en {width} px")
                page.wait_for_function(
                    "() => document.querySelector('[data-reader-prev]')?.disabled === true",
                    timeout=15_000,
                )
                state = page.evaluate("""() => {
                    const controls = document.querySelector('.v19-reader-progress');
                    const prev = document.querySelector('[data-reader-prev]');
                    const next = document.querySelector('[data-reader-next]');
                    const a = prev.getBoundingClientRect();
                    const b = next.getBoundingClientRect();
                    const input = document.querySelector('[data-reader-page-number]');
                    const computed = getComputedStyle(controls);
                    const w = window.innerWidth;
                    const inViewport = el => {
                        const r = el.getBoundingClientRect();
                        return r.left >= -1 && r.right <= w + 1;
                    };
                    return {
                        display: computed.display,
                        areas: computed.gridTemplateAreas,
                        sameRow: Math.abs(a.top - b.top) < 4,
                        prevWidth: a.width, nextWidth: b.width,
                        prevHeight: a.height, nextHeight: b.height,
                        within: inViewport(prev) && inViewport(next) && inViewport(input),
                        overflow: document.documentElement.scrollWidth > w + 2,
                        nextDisabled: next.disabled,
                        img: document.querySelector('.site-header .brand img')?.getAttribute('src'),
                    };
                }""")
                check(state["within"], f"commandes hors écran {width}px: {state}")
                check(not state["overflow"], f"débordement horizontal {width}px: {state}")
                check(state["prevHeight"] >= 44 and state["nextHeight"] >= 44,
                      f"zones tactiles trop petites {width}px: {state}")
                check(not state["nextDisabled"], f"page suivante désactivée à tort {width}px")
                check(state["img"] == "/assets/icons/sinjira-officiel-20261120.png",
                      f"marque SINJIRA non harmonisée {width}px")
                if width <= 540:
                    check(state["display"] == "grid" and state["sameRow"],
                          f"navigation 2 colonnes absente {width}px: {state}")
                    check('"prev next"' in state["areas"],
                          f"grille mobile non appliquée {width}px: {state}")
                else:
                    check(state["display"] == "flex",
                          f"navigation bureau/tablette dégradée {width}px: {state}")

                page.locator("[data-reader-next]").click()
                page.wait_for_function(
                    "() => document.querySelector('[data-reader-page-number]')?.value === '2'",
                    timeout=10_000,
                )
                page.locator("[data-reader-prev]").click()
                check(page.locator("[data-reader-page-number]").input_value() == "1",
                      f"retour à la page 1 impossible {width}px")
                print(f"OK {BROWSER}: démo, navigation, marque et ergonomie {width}px")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    run()
