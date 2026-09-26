#!/usr/bin/env python3
import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL=os.environ.get("BASE_URL","http://127.0.0.1:4173/").rstrip("/")+"/"


def assert_true(value,message):
    if not value:
        raise AssertionError(message)


def run():
    with sync_playwright() as p:
        browser=p.chromium.launch()
        context=browser.new_context(locale="fr-CA",viewport={"width":1280,"height":900},reduced_motion="reduce")
        page=context.new_page()
        errors=[]
        production_requests=[]
        page.on("pageerror",lambda error: errors.append(str(error)))
        page.on("request",lambda request: production_requests.append(request.url) if "supabase.co" in request.url else None)

        context.route(
            "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm",
            lambda route: route.fulfill(
                status=200,
                content_type="application/javascript",
                headers={"Access-Control-Allow-Origin":"*","Cache-Control":"no-store"},
                body=r"""
let posts=[{
  id:'post-junior-1',
  author_alias:'Explorateur-ABCD1234',
  body:'Bienvenue dans le fil Junior de test',
  created_at:'2026-09-17T12:00:00Z',
  mine:false,
  comments:[]
}];
const user={id:'child-test-11',email:'private-child@example.test'};
function query(data=[]){
  const api={
    select:()=>api,eq:()=>api,neq:()=>api,in:()=>api,or:()=>api,order:()=>api,limit:()=>api,
    insert:()=>api,update:()=>api,upsert:()=>api,delete:()=>api,
    maybeSingle:async()=>({data:null,error:null}),
    single:async()=>({data:null,error:null}),
    then:(resolve,reject)=>Promise.resolve({data,error:null}).then(resolve,reject)
  };
  return api;
}
export function createClient(){
  globalThis.__sinjiraTables=globalThis.__sinjiraTables||[];
  return {
    auth:{
      getUser:async()=>({data:{user},error:null}),
      mfa:{getAuthenticatorAssuranceLevel:async()=>({data:{currentLevel:'aal1',nextLevel:'aal1'},error:null})},
      signOut:async()=>({error:null})
    },
    rpc:async(name,args={})=>{
      if(name==='is_sinjira_admin')return {data:false,error:null};
      if(name==='sinjira_my_age_band')return {data:'child',error:null};
      if(name==='sinjira_my_account_capabilities'){
        await new Promise(resolve=>setTimeout(resolve,500));
        return {data:{account_mode:'child',age_band:'child',child_11_12:true,native_general_hubs:false,general_community:false,private_messages:false,dating:false,library_mode:'reviewed_11_12',junior_community_eligible:true,junior_community_enabled:true,junior_rules_accepted:true},error:null};
      }
      if(name==='sinjira_junior_community_enabled')return {data:true,error:null};
      if(name==='has_accepted_junior_community_rules')return {data:true,error:null};
      if(name==='junior_community_feed')return {data:posts,error:null};
      if(name==='junior_community_create_post'){
        const body=String(args.p_body||'');
        if(body.includes('http'))return {data:null,error:{message:'SINJIRA_JUNIOR_EXTERNAL_CONTACT_FORBIDDEN'}};
        posts=[{id:'mine-2',author_alias:'Explorateur-MOI12345',body,created_at:new Date().toISOString(),mine:true,comments:[]},...posts];
        return {data:{ok:true,id:'mine-2'},error:null};
      }
      if(name==='junior_community_create_comment'){
        const post=posts.find(p=>p.id===args.p_post_id);
        if(post)post.comments=[...(post.comments||[]),{id:'comment-mine',author_alias:'Explorateur-MOI12345',body:String(args.p_body||''),created_at:new Date().toISOString(),mine:true}];
        return {data:{ok:true,id:'comment-mine'},error:null};
      }
      if(name==='junior_community_delete_post')return {data:true,error:null};
      if(name==='junior_community_delete_comment')return {data:true,error:null};
      if(name==='junior_community_report_content')return {data:{ok:true,blocked:true},error:null};
      return {data:null,error:null};
    },
    from:(name)=>{globalThis.__sinjiraTables.push(String(name));return query([])}
  };
}
"""
            )
        )

        response=page.goto(urljoin(BASE_URL,"compte/communaute-junior.html"),wait_until="domcontentloaded",timeout=30000)
        assert_true(response is not None and response.status<400,"Page Communauté Junior inaccessible")
        composer=page.locator("[data-junior-post-form] textarea")
        assert_true(composer.is_disabled(),"Le compositeur Junior est actif avant la validation des capacités serveur")
        page.wait_for_function("document.querySelector('[data-junior-feed]')?.innerText.includes('Bienvenue dans le fil Junior de test')",timeout=10000)
        assert_true(composer.is_enabled(),"Le compositeur Junior reste verrouillé après validation des capacités")

        text=page.locator("main").inner_text()
        assert_true("Communauté Junior SINJIRA" in text,"Titre Junior absent")
        assert_true("Explorateur-ABCD1234" in text,"Pseudonyme Junior absent du fil")
        assert_true("private-child@example.test" not in text,"Courriel privé exposé dans la page")
        assert_true("child-test-11" not in text,"Identifiant technique exposé dans la page")
        assert_true("Messages privés" not in text or "Aucun message privé" in text,"La page laisse croire que les messages privés sont disponibles")

        composer.fill("Ma nouvelle publication Junior")
        page.locator("[data-junior-post-form] button[type='submit']").click()
        page.wait_for_function("document.querySelector('[data-junior-feed]')?.innerText.includes('Ma nouvelle publication Junior')",timeout=10000)

        first=page.locator("[data-junior-post]").first
        first.locator("[data-junior-comment-form] input").fill("Un commentaire Junior")
        first.locator("[data-junior-comment-form] button[type='submit']").click()
        page.wait_for_function("document.querySelector('[data-junior-feed]')?.innerText.includes('Un commentaire Junior')",timeout=10000)

        composer=page.locator("[data-junior-post-form] textarea")
        composer.fill("Ajoute-moi sur https://example.test")
        page.locator("[data-junior-post-form] button[type='submit']").click()
        page.wait_for_function("document.querySelector('[data-junior-status]')?.innerText.includes('liens, coordonnées')",timeout=10000)

        library=context.new_page()
        library.on("pageerror",lambda error: errors.append("library:"+str(error)))
        library.on("request",lambda request: production_requests.append(request.url) if "supabase.co" in request.url else None)
        response=library.goto(urljoin(BASE_URL,"compte/bibliotheque.html"),wait_until="domcontentloaded",timeout=30000)
        assert_true(response is not None and response.status<400,"Route Bibliothèque Junior inaccessible")
        library.wait_for_function("document.body.innerText.includes('Aucun contenu n’a encore été approuvé pour les comptes de 11–12 ans')",timeout=10000)
        assert_true("/compte/bibliotheque.html" in library.url,"La Bibliothèque approuvée 11–12 a été redirigée à tort")
        tables=library.evaluate("globalThis.__sinjiraTables||[]")
        forbidden={"access_requests","sinjira_reader_library","user_entitlements","playtests","playtest_participants"}
        assert_true(not (forbidden & set(tables)),"La Bibliothèque Junior a interrogé des modules non certifiés: "+", ".join(sorted(forbidden & set(tables))))

        restricted=context.new_page()
        restricted.on("pageerror",lambda error: errors.append("route:"+str(error)))
        restricted.on("request",lambda request: production_requests.append(request.url) if "supabase.co" in request.url else None)
        response=restricted.goto(urljoin(BASE_URL,"compte/playtests.html"),wait_until="domcontentloaded",timeout=30000)
        assert_true(response is not None and response.status<400,"Route Playtests inaccessible pendant le test")
        restricted.wait_for_url("**/compte/communaute-junior.html?from=restricted&module=playtests.html",timeout=10000)
        restricted.wait_for_function("document.querySelector('[data-junior-access-note]')?.hidden === false",timeout=10000)
        assert_true("pas encore certifiée" in restricted.locator("[data-junior-access-note]").inner_text(),"Le repli Junior n explique pas la restriction")

        assert_true(not production_requests,"Le test Junior a tenté de joindre Supabase production: "+" | ".join(production_requests[:3]))
        assert_true(not errors,"Erreurs JavaScript Junior: "+" | ".join(errors[:5]))

        context.close()
        browser.close()
        print("OK navigateur Junior: identité protégée, bibliothèque limitée aux contenus approuvés, aucun module sensible interrogé et routes non certifiées redirigées fail-closed.")


if __name__=="__main__":
    run()
