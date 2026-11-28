#!/usr/bin/env python3
"""Notifications privées: UX locale, aucune donnée ni session réelle."""
import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
ENGINE = os.environ.get("BROWSER", "chromium")
FIXTURE = r"""
const rows=[
 {id:'a',title:'Avis fictif A',body:'X'.repeat(160),notification_type:'character',created_at:'2026-11-20',read_at:null,action_path:'/compte/profil.html'},
 {id:'b',title:'Avis fictif B',body:'Autre avis',notification_type:'character',created_at:'2026-11-19',read_at:'2026-11-20',action_path:'/compte/profil.html'}
];
window.fixtureWrites=0;
window.fixtureFail=false;
export const requireUser=async()=>({id:'fixture-user'});
export const escapeHtml=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const formatDate=x=>x;
export function setStatus(node,msg,type){if(node){node.hidden=false;node.textContent=msg;node.setAttribute('role',type==='error'?'alert':'status');}}
export const getSupabase=()=>({from(table){
 if(table!=='user_notifications')throw Error('Unexpected table');
 let owner,id,unread=false,patch=null,head=false,limit=100;
 return {
  select(_,options){head=!!options?.head;return this;},
  eq(key,value){if(key==='user_id')owner=value;if(key==='id')id=value;return this;},
  is(key,value){if(key==='read_at'&&value===null)unread=true;return this;},
  order(){return this;},limit(n){limit=n;return this;},
  update(p){patch=p;return this;},
  then(resolve,reject){
    return (async()=>{
      if(owner!=='fixture-user')throw Error('Missing owner filter');
      const matched=rows.filter(r=>(!id||r.id===id)&&(!unread||!r.read_at));
      if(patch){
        window.fixtureWrites++;
        await new Promise(r=>setTimeout(r,300));
        if(window.fixtureFail)return {error:Error('Fictional failure')};
        for(const row of matched)row.read_at=patch.read_at;
        return {error:null};
      }
      return head?{count:matched.length,error:null}:{data:matched.slice(0,limit),error:null};
    })().then(resolve,reject);
  }
 };
}});
"""

def run():
    assert urlparse(BASE).hostname in {"127.0.0.1", "localhost"}
    assert ENGINE in {"chromium", "firefox", "webkit"}
    with sync_playwright() as p:
        browser = getattr(p, ENGINE).launch()
        try:
            ctx = browser.new_context(locale="fr-CA", service_workers="block", viewport={"width":390,"height":780})
            ctx.route("**/*", lambda route: route.continue_() if urlparse(route.request.url).hostname in {"127.0.0.1","localhost"} else route.abort())
            ctx.route("**/assets/js/sinjira-account.js*", lambda r:r.fulfill(content_type="text/javascript",body="export {};"))
            ctx.route("**/assets/js/sinjira-supabase.js*", lambda r:r.fulfill(content_type="text/javascript",body=FIXTURE))
            page=ctx.new_page()
            page.goto(urljoin(BASE,"compte/notifications.html"),wait_until="load")
            cards=page.locator("[data-notifications-list] [data-notification-id]")
            filt=page.locator("[data-notifications-filter]")
            read=page.get_by_role("button",name="Marquer comme lu : Avis fictif A")
            bulk=page.locator("[data-notifications-read-all]")
            expect(cards).to_have_count(2)
            expect(filt).to_be_enabled()
            for width in (320,390,768,1024,1440):
                page.set_viewport_size({"width":width,"height":780})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), f"overflow {width}"
                for locator in (filt,read,bulk):
                    rect=locator.bounding_box()
                    assert rect and rect["height"]>=44 and rect["width"]>=44, (width,rect)
            filt.select_option("read")
            expect(page.locator("[data-notification-id='a']")).to_be_hidden()
            expect(page.locator("[data-notification-id='b']")).to_be_visible()
            filt.select_option("unread")
            expect(page.locator("[data-notification-id='b']")).to_be_hidden()
            page.evaluate("window.fixtureFail=true")
            read.click()
            expect(page.locator("[data-notifications-status]")).to_contain_text("Impossible")
            expect(read).to_be_enabled()
            page.evaluate("window.fixtureFail=false")
            read.focus()
            read.press("Enter")
            expect(bulk).to_be_disabled()
            expect(page.locator("[data-notifications-status]")).to_contain_text("Avis marqué comme lu.")
            expect(page.locator("[data-notifications-filter-empty]")).to_be_visible()
            expect(page.locator("[data-notifications-unread-count]")).to_have_text("0")
            expect(filt).to_have_value("unread")
            assert page.evaluate("window.fixtureWrites")==2
            filt.select_option("all")
            expect(page.locator("[data-notification-id='a']")).to_be_visible()
            expect(bulk).to_be_disabled()
            ctx.close()
        finally:
            browser.close()
    print(f"OK notifications responsive: {ENGINE}")

if __name__ == "__main__":
    run()
