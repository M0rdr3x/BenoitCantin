#!/usr/bin/env python3
"""V54: véritables moteurs de navigateur, événements tactiles simulés.

AUCUNE connexion Supabase, aucun PDF protégé, aucun compte réel.
Cette recette ne remplace pas les essais sur téléphone physique.
"""
import argparse
import contextlib
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = "/tests/e2e/fixtures/sinjira-liseuse-mobile-v54.html"


@contextlib.contextmanager
def serve_fixture():
    handler = lambda *args, **kw: http.server.SimpleHTTPRequestHandler(
        *args, directory=str(ROOT), **kw
    )
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}{FIXTURE}"
        finally:
            server.shutdown()
            thread.join(timeout=3)


SWIPE_JS = """
({dx,dy=5,multiple=false})=>{
  const el=document.querySelector('#reader-viewer');
  // Touch() n'a pas de constructeur public sur certains WebKit Linux :
  // conserver le vrai dispatch/capture/bubble DOM avec un payload TouchLike.
  const start={identifier:9,target:el,clientX:255,clientY:250};
  const end={identifier:9,target:el,clientX:255+dx,clientY:250+dy};
  const arr=multiple?[start,{identifier:10,target:el,clientX:200,clientY:200}]:[start];
  const touchEvent=(type,touches,changed)=>{
    const ev=new Event(type,{bubbles:true,cancelable:true});
    Object.defineProperties(ev,{
      touches:{value:touches},targetTouches:{value:touches},
      changedTouches:{value:changed}
    });
    return ev;
  };
  el.dispatchEvent(touchEvent('touchstart',arr,[start]));
  const ev=touchEvent('touchend',[],[end]);
  el.dispatchEvent(ev);
  return {
    consumed:ev.defaultPrevented,
    page:Number(document.querySelector('#reader-page').value),
    scroll:el.scrollTop,
    changes:[...window.__readerFixture.changes],
    indicator:document.querySelector('#reader-screen-count').textContent
  };
}
"""


def state(page):
    return page.evaluate("""() => {
      const v=document.querySelector('#reader-viewer');
      return {page:Number(document.querySelector('#reader-page').value),
        scroll:v.scrollTop,max:v.scrollHeight-v.clientHeight,
        indicator:document.querySelector('#reader-screen-count').textContent,
        layout:v.dataset.readerLayout,
        nextDisabled:document.querySelector('#reader-touch-next').disabled,
        backDisabled:document.querySelector('#reader-touch-prev').disabled,
        changes:[...window.__readerFixture.changes]
      };
    }""")


def swipe(page, dx, dy=4, multiple=False):
    return page.evaluate(SWIPE_JS, {"dx": dx, "dy": dy, "multiple": multiple})


def ready(page):
    page.wait_for_function("""() => window.__readerFixture?.ready &&
        document.querySelector('#reader-viewer')?.dataset.readerLayout === 'screens' &&
        document.querySelector('#reader-screen-count')?.textContent.includes('Écran')""")


def run_browser(playwright, engine, origin):
    browser = getattr(playwright, engine).launch()
    try:
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            device_scale_factor=2,
            locale="fr-CA",
            reduced_motion="reduce",
            service_workers="block",
        )
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(origin, wait_until="load")
        ready(page)
        initial = state(page)
        assert initial["page"] == 3, initial
        assert initial["max"] > 500, initial
        assert initial["layout"] == "screens", initial

        # Balayages gauche/droite : c'est un écran du texte, pas la page PDF.
        one = swipe(page, -120)
        assert one["consumed"] and one["page"] == 3, one
        assert one["scroll"] > 0, one
        assert one["changes"] == [], one
        back = swipe(page, 120)
        assert back["consumed"] and back["page"] == 3, back
        assert back["scroll"] == 0, back

        # Les gestes verticaux ne provoquent aucune modification.
        before = state(page)
        vertical = swipe(page, -8, 140)
        assert not vertical["consumed"], vertical
        assert vertical["scroll"] == before["scroll"], (before, vertical)
        multi = swipe(page, -140, multiple=True)
        assert not multi["consumed"], multi

        # Sélection de texte : la citation reste sélectionnable et aucun saut.
        page.evaluate("""() => {
          const node=document.querySelector('#reader-text').firstChild;
          const sel=window.getSelection(),range=document.createRange();
          range.setStart(node,0);range.setEnd(node,Math.min(15,node.length));
          sel.removeAllRanges();sel.addRange(range);
        }""")
        selected = swipe(page, -120)
        assert not selected["consumed"], selected
        page.evaluate("window.getSelection().removeAllRanges()")

        # Une série de gestes doit atteindre la vraie page suivante UNE fois.
        crossed = False
        for _ in range(25):
            s = swipe(page, -130)
            if s["page"] == 4:
                crossed = True
                break
            assert s["page"] == 3, s
        assert crossed, "Impossible de franchir la dernière portion du PDF"
        assert state(page)["changes"] == [4], state(page)

        # Retour à la page précédente : afficher sa dernière portion.
        back_pdf = swipe(page, 130)
        assert back_pdf["page"] == 3, back_pdf
        page.wait_for_function("""() =>
          document.querySelector('#reader-page').value === '3' &&
          document.querySelector('#reader-viewer').scrollTop > 0""")
        previous = state(page)
        assert previous["scroll"] >= previous["max"] - 2, previous
        assert previous["changes"] == [4, 3], previous

        # Touches fléchées et boutons accessibles utilisent le mode pages.
        page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")
        page.locator("#reader-viewer").focus()
        page.keyboard.press("ArrowRight")
        keyboard = state(page)
        assert keyboard["page"] == 3 and keyboard["scroll"] > 0, keyboard
        page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")
        page.locator("#reader-touch-next").click()
        buttons = state(page)
        assert buttons["page"] == 3 and buttons["scroll"] > 0, buttons

        # Changer l'interligne et tourner le téléphone conserve le livre affiché.
        page.evaluate("""() => {
          const text=document.querySelector('#reader-text');
          text.style.fontSize='28px';
          text.style.lineHeight='1.8';
          window.dispatchEvent(new Event('resize'));
        }""")
        page.set_viewport_size({"width": 780, "height": 390})
        page.wait_for_function("""() =>
          document.querySelector('#reader-screen-count').textContent.includes('Écran')""")
        rotated = state(page)
        assert rotated["page"] == 3, rotated

        # Le mode PDF doit retomber sur les gestes V52 sans double page.
        page.evaluate("""() => {
          document.querySelector('#reader-text').hidden=true;
          document.querySelector('#reader-viewer').scrollTop=0;
        }""")
        page.wait_for_function("""() =>
          document.querySelector('#reader-viewer').dataset.readerLayout==='scroll'""")
        before_pdf = state(page)
        pdf_swipe = swipe(page, -130)
        assert pdf_swipe["page"] == before_pdf["page"] + 1, (before_pdf, pdf_swipe)
        assert len(pdf_swipe["changes"]) == len(before_pdf["changes"]) + 1, pdf_swipe

        # Le choix du défilement libre reste disponible.
        page.evaluate("""() => {
          document.querySelector('#reader-text').hidden=false;
          const x=document.querySelector('#reader-screens-enabled');
          x.checked=false;
          x.dispatchEvent(new Event('change',{bubbles:true}));
        }""")
        assert state(page)["layout"] == "scroll", state(page)
        assert not errors, errors
        print(f"PASS {engine}: gestes, écrans, page précédente, sélection,"
              " clavier, boutons, rotation, mode PDF, défilement libre")
        context.close()
    finally:
        browser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", choices=("chromium", "webkit", "firefox"),
                        required=True)
    args = parser.parse_args()
    with serve_fixture() as url:
        with sync_playwright() as playwright:
            run_browser(playwright, args.browser, url)


if __name__ == "__main__":
    main()
