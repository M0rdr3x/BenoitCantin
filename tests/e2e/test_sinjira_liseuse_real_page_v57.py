#!/usr/bin/env python3
"""V57 : vraie page compte/liseuse.html, moteur PDF simulé, aucun vrai roman.

Tests sur moteurs Chromium/WebKit dans un mobile simulé. Les ressources
externes sont toutes bloquées. Les données du livre sont synthétiques et
ne traversent jamais Supabase. Ce n'est pas une certification sur iPhone réel.
"""
import argparse
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from test_sinjira_liseuse_mobile_v54 import serve_fixture, swipe


MOCK_PDF_JS = """
export const GlobalWorkerOptions = {workerSrc:''};
function makePage(pageNumber){
  return {
    async getTextContent(){
      const items=Array.from({length:46},(_,i)=>({
        str:'LIVRE DE TEST · Page '+pageNumber+' · paragraphe '+(i+1)+
          ' : une phrase synthétique qui occupe de la place et permet de lire '+
          'avec une taille de texte confortable sur téléphone. Aucune donnée privée.',
        transform:[1,0,0,1,40,900-i*28],height:12,
        width:120,hasEOL:true
      }));
      return {items};
    },
    getViewport({scale=1}={}){return {width:612*scale,height:792*scale}},
    render(){return {promise:Promise.resolve()}}
  };
}
export function getDocument({data}={}){
  if(!data||data.length<1024)throw Error('V57 mock: missing test PDF');
  return {promise:Promise.resolve({
    numPages:82,getPage:async n=>{
      if(n<1||n>82)throw Error('V57 mock: invalid page '+n);
      return makePage(n);
    },destroy:async()=>{}
  })};
}
"""

SUPABASE_STUB = """
export function getSupabase(){throw Error('V57: unexpected Supabase access')};
export async function requireUser(){throw Error('V57: unexpected sign-in')};
export function safeInternalDestination(x){return x};
"""

def install_isolation(page):
    requests=[]
    def intercept(route):
        url=route.request.url
        parsed=urlparse(url)
        path=parsed.path
        if path == "/assets/js/sinjira-supabase.js":
            route.fulfill(status=200,content_type="text/javascript",
                          body=SUPABASE_STUB)
        elif "pdfjs-dist@4.9.155/build/pdf.min.mjs" in url:
            route.fulfill(status=200,content_type="text/javascript",body=MOCK_PDF_JS)
        elif path == "/projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf":
            route.fulfill(status=200,content_type="application/pdf",
                          body=b"%PDF-1.4 V57 synthetic only " + b"0"*2400)
        elif path == "/assets/js/site.js":
            route.fulfill(status=200,content_type="text/javascript",body="// isolated V57")
        elif parsed.hostname in ("127.0.0.1","localhost"):
            route.continue_()
        else:
            requests.append(url)
            route.abort()
    page.route("**/*", intercept)
    return requests


def snapshot(page):
    return page.evaluate("""()=>{
      const v=document.querySelector('#reader-viewer');
      const t=document.querySelector('#reader-text');
      const output=document.querySelector('#reader-screen-count');
      return {
        page:Number(document.querySelector('#reader-page').value),
        scroll:v.scrollTop,max:Math.max(0,v.scrollHeight-v.clientHeight),
        layout:v.dataset.readerLayout,text:t.textContent,
        textHidden:t.hidden,screen:output.textContent,
        prevDisabled:document.querySelector('#reader-previous').disabled,
        nextDisabled:document.querySelector('#reader-next').disabled,
        mode:document.querySelector('#reader-mode').textContent
      };
    }""")


def run(playwright, browser_type, url):
    browser=getattr(playwright,browser_type).launch()
    try:
        context=browser.new_context(viewport={"width":390,"height":844},
                                    is_mobile=True,has_touch=True,
                                    locale="fr-CA",device_scale_factor=2,
                                    service_workers="block",reduced_motion="reduce")
        page=context.new_page()
        failures=[]
        page.on("pageerror",lambda err: failures.append(str(err)))
        rejected=install_isolation(page)
        page.goto(url,wait_until="load")
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-viewer').dataset.readerLayout==='screens'&&
          document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST')""",timeout=15000)
        first=snapshot(page)
        assert first["page"]==3 and first["layout"]=="screens",first
        assert first["max"]>200 and first["prevDisabled"] is False,{
            "scroll":first["scroll"],"max":first["max"],"page":first["page"]}
        assert first["scroll"]<2,{
            "reason":"Page initiale PDF incorrectement repositionnée",
            "scroll":first["scroll"],"max":first["max"],"page":first["page"]}
        assert "LIVRE DE TEST · Page 3" in first["text"]
        assert not rejected,rejected

        # Tout le mouvement a lieu sur la vraie fenêtre de lecture, sans
        # modifier la page PDF tant qu'elle comporte du texte.
        forward=swipe(page,-130)
        second=snapshot(page)
        assert forward["consumed"] and second["page"]==3,{
            "first_scroll":first["scroll"],"first_max":first["max"],
            "forward":forward,"second_page":second["page"],
            "second_scroll":second["scroll"],"second_screen":second["screen"]}
        assert second["scroll"]>first["scroll"],(first,second)
        reverse=swipe(page,130)
        rewind=snapshot(page)
        assert reverse["consumed"] and rewind["scroll"]==0,rewind

        # Une page source complète ne doit pas être sautée; lorsque toutes
        # ses portions sont lues, une seule autre page PDF est chargée.
        crossed=False
        for _ in range(70):
            swipe(page,-130)
            if snapshot(page)["page"]==4:
                crossed=True
                break
        assert crossed,"V57: pas de transition vers la page PDF suivante"
        page.wait_for_function("""()=>document.querySelector('#reader-text')
          .textContent.includes('LIVRE DE TEST · Page 4')""")
        assert snapshot(page)["page"]==4,snapshot(page)
        assert snapshot(page)["scroll"]==0,snapshot(page)

        # Le retour depuis le premier écran d'une autre page doit exposer
        # la dernière portion de la page PDF précédente.
        swipe(page,130)
        page.wait_for_function("""()=>document.querySelector('#reader-page').value==='3'&&
           document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST · Page 3')""")
        page.wait_for_function("""()=>{const v=document.querySelector('#reader-viewer');
          return v.scrollTop>100&&v.scrollTop>=v.scrollHeight-v.clientHeight-3}""")
        assert snapshot(page)["page"]==3,snapshot(page)

        # Marque-page de progression : passage écran puis enregistrement de
        # la position du lecteur de démo dans la clé historique V31.
        page.locator("#reader-touch-prev").click()
        page.locator("#reader-save-position").click()
        page.wait_for_function("""()=>{const key='sinjira:liseuse:demo:la-cendre-du-jugement:spot';
          const value=JSON.parse(localStorage.getItem(key)||'null');
          return value?.page===3&&value?.ratio>0}""")
        saved=page.evaluate("""()=>JSON.parse(localStorage.getItem(
          'sinjira:liseuse:demo:la-cendre-du-jugement:spot'))""")
        assert saved["ratio"]>0,saved

        # Rechargement de la page réelle, sans faux stockage pour la position :
        # le moteur doit restaurer la page 3 et un ratio cohérent.
        page.reload(wait_until="load")
        page.wait_for_function("""()=>!document.querySelector('#reader-content').hidden&&
          document.querySelector('#reader-text').textContent.includes('LIVRE DE TEST · Page 3')""")
        page.wait_for_timeout(120)
        loaded=snapshot(page)
        new_ratio=loaded["scroll"]/max(1,loaded["max"])
        assert loaded["page"]==3 and abs(new_ratio-saved["ratio"])<0.12,(
            "V57: perte de la position après rechargement",saved,loaded
        )

        # La transition vers le PDF doit garder un seul gestionnaire tactile.
        page.locator("#reader-mode").click()
        page.wait_for_function("""()=>document.querySelector('#reader-text').hidden===true""")
        before_pdf=snapshot(page)
        swipe(page,-130)
        page.wait_for_function("""before=>Number(document.querySelector('#reader-page').value)===before+1""",
                               arg=before_pdf["page"])
        assert snapshot(page)["page"]==before_pdf["page"]+1, (
            "V57: double saut de PDF",before_pdf,snapshot(page)
        )

        # Repasser au texte et à la mise en page mobile.
        page.locator("#reader-mode").click()
        page.wait_for_function("""()=>document.querySelector('#reader-text').hidden===false""")
        assert snapshot(page)["layout"]=="screens",snapshot(page)
        assert not failures,failures
        assert not rejected,rejected
        context.close()
        print(f"PASS {browser_type}: vraie page, gestes, transitions PDF, "
              "sauvegarde V31, reprise après rechargement, mode PDF")
    finally:
        browser.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--browser",choices=("chromium","webkit"),required=True)
    args=parser.parse_args()
    with serve_fixture() as fixture:
        original=fixture.split("/tests/e2e/fixtures/")[0]
        with sync_playwright() as p:
            run(p,args.browser,original+"/compte/liseuse.html?edition=demo")


if __name__=="__main__":
    main()
