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
    changes:[...(window.__readerFixture?.changes||[])],
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

        # V91 : sur la vraie page HTML, un touchend après interruption du
        # geste par blur/pagehide/visibilitychange ne doit PAS changer d'écran.
        # Les événements sont synthétiques; aucun livre privé n'est chargé.
        interrupted=page.evaluate("""()=>{
          const v=document.querySelector('#reader-viewer');
          const s={identifier:9,target:v,clientX:255,clientY:250};
          const e={...s,clientX:125,clientY:253};
          const fire=(type,touches,changed)=>{
            const ev=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(ev,{
              touches:{value:touches},targetTouches:{value:touches},
              changedTouches:{value:changed}
            });
            v.dispatchEvent(ev);
            return ev.defaultPrevented;
          };
          const before=v.scrollTop;
          for(const kind of ['blur','visibilitychange']){
            fire('touchstart',[s],[s]);
            if(kind==='visibilitychange'){
              // Simuler document.hidden via événement avec lecture temporaire.
              const old=Object.getOwnPropertyDescriptor(document,'hidden');
              Object.defineProperty(document,'hidden',{configurable:true,value:true});
              document.dispatchEvent(new Event('visibilitychange'));
              if(old)Object.defineProperty(document,'hidden',old);
              else delete document.hidden;
            }else window.dispatchEvent(new Event('blur'));
            fire('touchend',[],[e]);
          }
          return {before,after:v.scrollTop,page:Number(
            document.querySelector('#reader-page').value)};
        }""")
        assert interrupted["before"]==interrupted["after"]==0,interrupted
        assert interrupted["page"]==3,interrupted

        # V96 : l'édition privée cache #reader-content à la suspension.
        # Même si du code conserve le focus, ni un touchend résiduel ni
        # une touche ni un click de bouton ne doivent tourner le roman.
        hidden_navigation=page.evaluate("""()=>{
          const root=document.querySelector('#reader-content');
          const viewer=document.querySelector('#reader-viewer');
          const pageField=document.querySelector('#reader-page');
          const start={identifier:42,clientX:270,clientY:220};
          const end={...start,clientX:130,clientY:222};
          const fire=(type,touches,changed)=>{
            const event=new Event(type,{bubbles:true,cancelable:true});
            Object.defineProperties(event,{
              touches:{value:touches},targetTouches:{value:touches},
              changedTouches:{value:changed}
            });
            viewer.dispatchEvent(event);
            return event.defaultPrevented;
          };
          const before={scroll:viewer.scrollTop,page:Number(pageField.value),
            layout:viewer.dataset.readerLayout};
          root.hidden=true;
          const moved=fire('touchstart',[start],[start]);
          const ended=fire('touchend',[],[end]);
          viewer.dispatchEvent(new KeyboardEvent('keydown',{
            key:'ArrowRight',bubbles:true,cancelable:true
          }));
          document.querySelector('#reader-next').click();
          document.querySelector('#reader-touch-next').click();
          const after={scroll:viewer.scrollTop,page:Number(pageField.value),
            layout:viewer.dataset.readerLayout};
          root.hidden=false;
          return {before,after,moved,ended};
        }""")
        assert hidden_navigation["before"]==hidden_navigation["after"],hidden_navigation
        assert not hidden_navigation["moved"] and not hidden_navigation["ended"],hidden_navigation

        # V95 : une vraie zone du lecteur sur la page mobile tourne un écran
        # au tapotement de marge, sans changer la page source PDF.
        # On n'utilise aucun service privé ni système de stockage.
        taps=page.evaluate("""()=>{
          const viewer=document.querySelector('#reader-viewer');
          const rect=viewer.getBoundingClientRect();
          const el=document.querySelector('#reader-text');
          const tap=(relativeX)=>{
            const x=rect.left+rect.width*relativeX;
            const y=rect.top+Math.min(rect.height*.5,180);
            const touch={identifier:31,target:el,clientX:x,clientY:y};
            const ev=(type,touches)=>{
              const e=new Event(type,{bubbles:true,cancelable:true});
              Object.defineProperties(e,{
                touches:{value:touches},targetTouches:{value:touches},
                changedTouches:{value:[touch]}
              });
              el.dispatchEvent(e);
              return e.defaultPrevented;
            };
            ev('touchstart',[touch]);
            return ev('touchend',[]);
          };
          const before=viewer.scrollTop;
          const forward=tap(.85),afterForward=viewer.scrollTop;
          const center=tap(.5),afterCenter=viewer.scrollTop;
          const backward=tap(.15),afterBack=viewer.scrollTop;
          return {before,forward,afterForward,center,afterCenter,
            backward,afterBack,
            pdfPage:Number(document.querySelector('#reader-page').value)};
        }""")
        assert taps["before"]==0 and taps["afterForward"]>0,taps
        assert taps["forward"] and taps["backward"],taps
        assert taps["afterCenter"]==taps["afterForward"] and not taps["center"],taps
        assert taps["afterBack"]==0 and taps["pdfPage"]==3,taps

        # Balayages gauche/droite : c'est un écran du texte, pas la page PDF.
        one = swipe(page, -120)
        assert one["consumed"] and one["page"] == 3, one
        assert one["scroll"] > 0, one
        # V55 : le changement d'écran tient compte du padding ET garde
        # un interligne visible en recouvrement, plutôt que sauter du texte.
        geometry = page.evaluate("""() => {
          const viewer=document.querySelector('#reader-viewer');
          const text=document.querySelector('#reader-text');
          const css=getComputedStyle(text);
          return {
            available:viewer.clientHeight-
              parseFloat(css.paddingTop)-parseFloat(css.paddingBottom),
            line:parseFloat(css.lineHeight)
          };
        }""")
        assert one["scroll"] <= geometry["available"]-geometry["line"]+1, (
            one, geometry
        )
        assert one["changes"] == [], one
        back = swipe(page, 120)
        assert back["consumed"] and back["page"] == 3, back
        assert back["scroll"] == 0, back

        # V56 : aria-live annonce le changement d'écran, pas les micro-scrolls.
        page.evaluate("""() => {
          window.__readerAnnounceCount=0;
          const output=document.querySelector('#reader-screen-count');
          window.__readerAnnounceObserver=new MutationObserver(records=>{
            window.__readerAnnounceCount+=records.length;
          });
          window.__readerAnnounceObserver.observe(output,{
            childList:true,characterData:true,subtree:true
          });
          document.querySelector('#reader-viewer').scrollTop=12;
        }""")
        page.wait_for_timeout(80)
        assert page.evaluate("window.__readerAnnounceCount") == 0, (
            "Annonce répétée pour un déplacement sans changement d'écran"
        )
        page.evaluate("document.querySelector('#reader-viewer').scrollTop=0")
        page.wait_for_timeout(50)

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
        fraction_before = buttons["scroll"] / max(1, buttons["max"])

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
        # Deux trames sont nécessaires au recalcul du lecteur après le resize.
        page.wait_for_timeout(150)
        rotated = state(page)
        assert rotated["page"] == 3, rotated
        fraction_after = rotated["scroll"] / max(1, rotated["max"])
        assert abs(fraction_after-fraction_before) < 0.08, (
            "Rotation : la position proportionnelle a été perdue",
            fraction_before, fraction_after, rotated
        )
        page.evaluate("window.__readerAnnounceObserver.disconnect()")

        # Le mode PDF doit retomber sur les gestes V52 sans double page.
        page.evaluate("""() => {
          document.querySelector('#reader-text').hidden=true;
          document.querySelector('#reader-viewer').scrollTop=0;
        }""")
        page.wait_for_function("""() =>
          document.querySelector('#reader-viewer').dataset.readerLayout==='scroll'""")
        before_pdf = state(page)

        # V97 : un PDF se tourne aussi par tapotement des marges intérieures.
        # La page source doit avancer puis revenir exactement une fois ;
        # le centre reste disponible pour les gestes ordinaires.
        pdf_taps=page.evaluate("""()=>{
          const viewer=document.querySelector('#reader-viewer');
          const rect=viewer.getBoundingClientRect();
          const tap=portion=>{
            const x=rect.left+rect.width*portion;
            const y=rect.top+Math.min(100,rect.height*.5);
            const t={identifier:97,target:viewer,clientX:x,clientY:y};
            const fire=(type,touches)=>{
              const event=new Event(type,{bubbles:true,cancelable:true});
              Object.defineProperties(event,{
                touches:{value:touches},targetTouches:{value:touches},
                changedTouches:{value:[t]}
              });
              viewer.dispatchEvent(event);
            };
            fire('touchstart',[t]);fire('touchend',[]);
            return Number(document.querySelector('#reader-page').value);
          };
          return {before:Number(document.querySelector('#reader-page').value),
            forward:tap(.85),middle:tap(.5),back:tap(.15),
            changes:[...window.__readerFixture.changes]};
        }""")
        assert pdf_taps["before"]==before_pdf["page"],pdf_taps
        assert pdf_taps["forward"]==before_pdf["page"]+1,pdf_taps
        assert pdf_taps["middle"]==pdf_taps["forward"],pdf_taps
        assert pdf_taps["back"]==before_pdf["page"],pdf_taps
        assert len(pdf_taps["changes"])==len(before_pdf["changes"])+2,pdf_taps

        pdf_swipe = swipe(page, -130)
        assert pdf_swipe["page"] == before_pdf["page"] + 1, (before_pdf, pdf_swipe)
        # V97 : les deux taps précédents ont volontairement tourné
        # deux pages source; ce balayage ne doit en ajouter qu'une.
        assert len(pdf_swipe["changes"]) == len(pdf_taps["changes"]) + 1, pdf_swipe

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
