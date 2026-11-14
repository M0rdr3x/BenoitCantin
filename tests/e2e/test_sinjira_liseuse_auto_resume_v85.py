#!/usr/bin/env python3
"""V85 : vraie lecture mobile, reprise automatique et sauvegarde refusée.

PDF fictif, Chromium/WebKit simulés, aucun roman privé ni accès Supabase.
La reprise est testée après un swipe sans bouton de sauvegarde manuelle.
"""
import argparse
from playwright.sync_api import sync_playwright

from test_sinjira_liseuse_mobile_v54 import serve_fixture, swipe
from test_sinjira_liseuse_real_page_v57 import install_isolation, snapshot

SPOT_KEY="sinjira:liseuse:demo:la-cendre-du-jugement:spot"


def ready(page, pdf_page=3, text=True):
    page.wait_for_function("""({pdfPage,hasText})=>{
      const viewer=document.querySelector('#reader-viewer');
      const t=document.querySelector('#reader-text');
      const c=document.querySelector('#reader-canvas');
      return !document.querySelector('#reader-content').hidden &&
        Number(document.querySelector('#reader-page').value)===pdfPage &&
        (hasText ? (!t.hidden && viewer.dataset.readerLayout==='screens' &&
           t.textContent.includes('LIVRE DE TEST · Page '+pdfPage))
         : (t.hidden && !c.hidden && viewer.dataset.readerLayout==='scroll'));
    }""",arg={"pdfPage":pdf_page,"hasText":text},timeout=15000)


def run(p,engine,url):
    browser=getattr(p,engine).launch()
    try:
        opts=dict(viewport={"width":390,"height":844},is_mobile=True,has_touch=True,
                  device_scale_factor=2,locale="fr-CA",service_workers="block",
                  reduced_motion="reduce")
        context=browser.new_context(**opts)
        page=context.new_page()
        errors=[]
        page.on("pageerror",lambda err:errors.append(str(err)))
        blocked=install_isolation(page,image_only_pages=(4,))
        page.goto(url,wait_until="load")
        ready(page)
        # V86 : l'ouverture seule ne certifie aucune nouvelle sauvegarde.
        initial_status=page.locator("#reader-position-status").inner_text()
        assert "Nouvelle sauvegarde non encore confirmée" in initial_status,initial_status
        assert "Enregistrement automatique actif" not in initial_status,initial_status
        assert snapshot(page)["scroll"]==0

        # V92 : la navigation Retour peut restaurer une page BFCache.
        # Le module des repères de la démo NE doit pas être fermé par pagehide
        # persisted=true, sans quoi ses boutons restent visibles mais inertes.
        # Aucun réseau privé : événement navigateur synthétique.
        resumed=page.evaluate("""()=>{
          const hide=new Event('pagehide');
          Object.defineProperty(hide,'persisted',{value:true});
          window.dispatchEvent(hide);
          const show=new Event('pageshow');
          Object.defineProperty(show,'persisted',{value:true});
          window.dispatchEvent(show);
          document.querySelector('#reader-bookmark-add').click();
          const marks=JSON.parse(localStorage.getItem(
            'sinjira:liseuse:demo:marks:v28')||'[]');
          return {page:Number(document.querySelector('#reader-page').value),
            count:marks.filter(m=>m.kind==='bookmark'&&m.page===3).length,
            contentVisible:!document.querySelector('#reader-content').hidden};
        }""")
        assert resumed["page"]==3 and resumed["count"]==1 and resumed["contentVisible"],resumed

        # V85 : avancer par le doigt doit enregistrer la portion d'écran
        # automatiquement, sans cliquer sur « Enregistrer ma position ».
        consumed=swipe(page,-130)
        assert consumed["consumed"] and snapshot(page)["scroll"]>50,consumed
        page.wait_for_function("""key=>{
          const s=JSON.parse(localStorage.getItem(key)||'null');
          return s?.page===3 && s.ratio>.005 && s.ratio<.95;
        }""",arg=SPOT_KEY,timeout=10000)
        saved=page.evaluate("""key=>JSON.parse(localStorage.getItem(key))""",SPOT_KEY)
        # V87 : confirmation locale seulement APRÈS l'écriture réussie,
        # et non lors de l'affichage initial. La synchronisation distante
        # n'est jamais annoncée par le scénario fictif.
        successful=page.locator("#reader-position-status")
        page.wait_for_function("""()=>{
          const s=document.querySelector('#reader-position-status');
          return s.dataset.type==='success' &&
                 s.textContent.includes('Position enregistrée sur cet appareil.');
        }""",timeout=10000)
        assert "compte" not in successful.inner_text(),successful.inner_text()
        page.reload(wait_until="load")
        ready(page)
        page.wait_for_function("""expected=>{
          const v=document.querySelector('#reader-viewer');
          const max=Math.max(0,v.scrollHeight-v.clientHeight);
          return max>100 && Math.abs(v.scrollTop/max-expected)<.12;
        }""",arg=saved["ratio"],timeout=10000)
        assert snapshot(page)["page"]==3

        # Transition texte -> image PDF -> texte au doigt : la NOUVELLE page
        # se sauvegarde immédiatement, même après rechargement de la page.
        page.locator("#reader-page").fill("4")
        page.locator("#reader-page").dispatch_event("change")
        ready(page,4,False)
        swipe(page,-130)
        ready(page,5,True)
        page.wait_for_function("""key=>JSON.parse(localStorage.getItem(key)||'null')?.page===5""",
                               arg=SPOT_KEY,timeout=10000)
        page.reload(wait_until="load")
        ready(page,5,True)
        assert page.locator("#reader-image-fallback").is_hidden()
        assert not errors,errors
        assert not blocked,blocked
        context.close()

        # Un navigateur qui refuse le stockage ne doit PAS afficher un
        # message mensonger « Page mémorisée ». Le livre doit rester lisible.
        denied_context=browser.new_context(**opts)
        denied_context.add_init_script("""(() => {
          Storage.prototype.setItem=function(){
            throw new DOMException('Storage blocked by browser','SecurityError');
          };
        })()""")
        denied=denied_context.new_page()
        rejected=install_isolation(denied)
        denied.goto(url,wait_until="load")
        ready(denied,3,True)
        # V86 : le stockage refusé ne doit pas être annoncé fonctionnel
        # pendant les instants précédant le premier changement de page.
        denied_initial=denied.locator("#reader-position-status").inner_text()
        assert "Nouvelle sauvegarde non encore confirmée" in denied_initial,denied_initial
        assert "Enregistrement automatique actif" not in denied_initial,denied_initial
        assert "sans écraser une progression" not in denied.locator(
            "#reader-position-help").inner_text()
        # V87 : l'échec d'un swipe sur écran doit afficher un avertissement
        # explicite, même si la navigation elle-même reste possible.
        denied_swipe=swipe(denied,-130)
        assert denied_swipe["consumed"],denied_swipe
        denied.wait_for_function("""()=>{
          const s=document.querySelector('#reader-position-status');
          return s.dataset.type==='warning' &&
                 s.textContent.includes('Position non enregistrée');
        }""",timeout=10000)
        assert denied.locator("#reader-position-status").get_attribute(
            "data-type")=="warning"
        assert snapshot(denied)["scroll"]>50
        # En mode pages d'écran, le bouton Suivante avance d'abord une
        # portion de texte. Aller explicitement à la page PDF suivante pour
        # exercer changePage() et la notification de stockage refusé.
        denied.locator("#reader-page").fill("4")
        denied.locator("#reader-page").dispatch_event("change")
        ready(denied,4,True)
        warning=denied.locator("#reader-position-status")
        assert warning.get_attribute("data-type")=="warning",warning.inner_text()
        assert "non enregistrée" in warning.inner_text(),warning.inner_text()
        assert "mémorisée automatiquement" not in warning.inner_text()
        assert denied.evaluate("""key=>localStorage.getItem(key)""",SPOT_KEY) is None
        assert not rejected,rejected
        denied_context.close()
        print(f"PASS {engine} V85/V86/V87: sauvegarde après swipe confirmée "
              "sur cet appareil, reprise après rechargement, stockage refusé signalé")
    finally:
        browser.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--browser",choices=("chromium","webkit"),required=True)
    args=parser.parse_args()
    with serve_fixture() as fixture:
        origin=fixture.split("/tests/e2e/fixtures/")[0]
        with sync_playwright() as p:
            run(p,args.browser,origin+"/compte/liseuse.html?edition=demo")


if __name__=="__main__":
    main()
