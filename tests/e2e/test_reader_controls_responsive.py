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


def check_reading_collection(browser):
    # Client fictif et DOM local. Aucune lecture ou mutation de compte réel.
    context=browser.new_context(service_workers="block",viewport={"width":390,"height":760})
    try:
        context.route("**/*",lambda route:route.continue_() if route.request.url.startswith(BASE) else route.abort())
        for script in ("site.js","sinjira-account.js","sinjira-account-v18.js","sinjira-nav-boot-v2.js"):
            context.route("**/assets/js/"+script+"*",lambda route:route.abort())
        context.route("**/assets/js/sinjira-supabase.js",lambda route:route.fulfill(content_type="text/javascript",body="""window.writes=[];
          let reads=0;let library=[];
          const novel={id:'fixture-1',title:'Roman fictif de contrôle',status:'announced',slug:'fixture',description:'Texte fictif'};
          export async function requireUser(){return {id:'fixture-user'}}
          export const escapeHtml=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
          export function setStatus(node,msg,type){node.textContent=msg;node.hidden=false;node.dataset.type=type}
          export function getSupabase(){return {from(table){return {
            select(){return {in(){return this},order:async()=>({data:[novel],error:null}),eq:async()=>({data:library,error:null})}},
            async upsert(payload,options){window.writes.push({payload,options});library=[{novel_id:novel.id,progress_percent:67.5,last_page:42}];return {error:null}},
            delete(){const filters={};return {eq(k,v){filters[k]=v;return this},then(resolve){window.writes.push({filters});library=[];resolve({error:null})}}}
          }}}}"""))
        page=context.new_page()
        page.goto(urljoin(BASE,"compte/mes-lectures.html"),wait_until="domcontentloaded")
        add=page.locator("[data-v2461-add-read]")
        remove=page.locator("[data-v2461-remove-read]")
        add.wait_for()
        add.click()
        remove.wait_for()
        check(page.evaluate("window.writes[0].options.ignoreDuplicates===true"),"ajout risque d’écraser la progression")
        check(page.locator("progress.reading-progress").get_attribute("value")=="67.5","progression serveur non préservée")
        dialog=page.locator("[data-reading-remove-dialog]")
        for width,height,zoom in ((240,420,"100%"),(320,760,"200%"),(390,360,"100%"),(1440,760,"100%")):
            page.set_viewport_size({"width":width,"height":height})
            page.evaluate("(z)=>document.documentElement.style.fontSize=z",zoom)
            card=page.locator("[data-v2461-novel]")
            state=card.evaluate("""el=>{const r=el.getBoundingClientRect();return r.left>=-2&&r.right<=innerWidth+2&&el.scrollWidth<=el.clientWidth+2&&[...el.querySelectorAll('.btn')].every(b=>b.getBoundingClientRect().height>=47.5)}""")
            check(state,f"carte de lecture hors écran {width}/{zoom}")
            remove.click()
            dialog.wait_for(state="visible")
            check(dialog.locator("[data-reading-remove-name]").inner_text()=="Roman fictif de contrôle","roman incorrect")
            check(dialog.locator('[value="cancel"]').evaluate("(el)=>document.activeElement===el"),"focus initial incorrect")
            state=dialog.evaluate("""el=>{const r=el.getBoundingClientRect();return r.left>=-2&&r.right<=innerWidth+2&&r.top>=-2&&r.bottom<=innerHeight+2&&el.scrollWidth<=el.clientWidth+2}""")
            check(state,f"dialogue hors écran {width}/{zoom}")
            if width==240:
                page.keyboard.press("Escape")
            else:
                dialog.locator('[value="cancel"]').click()
            dialog.wait_for(state="hidden")
            page.wait_for_function("document.activeElement===document.querySelector('[data-v2461-remove-read]')")
            check(page.evaluate("window.writes.length")==1,"retrait annulé transmis")
        remove.click()
        dialog.locator('[value="remove"]').click()
        add.wait_for()
        check(page.evaluate("window.writes.length===2&&window.writes[1].filters.user_id==='fixture-user'&&window.writes[1].filters.novel_id==='fixture-1'"),"retrait non ciblé")
        check(page.locator("progress.reading-progress").count()==0,"ancienne progression encore affichée")
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
            check_reading_collection(browser)
        finally:
            browser.close()
    print(f"OK {ENGINE}: liseuse V55, 6 largeurs, commandes accessibles, texte fictif seul")


if __name__ == "__main__":
    run()
