#!/usr/bin/env python3
"""Bibliothèque et candidatures fictives, aucun compte réel."""
import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
ENGINE = os.environ.get("BROWSER", "chromium")
FIXTURE = r"""
window.fixtureWrites=0;
window.fixtureFail=false;
window.fixtureAccessFail=false;
export const requireUser=async()=>({id:'fixture-user'});
export const escapeHtml=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function setStatus(n,m,t){if(n){n.hidden=false;n.textContent=m;n.setAttribute('role',t==='error'?'alert':'status');}}
export const getSupabase=()=>({
 rpc:async()=>({data:false,error:window.fixtureAccessFail?Error('fixture'):null}),
 from(table){
  let owner,insert;
  return {
   select(){return this},in(){return this},order(){return this},
   eq(k,v){if(k==='user_id')owner=v;return this;},
   insert(p){insert=p;return this;},
   then(resolve,reject){return (async()=>{
    if(insert){
     if(table!=='access_requests'||insert.user_id!=='fixture-user'||insert.project_id!=='fixture-game'||insert.requested_level!=='tester')throw Error('Invalid request');
     window.fixtureWrites++;window.fixtureMessage=insert.message;
     await new Promise(r=>setTimeout(r,250));
     if(window.fixtureFail)throw Error('network');
     return {error:null};
    }
    if(table==='projects')return {data:[{id:'fixture-game',name:'Projet fictif',description:'X'.repeat(180),slug:'fracture-du-reseau-mere',public_path:'/projets/sinjira/jeux/',play_path:'/compte/projet.html',allow_tester_requests:true}],error:null};
    if(owner!=='fixture-user')throw Error('Missing user');
    return {data:[],error:null};
   })().then(resolve,reject)}
  };
 }
});
"""

def run():
    assert urlparse(BASE).hostname in {"127.0.0.1","localhost"}
    assert ENGINE in {"chromium","firefox","webkit"}
    with sync_playwright() as p:
        browser=getattr(p,ENGINE).launch()
        try:
            ctx=browser.new_context(locale="fr-CA",service_workers="block",reduced_motion="reduce",viewport={"width":390,"height":780})
            ctx.route("**/*",lambda r:r.continue_() if urlparse(r.request.url).hostname in {"127.0.0.1","localhost"} else r.abort())
            ctx.route("**/assets/js/sinjira-account.js*",lambda r:r.fulfill(content_type="text/javascript",body="export {};"))
            ctx.route("**/assets/js/sinjira-supabase.js*",lambda r:r.fulfill(content_type="text/javascript",body=FIXTURE))
            page=ctx.new_page()
            for route in ("bibliotheque.html","bibliotheque-jeux.html","bibliotheque-ressources.html"):
                page.goto(urljoin(BASE,"compte/"+route),wait_until="load")
                tabs=page.locator(".sinjira-library-tabs a")
                expect(tabs).to_have_count(4)
                expect(page.locator(".sinjira-library-tabs [aria-current='page']")).to_have_count(1)
                for width in (240,320,390,768,1440):
                    page.set_viewport_size({"width":width,"height":780})
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+2"),(route,width)
                    for tab in tabs.all():
                        rect=tab.bounding_box()
                        assert rect and rect["height"]>=47.5 and rect["width"]>=44,(route,width,rect)
            page.goto(urljoin(BASE,"compte/bibliotheque-jeux.html"),wait_until="load")
            start=page.locator("[data-request-tester]")
            form=page.locator("[data-tester-form]")
            expect(start).to_be_enabled()
            expect(page.locator("[data-library-account-games]")).to_have_attribute("aria-busy","false")
            expect(page.get_by_role("link",name="Jouer",exact=True)).to_have_count(0)
            start.click()
            expect(form).to_be_visible()
            form.locator("textarea").fill("Brouillon fictif")
            form.locator("[data-tester-cancel]").click()
            expect(form).to_be_hidden()
            assert page.evaluate("window.fixtureWrites")==0
            start.click()
            expect(form.locator("textarea")).to_have_value("")
            form.locator("textarea").fill("Candidature fictive")
            submit=form.get_by_role("button",name="Envoyer la demande")
            submit.click()
            expect(start).to_be_disabled()
            expect(start).to_have_text("Demande testeur en attente")
            expect(form).to_be_hidden()
            assert page.evaluate("window.fixtureWrites")==1
            assert page.evaluate("window.fixtureMessage")=="Candidature fictive"
            page.reload(wait_until="load")
            expect(start).to_be_enabled()
            page.evaluate("window.fixtureFail=true")
            start.click()
            submit.click()
            expect(form.locator("[data-tester-feedback]")).to_contain_text("Envoi non confirmé")
            expect(submit).to_be_disabled()
            assert page.evaluate("window.fixtureWrites")==1
            ctx.close()
        finally:
            browser.close()
    print(f"OK bibliothèque responsive et candidature: {ENGINE}")

if __name__=="__main__":
    run()
