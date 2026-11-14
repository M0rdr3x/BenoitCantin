#!/usr/bin/env python3
"""V65 — événements tactiles natifs du moteur Chromium (CDP), pas DOM simulé.

Le scénario ouvre la VRAIE page compte/liseuse.html avec un PDF entièrement
fictif et Supabase interdit. Les événements tactiles sont émis par Chromium
Input.dispatchTouchEvent; ils ont isTrusted=true dans le navigateur, contrairement
aux objets TouchLike des tests V54. Ne certifie pas un téléphone physique.
"""
import argparse

from playwright.sync_api import sync_playwright

from test_sinjira_liseuse_mobile_v54 import serve_fixture
from test_sinjira_liseuse_real_page_v57 import install_isolation, snapshot


def native_swipe(page, cdp, direction="left", vertical=False, duration_ms=84):
    rect = page.locator("#reader-viewer").bounding_box()
    assert rect is not None, "V65: zone de lecture invisible"
    left = max(5, rect["x"] + 8)
    right = min(page.viewport_size["width"] - 5, rect["x"] + rect["width"] - 8)
    top = max(120, rect["y"] + 8)
    bottom = min(page.viewport_size["height"] - 18,
                 rect["y"] + rect["height"] - 8)
    assert right - left >= 185 and bottom - top >= 45, (
        "V65: lecteur pas assez visible pour un balayage natif", rect
    )
    x1 = round(right - 28 if direction == "left" else left + 28)
    x2 = round(left + 28 if direction == "left" else right - 28)
    y1 = round((top + bottom) / 2)
    if vertical:
        x2 = x1 + 5
        y2 = round(min(bottom - 10, y1 + 100))
    else:
        y2 = y1 + 3

    def send(kind, points):
        return cdp.send("Input.dispatchTouchEvent", {
            "type": kind,
            "touchPoints": [
                {"x": x, "y": y, "id": 9, "force": 1}
                for x, y in points
            ],
            "modifiers": 0,
        })

    send("touchStart", [(x1, y1)])
    for step in range(1, 7):
        t = step / 6
        send("touchMove", [(
            round(x1 + (x2 - x1) * t),
            round(y1 + (y2 - y1) * t),
        )])
        # V80 : la durée est réellement écoulée entre les messages CDP,
        # et non seulement inscrite dans un événement Javascript simulé.
        page.wait_for_timeout(max(1, duration_ms / 6))
    send("touchEnd", [])
    page.wait_for_timeout(90)
    return {"from": (x1, y1), "to": (x2, y2)}


def run(playwright, url):
    browser = playwright.chromium.launch()
    try:
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            device_scale_factor=2,
            locale="fr-CA",
            service_workers="block",
            reduced_motion="reduce",
        )
        page = context.new_page()
        page_errors = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        blocked = install_isolation(page)
        page.goto(url, wait_until="load")
        page.wait_for_function("""()=>{
          const v=document.querySelector('#reader-viewer');
          return !document.querySelector('#reader-content').hidden &&
            v.dataset.readerLayout==='screens' &&
            document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST');
        }""", timeout=15000)
        page.locator("#reader-viewer").scroll_into_view_if_needed()
        page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          v.scrollTop=0;
          window.__v65Trusted=[];
          ['touchstart','touchmove','touchend','touchcancel'].forEach(name=>
            v.addEventListener(name,event=>{
              window.__v65Trusted.push({
                type:name,
                trusted:event.isTrusted,
                touches:event.touches?.length,
                changed:event.changedTouches?.length,
                layout:v.dataset.readerLayout
              });
            },true)
          );
        }""")
        cdp = context.new_cdp_session(page)
        first = snapshot(page)
        assert first["page"] == 3 and first["scroll"] == 0, first
        assert first["max"] > 300, first

        native_swipe(page, cdp, direction="left")
        forward = snapshot(page)
        assert forward["page"] == 3 and forward["scroll"] > 0, (
            "V65: un seul geste gauche doit avancer UN écran du texte",
            {"before_page": first["page"], "after_page": forward["page"],
             "scroll": forward["scroll"]},
        )
        native_swipe(page, cdp, direction="right")
        backward = snapshot(page)
        assert backward["page"] == 3 and backward["scroll"] <= 3, (
            "V65: retour à l'écran précédent sur vraie entrée tactile",
            {"page": backward["page"], "scroll": backward["scroll"]},
        )

        # V80 : vérifier sur la vraie page HTML qu'un glissement volontaire
        # de 1,2 à 1,5 seconde fonctionne, sans fausse transition PDF.
        native_swipe(page, cdp, direction="left", duration_ms=1200)
        slow_forward = snapshot(page)
        assert slow_forward["page"] == 3 and slow_forward["scroll"] > 0, (
            "V80: geste gauche lent natif n'avance pas l'écran", slow_forward
        )
        native_swipe(page, cdp, direction="right", duration_ms=1500)
        slow_backward = snapshot(page)
        assert slow_backward["page"] == 3 and slow_backward["scroll"] <= 3, (
            "V80: geste droit lent natif ne revient pas", slow_backward
        )

        # Un geste vertical est laissé au défilement natif et ne tourne
        # pas une page PDF source.
        native_swipe(page, cdp, vertical=True)
        vertically = snapshot(page)
        assert vertically["page"] == 3, (
            "V65: déplacement vertical a changé le PDF", vertically["page"]
        )
        page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")

        # Le même contrôle doit fonctionner avec un petit téléphone.
        page.set_viewport_size({"width": 320, "height": 568})
        page.locator("#reader-viewer").scroll_into_view_if_needed()
        page.wait_for_timeout(130)
        native_swipe(page, cdp, direction="left")
        small = snapshot(page)
        assert small["page"] == 3 and small["scroll"] > 0, (
            "V65: geste gauche natif perdu à 320 px",
            {"page": small["page"], "scroll": small["scroll"]},
        )

        # Sans pagination par écran, V52 peut tourner exactement une page
        # source PDF; V28 ne doit pas dupliquer son ancienne écoute touchend.
        page.locator("#reader-screens-enabled").uncheck()
        page.wait_for_function("""()=>document.querySelector('#reader-viewer')
          .dataset.readerLayout==='scroll'""")
        page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")
        overflow = page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          return v.scrollWidth-v.clientWidth;
        }""")
        assert overflow <= 4, ("V65: PDF horizontal/pan priorité", overflow)
        native_swipe(page, cdp, direction="left")
        page.wait_for_function("""()=>Number(document.querySelector('#reader-page').value)===4""")
        assert snapshot(page)["page"] == 4, (
            "V65: double changement PDF en mode défilement libre"
        )

        # V80 : la navigation lente fonctionne aussi en PDF, et une
        # trajectoire trop longue est rejetée sans seconde page involontaire.
        native_swipe(page, cdp, direction="right", duration_ms=1250)
        page.wait_for_function("""()=>Number(document.querySelector('#reader-page').value)===3""")
        assert snapshot(page)["page"] == 3, "V80: retour PDF lent impossible"
        native_swipe(page, cdp, direction="left", duration_ms=1550)
        page.wait_for_function("""()=>Number(document.querySelector('#reader-page').value)===4""")
        assert snapshot(page)["page"] == 4, "V80: avance PDF lente impossible"
        native_swipe(page, cdp, direction="left", duration_ms=1900)
        assert snapshot(page)["page"] == 4, (
            "V80: un mouvement > 1800 ms a tourné une page PDF à tort"
        )

        evidence = page.evaluate("window.__v65Trusted")
        assert any(e["type"] == "touchstart" and e["trusted"] for e in evidence)
        assert any(e["type"] == "touchend" and e["trusted"] for e in evidence)
        assert all(e["trusted"] for e in evidence), (
            "V65: scénario a reçu un événement tactile synthétique non fiable",
            evidence,
        )
        assert not page_errors, page_errors
        assert not blocked, blocked
        print("PASS chromium V80: Input.dispatchTouchEvent isTrusted; "
              "écrans et PDF gauche/droite à vitesse normale et 1,2-1,55 s, "
              "rejet > 1,8 s, vertical, 320 px et absence de double page")
        context.close()
    finally:
        browser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", choices=("chromium",), default="chromium")
    parser.parse_args()
    with serve_fixture() as url:
        base = url.split("/tests/e2e/fixtures/")[0]
        with sync_playwright() as playwright:
            run(playwright, base + "/compte/liseuse.html?edition=demo")


if __name__ == "__main__":
    main()
