#!/usr/bin/env python3
"""Contrôle visuel responsive de la liseuse (texte fictif uniquement).

La page est chargée sans JavaScript applicatif, authentification, PDF, requête
Supabase ou données de compte. On expose le lecteur pour inspecter le CSS.
"""
import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
ENGINE = os.environ.get("BROWSER", "chromium").strip().lower()
WIDTHS = (320, 390, 540, 768, 1024, 1440)
OFFICIAL_LOGO = "/assets/icons/sinjira-officiel-20261120.png"


def check(value, message):
    if not value:
        raise AssertionError(f"{ENGINE}: {message}")


def inspect(page, width):
    page.set_viewport_size({"width": width, "height": 760})
    result = page.evaluate("""() => {
      const viewer=document.querySelector('#reader-viewer');
      const text=document.querySelector('#reader-text');
      const previous=document.querySelector('#reader-previous');
      const next=document.querySelector('#reader-next');
      const geom=element=>{
        const r=element.getBoundingClientRect();
        return {width:r.width,height:r.height,left:r.left,right:r.right};
      };
      return {
        overflow:document.documentElement.scrollWidth>innerWidth+2,
        viewer:geom(viewer),text:geom(text),
        scrollable:viewer.scrollHeight>viewer.clientHeight+10,
        scrollInside:viewer.scrollWidth<=viewer.clientWidth+2,
        buttons:[geom(previous),geom(next)],
        labels:[previous.textContent.trim(),next.textContent.trim()],
        aria:[previous.getAttribute('aria-controls'),next.getAttribute('aria-controls')],
        logo:document.querySelector('.reader-brand img')?.getAttribute('src'),
        help:viewer.getAttribute('aria-describedby'),
        keyboard:viewer.getAttribute('aria-keyshortcuts'),
      };
    }""")
    check(not result["overflow"], f"débordement de la page à {width}px : {result}")
    check(result["viewer"]["left"] >= -2 and result["viewer"]["right"] <= width + 2,
          f"zone de lecture hors écran à {width}px : {result}")
    check(result["text"]["width"] <= result["viewer"]["width"] + 2,
          f"texte non adapté à {width}px : {result}")
    check(result["scrollable"] and result["scrollInside"],
          f"texte fictif non défilable verticalement à {width}px : {result}")
    check(result["logo"] == OFFICIAL_LOGO, "icône officielle absente du lecteur")
    check(result["aria"] == ["reader-viewer","reader-viewer"] and
          result["help"] == "reader-turn-help" and "ArrowRight" in (result["keyboard"] or ""),
          "navigation non annoncée aux aides techniques")
    for button in result["buttons"]:
        check(button["height"] >= 44, f"commande trop petite à {width}px : {result}")
        check(button["left"] >= -2 and button["right"] <= width + 2,
              f"bouton hors écran à {width}px : {result}")
    check(result["labels"][0].startswith("← Écran") and "Écran suivant" in result["labels"][1],
          f"commandes du texte incorrectes à {width}px : {result}")


def run():
    check(ENGINE in {"chromium","firefox","webkit"}, "navigateur non pris en charge")
    with sync_playwright() as pw:
        browser = getattr(pw,ENGINE).launch()
        try:
            context = browser.new_context(java_script_enabled=False,
                service_workers="block",locale="fr-CA",
                viewport={"width":390,"height":760},
                reduced_motion="reduce")
            try:
                page=context.new_page()
                response=page.goto(urljoin(BASE,"compte/liseuse.html"),
                    wait_until="domcontentloaded",timeout=30_000)
                check(response is not None and response.status<400, "page liseuse inaccessible")
                page.evaluate("""() => {
                  document.getElementById('reader-content').hidden=false;
                  document.getElementById('reader-loading').hidden=true;
                  document.getElementById('reader-status').hidden=true;
                  document.getElementById('reader-canvas').hidden=true;
                  document.getElementById('reader-text').textContent=
                    ('Paragraphe fictif de contrôle, sans roman privé. '.repeat(8)+'\\n').repeat(150);
                }""")
                for width in WIDTHS:
                    inspect(page,width)
            finally:
                context.close()
        finally:
            browser.close()
    print(f"OK {ENGINE}: liseuse V55, 6 largeurs, commandes accessibles, texte fictif seul")


if __name__ == "__main__":
    run()
