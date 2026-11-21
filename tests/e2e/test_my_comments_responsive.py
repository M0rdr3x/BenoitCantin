#!/usr/bin/env python3
"""SINJIRA — interactions de Mes commentaires sur ordinateur et mobile.

Utilise la vraie page, son vrai module JS et une source de données entièrement
fictive fournie par le navigateur. Aucun compte, cookie ni service externe.
"""
import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
ENGINE = os.environ.get("BROWSER", "chromium").strip().lower()
WIDTHS = (320, 390, 520, 768, 1024, 1440)

FAKE_DATABASE = r"""
const comments = [
  {id:"fictional-pending-a",body:"Avis fictif A",status:"pending",spoiler:false,
   created_at:"2026-11-19T10:30:00Z",sinjira_novels:{title:"Roman fictif"}},
  {id:"fictional-approved-b",body:"Avis fictif B",status:"approved",spoiler:false,
   created_at:"2026-11-20T12:30:00Z",sinjira_novels:{title:"Roman fictif"}}
];
export const getSupabase = () => ({
  from(table) {
    if(table !== "sinjira_novel_comments") throw Error("Table de test non autorisée");
    const filters = {};
    let action = "select", values = null;
    return {
      select() {return this;},
      eq(key,value) {filters[key]=value;return this;},
      order() {return this;},
      limit(count) {return Promise.resolve({
        data:comments.filter(c => (!filters.user_id || filters.user_id==="fixture-user"))
          .slice(0,count),error:null
      });},
      update(patch) {action="update";values=patch;return this;},
      delete() {action="delete";return this;},
      then(resolve,reject) {
        if(filters.user_id !== "fixture-user" || filters.status !== "pending") {
          return Promise.resolve({error:Error("Garde serveur fictif")}).then(resolve,reject);
        }
        const i=comments.findIndex(c=>c.id===filters.id&&c.status==="pending");
        if(i<0) return Promise.resolve({error:Error("Statut non modifiable")}).then(resolve,reject);
        if(action==="update") comments[i].body=String(values.body);
        if(action==="delete") comments.splice(i,1);
        return Promise.resolve({error:null}).then(resolve,reject);
      }
    };
  }
});
export async function requireUser() {return {id:"fixture-user"};}
export const formatDate = value => String(value).slice(0,10);
export const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g,c=>({
  "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
}[c]));
export const friendlyBackendMessage = value => String(value ?? "");
"""


def verify(ok, message):
    if not ok:
        raise AssertionError(f"{ENGINE}: {message}")


def check_geometry(page, width):
    page.set_viewport_size({"width":width,"height":780})
    result=page.evaluate("""() => {
      const cards=[...document.querySelectorAll('[data-comment-id]')];
      const buttons=[...document.querySelectorAll('[data-edit-comment],[data-delete-comment]')];
      return {
        overflow:document.documentElement.scrollWidth>innerWidth+2,
        cards:cards.map(card=>{
          const r=card.getBoundingClientRect();
          return {left:r.left,right:r.right,width:r.width};
        }),
        buttons:buttons.map(button=>{
          const r=button.getBoundingClientRect();
          return {height:r.height,width:r.width,aria:button.getAttribute('aria-label')};
        })
      };
    }""")
    verify(not result["overflow"], f"débordement horizontal à {width}px : {result}")
    for card in result["cards"]:
        verify(card["left"]>=-2 and card["right"]<=width+2,
               f"carte hors écran à {width}px : {result}")
    for button in result["buttons"]:
        verify(button["height"]>=44 and button["width"]>=44,
               f"commande tactile trop petite à {width}px : {result}")
        verify(bool(button["aria"]) and "2026-11-19" in button["aria"],
               f"commande répétée sans intitulé contextualisé à {width}px : {result}")


def run():
    verify(ENGINE in {"chromium","firefox","webkit"}, "navigateur inconnu")
    verify((urlparse(BASE).hostname or "").lower() in {"127.0.0.1","localhost"},
           "ce test n'exécute aucun appel sur le site de production")
    with sync_playwright() as playwright:
        browser=getattr(playwright,ENGINE).launch()
        try:
            context=browser.new_context(
                locale="fr-CA",service_workers="block",
                viewport={"width":390,"height":780},reduced_motion="reduce")
            try:
                # Le compte générique et les éventuels appels distants sont bloqués.
                context.route("**/assets/js/sinjira-account.js*",lambda route:route.fulfill(
                    status=200,content_type="text/javascript",body="export {};"))
                context.route("**/assets/js/sinjira-supabase.js*",lambda route:route.fulfill(
                    status=200,content_type="text/javascript",body=FAKE_DATABASE))
                context.route("**/*.supabase.co/**",lambda route:route.abort())
                page=context.new_page()
                response=page.goto(urljoin(BASE,"compte/mes-commentaires.html"),
                                   wait_until="domcontentloaded",timeout=30_000)
                verify(response is not None and response.status<400,
                       "page Mes commentaires inaccessible")
                page.locator('[data-comment-id]').first.wait_for(timeout=12_000)
                verify(page.locator('[data-comment-id]').count()==2,
                       "les commentaires fictifs ne se chargent pas")
                verify(page.locator('[data-my-comments]').get_attribute('aria-busy')=='false',
                       "l'annonce de chargement n'est jamais terminée")
                verify(page.locator('[data-edit-comment]').count()==1 and
                       page.locator('[data-delete-comment]').count()==1,
                       "seul un commentaire en attente doit être modifiable")
                edit=page.locator('[data-edit-comment]').first
                delete=page.locator('[data-delete-comment]').first
                for width in WIDTHS:
                    check_geometry(page,width)
                    edit.click()
                    textarea=page.locator('[data-inline-edit] textarea')
                    verify(textarea.evaluate('(el) => document.activeElement === el'),
                           f"champ d'édition sans focus à {width}px")
                    verify(edit.is_disabled() and delete.is_disabled(),
                           f"actions concurrentes encore actives à {width}px")
                    verify(textarea.evaluate("(el)=>el.getBoundingClientRect().width<=innerWidth+2"),
                           f"zone d'édition hors écran à {width}px")
                    textarea.fill("Texte de validation fictif")
                    textarea.press("Escape")
                    verify(page.locator('[data-inline-edit]').count()==0,
                           f"Échap ne ferme pas l'édition à {width}px")
                    verify(edit.evaluate('(el) => document.activeElement === el') and not edit.is_disabled() and
                           not delete.is_disabled(),
                           f"le focus ou les actions ne sont pas restaurés à {width}px")

                edit.click()
                page.locator('[data-inline-edit] textarea').fill("Commentaire fictif corrigé")
                page.locator('[data-inline-edit] button[type=submit]').click()
                page.locator('[data-comment-id] p').first.filter(
                    has_text="Commentaire fictif corrigé").wait_for(timeout=10_000)
                verify(page.locator('[data-v18-status]').get_attribute('role')=='status',
                       "retour de sauvegarde non annoncé")
                page.on("dialog",lambda dialog:dialog.accept())
                page.locator('[data-delete-comment]').first.click()
                page.wait_for_function("() => document.querySelectorAll('[data-comment-id]').length===1")
                verify(page.locator('[data-comment-id]').count()==1,
                       "suppression de la ligne fictive non répercutée")
                verify(page.locator('[data-v18-status]').evaluate('(el) => document.activeElement === el'),
                       "focus non rétabli sur le statut après suppression")
                verify(page.locator('[data-comment-id]').first.get_attribute('data-comment-id')==
                       "fictional-approved-b", "un commentaire publié a été modifié")
            finally:
                context.close()
        finally:
            browser.close()
    print(f"OK {ENGINE}: Mes commentaires, 6 largeurs, annulation Échap, édition et suppression simulées")


if __name__=="__main__":
    run()
