#!/usr/bin/env python3
import json
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER_NAME = os.environ.get("BROWSER", "chromium").strip().lower()
SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
ASSISTANT_VERSION = "24.4.50"
PUBLIC_ROUTES = [
    "",
    "a-propos.html",
    "contact.html",
    "projets/projet-nova/contact.html",
    "projets/sinjira/",
    "projets/sinjira/registre/",
    "projets/sinjira/communaute/",
    "projets/sinjira/monde-parallele/",
    "projets/projet-nova/",
    "projets/projet-nova/boussole-electorale.html",
    "projets/projet-nova/sondage-citoyen.html",
    "projets/sinjira/jeux/",
    "projets/sinjira/jeux/fracture-du-reseau-mere/",
]
AUTH_ROUTES = [
    "compte/connexion.html",
    "compte/inscription.html",
    "compte/mot-de-passe-oublie.html",
    "compte/reinitialiser-mot-de-passe.html",
]
EXPECTED_FEATURES = {
    "/projets/sinjira/romans/",
    "/projets/sinjira/registre/",
    "/projets/sinjira/jeux/",
    "/projets/sinjira/communaute/",
}
IS_LOCAL = (urlparse(BASE_URL).hostname or "").lower() in {"127.0.0.1", "localhost"}


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def register_error_capture(page, target):
    # Indiquer uniquement le chemin, jamais les paramètres ni le fragment.
    # Conserver toutes les erreurs, y compris celles de ResizeObserver.
    page.on("pageerror", lambda error: target.append(
        f"pageerror [{urlparse(page.url).path}]: {error}"
    ))


def wait_for_assistant(page):
    if page.locator('html[data-disable-sinjira-assistant="true"]').count():
        page.wait_for_load_state("load")
        page.evaluate("window.dispatchEvent(new Event('pointerdown'))")
    page.wait_for_function(
        "([version]) => window.__SINJIRA_ASSISTANT__ && window.__SINJIRA_ASSISTANT__.version === version",
        arg=[ASSISTANT_VERSION],
        timeout=10_000,
    )


def check_legal_navigation(browser):
    # Sommaire natif : aucun compte, aucun script requis, aucune écriture.
    legal_pages = {"avis-legal.html": 10, "confidentialite.html": 13,
                   "gouvernance-vie-privee.html": 9}
    for js in (False, True):
        ctx = browser.new_context(locale="fr-CA", java_script_enabled=js,
                                  reduced_motion="reduce", service_workers="block")
        # Playwright désactive le cache HTTP avec le routage. Les réponses
        # conditionnelles 304 ne doivent pas être confondues avec un échec
        # de chargement et aucune ressource externe n’est nécessaire ici.
        ctx.route("**/*", lambda route: route.continue_() if
                  urlparse(route.request.url).netloc == urlparse(BASE_URL).netloc
                  else route.abort())
        try:
            page = ctx.new_page()
            for width in (240, 320, 390, 768, 1440):
                page.set_viewport_size({"width": width, "height": 820})
                for path, count in legal_pages.items():
                    response = page.goto(urljoin(BASE_URL, path), wait_until="load", timeout=30_000)
                    assert_true(response is not None and response.ok,
                                f"{BROWSER_NAME}: {path} indisponible, {width}px, JS={js}, "
                                f"HTTP={response.status if response else None}")
                    nav = page.locator("main nav#sommaire")
                    links = nav.locator("a")
                    headings = page.locator("main article h2[id]")
                    assert_true(links.count() == count == headings.count(), f"{path}: sommaire incomplet")
                    for i in range(count):
                        link = links.nth(i)
                        target = link.get_attribute("href")
                        assert_true(target == "#" + headings.nth(i).get_attribute("id"),
                                    f"{path}: ancre incohérente")
                        assert_true(link.inner_text() == headings.nth(i).inner_text(),
                                    f"{path}: libellé incohérent")
                        box = link.bounding_box()
                        assert_true(box is not None and box["height"] >= 44 and
                                    box["x"] >= -2 and box["x"] + box["width"] <= width + 2,
                                    f"{path}: lien tactile hors écran {width}px")
                    if width == 390:
                        link = links.last
                        target = link.get_attribute("href")
                        link.focus()
                        link.press("Enter")
                        assert_true(urlparse(page.url).fragment == target[1:], f"{path}: ancre clavier")
                        back = page.locator(".legal-toc-return a")
                        back.focus()
                        back.press("Enter")
                        assert_true(urlparse(page.url).fragment == "sommaire", f"{path}: retour sommaire")
        finally:
            ctx.close()


def check_message_layout(browser):
    # HTML/CSS réels, contenus synthétiques; tous les scripts de compte et
    # services externes sont bloqués. Aucun message réel ni envoi.
    ctx = browser.new_context(locale="fr-CA", service_workers="block",
                              reduced_motion="reduce")
    ctx.route("**/*", lambda route: route.continue_() if
              urlparse(route.request.url).netloc == urlparse(BASE_URL).netloc
              and route.request.resource_type != "script" else route.abort())
    try:
        page = ctx.new_page()
        for path, search_label, message_label in (
            ("compte/messages-reels.html", "Rechercher un membre", "Votre message"),
            ("compte/messages-personnage.html", "Rechercher un personnage",
             "Votre message en personnage"),
        ):
            response = page.goto(urljoin(BASE_URL, path), wait_until="load", timeout=30_000)
            assert_true(response is not None and response.ok, f"{path}: page inaccessible")
            search = page.get_by_role("textbox", name=search_label)
            form = page.locator("[data-chat-form]")
            assert_true(search.count() == 1 and form.is_hidden(),
                        f"{path}: recherche inaccessible ou formulaire ouvert avant sélection")
            page.evaluate("""() => {
              const long = 'Fictif'.repeat(60);
              const list = document.querySelector('[data-contact-list]');
              const chat = document.querySelector('[data-chat-log]');
              for (let i=0; i<20; i++) {
                const contact=document.createElement('button');
                contact.className='v20-contact';
                const span=document.createElement('span');
                span.textContent=long;
                contact.append(span); list.append(contact);
              }
              const bubble=document.createElement('div');
              bubble.className='v20-bubble';
              bubble.textContent=long; chat.append(bubble);
              document.querySelector('[data-chat-form]').hidden=false;
            }""")
            field = page.get_by_role("textbox", name=message_label)
            assert_true(field.count() == 1, f"{path}: zone de message sans nom")
            field.fill("Brouillon fictif")
            for width in (240, 320, 390, 768, 1440):
                page.set_viewport_size({"width":width,"height":720})
                metrics = page.evaluate("""() => {
                  const shell=document.querySelector('.v20-message-shell');
                  const list=document.querySelector('.v20-contact-list');
                  const log=document.querySelector('.v20-chat-log');
                  const form=document.querySelector('.v20-chat-form');
                  const field=form.querySelector('textarea');
                  const button=form.querySelector('button');
                  const sr=shell.getBoundingClientRect();
                  const inside=e=>{const r=e.getBoundingClientRect();
                    return r.left>=sr.left-2 && r.right<=sr.right+2;};
                  return {inside:[list,log,field,button].every(inside),
                    listOverflow:list.scrollWidth>list.clientWidth+2,
                    logOverflow:log.scrollWidth>log.clientWidth+2,
                    fieldFont:parseFloat(getComputedStyle(field).fontSize),
                    buttonHeight:button.getBoundingClientRect().height,
                    mobileListHeight:list.getBoundingClientRect().height};
                }""")
                assert_true(metrics["inside"] and not metrics["listOverflow"] and
                            not metrics["logOverflow"] and metrics["fieldFont"]>=16 and
                            metrics["buttonHeight"]>=47.5 and
                            (width>900 or metrics["mobileListHeight"]<=241),
                            f"{path} à {width}px: {metrics}")
                assert_true(field.input_value()=="Brouillon fictif",
                            f"{path}: brouillon perdu au redimensionnement")
            form.evaluate("(el) => el.hidden=true")
            assert_true(form.is_hidden(), f"{path}: attribut hidden ignoré")
    finally:
        ctx.close()


def check_conversation_isolation(browser):
    # Données entièrement fictives. Les modules officiels sont chargés sur
    # le serveur local; aucun compte ni trafic backend réel.
    for kind in ("real","character"):
        ctx=browser.new_context(service_workers="block",viewport={"width":390,"height":844})
        try:
            ctx.route("**/*",lambda route: route.continue_() if route.request.url.startswith(BASE_URL) else route.abort())
            source=(Path(__file__).resolve().parents[2]/("compte/messages-reels.html" if kind=="real" else "compte/messages-personnage.html")).read_text("utf-8")
            moderation=source[source.index('<dialog class="message-moderation-dialog"'):source.index("</dialog>")+len("</dialog>")]
            ctx.route("**/messages-race-fixture.html*",lambda route: route.fulfill(
                content_type="text/html",body=f"""<link rel="stylesheet" href="/assets/css/sinjira-message-moderation-v1.css"><input data-contact-search><div data-contact-list></div>
                <header data-chat-title></header><div data-chat-log></div><p data-social-status></p>
                <form data-chat-form hidden><textarea name="body"></textarea><button type="submit">Envoyer</button></form>
                {moderation}<script type="module" src="/assets/js/sinjira-messages-{kind}.js"></script>"""))
            ctx.route("**/assets/js/sinjira-message-read-state.js*",lambda route: route.fulfill(
                content_type="text/javascript",body="""export async function unreadCounts(){return new Map()}
                export async function markConversationRead(table,user,filters){window.reads.push({table,user,filters})}"""))
            ctx.route("**/assets/js/sinjira-social-common.js*",lambda route: route.fulfill(
                content_type="text/javascript",body="""window.requests=[];window.sends=[];window.reads=[];window.reports=[];window.blocks=[];
                const contacts=['a','b'].map(id=>({user_id:id,character_id:'char-'+id,pseudo:id,public_name:id}));
                export async function requireCommunityUser(){return {id:'self',email:'fixture@example.invalid'}}
                export const escapeHtml=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
                export const formatDate=()=>'';export const avatarUrl=()=>'/assets/icons/sinjira-favicon.png';
                export const reportContent=async(payload)=>{window.reports.push(payload);return {ok:true}};export const socialStatus=(node,msg)=>{node.textContent=msg};
                export const socialErrorStatus=(node,error,msg)=>{node.textContent=msg};
                export function getSupabase(){return {
                  from(table){return {
                    select(){let filter='';return {neq(){return this},eq(){return this},
                      maybeSingle:async()=>({data:{user_id:'self',character_id:'char-self'},error:null}),
                      or(value){filter=value;return this},
                      order(){return table.endsWith('_messages')?new Promise(resolve=>window.requests.push({filter,resolve})):Promise.resolve({data:contacts,error:null})}}},
                    insert(payload){return new Promise(resolve=>window.sends.push({payload,resolve}))},
                    async upsert(payload){window.blocks.push(payload);return {error:{message:'fixture'}}}
                  }},
                  channel(){return {on(){return this},subscribe(){return this}}}
                }}
                window.resolveRead=(index,id)=>{const other=id==='a'?'b':'a';window.requests[index].resolve({error:null,data:[
                  {id:'msg-'+id,body:'Message '+id,sender_user_id:id,recipient_user_id:'self',sender_character_id:'char-'+id,recipient_character_id:'char-self'},
                  {id:'wrong',body:'Hors conversation',sender_user_id:other,recipient_user_id:'self',sender_character_id:'char-'+other,recipient_character_id:'char-self'}
                ]})};"""))
            page=ctx.new_page()
            page.goto(urljoin(BASE_URL,"messages-race-fixture.html"),wait_until="domcontentloaded")
            attr="data-user" if kind=="real" else "data-character"
            prefix="" if kind=="real" else "char-"
            a=page.locator(f'[{attr}="{prefix}a"]')
            b=page.locator(f'[{attr}="{prefix}b"]')
            log=page.locator("[data-chat-log]")
            composer=page.locator('textarea[name="body"]')
            a.click()
            composer.fill("Brouillon A")
            b.click()
            assert_true(composer.input_value()=="","brouillon transféré au mauvais contact")
            assert_true("Chargement" in log.inner_text(),"ancien contenu non effacé")
            page.wait_for_function("window.requests.length===2")
            page.evaluate("window.resolveRead(1,'b')")
            page.wait_for_function("window.reads.length===1")
            page.evaluate("window.resolveRead(0,'a')")
            page.evaluate("() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
            assert_true("Message b" in log.inner_text() and "Message a" not in log.inner_text() and "Hors conversation" not in log.inner_text(),"réponse périmée affichée")
            assert_true(page.evaluate("window.reads.length")==1,"ancienne conversation marquée lue")
            assert_true(page.evaluate("Object.values(window.reads[0].filters)[0]")==prefix+"b","marquage du mauvais contact")
            report=log.locator("[data-report-message]")
            dialog=page.locator("[data-message-moderation]")
            for width,height,zoom in ((240,420,"100%"),(320,760,"200%"),(390,360,"100%"),(1440,760,"100%")):
                page.set_viewport_size({"width":width,"height":height})
                page.evaluate("(z)=>document.documentElement.style.fontSize=z",zoom)
                report.click()
                dialog.wait_for(state="visible")
                assert_true(dialog.locator('[value="cancel"]').evaluate("(el)=>document.activeElement===el"),"focus initial")
                state=dialog.evaluate("""el=>{const r=el.getBoundingClientRect();return r.left>=-2&&r.right<=innerWidth+2&&r.top>=-2&&r.bottom<=innerHeight+2&&el.scrollWidth<=el.clientWidth+2&&[...el.querySelectorAll('button')].every(b=>b.getBoundingClientRect().height>=47.5)}""")
                assert_true(state,f"dialogue hors écran {width}/{zoom}")
                if width==240:
                    page.keyboard.press("Escape")
                else:
                    dialog.locator('[value="cancel"]').click()
                dialog.wait_for(state="hidden")
                page.wait_for_function("window.reports.length===0&&document.activeElement===document.querySelector('[data-report-message]')")
            page.evaluate("document.documentElement.style.fontSize=''")
            report.click()
            dialog.locator('[name="reason"]').select_option("harassment")
            dialog.locator('[name="details"]').fill("Texte fictif")
            dialog.locator('[value="confirm"]').click()
            page.wait_for_function("window.reports.length===1")
            assert_true(page.evaluate("window.reports[0].target_id==='msg-b'&&window.reports[0].reason==='harassment'&&window.reports[0].details==='Texte fictif'"),"signalement mal ciblé")
            if kind=="real":
                page.locator("[data-block-peer]").click()
                dialog.locator('[value="cancel"]').click()
                dialog.wait_for(state="hidden")
                assert_true(page.evaluate("window.blocks.length===0"),"blocage annulé transmis")
                page.locator("[data-block-peer]").click()
                dialog.locator('[value="confirm"]').click()
                page.wait_for_function("window.blocks.length===1")
                assert_true(page.evaluate("window.blocks[0].blocked_user_id==='b'"),"mauvais compte bloqué")
            composer.fill("Brouillon B")
            a.click()
            assert_true(composer.input_value()=="Brouillon A","brouillon A perdu")
            page.locator('[data-chat-form] button[type="submit"]').click()
            page.evaluate("document.querySelector('[data-chat-form]').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))")
            assert_true(page.evaluate("window.sends.length")==1,"double envoi")
            b.click()
            assert_true(composer.input_value()=="Brouillon B","brouillon B perdu")
            page.evaluate("window.sends[0].resolve({error:null})")
            page.wait_for_function("!document.querySelector('[data-chat-form] button').disabled")
            assert_true(composer.input_value()=="Brouillon B","envoi précédent efface le brouillon courant")
            assert_true(page.evaluate("window.sends[0].payload.recipient_user_id")=="a","mauvais destinataire")
            a.click()
            assert_true(composer.input_value()=="","brouillon envoyé encore présent")
        finally:
            ctx.close()


def check_notification_counts(browser):
    # Real page and notification module; synthetic Supabase adapter only.
    mock = r"""
let unread=5;
const mode=new URLSearchParams(location.search).get('fixture');
export const requireUser=async()=>({id:'synthetic-user'});
export const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const formatDate=value=>String(value);
export const setStatus=(node,message,type)=>{node.textContent=message;node.hidden=false;node.dataset.statusType=type};
export const getSupabase=()=>({from(table){
  if(table!=='user_notifications')throw Error('unexpected table');
  let scoped=false,head=false,mutation=false,unreadOnly=false;
  const query={
    select(fields,options){head=options?.head===true;return this},
    eq(key,value){if(key==='user_id'&&value==='synthetic-user')scoped=true;return this},
    is(key,value){if(key==='read_at'&&value===null)unreadOnly=true;return this},
    order(){return this},limit(){return this},
    update(){mutation=true;return this},
    then(resolve,reject){
      return Promise.resolve().then(()=>{
        if(!scoped||((head||mutation)&&!unreadOnly))throw Error('unscoped query');
        if(mutation){
          if(mode==='update-error')return {error:{message:'synthetic failure'}};
          unread=0;return {error:null};
        }
        if(head)return mode==='count-error'?{error:{message:'synthetic failure'}}:{count:unread,error:null};
        return {data:Array.from({length:100},(_,i)=>({id:'fake-'+i,title:'Avis fictif',body:'Contenu fictif',read_at:'2026-01-01',created_at:'2026-01-01'})),error:null};
      }).then(resolve,reject);
    }
  };return query;
}});
"""
    for mode in ("success", "count-error", "update-error"):
        context = browser.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        page = context.new_page()
        def route_request(route):
            request = route.request
            parsed = urlparse(request.url)
            if parsed.netloc != urlparse(BASE_URL).netloc:
                return route.abort()
            if parsed.path.endswith("/sinjira-supabase.js"):
                return route.fulfill(status=200, content_type="text/javascript", body=mock)
            if request.resource_type == "script" and not parsed.path.endswith((
                "/sinjira-user-notifications-v24-4-63.js", "/sinjira-social-navigation-guard.mjs"
            )):
                return route.abort()
            return route.continue_()
        page.route("**/*", route_request)
        try:
            page.goto(urljoin(BASE_URL, "compte/notifications.html?fixture="+mode))
            page.wait_for_function("document.querySelector('[data-notifications-list]').getAttribute('aria-busy') === 'false'")
            count = page.locator("[data-notifications-unread-count]")
            total = page.locator("[data-notifications-total-count]")
            button = page.locator("[data-notifications-read-all]")
            status = page.locator("[data-notifications-status]")
            if mode == "count-error":
                assert_true(count.inner_text() == "—" and button.is_disabled(), "Failed count must not be reported as zero")
                assert_true("indisponibles" in page.locator("[data-notifications-list]").inner_text(), "Loading must end on failure")
            else:
                assert_true(count.inner_text() == "5" and total.inner_text() == "100", "Unread count must include older notifications")
                assert_true(button.is_enabled(), "Older unread notifications must be actionable")
                for width in (240, 320, 390, 768, 1440):
                    page.set_viewport_size({"width": width, "height": 760})
                    geometry=page.evaluate("""() => {
                      const controls=[...document.querySelectorAll('main .hero-actions :is(button,a)')];
                      const cards=[...document.querySelectorAll('[data-notification-id]')];
                      return document.documentElement.scrollWidth<=innerWidth+2 &&
                        cards.length===100 && cards.every(c=>{const r=c.getBoundingClientRect();return r.left>=-2&&r.right<=innerWidth+2;}) &&
                        controls.every(c=>{const r=c.getBoundingClientRect();return r.height>=47.5&&r.left>=-2&&r.right<=innerWidth+2;});
                    }""")
                    assert_true(geometry, f"Notifications: débordement ou commande trop petite à {width}px")
                button.click()
                page.wait_for_function("!document.querySelector('[data-notifications-status]').hidden")
                if mode == "success":
                    assert_true(count.inner_text() == "0" and button.is_disabled(), "Successful bulk action must refresh count")
                else:
                    assert_true(count.inner_text() == "5" and button.is_enabled(), "Failed action must preserve count and allow retry")
                    assert_true(status.get_attribute("data-status-type") == "error", "Failed update must be announced")
        finally:
            context.close()


def check_fulfillment_feedback(browser):
    # Réponses entièrement fictives, aucun accès ou changement de compte réel.
    ctx=browser.new_context(service_workers="block",viewport={"width":390,"height":760})
    try:
        ctx.route("**/*",lambda route:route.continue_() if route.request.url.startswith(BASE_URL) else route.abort())
        for script in ("site.js","sinjira-account.js","sinjira-nav-boot-v2.js","sinjira-preorders-v24-5-3.js","sinjira-preorder-commercial-v24-5-5.js","sinjira-preorder-cost-summary-v24-5-25.js","sinjira-preorder-tax-estimate-v24-5-27.js"):
            ctx.route("**/assets/js/"+script+"*",lambda route:route.fulfill(content_type="text/javascript",body=""))
        ctx.route("**/assets/js/sinjira-supabase.js*",lambda route:route.fulfill(content_type="text/javascript",body="""window.estimates=[];window.saves=[];window.failStatus=false;
          export const escapeHtml=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
          export async function getCurrentUser(){return {id:'fixture-user'}}
          export const isSinjiraBackendConfigured=()=>true;
          export function getSupabase(){return {async rpc(name,args){
            if(name==='product_preorder_fulfillment_options')return {data:{shipping_estimates_enabled:true,shipping_zones:[{zone_code:'fixture',label:'Zone fictive'}],pickup_points_enabled:false},error:null};
            if(name==='product_preorder_fulfillment_status')return window.failStatus?{data:null,error:{message:'fixture'}}:{data:{fulfillment_preference:'undecided'},error:null};
            if(name==='product_preorder_shipping_estimate')return new Promise(resolve=>window.estimates.push({args,resolve}));
            if(name==='product_preorder_set_fulfillment_preference')return new Promise(resolve=>window.saves.push({args,resolve}));
            throw Error('RPC inattendue');
          }}}
        """))
        page=ctx.new_page()
        page.goto(urljoin(BASE_URL,"compte/mes-achats.html"),wait_until="domcontentloaded")
        zone=page.locator("[data-pf-zone]")
        quantity=page.locator("[data-pf-quantity]")
        estimate=page.locator("[data-pf-estimate]")
        result=page.locator("[data-pf-estimate-result]")
        method=page.locator("[data-pf-method]")
        save=page.locator("[data-pf-save-preference]")
        status=page.locator("[data-pf-preference-status]")
        method.wait_for(state="visible")
        for width,zoom in ((240,"100%"),(320,"200%"),(390,"100%"),(1440,"100%")):
            page.set_viewport_size({"width":width,"height":760})
            page.evaluate("(z)=>document.documentElement.style.fontSize=z",zoom)
            geom=page.locator("[data-preorder-fulfillment]").evaluate("""el=>[...el.querySelectorAll('select,button')].filter(n=>n.getClientRects().length).every(n=>{const r=n.getBoundingClientRect();return r.left>=-2&&r.right<=innerWidth+2&&r.height>=47.5})""")
            assert_true(geom,f"contrôles livraison hors écran {width}/{zoom}")
        zone.select_option("fixture")
        estimate.click()
        page.wait_for_function("window.estimates.length===1")
        quantity.select_option("2")
        assert_true("Options modifiées" in result.inner_text(),"estimation périmée non invalidée")
        estimate.click()
        page.wait_for_function("window.estimates.length===2")
        page.evaluate("window.estimates[1].resolve({data:{estimate_min_cents:2000,estimate_max_cents:3000,zone_label:'Zone fictive',currency:'CAD'},error:null})")
        page.wait_for_function("document.querySelector('[data-pf-estimate-result]').textContent.includes('pour 2 exemplaire')")
        page.evaluate("window.estimates[0].resolve({data:{estimate_min_cents:1000,estimate_max_cents:1500,zone_label:'Zone fictive',currency:'CAD'},error:null})")
        page.evaluate("() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
        assert_true("pour 2 exemplaire" in result.inner_text(),"ancienne estimation remplace la nouvelle")
        estimate.click()
        page.wait_for_function("window.estimates.length===3")
        page.evaluate("window.estimates[2].resolve({data:{estimate_min_cents:null,estimate_max_cents:3000,zone_label:'Zone fictive',currency:'CAD'},error:null})")
        page.wait_for_function("document.querySelector('[data-pf-estimate-result]').dataset.kind==='error'")
        assert_true("Estimation :" not in result.inner_text(),"montant absent présenté comme zéro")
        method.select_option("pickup")
        page.evaluate("window.dispatchEvent(new Event('sinjira:preorder-updated'))")
        page.wait_for_function("document.querySelector('[data-pf-preference-status]').textContent.includes('conservé')")
        assert_true(method.input_value()=="pickup","brouillon écrasé par actualisation")
        save.click()
        page.evaluate("document.querySelector('[data-pf-save-preference]').click()")
        assert_true(page.evaluate("window.saves.length")==1 and method.is_disabled(),"soumission parallèle")
        page.evaluate("window.saves[0].resolve({data:null,error:{message:'fixture'}})")
        page.wait_for_function("document.querySelector('[data-pf-preference-status]').textContent.includes('non confirmé')")
        assert_true(method.input_value()=="pickup" and save.is_disabled(),"choix incertain perdu ou rejouable")
        page.evaluate("window.failStatus=true;window.dispatchEvent(new Event('sinjira:preorder-updated'))")
        page.wait_for_function("document.querySelector('[data-pf-preference-status]').textContent.includes('Impossible de vérifier')")
        assert_true(not page.locator("[data-pf-no-preorder]").is_visible(),"erreur présentée comme absence de réservation")
        assert_true(save.is_disabled(),"mutation autorisée sans état serveur")
    finally:
        ctx.close()


def check_cost_summary_feedback(browser):
    # Aucun prix réel, aucune adresse, aucun fournisseur de paiement.
    ctx=browser.new_context(service_workers="block",viewport={"width":390,"height":760})
    try:
        ctx.route("**/*",lambda route:route.continue_() if route.request.url.startswith(BASE_URL) else route.abort())
        ctx.route("**/cost-summary-fixture.html*",lambda route:route.fulfill(content_type="text/html",body="""<!doctype html><html lang="fr-CA"><meta name="viewport" content="width=device-width,initial-scale=1"><main data-preorder-fulfillment></main>
          <script type="module" src="/assets/js/sinjira-preorder-cost-summary-v24-5-25.js?v=24.5.46.3"></script>
          <script type="module" src="/assets/js/sinjira-preorder-tax-estimate-v24-5-27.js?v=24.5.46.3"></script></html>"""))
        ctx.route("**/assets/js/sinjira-supabase.js*",lambda route:route.fulfill(content_type="text/javascript",body="""window.ship=[];window.tax=[];
          export const escapeHtml=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
          export const isSinjiraBackendConfigured=()=>true;
          const guards={estimate_nonbinding:true,billing_authoritative:false,external_tax_api_enabled:false,final_tax_confirmation_required:true};
          export function getSupabase(){return {async rpc(name,args){
            if(name==='product_preorder_commercial_info')return {data:{currency:'CAD',paper_price_cents:2000,digital_price_cents:1000,sales_enabled:false,checkout_enabled:false,payment_enabled:false,external_fulfillment_enabled:false,auto_conversion_allowed:false},error:null};
            if(name==='product_preorder_fulfillment_options')return {data:{shipping_estimates_enabled:true,shipping_zones:[{zone_code:'fixture',label:'Zone fictive'}]},error:null};
            if(name==='product_preorder_tax_options')return {data:{...guards,tax_profiles:[{tax_code:'fixture-tax',label:'Profil fictif'}]},error:null};
            if(name==='product_preorder_shipping_estimate')return new Promise(resolve=>window.ship.push({args,resolve}));
            if(name==='product_preorder_tax_estimate')return new Promise(resolve=>window.tax.push({args,resolve}));
            throw Error('RPC inattendue');
          }}}
          window.shipResult=(i,min,max,currency='CAD')=>window.ship[i].resolve({data:{estimate_min_cents:min,estimate_max_cents:max,currency,shipping_customer_pays:true,estimate_nonbinding:true,zone_label:'Zone fictive'},error:null});
          window.taxResult=(i,min,max,totalMin,totalMax,currency='CAD')=>window.tax[i].resolve({data:{...guards,estimate_complete:true,currency,estimated_tax_min_cents:min,estimated_tax_max_cents:max,estimated_total_min_cents:totalMin,estimated_total_max_cents:totalMax,source_reference:'Source fictive'},error:null});
        """))
        page=ctx.new_page()
        page.goto(urljoin(BASE_URL,"cost-summary-fixture.html"),wait_until="domcontentloaded")
        fmt=page.locator("[data-pcs-format]")
        qty=page.locator("[data-pcs-quantity]")
        method=page.locator("[data-pcs-method]")
        zone=page.locator("[data-pcs-zone]")
        total=page.locator("[data-pcs-total]")
        tax=page.locator("[data-ptax-public]")
        tax_total=page.locator("[data-ptax-total]")
        page.wait_for_function("!!document.querySelector('link[data-preorder-cost-summary-style]')?.sheet")
        fmt.select_option("paper")
        method.select_option("shipping")
        assert_true(zone.input_value()=="","zone de livraison choisie automatiquement")
        zone.select_option("fixture")
        page.wait_for_function("window.ship.length===1")
        page.evaluate("window.shipResult(0,1000,1200)")
        page.wait_for_function("document.querySelector('[data-pcs-total]').textContent.includes('30')")
        qty.select_option("2")
        page.wait_for_function("window.ship.length===2")
        assert_true("Nouveau calcul" in total.inner_text(),"ancien sous-total conservé pendant le calcul")
        qty.select_option("3")
        page.wait_for_function("window.ship.length===3")
        page.evaluate("window.shipResult(2,2000,1000)")
        page.wait_for_function("document.querySelector('[data-pcs-total]').textContent.includes('indisponible')")
        page.evaluate("window.shipResult(1,1000,1200)")
        page.evaluate("() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
        assert_true("indisponible" in total.inner_text(),"réponse périmée ou fourchette inversée affichée")
        qty.select_option("4")
        page.wait_for_function("window.ship.length===4")
        page.evaluate("window.shipResult(3,1000,1200,null)")
        page.wait_for_function("document.querySelector('[data-pcs-total]').textContent.includes('indisponible')")
        fmt.select_option("digital")
        assert_true(not zone.is_visible() and zone.is_disabled(),"zone inutile visible")
        assert_true(tax.input_value()=="","zone fiscale présélectionnée")
        tax.select_option("fixture-tax")
        assert_true("Profil fictif" in tax.locator("xpath=../following-sibling::small[1]").text_content(),
                    "libellé fiscal complet absent hors contrôle natif")
        page.wait_for_function("window.tax.length===1")
        page.evaluate("window.taxResult(0,100,200,4100,4200)")
        page.wait_for_function("document.querySelector('[data-ptax-tax-note]').textContent.includes('Source fictive')")
        qty.select_option("5")
        page.wait_for_function("window.tax.length===2")
        assert_true("Calcul" in tax_total.inner_text() and "Source fictive" not in page.locator("[data-ptax-tax-note]").inner_text(),"ancienne information fiscale conservée")
        page.evaluate("window.taxResult(1,-100,200,4900,5200)")
        page.wait_for_function("document.querySelector('[data-ptax-tax]').textContent.includes('incomplète')")
        # Tester le libellé ordinaire puis le libellé serveur sans espace.
        for long_label in (False,True):
            if long_label:
                page.evaluate("""() => {
                  const select=document.querySelector('[data-ptax-public]');
                  select.selectedOptions[0].textContent='Profil fiscal fictif très long '+ 'X'.repeat(100);
                  select.dispatchEvent(new Event('change'));
                }""")
            for width,zoom in ((240,"100%"),(320,"200%"),(390,"100%"),(768,"100%"),(1440,"100%")):
                page.set_viewport_size({"width":width,"height":760})
                page.evaluate("(z)=>document.documentElement.style.fontSize=z",zoom)
                page.evaluate("() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                state=page.locator("[data-preorder-cost-summary]").evaluate("""el=>{
                  const edge=el.getBoundingClientRect().right;
                  const visible=[...el.querySelectorAll('*')].filter(n=>n.getClientRects().length);
                  const overflowing=visible.filter(n=>n.scrollWidth>n.clientWidth+2).slice(0,12)
                    .map(n=>({tag:n.tagName,cls:String(n.className),client:n.clientWidth,scroll:n.scrollWidth}));
                  const textOutside=[];
                  for(const n of el.querySelectorAll('.sinjira-selected-option')){
                    const range=document.createRange();range.selectNodeContents(n);
                    if([...range.getClientRects()].some(r=>r.right>edge+2))textOutside.push(n.textContent.slice(0,40));
                  }
                  return {overflow:el.scrollWidth>el.clientWidth+2,width:el.clientWidth,scrollWidth:el.scrollWidth,
                    overflowing,textOutside,
                    outside:visible.filter(n=>n.getBoundingClientRect().right>edge+2).slice(0,8).map(n=>[n.tagName,String(n.className)]),
                    controls:visible.filter(n=>n.tagName==='SELECT').every(n=>{const r=n.getBoundingClientRect();return r.left>=-2&&r.right<=innerWidth+2&&r.height>=47.5})};
                }""")
                assert_true(not state["overflow"] and not state["textOutside"] and state["controls"],
                            f"résumé coût hors écran {width}/{zoom}, long={long_label}: {state}")
                assert_true(page.evaluate("document.documentElement.scrollWidth<=innerWidth+2"),
                            f"débordement du document coût {width}/{zoom}")
                if long_label:
                    assert_true("X"*100 in tax.locator("xpath=../following-sibling::small[1]").text_content(),
                                "libellé long tronqué hors contrôle")
    finally:
        ctx.close()


def check_reservation_feedback(browser):
    # Réservation fictive : aucun compte réel, aucun paiement.
    ctx=browser.new_context(service_workers="block",viewport={"width":390,"height":760})
    try:
        ctx.route("**/*",lambda route:route.continue_() if route.request.url.startswith(BASE_URL) else route.abort())
        for script in ("site.js","sinjira-account.js","sinjira-nav-boot-v2.js","sinjira-preorder-commercial-v24-5-5.js","sinjira-preorder-fulfillment-v24-5-6.js"):
            ctx.route("**/assets/js/"+script+"*",lambda route:route.fulfill(content_type="text/javascript",body=""))
        ctx.route("**/assets/js/sinjira-supabase.js*",lambda route:route.fulfill(content_type="text/javascript",body="""window.writes=[];window.failRead=false;
          const reservation={status:'reserved',reservation_reference:'PR-0123456789ABCDEF',quantity:1,preferred_format:'paper',payment_status:'not_collected',financial_commitment:false};
          export const escapeHtml=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
          export const formatDate=()=> 'Date fictive';
          export async function getCurrentUser(){return {id:'fixture'}}
          export const isSinjiraBackendConfigured=()=>true;
          export function setStatus(node,msg,type){node.hidden=false;node.textContent=msg;node.dataset.type=type}
          export function getSupabase(){return {async rpc(name,args){
            if(name==='product_preorder_my_status')return window.failRead?{data:null,error:{message:'fixture'}}:{data:reservation,error:null};
            if(name==='product_preorder_cancel'||name==='product_preorder_reserve_confirmed')return new Promise(resolve=>window.writes.push({name,args,resolve}));
            throw Error('RPC inattendue');
          }}}
        """))
        page=ctx.new_page()
        page.goto(urljoin(BASE_URL,"compte/mes-achats.html"),wait_until="domcontentloaded")
        cancel=page.locator("[data-preorder-cancel]")
        form=page.locator("[data-preorder-form]")
        submit=page.locator("[data-preorder-submit]")
        dialog=page.locator("[data-preorder-cancel-dialog]")
        status=page.locator("[data-preorder-status]")
        cancel.wait_for(state="visible")
        for width,height,zoom in ((240,420,"100%"),(320,760,"200%"),(390,360,"100%"),(1440,760,"100%")):
            page.set_viewport_size({"width":width,"height":height})
            page.evaluate("(z)=>document.documentElement.style.fontSize=z",zoom)
            cancel.click()
            dialog.wait_for(state="visible")
            assert_true(dialog.locator('[value="keep"]').evaluate("(el)=>document.activeElement===el"),"focus initial non sûr")
            geometry=dialog.evaluate("""el=>{const r=el.getBoundingClientRect();return r.left>=-2&&r.right<=innerWidth+2&&r.top>=-2&&r.bottom<=innerHeight+2&&el.scrollWidth<=el.clientWidth+2&&[...el.querySelectorAll('button')].every(b=>b.getBoundingClientRect().height>=47.5)}""")
            assert_true(geometry,f"annulation hors écran {width}/{zoom}")
            if width==240:
                page.keyboard.press("Escape")
            else:
                dialog.locator('[value="keep"]').click()
            dialog.wait_for(state="hidden")
            page.wait_for_function("document.activeElement===document.querySelector('[data-preorder-cancel]')")
            assert_true(page.evaluate("window.writes.length")==0,"annulation non confirmée transmise")
        cancel.click()
        dialog.locator('[value="cancel-reservation"]').click()
        page.wait_for_function("window.writes.length===1")
        assert_true(submit.is_disabled() and cancel.is_disabled(),"actions concurrentes autorisées")
        form.evaluate("el=>el.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))")
        assert_true(page.evaluate("window.writes.length===1"),"double mutation")
        page.evaluate("window.failRead=true;window.writes[0].resolve({data:true,error:null})")
        page.wait_for_function("document.querySelector('[data-preorder-status]').textContent.includes('Annulation traitée')")
        assert_true(not page.locator("[data-preorder-state]").is_visible() and submit.is_disabled(),"confirmation périmée ou nouvelle mutation possible")
        assert_true(page.evaluate("window.writes[0].name==='product_preorder_cancel'&&Object.keys(window.writes[0].args).join()==='p_product_slug'"),"contrat de mutation modifié")
        page.reload(wait_until="domcontentloaded")
        submit.wait_for(state="visible")
        page.wait_for_function("!document.querySelector('[data-preorder-submit]').disabled")
        page.locator("[data-preorder-disclosure]").check()
        submit.click()
        page.wait_for_function("window.writes.length===1")
        page.evaluate("window.writes[0].resolve({data:null,error:null})")
        page.wait_for_function("document.querySelector('[data-preorder-status]').textContent.includes('non confirmé')")
        assert_true(submit.is_disabled() and not page.locator("[data-preorder-state]").is_visible(),
                    "réservation sans référence valide annoncée comme confirmée")
    finally:
        ctx.close()


def check_admin_responsive_layout(browser):
    # Uniquement le squelette HTML local : aucun script administratif ni backend.
    context=browser.new_context(service_workers="block",viewport={"width":390,"height":760})
    try:
        context.route("**/*",lambda route: route.continue_() if
            route.request.url.startswith(BASE_URL) and route.request.resource_type!="script"
            else route.abort())
        page=context.new_page()
        for path in ("admin/sinjira/index.html","admin/sinjira/licences.html",
                     "admin/sinjira/heritage.html","admin/sinjira/precommandes.html",
                     "admin/sinjira/precommandes-readiness.html"):
            page.goto(urljoin(BASE_URL,path),wait_until="load")
            assert_true(page.locator('meta[name="robots"]').get_attribute("content")=="noindex,nofollow",
                        f"indexation admin modifiée : {path}")
            assert_true(page.locator("main").get_attribute("tabindex")=="-1",
                        f"cible clavier absente : {path}")
            assert_true(page.evaluate("""() => {
              const links=[...document.querySelectorAll('.universe-subnav a')];
              const labels=[...document.querySelectorAll('label[for^="admin-ux-"]')];
              return links.length===5 && links.filter(a=>a.getAttribute('aria-current')==='page').length===1 &&
                labels.every(l=>l.control && document.querySelectorAll('[id="'+l.htmlFor+'"]').length===1);
            }"""),f"navigation ou labels incorrects : {path}")
            for width,height,zoom in ((240,760,"100%"),(320,760,"200%"),(390,360,"100%"),(768,760,"100%"),(1440,900,"100%")):
                page.set_viewport_size({"width":width,"height":height})
                page.evaluate("(z)=>document.documentElement.style.fontSize=z",zoom)
                page.evaluate("() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                state=page.evaluate("""() => {
                  const controls=[...document.querySelectorAll('main button,main .btn,main select,main input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]),main textarea,.universe-subnav a')].filter(n=>n.getClientRects().length&&getComputedStyle(n).visibility==='visible');
                  const invalid=controls.filter(n=>{const r=n.getBoundingClientRect();return r.left<-2||r.right>innerWidth+2||r.height<47.5});
                  return {count:controls.length,invalid:invalid.slice(0,8).map(n=>({tag:n.tagName,cls:String(n.className),width:n.getBoundingClientRect().width,height:n.getBoundingClientRect().height})),
                    overflow:document.documentElement.scrollWidth>innerWidth+2};
                }""")
                assert_true(not state["invalid"] and not state["overflow"],
                            f"admin {path} {width}x{height}/{zoom}: {state}")
    finally:
        context.close()


def run() -> None:
    assert_true(BROWSER_NAME in SUPPORTED_BROWSERS, f"Navigateur Playwright inconnu: {BROWSER_NAME}")

    with sync_playwright() as p:
        browser_type = getattr(p, BROWSER_NAME)
        browser = browser_type.launch()

        context = browser.new_context(
            locale="fr-CA",
            viewport={"width": 1440, "height": 1000},
            reduced_motion="reduce",
            service_workers="block",
        )
        page = context.new_page()
        page_errors = []
        register_error_capture(page, page_errors)

        # L'E2E isole toujours l'API externe du vote, même sur le domaine public.
        # Le GET réel est couvert par le smoke de la fonction Edge séparé.
        # Aucune méthode d'écriture politique ne peut être exécutée en E2E.
        poll_corpus_path = Path(__file__).resolve().parents[2] / "projets/projet-nova/data/sondage-citoyen-v1.json"
        poll_corpus = json.loads(poll_corpus_path.read_text(encoding="utf-8"))
        assert_true(poll_corpus["published"] is False, "Le corpus de sondage est provisoire")
        poll_public_snapshot = json.dumps({
            "version": poll_corpus["version"],
            "open": False,
            "siteKey": None,
            "minPublicBallots": 10,
            "resultsVisible": False,
            "ballots": None,
            "publishedAt": None,
            "questions": [
                {"id": q["id"], "ordinal": q["ordinal"], "text": q["text"], "counts": None}
                for q in poll_corpus["questions"]
            ],
        }, ensure_ascii=False)
        unexpected_poll_writes = []

        def serve_closed_poll_snapshot(route):
            if route.request.method != "GET":
                unexpected_poll_writes.append(route.request.method)
                route.fulfill(status=405, content_type="application/json", body='{"error":"vote_interdit_en_test"}')
                return
            route.fulfill(
                status=200,
                content_type="application/json",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET",
                    "Cache-Control": "no-store",
                },
                body=poll_public_snapshot,
            )

        context.route("**/functions/v1/nova-civic-poll*", serve_closed_poll_snapshot)

        for route in PUBLIC_ROUTES:
            url = urljoin(BASE_URL, route)
            response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            assert_true(response is not None, f"Aucune réponse navigateur pour {url}")
            assert_true(response.status < 400, f"HTTP {response.status} pour {url}")
            assert_true(page.locator("main").count() >= 1, f"Repère main absent: {url}")
            assert_true(page.locator("h1").count() >= 1, f"H1 absent: {url}")
            assert_true(bool(page.title().strip()), f"Titre absent: {url}")

        # Canaux officiels SINJIRA : liens réels et icône YouTube visible.
        page.goto(urljoin(BASE_URL, "projets/sinjira/"), wait_until="domcontentloaded", timeout=30_000)
        official_channels = page.locator(".sinjira-official-channels")
        assert_true(official_channels.count() == 1 and official_channels.is_visible(),
                    f"{BROWSER_NAME}: accès officiels SINJIRA absents")
        youtube = official_channels.locator(".sinjira-official-channel-youtube")
        assert_true(youtube.count() == 1 and youtube.is_visible(),
                    f"{BROWSER_NAME}: chaîne YouTube SINJIRA absente")
        assert_true(youtube.get_attribute("href") == "https://www.youtube.com/@SinjiraOfficiel",
                    f"{BROWSER_NAME}: lien YouTube SINJIRA incorrect")
        assert_true(youtube.locator("svg.sinjira-channel-icon path").count() == 1,
                    f"{BROWSER_NAME}: icône YouTube SINJIRA manquante")
        email_link = official_channels.locator('.sinjira-official-channel-email')
        assert_true(email_link.count() == 1 and email_link.is_visible(),
                    f"{BROWSER_NAME}: courriel SINJIRA non visible")
        assert_true(email_link.get_attribute("href") == "mailto:sinjiraofficiel@gmail.com",
                    f"{BROWSER_NAME}: adresse courriel SINJIRA incorrecte")
        assert_true(
            page.locator('footer a[href="mailto:sinjiraofficiel@gmail.com"]').count() == 1,
            f"{BROWSER_NAME}: contact officiel absent du pied de page SINJIRA",
        )

        # Cibles tactiles du hub Univers : contrôler la géométrie, pas seulement le CSS.
        for width in (320, 390, 1440):
            touch_context = browser.new_context(
                viewport={"width": width, "height": 760},
                locale="fr-CA", service_workers="block", java_script_enabled=False,
            )
            try:
                touch_page = touch_context.new_page()
                touch_page.goto(urljoin(BASE_URL, "projets/sinjira/"),
                                wait_until="load", timeout=30_000)
                targets = touch_page.locator(".site-footer .footer-col a")
                assert_true(targets.count() >= 10, "liens du pied de page absents")
                for link in targets.all():
                    bounds = link.bounding_box()
                    assert_true(bounds is not None and bounds["height"] >= 43.5
                                and bounds["width"] >= 43.5,
                                f"{BROWSER_NAME}: cible du pied de page trop petite à {width}px")
                assert_true(touch_page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
                            f"{BROWSER_NAME}: Univers hors écran à {width}px")
            finally:
                touch_context.close()

        page.goto(urljoin(BASE_URL, "contact.html"), wait_until="domcontentloaded", timeout=30_000)
        assert_true(
            page.locator('a[href="mailto:sinjiraofficiel@gmail.com"]').count() >= 2,
            f"{BROWSER_NAME}: page Contact ne propose pas le courriel officiel SINJIRA",
        )
        assert_true(
            page.locator('a[href="/projets/projet-nova/contact.html"]').count() >= 1,
            f"{BROWSER_NAME}: canal distinct Projet Nova indisponible",
        )

        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_function(
            "document.querySelector('link[data-sinjira-browser-compat]') !== null",
            timeout=10_000,
        )
        compat_href = page.locator("link[data-sinjira-browser-compat]").get_attribute("href") or ""
        assert_true("browser-compat-v24-4-22.css" in compat_href, "Couche CSS de compatibilité non chargée")

        runtime_version = page.evaluate("window.__SINJIRA_RUNTIME__ && window.__SINJIRA_RUNTIME__.version")
        assert_true(runtime_version == "24.4.22", f"Runtime public inattendu: {runtime_version!r}")

        # Accueil recentré : un seul projet visuellement dans le cercle.
        # Les quatre liens ci-dessous sont des rubriques du même univers,
        # pas d'autres projets.
        page.locator("body.home-sinjira-only").wait_for(state="attached")
        orbit = page.locator(".home-cosmos a.sinjira-orbit")
        assert_true(orbit.count() == 1 and orbit.is_visible(),
                    f"{BROWSER_NAME}: SINJIRA doit être seul dans le cercle")
        assert_true(orbit.get_attribute("href") == "/projets/sinjira/",
                    f"{BROWSER_NAME}: porte unique SINJIRA incorrecte")
        orbit_img = orbit.locator('img[src="/assets/icons/sinjira-officiel-20261120.png"]')
        assert_true(orbit_img.count() == 1,
                    f"{BROWSER_NAME}: visuel SINJIRA absent du cercle")
        orbit_img.scroll_into_view_if_needed()
        page.wait_for_function(
            """() => {
                const image = document.querySelector('.home-cosmos .sinjira-orbit img');
                return !!image && image.complete && image.naturalWidth > 0;
            }""",
            timeout=15_000,
        )
        assert_true(page.locator(".home-cosmos .orbit-node").count() == 0,
                    f"{BROWSER_NAME}: anciennes portes encore présentes dans le cercle")
        cards = page.locator("a.home-project")
        assert_true(cards.count() == 4,
                    f"{BROWSER_NAME}: 4 rubriques SINJIRA attendues, trouvé {cards.count()}")
        hrefs = {cards.nth(i).get_attribute("href") for i in range(cards.count())}
        assert_true(hrefs == EXPECTED_FEATURES,
                    f"{BROWSER_NAME}: rubriques SINJIRA inattendues: {hrefs}")
        assert_true(page.locator('body.home-sinjira-only a[href^="/projets/projet-nova"]').count() == 0,
                    f"{BROWSER_NAME}: lien Nova encore affiché sur la page d'accueil")
        assert_true("Projet Nova" not in page.locator("main").inner_text(),
                    f"{BROWSER_NAME}: Nova encore présenté dans la section principale")
        assert_true("Boussole électorale" not in page.locator("main").inner_text(),
                    f"{BROWSER_NAME}: Boussole encore présentée dans l'accueil")
        assert_true(page.locator('link[href*="home-sinjira-only-v1.css"]').count() == 1,
                    f"{BROWSER_NAME}: styles ergonomiques de l'accueil absents")

        # La nouvelle orbite SINJIRA doit être rouge/noire, et non mauve.
        # Tester les couleurs calculées, pas seulement la présence du CSS.
        portal = page.evaluate("""() => {
            const cosmos = document.querySelector(".home-sinjira-cosmos");
            const orbit = cosmos?.querySelector(".sinjira-orbit");
            if (!cosmos || !orbit) return {ok:false, reason:"missing elements"};
            const before = getComputedStyle(cosmos, "::before");
            const after = getComputedStyle(cosmos, "::after");
            const center = getComputedStyle(orbit);
            const crimson = (value) => {
                const match = value.match(/rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)/);
                if (!match) return false;
                const [red, green, blue] = match.slice(1, 4).map(Number);
                return red >= 150 && red > green * 1.45 && red > blue * 1.35;
            };
            return {
                ok: crimson(before.borderTopColor) &&
                    crimson(after.borderTopColor) &&
                    crimson(center.borderTopColor) &&
                    before.backgroundImage.includes("radial-gradient") &&
                    after.backgroundImage.includes("radial-gradient") &&
                    center.backgroundImage.includes("radial-gradient"),
                outer: before.borderTopColor,
                middle: after.borderTopColor,
                center: center.borderTopColor
            };
        }""")
        assert_true(
            portal["ok"],
            f"{BROWSER_NAME}: portail mauve ou sans éclairage rouge sur SINJIRA: {portal}",
        )


        page.goto(urljoin(BASE_URL, "projets/projet-nova/"), wait_until="domcontentloaded", timeout=30_000)
        assert_true(
            page.locator('a[href="boussole-electorale.html"]').count() >= 3,
            f"{BROWSER_NAME}: la Boussole doit avoir au moins trois accès depuis l’accueil Nova",
        )
        # Les deux outils partagent volontairement le style de carte, mais pas
        # leur rôle : chaque sélecteur doit être propre à son accès public.
        assert_true(
            page.locator('a[href="sondage-citoyen.html"]').count() >= 3,
            f"{BROWSER_NAME}: le sondage doit avoir au moins trois accès depuis l’accueil Nova",
        )
        nova_poll_entry = page.locator(".nova-poll-home-entry .nova-compass-entry-link")
        assert_true(nova_poll_entry.count() == 1, f"{BROWSER_NAME}: accès prioritaire Sondage absent de Nova")
        assert_true(nova_poll_entry.is_visible(), f"{BROWSER_NAME}: accès prioritaire Sondage non visible")
        assert_true(
            nova_poll_entry.locator('img[src="assets/sondage-citoyen.svg"]').count() == 1,
            f"{BROWSER_NAME}: illustration du sondage absente de l’accès prioritaire",
        )
        assert_true(
            page.locator('a.hero-side-link-sondage img[src="assets/sondage-citoyen.svg"]').count() == 1,
            f"{BROWSER_NAME}: illustration du sondage absente des accès rapides",
        )
        nova_compass_entry = page.locator(
            ".nova-compass-entry:not(.nova-poll-home-entry) .nova-compass-entry-link"
        )
        assert_true(nova_compass_entry.count() == 1, f"{BROWSER_NAME}: accès prioritaire Boussole absent en haut de Nova")
        assert_true(nova_compass_entry.is_visible(), f"{BROWSER_NAME}: accès prioritaire Boussole non visible")
        assert_true(
            nova_compass_entry.locator('img[src="../../assets/media/nova-boussole-electorale-v2.webp"]').count() == 1,
            f"{BROWSER_NAME}: visuel officiel absent de l’accès prioritaire Nova",
        )
        assert_true(
            page.locator('nav .nav-link-boussole').inner_text().strip() == "Boussole électorale",
            f"{BROWSER_NAME}: libellé complet Boussole électorale absent de la navigation Nova",
        )

        # Le questionnaire politique doit rester en lecture seule tant que
        # la version n'a pas été explicitement approuvée. Aucun bulletin de
        # production n'est envoyé par cette vérification navigateur.
        page.goto(urljoin(BASE_URL, "projets/projet-nova/sondage-citoyen.html"), wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_function(
            """() => {
              const corpus = window.__NOVA_POLL_PUBLIC_CORPUS;
              return !!corpus && corpus.published === false &&
                corpus.questions?.length === 8 && corpus.options?.length === 6;
            }""",
            timeout=10_000,
        )
        assert_true(page.locator("#poll-form").count() == 1, f"{BROWSER_NAME}: formulaire sondage absent")
        assert_true(page.locator("#poll-send").is_disabled(), f"{BROWSER_NAME}: collecte provisoire ouverte par erreur")
        assert_true(
            page.locator('a[href="sondages-a-valider.html"]').count() >= 1,
            f"{BROWSER_NAME}: questionnaires candidats 40/64 non accessibles",
        )
        assert_true(
            page.locator("#poll-results").count() == 1,
            f"{BROWSER_NAME}: zone des résultats agrégés absente",
        )

        assert_true(
            not unexpected_poll_writes,
            f"{BROWSER_NAME}: une écriture politique a été tentée pendant un test en lecture seule",
        )

        page.goto(urljoin(BASE_URL, "projets/projet-nova/boussole-electorale.html"), wait_until="domcontentloaded", timeout=30_000)
        assert_true(
            page.locator('.compass-hero-visual img[src="../../assets/media/nova-boussole-electorale-v2.webp"]').count() == 1,
            f"{BROWSER_NAME}: visuel officiel absent du héros de la Boussole",
        )
        hero_image = page.locator('.compass-hero-visual img')
        page.wait_for_function(
            "() => { const img = document.querySelector('.compass-hero-visual img'); return !!img && img.complete && img.naturalWidth > 0 && img.naturalHeight > 0; }",
            timeout=10_000,
        )
        assert_true(
            hero_image.evaluate("(img) => img.naturalWidth === 360 && img.naturalHeight === 360"),
            f"{BROWSER_NAME}: dimensions du visuel Boussole inattendues",
        )
        assert_true(page.locator(".compass-hero-visual figcaption").count() == 0, f"{BROWSER_NAME}: légende indésirable encore présente")
        assert_true(
            "Votre profil, plusieurs dimensions, aucune consigne de vote" not in page.content(),
            f"{BROWSER_NAME}: texte indésirable encore présent sur la Boussole",
        )
        assert_true(page.locator("#dimensions .compass-dimension-card").count() == 16, f"{BROWSER_NAME}: 16 dimensions publiques attendues")
        assert_true(page.locator("#lecture-resultat .compass-reading-card").count() == 4, f"{BROWSER_NAME}: explication du résultat incomplète")
        assert_true(page.locator("#faq-boussole article").count() == 4, f"{BROWSER_NAME}: FAQ Boussole incomplète")
        evidence_cards = page.locator("#compass-evidence-parties .compass-evidence-card")
        evidence_cards.first.wait_for(state="visible", timeout=10_000)
        assert_true(evidence_cards.count() == 22, f"{BROWSER_NAME}: 22 formations attendues dans l’état documentaire")
        summary_cards = page.locator("#compass-evidence-summary article")
        assert_true(summary_cards.count() == 9, f"{BROWSER_NAME}: résumé documentaire incomplet")
        summary_text = page.locator("#compass-evidence-summary").inner_text()
        assert_true("Questions recherchées" in summary_text and "64/64" in summary_text, f"{BROWSER_NAME}: couverture 64/64 absente du résumé documentaire")
        assert_true("Questions avec preuve" in summary_text, f"{BROWSER_NAME}: couverture de preuve candidate absente du résumé documentaire")
        assert_true("Questions à preuve unique" in summary_text, f"{BROWSER_NAME}: compteur de couverture documentaire limitée absent")
        # Vérifier les chiffres affichés à partir de la matrice, sans total figé
        # (les sources et statuts peuvent évoluer d'une PR à l'autre).
        documentary_metrics = page.evaluate("""async () => {
            // Pages legacy héberge le corpus JS versionné, non les JSON.
            // Utiliser la même source que le runtime; JSON reste le repli Netlify.
            let corpus = window.__NOVA_COMPASS_PUBLIC_CORPORA?.evidence;
            if(!corpus){
                const response = await fetch("data/boussole-preuves-2026.json", {cache:"no-store"});
                if(!response.ok) throw new Error("Corpus de preuves indisponible");
                corpus = await response.json();
            }
            if(!Array.isArray(corpus.questions) || corpus.questions.length !== 64)
                throw new Error("Corpus de preuves incomplet");
            const statuses = corpus.questions.flatMap(q => Object.values(q.statuses || {}));
            const expected = {
                "Fiches finalisées": statuses.filter(v => v !== "unknown").length,
                "Sans direction certaine": statuses.filter(v => v === "ambiguous" || v === "contradictory").length,
                "Appuis et oppositions documentés": statuses.filter(v => v === "documented_support" || v === "documented_opposition").length
            };
            const actual = Object.fromEntries(
                Array.from(document.querySelectorAll("#compass-evidence-summary article")).map(card => [
                    card.querySelector("span").textContent.trim(),
                    Number(card.querySelector("strong").textContent.trim())
                ])
            );
            return {expected, actual};
        }""")
        for label, expected_value in documentary_metrics["expected"].items():
            assert_true(
                documentary_metrics["actual"].get(label) == expected_value,
                f"{BROWSER_NAME}: métrique documentaire incohérente pour {label}",
            )
        evidence_status = page.locator("#compass-evidence-status").inner_text()
        assert_true(
            "64/64 questions recherchées" in evidence_status,
            f"{BROWSER_NAME}: couverture de recherche exhaustive absente du statut documentaire",
        )
        assert_true(
            "avec au moins une preuve candidate" in evidence_status
            and "sans preuve candidate suffisamment exacte" in evidence_status,
            f"{BROWSER_NAME}: distinction recherche/preuve candidate absente du statut documentaire",
        )
        assert_true(
            "Une preuve révisée ne permet pas toujours de conclure à la position exacte" in evidence_status,
            f"{BROWSER_NAME}: prudence sur la conclusion politique d’une preuve absente",
        )
        assert_true(
            "L’absence de preuve candidate ne signifie pas absence de position réelle" in evidence_status,
            f"{BROWSER_NAME}: prudence sur l’absence de preuve candidate absente",
        )
        assert_true(
            "Aucun de ces nombres ne modifie le poids d’un parti" in evidence_status,
            f"{BROWSER_NAME}: avertissement anti-biais documentaire absent",
        )
        evidence_question_select = page.locator("#compass-evidence-question")
        evidence_question_select.wait_for(state="visible", timeout=10_000)
        assert_true(
            evidence_question_select.locator("option").count() == 64,
            f"{BROWSER_NAME}: l’explorateur documentaire doit proposer 64 questions",
        )
        # Les intitulés courts évitent le débordement Safari; le texte exact
        # doit rester intégralement consultable et changer avec la sélection.
        evidence_option_labels = evidence_question_select.evaluate("""select =>
            Array.from(select.options).map(option => option.textContent.trim())
        """)
        assert_true(
            len(evidence_option_labels) == 64 and max(map(len, evidence_option_labels)) < 65,
            f"{BROWSER_NAME}: menu documentaire contient des intitulés trop longs",
        )
        document_question_sync = page.evaluate("""async () => {
            let corpus = window.__NOVA_COMPASS_PUBLIC_CORPORA?.questionnaire;
            if(!corpus){
                const response = await fetch("data/boussole-electorale-v2.json", {cache:"no-store"});
                if(!response.ok) return false;
                corpus = await response.json();
            }
            const select = document.querySelector("#compass-evidence-question");
            const text = document.querySelector("#compass-evidence-selected-question");
            const first = corpus.questions.find(q => q.id === "q01");
            const second = corpus.questions.find(q => q.id === "q29");
            if(!first || !second || text?.textContent !== first.text) return false;
            select.value = "q29";
            select.dispatchEvent(new Event("change",{bubbles:true}));
            const matched = text.textContent === second.text;
            select.value = "q01";
            select.dispatchEvent(new Event("change",{bubbles:true}));
            return matched && text.textContent === first.text;
        }""")
        assert_true(
            document_question_sync,
            f"{BROWSER_NAME}: texte officiel de la proposition non synchronisé avec le menu court",
        )
        # Les liens d'accès direct et le compteur doivent suivre le corpus,
        # sans jamais supposer que q29, q30 ou une autre question restera limitée.
        mono_proof_question_ids = evidence_question_select.evaluate("""select =>
            Array.from(select.options)
                .filter(option => option.textContent.trim().endsWith(" · 1 preuve"))
                .map(option => option.value)
        """)
        priority_panel = page.locator("#compass-evidence-priorities")
        priority_buttons = page.locator("#compass-evidence-priority-links button[data-compass-priority]")
        assert_true(
            priority_buttons.count() == len(mono_proof_question_ids),
            f"{BROWSER_NAME}: raccourcis des questions à preuve unique désalignés de l'explorateur",
        )
        if mono_proof_question_ids:
            assert_true(priority_panel.is_visible(), f"{BROWSER_NAME}: questions limitées non signalées")
            assert_true(
                priority_buttons.evaluate_all(
                    "(buttons) => buttons.map(button => button.dataset.compassPriority)"
                ) == mono_proof_question_ids,
                f"{BROWSER_NAME}: raccourcis documentaires dans un ordre incorrect",
            )
            priority_buttons.first.click()
            assert_true(
                evidence_question_select.input_value() == mono_proof_question_ids[0],
                f"{BROWSER_NAME}: le raccourci ne sélectionne pas la bonne proposition",
            )
            assert_true(
                "Couverture documentaire limitée : une seule formation dispose d’une preuve finalisée" in page.locator("#compass-evidence-question-status").inner_text(),
                f"{BROWSER_NAME}: avertissement de question mono-preuve absent",
            )
        else:
            assert_true(priority_panel.is_hidden(), f"{BROWSER_NAME}: raccourcis affichés sans questions limitées")
        evidence_question_select.select_option("q01")
        evidence_question_results = page.locator("#compass-evidence-question-results")
        evidence_question_results.locator(".compass-evidence-record").first.wait_for(state="visible", timeout=10_000)
        assert_true(
            evidence_question_results.locator(".compass-evidence-record").count() == 22,
            f"{BROWSER_NAME}: les 22 formations doivent être visibles par défaut dans l’explorateur",
        )
        assert_true(
            evidence_question_results.locator(".compass-evidence-record-unknown").count() >= 1,
            f"{BROWSER_NAME}: les positions non documentées doivent rester visibles",
        )
        assert_true(
            evidence_question_results.locator('a[target="_blank"][rel*="noopener"]').count() >= 1,
            f"{BROWSER_NAME}: lien vers la source officielle absent de l’explorateur",
        )
        assert_true(
            evidence_question_results.locator("dt", has_text="Confiance").count() >= 1,
            f"{BROWSER_NAME}: niveau de confiance absent de l’explorateur",
        )
        assert_true(
            evidence_question_results.locator("dt", has_text="Vérifiée le").count() >= 1,
            f"{BROWSER_NAME}: date de vérification absente de l’explorateur",
        )
        assert_true(
            evidence_question_results.locator("dt", has_text="Deuxième révision").count() >= 1,
            f"{BROWSER_NAME}: date de seconde révision absente de l’explorateur",
        )
        assert_true(
            evidence_question_results.locator("strong", has_text="Justification du codage").count() >= 1,
            f"{BROWSER_NAME}: justification du codage absente de l’explorateur",
        )
        evidence_filter = page.locator("#compass-evidence-only-documented")
        evidence_filter.check()
        assert_true(
            evidence_question_results.locator(".compass-evidence-record-unknown").count() == 0,
            f"{BROWSER_NAME}: filtre des positions finalisées laisse des positions inconnues",
        )
        assert_true(
            1 <= evidence_question_results.locator(".compass-evidence-record").count() < 22,
            f"{BROWSER_NAME}: filtre documentaire n’a pas réduit les 22 formations",
        )
        evidence_filter.uncheck()
        assert_true(
            evidence_question_results.locator(".compass-evidence-record").count() == 22,
            f"{BROWSER_NAME}: restauration des 22 formations après filtrage impossible",
        )
        evidence_alphabetical = page.evaluate("""() => {
            const names = Array.from(document.querySelectorAll('#compass-evidence-parties .compass-evidence-card h3')).map(node => node.textContent.trim());
            const collator = new Intl.Collator('fr-CA');
            return names.every((name,index) => index === 0 || collator.compare(names[index - 1], name) <= 0);
        }""")
        assert_true(evidence_alphabetical, f"{BROWSER_NAME}: état documentaire non alphabétique")
        page.locator("#compass-start").wait_for(state="visible", timeout=10_000)
        assert_true(not page.locator("#compass-start").is_disabled(), f"{BROWSER_NAME}: démarrage Boussole indisponible")
        # Observer tout le parcours politique : aucun appel réseau vers un
        # tiers, aucun POST, beacon, PUT ou DELETE ne doit contenir les réponses.
        # Le chargement initial des corpus publics est déjà terminé.
        compass_requests = []
        if IS_LOCAL:
            page.on("request", lambda req: compass_requests.append({
                "method": req.method, "url": req.url,
            }))
        page.locator("#compass-start").click()
        page.locator("#compass-question-stage .compass-question").wait_for(state="visible", timeout=10_000)
        assert_true(
            page.evaluate(
                """() => {
                  const form = document.querySelector("#compass-form");
                  const event = new Event("submit", {bubbles: true, cancelable: true});
                  form.dispatchEvent(event);
                  return event.defaultPrevented;
                }"""
            ),
            f"{BROWSER_NAME}: la soumission clavier de la Boussole doit être interceptée sans code HTML inline",
        )
        assert_true(
            page.locator("#compass-question-stage .compass-question").count() == 1,
            f"{BROWSER_NAME}: une seule question doit être visible à la fois",
        )
        assert_true(page.locator("#compass-prev").is_disabled(), f"{BROWSER_NAME}: Précédent doit être désactivé à la question 1")
        assert_true(
            page.evaluate("""() => {
                const fieldset = document.querySelector("#compass-question-stage fieldset");
                const legend = fieldset?.querySelector("legend");
                const group = fieldset?.querySelector('[role="radiogroup"]');
                return fieldset?.firstElementChild === legend &&
                    document.activeElement === legend?.querySelector("[data-compass-question-focus]") &&
                    group?.getAttribute("aria-labelledby") === legend.id;
            }"""),
            f"{BROWSER_NAME}: titre de question non associé aux réponses ou focus absent",
        )
        assert_true(
            page.locator("#compass-progress-track").get_attribute("aria-valuenow") == "1",
            f"{BROWSER_NAME}: progression ARIA initiale incorrecte",
        )
        assert_true(page.locator("#compass-next").is_disabled(), f"{BROWSER_NAME}: Suivant doit attendre une réponse")
        page.locator('#compass-question-stage input[type="radio"]').first.check()
        assert_true(not page.locator("#compass-next").is_disabled(), f"{BROWSER_NAME}: Suivant doit s’activer après une réponse")
        page.locator("#compass-next").click()
        assert_true(
            "Question 2 sur 64" in page.locator("#compass-progress-text").inner_text(),
            f"{BROWSER_NAME}: progression guidée vers la question 2 absente",
        )
        assert_true(
            page.evaluate("""() => {
                const legend = document.querySelector("#compass-question-stage legend");
                return document.activeElement === legend?.querySelector("[data-compass-question-focus]") &&
                    legend?.parentElement?.firstElementChild === legend;
            }"""),
            f"{BROWSER_NAME}: focus clavier ou structure sémantique perdus à la question 2",
        )
        assert_true(
            page.locator("#compass-progress-track").get_attribute("aria-valuenow") == "2",
            f"{BROWSER_NAME}: progression ARIA non actualisée",
        )
        # Parcours des 64 questions en déclenchant les vrais événements de
        # réponse/changement. L'écran final doit reprendre le focus clavier.
        parcours_64_questions = page.evaluate("""() => {
            for(let i = 2; i <= 64; i++){
                const legend = document.querySelector("#compass-question-stage legend");
                const fieldset = document.querySelector("#compass-question-stage fieldset");
                if(!legend || fieldset?.firstElementChild !== legend ||
                   document.activeElement !== legend.querySelector("[data-compass-question-focus]")){
                    return {valid:false,step:i,reason:"focus ou légende perdu"};
                }
                const radio = fieldset.querySelector('input[type="radio"]');
                if(!radio) return {valid:false,step:i,reason:"réponse absente"};
                radio.click();
                document.querySelector("#compass-next").click();
            }
            const heading = document.querySelector("#compass-results-title");
            const progress = document.querySelector("#compass-progress-track");
            return {
                valid:!document.querySelector("#compass-results").hidden &&
                    document.activeElement === heading &&
                    heading.getAttribute("tabindex") === "-1" &&
                    document.querySelectorAll("#compass-results-grid .compass-result-card").length === 16 &&
                    progress.getAttribute("aria-valuenow") === "64" &&
                    progress.getAttribute("aria-valuemax") === "64",
                step:64,
                reason:"état final du questionnaire"
            };
        }""")
        assert_true(
            parcours_64_questions["valid"],
            f"{BROWSER_NAME}: parcours guidé ou focus des résultats incorrect: {parcours_64_questions}",
        )

        # Scénario navigateur distinct : 64 choix « Sans opinion » doivent
        # se terminer sans score inventé, puis revenir à zéro. Aucun POST.
        # On utilise les véritables événements DOM, sans API privée de test.
        profil_sans_opinion = page.evaluate("""() => {
            const panel = document.querySelector("#compass-start-panel");
            const stepper = document.querySelector("#compass-stepper");
            const results = document.querySelector("#compass-results");
            const reset = document.querySelector("#compass-reset");
            const start = document.querySelector("#compass-start");
            if(!panel || !stepper || !results || !reset || !start){
                return {ok:false,stage:"missing_controls"};
            }
            reset.click();
            if(panel.hidden || !stepper.hidden || !results.hidden || start.disabled){
                return {ok:false,stage:"initial_reset"};
            }
            start.click();
            let visited=0;
            for(let step=1;step<=64;step++){
                const fieldset = document.querySelector("#compass-question-stage fieldset");
                const progress = document.querySelector("#compass-progress-track");
                const skip = fieldset?.querySelector('input[type="radio"][value="skip"]');
                const next = document.querySelector("#compass-next");
                if(!skip || progress?.getAttribute("aria-valuenow")!==String(step) ||
                   !next || !next.disabled){
                    return {ok:false,stage:"question",step,visited};
                }
                skip.click();
                if(next.disabled || !skip.checked){
                    return {ok:false,stage:"skip",step,visited};
                }
                next.click();
                visited++;
            }
            const cards = [...document.querySelectorAll("#compass-results-grid .compass-result-card")];
            const summary = document.querySelector("#compass-summary")?.textContent || "";
            const radar = document.querySelector("#compass-radar");
            const noArtificialScores = cards.length===16 &&
                cards.every(card => card.querySelector("strong")?.textContent.trim()==="—") &&
                !radar?.querySelector("polygon") &&
                summary.includes("Aucune dimension calculable") &&
                !results.hidden;
            reset.click();
            const zeroed = !panel.hidden && stepper.hidden && results.hidden &&
                document.querySelector("#compass-progress-track")?.getAttribute("aria-valuenow")==="1";
            return {ok:noArtificialScores&&zeroed&&visited===64,visited,
                noArtificialScores,zeroed,summary};
        }""")
        assert_true(
            profil_sans_opinion["ok"],
            f"{BROWSER_NAME}: 64 « Sans opinion », résultats non artificiels ou réinitialisation: {profil_sans_opinion}",
        )

        # Réception du profil partiel dans le VRAI DOM : à une seule réponse,
        # aucun score et aucun marqueur. À deux questions principales du même
        # axe, exactement un score. Le contrôle sur la version locale évite
        # de présumer que le nouveau JS est déjà publié en production.
        if IS_LOCAL:
            partial_profile = page.evaluate("""() => {
                const reset = document.querySelector("#compass-reset");
                const start = document.querySelector("#compass-start");
                const next = document.querySelector("#compass-next");
                const preview = document.querySelector("#compass-preview");
                const stage = document.querySelector("#compass-question-stage");
                const results = document.querySelector("#compass-results");
                if(!reset || !start || !next || !preview || !stage || !results)
                    return {ok:false,where:"missing_controls"};
                reset.click();
                start.click();
                const first = stage.querySelector('input[type="radio"]');
                if(!first) return {ok:false,where:"q01_missing"};
                first.click();
                preview.click();
                const cardsOne = [...document.querySelectorAll("#compass-results-grid .compass-result-card")];
                const noScore = cardsOne.length===16 &&
                    cardsOne.every(card =>
                        card.querySelector("strong")?.getAttribute("aria-label")==="Score indisponible : données insuffisantes" &&
                        !card.querySelector(".compass-axis-track i")) &&
                    document.querySelector("#compass-summary")?.textContent.includes("Aucune dimension calculable") &&
                    !results.hidden;
                next.click();
                const second = stage.querySelector('input[type="radio"]');
                if(!second) return {ok:false,where:"q02_missing",noScore};
                second.click();
                preview.click();
                const cardsTwo = [...document.querySelectorAll("#compass-results-grid .compass-result-card")];
                const oneScore = cardsTwo.length===16 &&
                    cardsTwo.filter(card=>!!card.querySelector(".compass-axis-track i")).length===1 &&
                    cardsTwo.filter(card=>
                        card.querySelector("strong")?.getAttribute("aria-label")==="Score indisponible : données insuffisantes"
                    ).length===15 &&
                    document.querySelector("#compass-summary")?.textContent.includes("Profil partiel");
                reset.click();
                return {
                    ok:noScore&&oneScore&&!document.querySelector("#compass-start-panel").hidden,
                    noScore,oneScore,returnedToStart:!document.querySelector("#compass-start-panel").hidden
                };
            }""")
            assert_true(
                partial_profile["ok"],
                f"{BROWSER_NAME}: profil partiel avec 1/2 réponses, repères et accessibilité incorrects: {partial_profile}",
            )

        # Scénario de pondération sur les vrais éléments de formulaire.
        # Les 16 scores, les réponses passées et les partages restent locaux.
        # Ce contrôle est réservé au serveur de test et ne vote jamais.
        if IS_LOCAL:
            weighted_journey = page.evaluate("""() => {
                const el = selector => document.querySelector(selector);
                const reset = el("#compass-reset");
                const start = el("#compass-start");
                const next = el("#compass-next");
                const previous = el("#compass-prev");
                const preview = el("#compass-preview");
                const results = el("#compass-results");
                if (![reset, start, next, previous, preview, results].every(Boolean))
                    return {ok:false, stage:"missing_controls"};

                const score = () => el("#compass-results-grid .compass-result-card strong")?.textContent.trim();
                const markers = () => document.querySelectorAll("#compass-results-grid .compass-axis-track i").length;
                const importance = () => el("#compass-question-stage select[data-importance]");
                const choose = (value, weight) => {
                    const input = el('#compass-question-stage input[type="radio"][value="' + value + '"]');
                    const select = importance();
                    if (!input || !select) return false;
                    select.value = weight;
                    select.dispatchEvent(new Event("change", {bubbles:true}));
                    input.click();
                    return true;
                };

                reset.click();
                start.click();
                if (!choose("3", "forte")) return {ok:false, stage:"q01"};
                next.click();
                if (el("#compass-question-stage fieldset")?.dataset.questionId !== "q02" ||
                    !choose("3", "faible")) return {ok:false, stage:"q02"};
                preview.click();
                // q01 et q02 ont des directions opposées :
                // (3*1,5 - 3*0,5) / (3*(1,5+0,5)) = +50.
                const weighted = score() === "+50" && markers() === 1 &&
                    el("#compass-summary")?.textContent.includes("Profil partiel") && !results.hidden;

                const control = importance();
                control.focus();
                control.value = "forte";
                control.dispatchEvent(new Event("change", {bubbles:true}));
                const liveUpdate = score() === "0" && markers() === 1 &&
                    document.activeElement === control &&
                    el("#compass-status")?.textContent.includes("actualisés localement");

                previous.click();
                const back = el("#compass-question-stage fieldset")?.dataset.questionId === "q01" &&
                    importance()?.value === "forte";
                if (!choose("skip", "normal")) return {ok:false, stage:"skip"};
                const skipped = score() === "—" && markers() === 0 &&
                    el("#compass-results-grid .compass-result-card strong")
                      ?.getAttribute("aria-label") === "Score indisponible : données insuffisantes";
                if (!choose("3", "faible")) return {ok:false, stage:"restore"};
                // q01 faible et q02 forte : le score est maintenant -50.
                const restored = score() === "-50" && markers() === 1;

                reset.click();
                start.click();
                const cleared = results.hidden && next.disabled &&
                    importance()?.value === "normal" &&
                    document.querySelectorAll("#compass-question-stage input[type='radio']:checked").length === 0 &&
                    el("#compass-progress-track")?.getAttribute("aria-valuenow") === "1";
                reset.click();

                return {ok:weighted && liveUpdate && back && skipped && restored && cleared,
                    weighted, liveUpdate, back, skipped, restored, cleared};
            }""")
            assert_true(
                weighted_journey["ok"],
                f"{BROWSER_NAME}: pondération, modification en direct, retour, sans opinion, reprise ou remise à zéro incorrects: {weighted_journey}",
            )

        # Sécurité du partage : aucun jeton en query/fragment et aucun
        # appel aux plateformes. Le partage natif et le presse-papiers sont
        # remplacés par des doubles de test, uniquement sur le serveur local.
        if IS_LOCAL:
            sharing_journey = page.evaluate("""async () => {
                const get = id => document.getElementById(id);
                const reset = get("compass-reset");
                const start = get("compass-start");
                const next = get("compass-next");
                const preview = get("compass-preview");
                const origin = window.location.href.split(/[?#]/,1)[0];
                const canary = "JETON_PRIVE_FICTIF_12345";
                const failures = [];
                const check = (condition,label) => {if (!condition) failures.push(label);};
                // Simuler un URL porteur de données confidentielles.
                history.replaceState(null,"",location.pathname+"?jeton="+canary+"#fragment-prive");
                reset.click();
                start.click();
                get("compass-question-stage").querySelector('input[type="radio"][value="3"]')?.click();
                next.click();
                get("compass-question-stage").querySelector('input[type="radio"][value="-3"]')?.click();
                preview.click();
                const ids=["compass-share-email","compass-share-facebook","compass-share-x","compass-share-linkedin"];
                const links=()=>ids.map(id=>get(id)?.href||"");
                const initialLinks=links();
                check(initialLinks.length===4&&initialLinks.every(href=>href.includes(encodeURIComponent(origin)) ||
                  href.includes(origin)), "liens canoniques manquants");
                check(initialLinks.every(href=>!decodeURIComponent(href).includes(canary) &&
                  !decodeURIComponent(href).includes("fragment-prive")), "fuite du jeton dans les liens");
                const initialEmail=decodeURIComponent(get("compass-share-email").href);
                check(initialEmail.includes("+100"), "résumé pondéré initial manquant");

                const email=get("compass-email-recipient");
                email.value="adresse-test@example.invalid";
                email.dispatchEvent(new Event("input",{bubbles:true}));
                check(decodeURIComponent(get("compass-share-email").href)
                  .startsWith("mailto:adresse-test@example.invalid?"), "destinataire de test non ajouté");

                let nativePayload=null;
                let clipboardPayload=null;
                Object.defineProperty(navigator,"share",{configurable:true,value:async payload=>{nativePayload=payload;}});
                Object.defineProperty(navigator,"clipboard",{configurable:true,value:{
                  writeText:async value=>{clipboardPayload=value;}
                }});
                await get("compass-share-native").onclick();
                check(nativePayload?.url===origin &&
                  !JSON.stringify(nativePayload).includes(canary) &&
                  !JSON.stringify(nativePayload).includes("fragment-prive"),"partage natif non canonique");
                await get("compass-copy-result").onclick();
                check(clipboardPayload?.includes(origin) &&
                  clipboardPayload?.includes("+100") &&
                  !clipboardPayload?.includes(canary), "copie initiale incomplète");

                const before=get("compass-share-email").href;
                const input=get("compass-question-stage").querySelector('input[type="radio"][value="3"]');
                input?.click();  // q02 passe de -3 à +3 : score +100 -> 0
                const updated=decodeURIComponent(get("compass-share-email").href);
                check(get("compass-results-grid").querySelector("strong")?.textContent.trim()==="0",
                  "score non recalculé");
                check(before!==get("compass-share-email").href &&
                  updated.includes("Équilibre") &&
                  !updated.includes("+100"),"courriel périmé après modification");
                clipboardPayload=null;
                await get("compass-copy-result").onclick();
                check(clipboardPayload?.includes("Équilibre") &&
                  !clipboardPayload?.includes("+100") &&
                  !clipboardPayload?.includes(canary),"presse-papiers périmé");
                // Refus d'autorisation : ne jamais annoncer une copie réussie.
                Object.defineProperty(navigator,"clipboard",{configurable:true,value:{
                  writeText:async () => {throw new Error("NotAllowedError");}
                }});
                await get("compass-copy-result").onclick();
                check(get("compass-status")?.textContent.includes("Copie impossible"),
                  "copie refusée annoncée comme réussie");
                Object.defineProperty(navigator,"share",{configurable:true,value:undefined});
                await get("compass-share-native").onclick();
                check(get("compass-status")?.textContent.includes("Copie impossible"),
                  "partage de repli annoncé comme réussi malgré un refus");
                // Vieux navigateurs sans API Clipboard : execCommand(false)
                // doit signaler l'échec et supprimer le textarea temporaire.
                Object.defineProperty(navigator,"clipboard",{configurable:true,value:undefined});
                const oldExec=document.execCommand;
                const oldTextareas=document.querySelectorAll("textarea").length;
                document.execCommand=()=>false;
                try{
                    await get("compass-copy-result").onclick();
                    check(get("compass-status")?.textContent.includes("Copie impossible") &&
                      document.querySelectorAll("textarea").length===oldTextareas,
                      "repli clipboard faux-positif ou élément temporaire conservé");
                }finally{
                    document.execCommand=oldExec;
                }
                const clean=history.state;
                history.replaceState(clean,"",origin);
                reset.click();
                return {ok:failures.length===0,failures,channels:ids.length,
                    nativeShareMocked:!!nativePayload,clipboardMocked:!!clipboardPayload};
            }""")
            assert_true(
                sharing_journey["ok"],
                f"{BROWSER_NAME}: fuite de confidentialité, résultat périmé ou erreur de partage: {sharing_journey}",
            )

        if IS_LOCAL:
            site_host = urlparse(BASE_URL).hostname
            unexpected_compass_requests = [
                request for request in compass_requests
                if request["method"].upper() != "GET"
                or (
                    urlparse(request["url"]).scheme in ("http", "https")
                    and urlparse(request["url"]).hostname != site_host
                )
            ]
            assert_true(
                not unexpected_compass_requests,
                f"{BROWSER_NAME}: le parcours Boussole a déclenché un transfert "
                f"de données ou un appel réseau tiers: {unexpected_compass_requests}",
            )

        home_text = page.locator("main").inner_text().lower()
        for retired_name in ("lumina", "futurax", "chroniques de l’ombre", "chroniques de l'ombre"):
            assert_true(retired_name not in home_text, f"Accueil: univers secondaire remis au premier plan: {retired_name}")

        assert_true(
            page.evaluate("CSS && CSS.supports && CSS.supports('display', 'grid')"),
            f"{BROWSER_NAME}: CSS Grid indisponible dans le moteur testé",
        )

        page.goto(urljoin(BASE_URL, "contact.html"), wait_until="domcontentloaded", timeout=30_000)
        project = page.locator("#contact-project")
        form = page.locator("#contact-general")
        route = page.locator("#contact-route")
        submit = page.locator("#contact-submit")
        preview = page.locator("#contact-preview")
        assert_true(preview.count() == 1 and preview.get_attribute("open") is None,
                    f"{BROWSER_NAME}: l’aperçu désactivé encombre la page Contact")
        preview.locator("summary").click()
        assert_true(preview.get_attribute("open") is not None,
                    f"{BROWSER_NAME}: l’aperçu contact ne s’ouvre pas au clic")
        assert_true(project.locator('option[value="Projet Nova"]').count() == 0, f"{BROWSER_NAME}: Projet Nova encore routé par le formulaire personnel")
        personal_fields = page.locator("#contact-personal-fields")
        assert_true(
            personal_fields.count() == 1 and personal_fields.get_attribute("disabled") is not None,
            f"{BROWSER_NAME}: champs de contact personnel non verrouillés",
        )
        for selector in ("#contact-name", "#contact-email", "#contact-project", "#contact-message", 'input[name="consentement_contact"]'):
            assert_true(page.locator(selector).is_disabled(), f"{BROWSER_NAME}: saisie personnelle encore active: {selector}")
        assert_true(
            page.locator('a[href="/projets/projet-nova/contact.html"]').count() >= 1
            and page.locator('a[href="/compte/vie-privee.html"]').count() >= 1,
            f"{BROWSER_NAME}: un des deux parcours de contact disponibles est absent",
        )
        # Ne dépend pas d'un submit visible : forcer un événement submit dans
        # le navigateur confirme que le script l'annule aussi au clavier/API.
        personal_submit_blocked = page.evaluate("""() => {
            const form = document.querySelector("#contact-general");
            const event = new Event("submit", {bubbles:true, cancelable:true});
            return form.dispatchEvent(event) === false && event.defaultPrevented;
        }""")
        assert_true(personal_submit_blocked, f"{BROWSER_NAME}: soumission personnelle non bloquée par le script")
        assert_true(
            page.evaluate('new FormData(document.querySelector("#contact-general")).entries().next().done'),
            f"{BROWSER_NAME}: des données de formulaire personnel restent sérialisables malgré le verrouillage",
        )
        assert_true(
            "?" not in urlparse(page.url).path and not urlparse(page.url).query,
            f"{BROWSER_NAME}: le formulaire personnel a produit une URL avec paramètres",
        )
        assert_true(form.get_attribute("action") is None, f"{BROWSER_NAME}: endpoint personnel actif avant configuration")
        assert_true(form.get_attribute("method") is None, f"{BROWSER_NAME}: POST personnel actif avant configuration")
        assert_true(form.get_attribute("data-personal-formspree-state") == "pending-separate-endpoint", f"{BROWSER_NAME}: état fail-closed Formspree absent")
        assert_true(
            page.locator('script[src="/assets/js/sinjira-contact-route-v1.js?v=1.0.0"]').count() == 1,
            f"{BROWSER_NAME}: runtime externe de verrouillage du contact personnel absent",
        )
        assert_true(submit.is_disabled(), f"{BROWSER_NAME}: bouton personnel actif avant endpoint distinct")
        assert_true("désactivé" in route.inner_text().lower(), f"{BROWSER_NAME}: message fail-closed absent")
        assert_true(page.locator('a[href="/projets/projet-nova/contact.html"]').count() >= 1, f"{BROWSER_NAME}: lien contact officiel Nova absent")
        contact_html = page.content().lower()
        assert_true("formspree.io/f/xdenkzrv" not in contact_html, f"{BROWSER_NAME}: ancien endpoint personnel encore exposé")
        assert_true("formspree.io/f/xkolwjdg" not in contact_html, f"{BROWSER_NAME}: endpoint Nova encore exposé dans le contact personnel")
        assert_true("kingtyrano@gmail.com" not in contact_html, "Adresse privée embarquée dans le formulaire de contact")
        page.goto(urljoin(BASE_URL, "projets/projet-nova/contact.html"), wait_until="domcontentloaded", timeout=30_000)
        assert_true(
            page.locator('a[href="mailto:officiellenovaparti@gmail.com"]').count() >= 1,
            f"{BROWSER_NAME}: courriel officiel Nova non accessible",
        )
        assert_true(
            page.locator('a[href="../../contact.html"]').count() == 1
            and page.locator('a[href="../../compte/vie-privee.html"]').count() == 1,
            f"{BROWSER_NAME}: liens vers le portail personnel et le Centre Vie privée absents de Nova",
        )
        assert_true(
            page.locator("main form").count() == 0
            and page.locator('form[action*="formspree.io"]').count() == 0,
            f"{BROWSER_NAME}: un formulaire de collecte ou un endpoint Formspree apparaît dans le contact Nova",
        )

        if IS_LOCAL:
            for auth_route in AUTH_ROUTES:
                auth_url = urljoin(BASE_URL, auth_route)
                response = page.goto(auth_url, wait_until="domcontentloaded", timeout=30_000)
                assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: page Auth inaccessible: {auth_route}")
                assert_true(page.locator("main#main-content").count() == 1, f"{BROWSER_NAME}: main Auth accessible absent: {auth_route}")
                assert_true(page.locator("h1").count() == 1, f"{BROWSER_NAME}: H1 Auth invalide: {auth_route}")
                assert_true(page.locator('a.skip-link[href="#main-content"]').count() == 1, f"{BROWSER_NAME}: lien d'évitement Auth absent: {auth_route}")
                assert_true(page.locator('[data-account-status]').count() == 1, f"{BROWSER_NAME}: zone de statut Auth absente: {auth_route}")
                robots = page.locator('meta[name="robots"]').get_attribute("content") or ""
                assert_true("noindex" in robots.lower(), f"{BROWSER_NAME}: page Auth indexable: {auth_route}")
                assert_true(bool(page.title().strip()), f"{BROWSER_NAME}: titre Auth absent: {auth_route}")

            page.goto(urljoin(BASE_URL, "compte/inscription.html"), wait_until="domcontentloaded", timeout=30_000)
            assert_true(page.locator('input[type="password"][minlength="12"]').count() == 2, f"{BROWSER_NAME}: politique 12 caractères incohérente à l'inscription")

            # Ergonomie du compte : la révélation reste volontaire, le type
            # password revient après Masquer, et aucun envoi n'est effectué.
            page.wait_for_function(
                "() => document.querySelectorAll('[data-password-visibility]').length === 2",
                timeout=10_000,
            )
            pwd_toggles = page.locator('[data-password-visibility]')
            assert_true(pwd_toggles.count() == 2, f"{BROWSER_NAME}: boutons afficher/masquer absents à l'inscription")
            pwd_toggles.first.click()
            assert_true(
                page.locator('#signup-password').get_attribute('type') == 'text'
                and pwd_toggles.first.get_attribute('aria-pressed') == 'true',
                f"{BROWSER_NAME}: affichage accessible du mot de passe inopérant",
            )
            pwd_toggles.first.click()
            assert_true(
                page.locator('#signup-password').get_attribute('type') == 'password'
                and pwd_toggles.first.get_attribute('aria-pressed') == 'false',
                f"{BROWSER_NAME}: masquage du mot de passe inopérant",
            )
            signup_optional = page.locator('[data-optional-personal-info]')
            assert_true(
                signup_optional.count() == 1 and signup_optional.get_attribute('open') is None,
                f"{BROWSER_NAME}: section facultative de l'inscription initialement ouverte",
            )
            signup_optional.locator('summary').click()
            assert_true(
                signup_optional.get_attribute('open') is not None
                and page.locator('#signup-extra-origin_city').is_visible(),
                f"{BROWSER_NAME}: champs complémentaires non accessibles au toucher",
            )
            assert_true(
                page.locator('#signup-birth-date').is_visible()
                and page.locator('#signup-gender').is_visible(),
                f"{BROWSER_NAME}: contrôles d'âge obligatoires masqués",
            )
            page.goto(urljoin(BASE_URL, "compte/connexion.html"), wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_function(
                "() => document.querySelectorAll('[data-password-visibility]').length === 1",
                timeout=10_000,
            )
            login_toggle = page.locator('[data-password-visibility]')
            assert_true(login_toggle.count() == 1, f"{BROWSER_NAME}: visibilité du mot de passe de connexion absente")
            login_toggle.click()
            assert_true(page.locator('#login-password').get_attribute('type') == 'text',
                        f"{BROWSER_NAME}: mot de passe de connexion non affiché après commande")
            login_toggle.click()
            assert_true(page.locator('#login-password').get_attribute('type') == 'password',
                        f"{BROWSER_NAME}: mot de passe de connexion non masqué après commande")

            page.goto(urljoin(BASE_URL, "compte/reinitialiser-mot-de-passe.html"), wait_until="domcontentloaded", timeout=30_000)
            assert_true(page.locator('input[type="password"][minlength="12"]').count() == 2, f"{BROWSER_NAME}: politique 12 caractères incohérente à la réinitialisation")

            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(500)
            assert_true(
                page.evaluate("typeof window.__SINJIRA_ASSISTANT__ === 'undefined'"),
                f"{BROWSER_NAME}: assistant chargé malgré sa désactivation sur l’accueil",
            )
            assert_true(
                page.locator(".sinjira-assistant-toggle").count() == 0,
                f"{BROWSER_NAME}: bouton assistant présent sur l’accueil désactivé",
            )

            page.goto(urljoin(BASE_URL, "projets/sinjira/"), wait_until="domcontentloaded", timeout=30_000)
            wait_for_assistant(page)
            assistant = page.evaluate("window.__SINJIRA_ASSISTANT__")
            assert_true(assistant.get("providerMode") == "local", f"{BROWSER_NAME}: assistant non local")
            assert_true(assistant.get("externalProviderEnabled") is False, f"{BROWSER_NAME}: fournisseur externe activé")
            assert_true(assistant.get("privacy") == "ephemeral-memory-only", f"{BROWSER_NAME}: contrat de confidentialité assistant invalide")
            assert_true(assistant.get("contextLabel") == "Portail SINJIRA™", f"{BROWSER_NAME}: contexte SINJIRA assistant invalide")
            assert_true(int(assistant.get("intentCount") or 0) >= 20, f"{BROWSER_NAME}: base d’aide assistant trop limitée")
            suggestions = page.locator(".sinjira-assistant-chip").all_text_contents()
            assert_true(suggestions == ["Lire les romans", "Découvrir les jeux", "Créer mon personnage"],
                        f"{BROWSER_NAME}: les suggestions du portail SINJIRA doivent aider à naviguer : {suggestions}")
            assert_true("Projet Nova" not in page.locator(".sinjira-assistant-suggestions").inner_text(),
                        f"{BROWSER_NAME}: une archive ne doit plus être promue sur le portail SINJIRA")

            assistant_toggle = page.locator(".sinjira-assistant-toggle")
            assert_true(assistant_toggle.count() == 1, f"{BROWSER_NAME}: bouton Aide IA absent")
            assistant_toggle.click()
            panel = page.locator("#sinjira-assistant-panel")
            assert_true(panel.is_visible(), f"{BROWSER_NAME}: panneau assistant ne s’ouvre pas")
            assert_true(assistant_toggle.get_attribute("aria-expanded") == "true", f"{BROWSER_NAME}: aria-expanded assistant invalide")
            assert_true(
                assistant_toggle.evaluate("(el) => getComputedStyle(el).visibility === 'hidden'"),
                f"{BROWSER_NAME}: commande d'ouverture invisible encore focusable dans le panneau",
            )
            assert_true(
                page.locator("#sinjira-assistant-input").evaluate("(el) => document.activeElement === el"),
                f"{BROWSER_NAME}: le focus n'arrive pas directement dans le panneau d'aide",
            )

            question = page.locator("#sinjira-assistant-input")
            question.fill("Comment créer mon personnage ?")
            question.press("Enter")
            log_text = page.locator(".sinjira-assistant-log").inner_text().lower()
            assert_true("registre des consciences" in log_text, f"{BROWSER_NAME}: réponse Registre absente")
            assert_true(page.locator('.sinjira-assistant-link[href="/projets/sinjira/registre/"]').count() >= 1, f"{BROWSER_NAME}: lien Registre assistant absent")

            page.wait_for_timeout(400)
            question.fill("Résistant ou Réseau-Mère")
            question.press("Enter")
            log_text = page.locator(".sinjira-assistant-log").inner_text().lower()
            assert_true("seule votre propre identité" in log_text, f"{BROWSER_NAME}: garde-fou identité Fracture absent")

            page.wait_for_timeout(400)
            question.fill("Mon questionnaire est enregistré mais la notification n’a pas été envoyée")
            question.press("Enter")
            log_text = page.locator(".sinjira-assistant-log").inner_text().lower()
            assert_true("sans annuler le dossier" in log_text, f"{BROWSER_NAME}: dépannage notification Registre absent")

            page.wait_for_timeout(400)
            question.fill("Mon compte reste bloqué en synchronisation")
            question.press("Enter")
            log_text = page.locator(".sinjira-assistant-log").inner_text().lower()
            assert_true("session est toujours connectée" in log_text, f"{BROWSER_NAME}: dépannage synchronisation absent")

            page.wait_for_timeout(400)
            question.fill("voici mon mot de passe est test-seulement")
            question.press("Enter")
            log_text = page.locator(".sinjira-assistant-log").inner_text().lower()
            assert_true("n’envoyez pas de mot de passe" in log_text or "n'envoyez pas de mot de passe" in log_text, f"{BROWSER_NAME}: garde-fou secret assistant absent")

            page.keyboard.press("Escape")
            assert_true(panel.is_hidden(), f"{BROWSER_NAME}: Escape ne ferme pas l’assistant")
            assert_true(
                assistant_toggle.evaluate(
                    "(el) => getComputedStyle(el).visibility === 'visible' && document.activeElement === el"
                ),
                f"{BROWSER_NAME}: le focus ne revient pas au bouton visible après Échap",
            )
            # Le déclencheur reste accessible au clavier après fermeture, et
            # la commande Fermer doit rendre le focus au même endroit.
            assistant_toggle.press("Enter")
            assert_true(panel.is_visible(), f"{BROWSER_NAME}: réouverture clavier impossible")
            assert_true(
                assistant_toggle.evaluate("(el) => getComputedStyle(el).visibility === 'hidden'"),
                f"{BROWSER_NAME}: bouton masqué toujours focusable après réouverture",
            )
            panel.locator(".sinjira-assistant-close").click()
            assert_true(panel.is_hidden(), f"{BROWSER_NAME}: bouton Fermer inopérant")
            assert_true(
                assistant_toggle.evaluate("(el) => document.activeElement === el"),
                f"{BROWSER_NAME}: Fermer ne restitue pas le focus au déclencheur",
            )

            # Les suggestions doivent suivre la rubrique courante, y compris
            # la page du jeu Fracture. L'archive Nova reste accessible seulement
            # par demande explicite ou par sa propre route.
            page.goto(urljoin(BASE_URL, "projets/sinjira/jeux/"), wait_until="domcontentloaded", timeout=30_000)
            wait_for_assistant(page)
            assert_true(page.evaluate("window.__SINJIRA_ASSISTANT__.contextLabel") == "Jeux SINJIRA™",
                        f"{BROWSER_NAME}: contexte assistant Jeux incorrect")
            assert_true(page.locator(".sinjira-assistant-chip").all_text_contents() ==
                        ["Voir les jeux", "Mes parties", "Fracture"],
                        f"{BROWSER_NAME}: accès rapides jeux manquants")
            page.goto(urljoin(BASE_URL, "projets/sinjira/jeux/fracture-du-reseau-mere/"),
                      wait_until="domcontentloaded", timeout=30_000)
            wait_for_assistant(page)
            assert_true(page.evaluate("window.__SINJIRA_ASSISTANT__.contextLabel") == "Fracture du Réseau-Mère",
                        f"{BROWSER_NAME}: aide contextuelle Fracture absente")
            assert_true("Projet Nova" not in page.locator(".sinjira-assistant-suggestions").inner_text(),
                        f"{BROWSER_NAME}: promotion Nova présente sur une page Jeux")

            # Le Registre SINJIRA est désormais progressif, sans persistance
            # locale des réponses. Les tests restent anonymes et ne soumettent
            # jamais le questionnaire ni ne manipulent un compte privé.
            page.goto(urljoin(BASE_URL, "projets/sinjira/registre/"), wait_until="domcontentloaded", timeout=30_000)
            wizard = page.locator("[data-registry-wizard]")
            wizard.wait_for(state="visible", timeout=10_000)
            assert_true(
                page.locator('form[data-character-form] fieldset[data-registry-wizard-step]').count() == 9,
                f"{BROWSER_NAME}: le Registre doit contenir neuf étapes",
            )
            assert_true(
                "Étape 1 sur 9" in wizard.locator(".registry-wizard-step").inner_text(),
                f"{BROWSER_NAME}: progression du Registre absente",
            )
            assert_true(
                page.locator('fieldset[data-registry-wizard-step="2"]').is_hidden(),
                f"{BROWSER_NAME}: les champs de l'étape suivante sont visibles prématurément",
            )
            assert_true(
                page.locator('form[data-character-form] button[type="submit"]').is_hidden(),
                f"{BROWSER_NAME}: envoi accessible avant l'écran de consentement",
            )
            page.locator('[data-registry-wizard-next]').click()
            assert_true(
                "Étape 2 sur 9" in wizard.locator(".registry-wizard-step").inner_text(),
                f"{BROWSER_NAME}: passage à l'étape 2 impossible",
            )
            # L'apparence (étape 2) est facultative; la personnalité
            # (étape 3) contient huit réponses obligatoires.
            page.locator('[data-registry-wizard-next]').click()
            assert_true(
                "Étape 3 sur 9" in wizard.locator(".registry-wizard-step").inner_text(),
                f"{BROWSER_NAME}: l'apparence facultative ne doit pas bloquer la progression",
            )
            page.locator('[data-registry-wizard-next]').click()
            assert_true(
                "Étape 3 sur 9" in wizard.locator(".registry-wizard-step").inner_text()
                and page.locator('[data-registry-wizard-error]').is_visible(),
                f"{BROWSER_NAME}: le Registre doit bloquer une étape requise incomplète",
            )
            page.locator('[data-registry-wizard-back]').click()
            page.locator('[data-registry-wizard-back]').click()
            assert_true(
                "Étape 1 sur 9" in wizard.locator(".registry-wizard-step").inner_text(),
                f"{BROWSER_NAME}: retour en arrière du Registre impossible",
            )
            assert_true(
                page.locator('label[for="registry-pseudo"]').count() == 1
                and page.locator('label[for="registry-email"]').count() == 1,
                f"{BROWSER_NAME}: labels du compte Registre non associés",
            )
            # Un submit synthétique avant la dernière étape ne doit atteindre
            # aucun listener métier; il ne réalise aucun envoi réseau.
            blocked_early_submit = page.evaluate("""() => {
                const form = document.querySelector('[data-character-form]');
                let reachedBusiness = false;
                const observer = () => { reachedBusiness = true; };
                form.addEventListener('submit', observer);
                const event = new Event('submit', {bubbles: true, cancelable: true});
                form.dispatchEvent(event);
                form.removeEventListener('submit', observer);
                return event.defaultPrevented && !reachedBusiness;
            }""")
            assert_true(
                blocked_early_submit,
                f"{BROWSER_NAME}: soumission prématurée du Registre non interceptée",
            )
            page.locator('[data-registry-wizard-back]').click()
            wait_for_assistant(page)
            assert_true(page.evaluate("window.__SINJIRA_ASSISTANT__.contextLabel") == "Registre des Consciences", f"{BROWSER_NAME}: contexte Registre invalide")
            page.locator(".sinjira-assistant-toggle").click()
            page.locator("#sinjira-assistant-input").fill("Que puis-je faire sur cette page ?")
            page.locator("#sinjira-assistant-input").press("Enter")
            assert_true("base humaine" in page.locator(".sinjira-assistant-log").inner_text().lower(), f"{BROWSER_NAME}: aide contextuelle Registre absente")

            page.goto(urljoin(BASE_URL, "projets/projet-nova/"), wait_until="domcontentloaded", timeout=30_000)
            wait_for_assistant(page)
            assert_true(page.locator(".sinjira-assistant-toggle").count() == 1, f"{BROWSER_NAME}: assistant absent de Projet Nova")
            assert_true(page.evaluate("window.__SINJIRA_ASSISTANT__.contextLabel") == "Projet Nova", f"{BROWSER_NAME}: contexte Projet Nova invalide")

        if IS_LOCAL:
            # Simuler la panne des JSON en forçant le chemin de secours :
            # en production le corpus JS versionné est normalement prioritaire.
            # Sans neutraliser ce bundle dans le test, le routage des JSON ne
            # serait jamais utilisé et les boutons de reprise resteraient cachés.
            retry_context = browser.new_context(
                locale="fr-CA",
                viewport={"width": 1440, "height": 1000},
                reduced_motion="reduce",
                service_workers="block",
            )
            retry_page = retry_context.new_page()
            retry_page_errors = []
            register_error_capture(retry_page, retry_page_errors)
            corpus_pattern = "**/boussole-electorale-v2.json"
            rejected_requests = []

            def reject_compass_corpus(route):
                rejected_requests.append(route.request.url)
                route.fulfill(status=503, content_type="application/json", body="{}")

            retry_page.route(
                "**/assets/boussole-public-corpus.js*",
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/javascript",
                    body="window.__NOVA_COMPASS_PUBLIC_CORPORA = null;",
                ),
            )
            retry_page.route(corpus_pattern, reject_compass_corpus)
            retry_page.goto(
                urljoin(BASE_URL, "projets/projet-nova/boussole-electorale.html"),
                wait_until="domcontentloaded",
                timeout=30_000,
            )
            retry_questionnaire = retry_page.locator("#compass-questionnaire-retry")
            retry_documentary = retry_page.locator("#compass-evidence-retry")
            retry_questionnaire.wait_for(state="visible", timeout=10_000)
            assert_true(
                len(rejected_requests) >= 2,
                f"{BROWSER_NAME}: la panne simulée n’intercepte pas les deux chargements JSON",
            )
            retry_documentary.wait_for(state="visible", timeout=10_000)
            assert_true(
                retry_page.locator("#compass-start").is_disabled(),
                f"{BROWSER_NAME}: questionnaire démarrable malgré son corpus indisponible",
            )
            assert_true(
                "Échec du chargement documentaire" in retry_page.locator("#compass-evidence-status").inner_text(),
                f"{BROWSER_NAME}: erreur documentaire non annoncée",
            )
            retry_page.unroute(corpus_pattern, reject_compass_corpus)
            retry_questionnaire.click()
            retry_page.wait_for_function(
                "() => !document.querySelector('#compass-start').disabled",
                timeout=10_000,
            )
            assert_true(
                retry_questionnaire.is_hidden(),
                f"{BROWSER_NAME}: bouton de reprise questionnaire toujours visible après succès",
            )
            retry_documentary.click()
            retry_page.locator("#compass-evidence-parties .compass-evidence-card").first.wait_for(
                state="visible", timeout=10_000
            )
            assert_true(
                retry_page.locator("#compass-evidence-parties .compass-evidence-card").count() == 22,
                f"{BROWSER_NAME}: registre non restauré après une panne temporaire",
            )
            assert_true(
                retry_page.locator("#compass-evidence-summary article").count() == 9,
                f"{BROWSER_NAME}: métriques documentaires non restaurées",
            )
            assert_true(
                retry_documentary.is_hidden(),
                f"{BROWSER_NAME}: bouton de reprise documentaire toujours visible après succès",
            )
            assert_true(
                not retry_page_errors,
                f"{BROWSER_NAME}: exception après reprise du chargement: " + " | ".join(retry_page_errors[:3]),
            )
            retry_context.close()

            # Une mise en ligne partielle ne doit jamais associer des preuves
            # révisées à la mauvaise formulation des 64 propositions.
            mismatch_context = browser.new_context(
                locale="fr-CA",
                viewport={"width": 1440, "height": 1000},
                service_workers="block",
            )
            mismatch_page = mismatch_context.new_page()
            mismatch_errors = []
            register_error_capture(mismatch_page, mismatch_errors)
            mismatch_pattern = "**/boussole-preuves-2026.json"
            altered_requests = []

            def corrupt_evidence_binding(route):
                upstream = route.fetch()
                payload = json.loads(upstream.body())
                payload["questionnaireBinding"]["questionTexts"]["q29"] += " VERSION DÉCALÉE"
                altered_requests.append(route.request.url)
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(payload, ensure_ascii=False),
                )

            mismatch_page.route(
                "**/assets/boussole-public-corpus.js*",
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/javascript",
                    body="window.__NOVA_COMPASS_PUBLIC_CORPORA = null;",
                ),
            )
            mismatch_page.route(mismatch_pattern, corrupt_evidence_binding)
            mismatch_page.goto(
                urljoin(BASE_URL, "projets/projet-nova/boussole-electorale.html"),
                wait_until="domcontentloaded",
                timeout=30_000,
            )
            mismatch_retry = mismatch_page.locator("#compass-evidence-retry")
            mismatch_retry.wait_for(state="visible", timeout=10_000)
            assert_true(altered_requests, f"{BROWSER_NAME}: version documentaire simulée non interceptée")
            assert_true(
                mismatch_page.locator("#compass-evidence-parties .compass-evidence-card").count() == 0,
                f"{BROWSER_NAME}: des positions ont été affichées malgré un décalage sémantique",
            )
            assert_true(
                mismatch_page.locator("#compass-start").is_enabled(),
                f"{BROWSER_NAME}: la panne documentaire bloque incorrectement le questionnaire local valide",
            )
            assert_true(
                mismatch_page.locator("#compass-evidence-status").inner_text().startswith(
                    "Échec du chargement documentaire"
                ),
                f"{BROWSER_NAME}: incompatibilité documentaire non annoncée",
            )
            mismatch_page.unroute(mismatch_pattern, corrupt_evidence_binding)
            mismatch_retry.click()
            mismatch_page.locator("#compass-evidence-parties .compass-evidence-card").first.wait_for(
                state="visible", timeout=10_000
            )
            assert_true(
                mismatch_page.locator("#compass-evidence-parties .compass-evidence-card").count() == 22,
                f"{BROWSER_NAME}: récupération des preuves synchronisées impossible",
            )
            assert_true(mismatch_retry.is_hidden(), f"{BROWSER_NAME}: reprise documentaire encore visible")
            assert_true(not mismatch_errors, f"{BROWSER_NAME}: erreur JS lors du contrôle d'intégrité")
            mismatch_context.close()

        mobile = browser.new_context(
            locale="fr-CA",
            viewport={"width": 390, "height": 844},
            has_touch=True,
            reduced_motion="reduce",
            service_workers="block",
        )
        mobile.route("**/functions/v1/nova-civic-poll*", serve_closed_poll_snapshot)
        mobile_page = mobile.new_page()
        mobile_errors = []
        register_error_capture(mobile_page, mobile_errors)
        response = mobile_page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: accueil mobile inaccessible")

        # Contrôler l'état initial ET l'état après les ressources tardives, sans
        # relancer ou masquer une anomalie. Ne journaliser ni texte ni données personnelles.
        def assert_mobile_reflow(stage):
            geometry = mobile_page.evaluate("""() => {
                const root = document.documentElement;
                const width = innerWidth;
                return {
                  width, scrollWidth: root.scrollWidth,
                  offenders: [...document.querySelectorAll('body *')].filter(el => {
                    const r = el.getBoundingClientRect();
                    return r.width > 0 && (r.right > width + 2 || r.left < -2)
                      && getComputedStyle(el).position !== 'fixed';
                  }).slice(0, 12).map(el => ({
                    tag: el.tagName, id: el.id, className: typeof el.className === 'string' ? el.className : '',
                    left: Math.round(el.getBoundingClientRect().left),
                    right: Math.round(el.getBoundingClientRect().right)
                  }))
                };
            }""")
            assert_true(geometry["scrollWidth"] <= geometry["width"] + 2,
                        f"{BROWSER_NAME}: débordement horizontal à 390 px ({stage}): {geometry}")
        assert_mobile_reflow("DOMContentLoaded")
        mobile_page.wait_for_load_state("load", timeout=30_000)
        assert_mobile_reflow("load")

        toggle = mobile_page.locator("[data-menu-toggle]")
        assert_true(toggle.count() == 1, f"{BROWSER_NAME}: bouton de menu mobile absent")
        toggle.click()
        assert_true(toggle.get_attribute("aria-expanded") == "true", f"{BROWSER_NAME}: menu mobile n’annonce pas son état ouvert")
        assert_true(
            toggle.get_attribute("aria-label") == "Fermer le menu",
            f"{BROWSER_NAME}: titre accessible incorrect quand le menu est ouvert",
        )
        mobile_nav = mobile_page.locator("[data-main-nav]")
        nav_class = mobile_nav.get_attribute("class") or ""
        assert_true("open" in nav_class.split(), f"{BROWSER_NAME}: menu mobile ne s’ouvre pas")
        toggle.click()
        assert_true(toggle.get_attribute("aria-expanded") == "false", f"{BROWSER_NAME}: menu mobile ne se referme pas")
        assert_true(
            toggle.get_attribute("aria-label") == "Ouvrir le menu",
            f"{BROWSER_NAME}: titre accessible incorrect quand le menu est fermé",
        )

        # Fermeture clavier : Échap depuis un lien du menu restaure le focus.
        toggle.click()
        mobile_nav.locator("a").first.focus()
        mobile_page.keyboard.press("Escape")
        assert_true(
            toggle.get_attribute("aria-expanded") == "false"
            and mobile_page.evaluate("document.activeElement === document.querySelector('[data-menu-toggle]')")
            and "open" not in (mobile_nav.get_attribute("class") or "").split(),
            f"{BROWSER_NAME}: Échap ne ferme pas le menu ou ne rend pas le focus au bouton",
        )

        # Fermer au toucher hors du panneau, sans attendre un nouveau clic
        # sur le bouton. Le bas de page est hors du menu en surimpression.
        toggle.tap()
        # V1 accueil SINJIRA : toucher un lien du pied de page pourrait
        # naviguer vers une autre section (et y charger l'assistant) au
        # lieu de valider la fermeture du menu. La zone copyright n'a
        # aucun lien : le test reste un VRAI tap en dehors du panneau.
        mobile_page.locator("footer .footer-bottom > span").first.tap()
        assert_true(
            mobile_page.url.rstrip("/") == BASE_URL.rstrip("/"),
            f"{BROWSER_NAME}: le tap hors menu a navigué au lieu de rester sur l'accueil: {mobile_page.url}",
        )
        assert_true(
            toggle.get_attribute("aria-expanded") == "false",
            f"{BROWSER_NAME}: toucher hors du menu ne le ferme pas",
        )

        # L'état du menu ne doit pas rester ouvert si on passe au bureau.
        toggle.tap()
        # La tablette (1000 px) utilise maintenant le menu compact;
        # seule la largeur bureau (>=1021 px) doit refermer ce panneau.
        mobile_page.set_viewport_size({"width": 1000, "height": 844})
        assert_true(
            toggle.get_attribute("aria-expanded") == "true",
            f"{BROWSER_NAME}: le menu tablette s'est refermé avant 1021 px",
        )
        mobile_page.set_viewport_size({"width": 1080, "height": 844})
        mobile_page.wait_for_function(
            "document.querySelector('[data-menu-toggle]').getAttribute('aria-expanded') === 'false'",
            timeout=5_000,
        )
        assert_true(
            toggle.get_attribute("aria-expanded") == "false",
            f"{BROWSER_NAME}: menu mobile conserve son état ouvert au bureau",
        )
        mobile_page.set_viewport_size({"width": 390, "height": 844})
        assert_true(
            toggle.get_attribute("aria-label") == "Ouvrir le menu"
            and mobile_nav.locator("a").first.is_visible() is False,
            f"{BROWSER_NAME}: menu mobile ne retrouve pas son état fermé",
        )

        if IS_LOCAL:
            mobile_page.wait_for_timeout(500)
            assert_true(
                mobile_page.locator(".sinjira-assistant-toggle").count() == 0,
                f"{BROWSER_NAME}: assistant mobile présent sur l’accueil désactivé",
            )
            mobile_page.goto(urljoin(BASE_URL, "projets/sinjira/"), wait_until="domcontentloaded", timeout=30_000)
            wait_for_assistant(mobile_page)
            mobile_assistant = mobile_page.locator(".sinjira-assistant-toggle")
            mobile_assistant.click()
            mobile_panel = mobile_page.locator("#sinjira-assistant-panel")
            assert_true(mobile_panel.is_visible(), f"{BROWSER_NAME}: assistant mobile SINJIRA ne s’ouvre pas")
            assistant_overflow = mobile_page.evaluate("document.documentElement.scrollWidth <= Math.ceil(window.innerWidth) + 2")
            assert_true(assistant_overflow, f"{BROWSER_NAME}: assistant crée un débordement horizontal en 390 px")
            for width, height in ((390, 360), (320, 420), (240, 420)):
                mobile_page.set_viewport_size({"width": width, "height": height})
                visible = mobile_page.evaluate("""() => {
                  const panel = document.querySelector('#sinjira-assistant-panel');
                  const children = ['.sinjira-assistant-close', '.sinjira-assistant-input',
                                    '.sinjira-assistant-send', '.sinjira-assistant-privacy'];
                  const bounds = node => {
                    const b = node.getBoundingClientRect();
                    return {left:b.left,right:b.right,top:b.top,bottom:b.bottom,
                            height:b.height,width:b.width};
                  };
                  return {panel:bounds(panel),
                          children:children.map(sel => ({selector:sel, ...bounds(panel.querySelector(sel))})),
                          overflow:document.documentElement.scrollWidth > innerWidth + 2};
                }""")
                assert_true(not visible["overflow"] and visible["panel"]["top"] >= -2
                            and visible["panel"]["bottom"] <= height + 2,
                            f"{BROWSER_NAME}: panneau assistant déborde à {width}x{height}: {visible}")
                for child in visible["children"]:
                    assert_true(child["top"] >= visible["panel"]["top"] - 2
                                and child["bottom"] <= visible["panel"]["bottom"] + 2
                                and child["left"] >= visible["panel"]["left"] - 2
                                and child["right"] <= visible["panel"]["right"] + 2,
                                f"{BROWSER_NAME}: commande ou confidentialité masquée à "
                                f"{width}x{height}: {child}")
                    if child["selector"] in (".sinjira-assistant-close", ".sinjira-assistant-send"):
                        assert_true(child["height"] >= 43.5,
                                    f"{BROWSER_NAME}: cible tactile assistant sous 44px à {width}x{height}")
            mobile_page.keyboard.press("Escape")

        # Le Centre Vie privée SINJIRA est volontairement exclu des essais
        # anonymes : sa route peut renvoyer vers la connexion; son script
        # est quand même contrôlé par le validateur statique du dépôt.
        # Navigation de continuité : les pages secondaires et les pages 404
        # doivent utiliser les mêmes correctifs clavier que les accueils.
        for route, script_version in (
            ("404.html", "site.js?v=24.4.105"),
            ("univers.html", "site.js?v=24.4.105"),
            ("transparence-ia.html", "site.js?v=24.4.105"),
            ("confidentialite.html", "site.js?v=24.4.105"),
            ("gouvernance-vie-privee.html", "site.js?v=24.4.105"),
            ("avis-legal.html", "site.js?v=24.4.105"),
            ("projets/projet-nova/registre-rencontres.html", "script.js?v=26.1.0"),
            ("projets/projet-nova/visionneuse.html?doc=resume", "script.js?v=26.1.0"),
            ("projets/projet-nova/document.html?doc=corpus", "script.js?v=26.1.0"),
            ("projets/projet-nova/code-conduite.html", "script.js?v=26.1.0"),
            ("projets/projet-nova/finances.html", "script.js?v=26.1.0"),
        ):
            response = mobile_page.goto(
                urljoin(BASE_URL, route), wait_until="domcontentloaded", timeout=30_000
            )
            assert_true(
                response is not None and response.status < 400,
                f"{BROWSER_NAME}: parcours secondaire inaccessible: {route}",
            )
            assert_true(
                mobile_page.locator("main").count() >= 1
                and mobile_page.locator(f'script[src*="{script_version}"]').count() == 1,
                f"{BROWSER_NAME}: script de navigation divergent: {route}",
            )
            menu = mobile_page.locator("[data-menu-toggle]")
            assert_true(menu.count() == 1, f"{BROWSER_NAME}: commande menu absente: {route}")
            menu.tap()
            assert_true(
                menu.get_attribute("aria-expanded") == "true"
                and menu.get_attribute("aria-label") == "Fermer le menu",
                f"{BROWSER_NAME}: menu secondaire ne s'ouvre pas: {route}",
            )
            mobile_page.keyboard.press("Escape")
            assert_true(
                menu.get_attribute("aria-expanded") == "false"
                and menu.get_attribute("aria-label") == "Ouvrir le menu"
                and mobile_page.evaluate(
                    "document.activeElement === document.querySelector('[data-menu-toggle]')"
                ),
                f"{BROWSER_NAME}: Échap ne ferme pas le menu secondaire: {route}",
            )

        # Le portail Nova dispose d'un autre moteur de navigation :
        # vérifier le même contrat accessible sur son accueil mobile.
        mobile_page.goto(
            urljoin(BASE_URL, "projets/projet-nova/"),
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        nova_toggle = mobile_page.locator("[data-menu-toggle]")
        nova_menu = mobile_page.locator("[data-main-nav]")
        assert_true(
            nova_toggle.count() == 1
            and nova_toggle.get_attribute("aria-expanded") == "false"
            and nova_toggle.get_attribute("aria-label") == "Ouvrir le menu"
            and nova_toggle.get_attribute("aria-controls") == nova_menu.get_attribute("id")
            and nova_menu.get_attribute("id") == "navigation-principale",
            f"{BROWSER_NAME}: menu Nova initial non conforme ou navigation non associée",
        )
        nova_toggle.tap()
        assert_true(
            nova_toggle.get_attribute("aria-expanded") == "true"
            and nova_toggle.get_attribute("aria-label") == "Fermer le menu"
            and "open" in (nova_menu.get_attribute("class") or "").split(),
            f"{BROWSER_NAME}: ouverture tactile ou libellé Nova incorrect",
        )
        nova_menu.locator("a").first.focus()
        mobile_page.keyboard.press("Escape")
        assert_true(
            nova_toggle.get_attribute("aria-expanded") == "false"
            and mobile_page.evaluate(
                "document.activeElement === document.querySelector('[data-menu-toggle]')"
            ),
            f"{BROWSER_NAME}: Échap Nova ne rend pas le focus au bouton",
        )
        nova_toggle.tap()
        mobile_page.locator(".header-project-pro").first.tap()
        assert_true(
            nova_toggle.get_attribute("aria-expanded") == "false",
            f"{BROWSER_NAME}: clic extérieur Nova ne ferme pas le menu",
        )
        nova_toggle.tap()
        mobile_page.set_viewport_size({"width": 1200, "height": 844})
        mobile_page.wait_for_function(
            "document.querySelector('[data-menu-toggle]').getAttribute('aria-expanded') === 'false'",
            timeout=5_000,
        )
        assert_true(
            nova_toggle.get_attribute("aria-expanded") == "false"
            and nova_toggle.get_attribute("aria-label") == "Ouvrir le menu",
            f"{BROWSER_NAME}: retour bureau Nova conserve un menu déclaré ouvert",
        )
        mobile_page.set_viewport_size({"width": 390, "height": 844})

        # Vérifier aussi le menu Nova sur la page du questionnaire.
        # Vérification tactile réelle de la Boussole sur téléphones étroits.
        # Aucune interaction simulée par evaluate() : les contrôles reçoivent
        # des tap() comme sur un appareil tactile.
        mobile_page.goto(
            urljoin(BASE_URL, "projets/projet-nova/boussole-electorale.html"),
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        mobile_page.locator("#compass-start").wait_for(state="visible", timeout=10_000)
        assert_true(
            mobile_page.locator("[data-menu-toggle]").get_attribute("aria-controls")
            == mobile_page.locator("[data-main-nav]").get_attribute("id")
            == "navigation-principale",
            f"{BROWSER_NAME}: menu Boussole Nova non associé à la navigation",
        )
        mobile_page.locator("[data-menu-toggle]").tap()
        mobile_page.keyboard.press("Escape")
        assert_true(
            mobile_page.locator("[data-menu-toggle]").get_attribute("aria-expanded") == "false"
            and mobile_page.locator("[data-menu-toggle]").get_attribute("aria-label") == "Ouvrir le menu",
            f"{BROWSER_NAME}: fermeture clavier du menu Boussole Nova incorrecte",
        )
        # Le bouton est visible pendant le chargement asynchrone du JSON.
        # Attendre la readiness réelle, sur le domaine officiel comme en
        # local : une simple vérification immédiate est une course réseau.
        # Ne pas forcer l'activation : une vraie erreur HTTP/JSON doit rester
        # un échec du test, accompagné du statut affiché à l'utilisateur.
        try:
            mobile_page.wait_for_function(
                """() => {
                    const start = document.querySelector('#compass-start');
                    const status = document.querySelector('#compass-status');
                    return Boolean(
                        start && !start.disabled &&
                        status && status.textContent.includes('boussole est prête')
                    );
                }""",
                timeout=20_000,
            )
        except PlaywrightTimeoutError as exc:
            status = mobile_page.locator("#compass-status")
            detail = status.inner_text() if status.count() else "(statut absent)"
            raise AssertionError(
                f"{BROWSER_NAME}: Boussole mobile indisponible après chargement "
                f"(URL={mobile_page.url}; statut={detail})"
            ) from exc
        assert_true(
            not mobile_page.locator("#compass-start").is_disabled(),
            f"{BROWSER_NAME}: Boussole mobile indisponible",
        )
        for viewport_width in (390, 320):
            mobile_page.set_viewport_size({"width": viewport_width, "height": 844})
            mobile_overflow = mobile_page.evaluate("""() => {
                const width = window.innerWidth;
                const skip = document.querySelector(".skip-link");
                const skipCss = skip ? {
                    left: getComputedStyle(skip).left,
                    clip: getComputedStyle(skip).clipPath,
                    display: getComputedStyle(skip).display
                } : null;
                let widthWithoutSkip = null;
                if(skip){
                    skip.style.display = "none";
                    void document.body.offsetWidth;
                    widthWithoutSkip = document.documentElement.scrollWidth;
                    skip.style.removeProperty("display");
                }
                const containers = Array.from(document.querySelectorAll("body *")).map(element => {
                    const rect = element.getBoundingClientRect();
                    return {
                        name: element.tagName.toLowerCase(), id: element.id || "",
                        className: typeof element.className === "string" ? element.className.slice(0,65) : "",
                        scrollWidth: element.scrollWidth, clientWidth: element.clientWidth,
                        right: Math.round(rect.right),
                        overflowX: getComputedStyle(element).overflowX
                    };
                }).filter(x => x.scrollWidth > x.clientWidth + 5)
                  .sort((a,b) => (b.scrollWidth-b.clientWidth) - (a.scrollWidth-a.clientWidth))
                  .slice(0,12);
                return {
                    width,
                    scrollWidth: document.documentElement.scrollWidth,
                    bodyScrollWidth: document.body.scrollWidth,
                    widthWithoutSkip,
                    skipCss,
                    containers,
                    offenders: Array.from(document.querySelectorAll("body *")).map(element => {
                        const rect = element.getBoundingClientRect();
                        return {
                            name: element.tagName.toLowerCase(),
                            className: typeof element.className === "string" ? element.className.slice(0, 100) : "",
                            id: element.id || "",
                            right: Math.round(rect.right),
                            left: Math.round(rect.left),
                            scrollWidth: element.scrollWidth,
                            clientWidth: element.clientWidth
                        };
                    }).filter(x => x.right > width + 2 || x.left < -2)
                      .sort((a,b) => b.right - a.right).slice(0, 12)
                };
            }""")
            assert_true(
                mobile_overflow["scrollWidth"] <= viewport_width + 2,
                f"{BROWSER_NAME}: Boussole déborde horizontalement en {viewport_width}px: {mobile_overflow}",
            )
            assert_true(
                mobile_page.locator("#compass-evidence-question").is_visible(),
                f"{BROWSER_NAME}: explorateur des preuves non accessible en {viewport_width}px",
            )
        mobile_page.set_viewport_size({"width": 390, "height": 844})
        mobile_page.locator("#compass-start").tap()
        mobile_page.locator("#compass-question-stage fieldset").wait_for(state="visible", timeout=10_000)
        assert_true(
            mobile_page.locator("#compass-question-stage fieldset").count() == 1,
            f"{BROWSER_NAME}: plusieurs questions visibles sur téléphone",
        )
        mobile_tap_labels = mobile_page.locator("#compass-question-stage .compass-response-stack label")
        assert_true(
            mobile_tap_labels.count() == 8,
            f"{BROWSER_NAME}: choix de réponse tactile incomplet",
        )
        for selector in (
            "#compass-question-stage .compass-response-stack label",
            "#compass-question-stage [data-importance]",
            "#compass-next",
            "#compass-reset",
        ):
            box = mobile_page.locator(selector).first.bounding_box()
            assert_true(
                box is not None and box["height"] >= 44,
                f"{BROWSER_NAME}: cible tactile inférieure à 44px: {selector}",
            )
        assert_true(
            mobile_page.evaluate("""() => {
                const target = document.querySelector("[data-compass-question-focus]");
                return document.activeElement === target &&
                    getComputedStyle(target).outlineStyle === "solid";
            }"""),
            f"{BROWSER_NAME}: titre de question sans repère visuel de focus",
        )
        mobile_tap_labels.first.tap()
        assert_true(
            mobile_page.locator("#compass-next").is_enabled(),
            f"{BROWSER_NAME}: Suivant ne s'active pas au toucher",
        )
        mobile_page.locator("#compass-next").tap()
        assert_true(
            mobile_page.locator("#compass-progress-track").get_attribute("aria-valuenow") == "2",
            f"{BROWSER_NAME}: progression mobile non mise à jour",
        )
        mobile_page.locator("#compass-prev").tap()
        assert_true(
            mobile_page.locator("#compass-progress-track").get_attribute("aria-valuenow") == "1",
            f"{BROWSER_NAME}: retour tactile à la première question indisponible",
        )
        assert_true(
            mobile_page.locator("#compass-question-stage input[type='radio']").first.is_checked(),
            f"{BROWSER_NAME}: réponse perdue après retour tactile",
        )
        mobile_page.set_viewport_size({"width": 320, "height": 844})
        assert_true(
            mobile_page.evaluate(
                "document.documentElement.scrollWidth <= Math.ceil(window.innerWidth) + 2"
            ),
            f"{BROWSER_NAME}: débordement sur Boussole active en 320px",
        )
        mobile_page.locator("#compass-reset").tap()
        assert_true(
            mobile_page.locator("#compass-start-panel").is_visible() and
            mobile_page.locator("#compass-stepper").is_hidden(),
            f"{BROWSER_NAME}: réinitialisation mobile ne restaure pas l'écran d'accueil",
        )

        mobile.close()

        # Même lorsque le JavaScript principal ne charge pas, les liens
        # publics SINJIRA doivent rester accessibles au clavier et au toucher.
        # Aucune session privée n'est utilisée pour ce test de repli.
        fallback = browser.new_context(
            locale="fr-CA",
            viewport={"width": 320, "height": 720},
            reduced_motion="reduce",
            service_workers="block",
        )
        fallback.route("**/assets/js/site.js*", lambda route: route.abort())
        fallback_page = fallback.new_page()
        response = fallback_page.goto(
            urljoin(BASE_URL, "projets/sinjira/romans/"),
            wait_until="domcontentloaded", timeout=30_000,
        )
        assert_true(response is not None and response.status < 400,
                    f"{BROWSER_NAME}: fiche Romans inaccessible sans site.js")
        public_nav = fallback_page.locator('[data-main-nav]')
        assert_true(public_nav.is_visible(),
                    f"{BROWSER_NAME}: navigation masquée lorsque site.js est bloqué")
        assert_true(public_nav.locator('a[href="/projets/sinjira/"]').is_visible(),
                    f"{BROWSER_NAME}: lien portail SINJIRA masqué sans JavaScript")
        assert_true(fallback_page.locator('[data-menu-toggle]').get_attribute("hidden") is not None,
                    f"{BROWSER_NAME}: commande inactive non masquée par le HTML natif")
        assert_true(fallback_page.locator('[data-menu-toggle]').is_hidden(),
                    f"{BROWSER_NAME}: bouton de menu inactif affiché sans JavaScript")
        assert_true(
            fallback_page.locator('.site-header').evaluate(
                "(el) => getComputedStyle(el).position !== 'sticky'"
            ),
            f"{BROWSER_NAME}: en-tête de repli bloque le défilement mobile",
        )
        assert_true(
            fallback_page.evaluate(
                "document.documentElement.scrollWidth <= Math.ceil(window.innerWidth) + 2"
            ),
            f"{BROWSER_NAME}: débordement horizontal du menu de repli à 320px",
        )
        fallback.close()

        account_url = urljoin(BASE_URL, "compte/")
        account_response = context.request.get(account_url, timeout=30_000)
        assert_true(account_response.ok, f"{BROWSER_NAME}: page compte inaccessible")
        account_html = account_response.text().lower()
        assert_true("kingtyrano@gmail.com" not in account_html, "Adresse propriétaire embarquée dans la page compte")
        has_robots = 'name="robots"' in account_html or "name='robots'" in account_html
        assert_true(has_robots and "noindex" in account_html, "Page compte non protégée contre l’indexation")

        all_errors = page_errors + mobile_errors
        assert_true(not all_errors, f"{BROWSER_NAME}: erreurs JavaScript navigateur: " + " | ".join(all_errors[:5]))
        context.close()
        if IS_LOCAL:
            check_legal_navigation(browser)
            check_message_layout(browser)
            check_conversation_isolation(browser)
            check_notification_counts(browser)
            check_fulfillment_feedback(browser)
            check_cost_summary_feedback(browser)
            check_reservation_feedback(browser)
            check_admin_responsive_layout(browser)
        browser.close()
        auth_note = f", {len(AUTH_ROUTES)} pages Auth locales + assistant V{ASSISTANT_VERSION} contextuel" if IS_LOCAL else ""
        print(
            f"OK E2E {BROWSER_NAME}: {len(PUBLIC_ROUTES)} routes publiques{auth_note}, "
            f"accueil desktop/mobile, contact, compatibilité CSS/runtime et frontière compte vérifiés sur {BASE_URL}"
        )


if __name__ == "__main__":
    run()
