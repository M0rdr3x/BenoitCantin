#!/usr/bin/env python3
"""Contrôle visuel responsive de la liseuse (texte fictif uniquement).

La page est chargée sans JavaScript applicatif, authentification, PDF, requête
Supabase ou données de compte. On expose le lecteur pour inspecter le CSS.
"""
import os
from pathlib import Path
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


def check_tester_request_confirmation(browser):
    # Module réel, client fictif : aucune candidature réelle ou donnée privée.
    context=browser.new_context(service_workers="block",viewport={"width":390,"height":760})
    try:
        context.route("**/*",lambda route: route.continue_() if route.request.url.startswith(BASE) else route.abort())
        # Charger le HTML/CSS exact de la page, mais aucun autre module applicatif.
        markup=(Path(__file__).resolve().parents[2]/"compte/bibliotheque-jeux.html").read_text("utf-8")
        context.route("**/tester-fixture.html*",lambda route:route.fulfill(
            content_type="text/html",body=markup))
        for script in ("site.js","sinjira-account.js","sinjira-nav-boot-v2.js"):
            context.route("**/assets/js/"+script+"*",lambda route:route.abort())
        context.route("**/assets/js/sinjira-supabase.js",lambda route:route.fulfill(
            content_type="text/javascript",body="""window.writes=[];
            const mode=new URLSearchParams(location.search).get('mode');
            export async function requireUser(){return {id:'fixture-user'}}
            export const escapeHtml=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
            export function setStatus(node,msg,type){node.hidden=false;node.textContent=msg;node.dataset.type=type}
            export function getSupabase(){return {
              rpc:async()=>({data:false,error:null}),
              from(table){return {
                select(){return {in(){return this},eq(){return this},order:async()=>({data:[{
                  id:'fixture-project',name:'Projet fictif',slug:'fracture-du-reseau-mere',allow_tester_requests:true
                }],error:null}),then(resolve){resolve({data:[],error:mode==='load-error'&&table==='access_requests'?{code:'fixture'}:null})}}},
                async insert(payload){window.writes.push(payload);if(mode==='send-error')throw Error('fixture');return {error:null}}
              }}
            }}"""))
        page=context.new_page()
        fixture=urljoin(BASE,"tester-fixture.html")
        page.goto(fixture,wait_until="domcontentloaded")
        button=page.locator("[data-request-tester]")
        button.wait_for()
        dialog=page.locator("[data-library-request-dialog]")
        cancel=dialog.locator('[value="cancel"]')
        send=dialog.locator('[value="send"]')
        for width,height,zoom in ((240,420,"100%"),(320,760,"200%"),(390,360,"100%"),(1440,760,"100%")):
            page.set_viewport_size({"width":width,"height":height})
            page.evaluate("(z)=>document.documentElement.style.fontSize=z",zoom)
            button.click()
            check(dialog.is_visible(),"dialogue inaccessible")
            check(cancel.evaluate("(el)=>document.activeElement===el"),"focus initial non sûr")
            check(dialog.locator("[data-request-project-name]").inner_text()=="Projet fictif","projet non identifié")
            state=dialog.evaluate("""el=>{
              const r=el.getBoundingClientRect();
              return {contained:r.left>=-2&&r.right<=innerWidth+2&&r.top>=-2&&r.bottom<=innerHeight+2,
                overflow:el.scrollWidth>el.clientWidth+2,
                buttons:[...el.querySelectorAll('button')].every(b=>{const x=b.getBoundingClientRect();return x.left>=r.left-2&&x.right<=r.right+2&&x.height>=47.5})};
            }""")
            check(state["contained"] and not state["overflow"] and state["buttons"],f"dialogue {width} / {zoom}: {state}")
            dialog.locator("textarea").fill("Texte annulé")
            if width==240:
                page.keyboard.press("Escape")
            else:
                cancel.click()
            dialog.wait_for(state="hidden")
            page.wait_for_function("document.activeElement===document.querySelector('[data-request-tester]')")
            check(page.evaluate("window.writes.length")==0,"annuler a transmis une candidature")
            check(button.is_enabled(),"annuler a bloqué la commande")
        page.evaluate("document.documentElement.style.fontSize=''")
        button.click()
        check(dialog.locator("textarea").input_value()=="","texte annulé conservé")
        send.click()
        page.wait_for_function("document.querySelector('[data-request-tester]').textContent==='Demande testeur en attente'")
        check(page.evaluate("window.writes.length===1&&window.writes[0].message===''&&window.writes[0].user_id==='fixture-user'"),"confirmation vide volontaire non respectée")
        check(button.is_disabled(),"nouvelle demande possible après succès")
        page.goto(fixture+"?mode=send-error",wait_until="domcontentloaded")
        button.wait_for()
        button.click()
        dialog.locator("textarea").fill("Exemple fictif")
        send.click()
        page.wait_for_function("document.querySelector('[data-request-tester]').textContent==='Vérification requise'")
        check(button.is_disabled() and page.evaluate("window.writes.length")==1,"envoi incertain rejouable")
        page.goto(fixture+"?mode=load-error",wait_until="domcontentloaded")
        page.wait_for_function("document.querySelector('[data-library-status]').dataset.type==='error'")
        check(button.count()==0,"candidature possible sans état serveur confirmé")
        check(page.locator('[data-library-account-games] a').count()>0,"liens du projet supprimés")
    finally:
        context.close()


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
            check_tester_request_confirmation(browser)
        finally:
            browser.close()
    print(f"OK {ENGINE}: liseuse V55, 6 largeurs, commandes accessibles, texte fictif seul")


if __name__ == "__main__":
    run()
