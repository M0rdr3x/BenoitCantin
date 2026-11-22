#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER_NAME = os.environ.get("BROWSER", "chromium").strip().lower()
SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
LITERATURE_ROUTE = "projets/sinjira/romans/"
READER_ROUTE = "projets/sinjira/romans/lire-demo.html"
SITEMAP_ROUTE = "sitemap.xml"
DEMO_ROUTE = "projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"
DEMO_BASENAME = "SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"
FULL_BASENAME = "SINJIRA_LIVRE_I_LA_CENDRE_DU_JUGEMENT.pdf"
CANONICAL = "https://www.benoitcantin.com/projets/sinjira/romans/"
READER_CANONICAL = "https://www.benoitcantin.com/projets/sinjira/romans/lire-demo.html"
BOOK_NAME = "SINJIRA™ — Livre I : La Cendre du Jugement"
READER_WORK_NAME = f"{BOOK_NAME} — Démo officielle"
COVER_URL = "https://www.benoitcantin.com/assets/media/sinjira-livre-1-cover.webp"
COVER_ALT = "Couverture de SINJIRA™ — Livre I : La Cendre du Jugement"


def assert_true(value, message: str) -> None:
    if not value:
        raise AssertionError(message)


def collect_page_errors(page, target: list[str]) -> None:
    page.on("pageerror", lambda error: target.append(f"pageerror: {error}"))


def block_embedded_pdf(context) -> None:
    # Le contrat du lecteur est testé sans dépendre du moteur PDF natif de Chromium/Firefox/WebKit.
    # La disponibilité HTTP du PDF est vérifiée séparément par une requête HEAD.
    context.route(
        f"**/{DEMO_BASENAME}",
        lambda route: route.fulfill(status=204, content_type="application/pdf", body=""),
    )




def mock_web_reader(context) -> None:
    """Liseuse en situation navigateur, sans accès serveur privé ni réseau CDN."""
    context.unroute(f"**/{DEMO_BASENAME}")
    context.route(
        f"**/{DEMO_BASENAME}",
        lambda route: route.fulfill(
            status=200, content_type="application/pdf",
            body=b"%PDF-1.7\n" + b"0" * 2048,
        ),
    )
    context.route(
        "**/npm/@supabase/supabase-js@2.119.0/+esm*",
        lambda route: route.fulfill(
            status=200,
            content_type="text/javascript",
            headers={"access-control-allow-origin": "*"},
            body="export function createClient(){throw Error('Supabase privé non disponible au test démo')}",
        ),
    )
    fake_pdfjs = """
      export const GlobalWorkerOptions={workerSrc:''};
      export function getDocument(){
        return {promise:Promise.resolve({
          numPages:82,
          async getPage(pageNumber){
            return {
              async getTextContent(){
                return {items:[
                  {str:'Page '+pageNumber,transform:[1,0,0,1,10,500],width:80,height:12,hasEOL:true},
                  {str:'Le texte est lisible dans la page.',transform:[1,0,0,1,10,482],width:180,height:12,hasEOL:true}
                ]};
              },
              getViewport({scale}){return {width:600*scale,height:900*scale}},
              render(){return {promise:Promise.resolve()}}
            };
          }
        })};
      }
    """
    context.route(
        "**/pdfjs-dist@4.9.155/build/pdf.min.mjs*",
        lambda route: route.fulfill(
            status=200, content_type="text/javascript",
            headers={"access-control-allow-origin": "*"},
            body=fake_pdfjs,
        ),
    )
    context.add_init_script("""
      document.addEventListener('DOMContentLoaded',()=>{
        if(!location.pathname.endsWith('/compte/liseuse.html'))return;
        const style=document.createElement('style');
        style.textContent='#reader-viewer{height:300px!important;min-height:300px!important} #reader-text{min-height:1800px!important}';
        document.head.append(style);
      });
    """)



def mock_private_reader(context) -> None:
    """Essai exclusivement simulé : utilisateur fictif, aucun jeton/roman réel."""
    fake_supabase = """
      const user={id:'ci-fictitious-owner',email:'test@example.invalid'};
      export function createClient(){
        return {
          auth:{
            async getUser(){return {data:{user},error:null}},
            mfa:{async getAuthenticatorAssuranceLevel(){
              return {data:{currentLevel:'aal1',nextLevel:'aal1'},error:null};
            }},
            onAuthStateChange(callback){
              window.__testReaderSignOut=()=>callback('SIGNED_OUT',null);
              return {data:{subscription:{unsubscribe(){}}}};
            }
          },
          functions:{async invoke(){
            return {data:{ok:true,url:'https://gpvivleexywljowcqkru.supabase.co/storage/v1/object/sign/romans/test.pdf?token=fictitious'},error:null};
          }},
          from(){throw Error('Ne jamais interroger les tables pendant ce test')}
        };
      }
    """
    fake_pdfjs = """
      export const GlobalWorkerOptions={workerSrc:''};
      export function getDocument(){
        window.__testPdfParsingStarted=true;
        return {promise:new Promise(resolve=>{
          window.__testCompletePdfParsing=()=>resolve({
            numPages:520,
            async destroy(){window.__testPdfDestroyed=true},
            async getPage(){throw Error('Un PDF verrouillé ne doit jamais être affiché')}
          });
        })};
      }
    """
    def javascript(route,body):
        route.fulfill(status=200,content_type='text/javascript',
            headers={'access-control-allow-origin':'*'},body=body)
    context.route('**/npm/@supabase/supabase-js@2.119.0/+esm*',
        lambda route: javascript(route,fake_supabase))
    context.route('**/pdfjs-dist@4.9.155/build/pdf.min.mjs*',
        lambda route: javascript(route,fake_pdfjs))
    context.route('https://gpvivleexywljowcqkru.supabase.co/storage/v1/object/sign/**',
        lambda route: route.fulfill(status=200, content_type='application/pdf',
                                  headers={'access-control-allow-origin':'*'},
                                  body=b'%PDF-1.7\n' + b'0'*2048))


def assert_private_signout_during_load(browser):
    """Déconnexion durant l'analyse PDF : le roman ne doit jamais apparaître."""
    private_context=browser.new_context(locale='fr-CA',
        viewport={'width':1440,'height':900})
    mock_private_reader(private_context)
    private_page=private_context.new_page()
    errs=[]
    collect_page_errors(private_page,errs)
    try:
        response=private_page.goto(urljoin(BASE_URL,'compte/liseuse.html?edition=integrale'),
            wait_until='domcontentloaded',timeout=30_000)
        assert_true(response is not None and response.status<400,
            f'{BROWSER_NAME}: route intégrale privée introuvable')
        private_page.wait_for_function(
            '() => window.__testPdfParsingStarted===true && typeof window.__testReaderSignOut==="function"',
            timeout=25_000)
        assert_true(private_page.locator('#reader-content').is_hidden(),
            f'{BROWSER_NAME}: contenu intégral visible avant autorisation finale')
        private_page.evaluate('window.__testReaderSignOut()')
        private_page.evaluate('window.__testCompletePdfParsing()')
        private_page.wait_for_function(
            '() => document.getElementById("reader-status")?.textContent.includes("Reconnectez-vous")',
            timeout=12_000)
        assert_true(private_page.locator('#reader-content').is_hidden(),
            f'{BROWSER_NAME}: fuite visuelle après déconnexion durant le chargement')
        assert_true(private_page.locator('#reader-text').text_content()=='',
            f'{BROWSER_NAME}: contenu privé persistant après déconnexion')
        assert_true(private_page.locator('#reader-error').is_visible(),
            f'{BROWSER_NAME}: refus de session non signalé')
        assert_true(private_page.evaluate(
            "() => !Object.keys(localStorage).some(k => k.includes('roman-integral-pdf'))"),
            f'{BROWSER_NAME}: livre privé stocké localement')
        assert_true(private_page.evaluate('window.__testPdfDestroyed===true'),
            f'{BROWSER_NAME}: ressources PDF non détruites après annulation')
        assert_true(not errs, f'{BROWSER_NAME}: erreur JavaScript privée : {errs[:3]}')
    finally:
        private_context.close()



def assert_private_cross_device_resume_mock(browser) -> None:
    """V33 : deux navigateurs indépendants et un backend *simulé*.
    Aucun compte réel, aucun PDF intégral, aucune opération en production.
    Les contrôles RLS réels restent à vérifier séparément sur Supabase.
    """
    cloud = {}
    schema = {"legacy": False}
    network = {"online": True}
    owner = "ci-fictional-reader-a"
    other = "ci-fictional-reader-b"

    def fake_backend(request):
        table = request.get("table")
        actor = request.get("actor")
        method = request.get("method")
        if table == "sinjira_novels" and method == "single":
            return {"data": {"id": "ci-fictional-novel"}, "error": None}
        if table != "sinjira_reader_library":
            raise AssertionError("Table privée non prévue dans le test : " + str(table))
        if method == "single":
            columns = str(request.get("columns") or "")
            if schema["legacy"] and "scroll_ratio" in columns:
                return {"data": None, "error": {
                    "code": "42703", "message": "column scroll_ratio does not exist"
                }}
            data = cloud.get(actor)
            if data and schema["legacy"]:
                data = {key: val for key, val in data.items() if key != "scroll_ratio"}
            return {"data": data, "error": None}
        if method == "upsert":
            if not network["online"]:
                return {"data": None, "error": {"code": "NETWORK_ERROR",
                                              "message": "Simulated network outage"}}
            payload = request.get("payload") or {}
            if payload.get("user_id") != actor:
                return {"error": {"code": "42501", "message": "RLS fake deny"}}
            if schema["legacy"] and "scroll_ratio" in payload:
                return {"error": {"code": "PGRST204",
                                  "message": "Could not find the scroll_ratio column"}}
            cloud[actor] = {**cloud.get(actor, {}), **payload}
            if schema["legacy"]:
                cloud[actor].pop("scroll_ratio", None)
            return {"data": None, "error": None}
        raise AssertionError("Opération de test inattendue : " + str(request))

    fake_supabase = r"""
const actor = __TEST_USER__;
class Builder {
  constructor(table){this.table=table;this.columns='';this.filters={};}
  select(cols){this.columns=cols;return this;}
  eq(key,value){this.filters[key]=value;return this;}
  order(){return this;}
  limit(){return Promise.resolve({data:[],error:null});}
  maybeSingle(){return window.__sinjiraTestDb({
    table:this.table,actor,method:'single',columns:this.columns,filters:this.filters
  });}
  upsert(payload){return window.__sinjiraTestDb({
    table:this.table,actor,method:'upsert',payload
  });}
}
export function createClient(){
  const user={id:actor,email:'fictional@example.invalid'};
  return {
    auth:{
      async getUser(){return {data:{user},error:null};},
      mfa:{async getAuthenticatorAssuranceLevel(){
        return {data:{currentLevel:'aal1',nextLevel:'aal1'},error:null};
      }},
      onAuthStateChange(){return {data:{subscription:{unsubscribe(){}}}};}
    },
    functions:{async invoke(name){
      if(name!=='get-novel-file-url')throw Error('Unexpected function');
      return {data:{ok:true,url:'https://gpvivleexywljowcqkru.supabase.co/storage/v1/object/sign/romans/ci-test.pdf?token=fictitious'},error:null};
    }},
    from(table){return new Builder(table);}
  };
}
"""
    fake_pdfjs = r"""
export const GlobalWorkerOptions={workerSrc:''};
export function getDocument(){
  return {promise:Promise.resolve({
    numPages:520,
    async destroy(){},
    async getPage(pageNumber){
      return {
        async getTextContent(){return {items:[
          {str:'Page '+pageNumber,transform:[1,0,0,1,10,500],width:80,height:12,hasEOL:true},
          {str:'Contenu artificiel pour le test de position.',transform:[1,0,0,1,10,480],width:250,height:12}
        ]};},
        getViewport({scale}){return {width:600*scale,height:900*scale};},
        render(){return {promise:Promise.resolve()};}
      };
    }
  })};
}
"""
    contexts = []

    def open_device(actor):
        ctx = browser.new_context(locale="fr-CA", viewport={"width": 1440, "height": 920})
        contexts.append(ctx)
        ctx.route("**/npm/@supabase/supabase-js@2.119.0/+esm*",
                  lambda route: route.fulfill(
                      status=200, content_type="text/javascript",
                      headers={"access-control-allow-origin": "*"},
                      body=fake_supabase.replace("__TEST_USER__", json.dumps(actor))))
        ctx.route("**/pdfjs-dist@4.9.155/build/pdf.min.mjs*",
                  lambda route: route.fulfill(
                      status=200, content_type="text/javascript",
                      headers={"access-control-allow-origin": "*"}, body=fake_pdfjs))
        ctx.route("https://gpvivleexywljowcqkru.supabase.co/storage/v1/object/sign/**",
                  lambda route: route.fulfill(
                      status=200, content_type="application/pdf",
                      headers={"access-control-allow-origin": "*"},
                      body=b"%PDF-1.7\n" + b"0" * 2048))
        ctx.add_init_script("""
          document.addEventListener('DOMContentLoaded',()=>{
            const style=document.createElement('style');
            style.textContent='#reader-viewer{height:300px!important;min-height:300px!important} #reader-text{min-height:1800px!important}';
            document.head.append(style);
          });
        """)
        page = ctx.new_page()
        page.expose_function("__sinjiraTestDb", fake_backend)
        response = page.goto(
            urljoin(BASE_URL, "compte/liseuse.html?edition=integrale"),
            wait_until="domcontentloaded", timeout=30_000)
        assert_true(response is not None and response.status < 400,
                    f"{BROWSER_NAME}: page privée simulée indisponible")
        page.locator("#reader-content:not([hidden])").wait_for(timeout=25_000)
        return page

    try:
        first = open_device(owner)
        first.locator("#reader-page").fill("37")
        first.locator("#reader-page").dispatch_event("change")
        first.wait_for_function(
            "() => document.getElementById('reader-text')?.textContent.includes('Page 37')")
        # La restauration réinitialise temporairement le défilement :
        # attendre ses frames avant une interaction réelle simulée.
        first.evaluate("""() => new Promise(resolve =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)))""")
        first.locator("#reader-viewer").evaluate("""(el) => {
            el.style.setProperty('height','300px','important');
            el.style.setProperty('min-height','300px','important');
            el.style.setProperty('max-height','300px','important');
            el.style.setProperty('overflow-y','auto','important');
            document.getElementById('reader-text').style.setProperty('min-height','1800px','important');
            el.scrollTop=420;
            el.dispatchEvent(new Event('scroll'));
        }""")
        assert_true(first.locator("#reader-viewer").evaluate("(el) => el.scrollTop > 0"),
                    f"{BROWSER_NAME}: impossible de simuler le défilement privé")
        first.locator("#reader-save-position").click()
        first.wait_for_function(
            "() => document.getElementById('reader-position-status')?.textContent.includes('synchronisés sur votre compte')",
            timeout=15_000)
        saved = cloud.get(owner)
        assert_true(saved is not None and saved.get("last_page") == 37
                    and 0 < saved.get("scroll_ratio", 0) < 1,
                    f"{BROWSER_NAME}: position précise du compte non enregistrée "
                    f"(last_page={saved.get('last_page') if saved else None}, "
                    f"scroll_ratio={saved.get('scroll_ratio') if saved else None})")
        assert_true("text" not in saved and "content" not in saved,
                    f"{BROWSER_NAME}: le texte privé ne doit pas être enregistré")
        ratio = saved["scroll_ratio"]
        second = open_device(owner)
        assert_true(second.locator("#reader-page").input_value() == "37",
                    f"{BROWSER_NAME}: la page du compte n'est pas reprise sur appareil B")
        assert_true("reprise depuis votre compte" in
                    second.locator("#reader-position-status").inner_text(),
                    f"{BROWSER_NAME}: origine cloud non identifiée")
        second.wait_for_function(
            "() => document.getElementById('reader-viewer')?.scrollTop > 0",
            timeout=15_000)
        restored = second.locator("#reader-viewer").evaluate(
            "(el) => el.scrollTop / Math.max(1,el.scrollHeight-el.clientHeight)")
        assert_true(abs(restored - ratio) < 0.04,
                    f"{BROWSER_NAME}: défilement cloud non repris ({restored} ≠ {ratio})")
        third = open_device(other)
        assert_true(third.locator("#reader-page").input_value() == "4",
                    f"{BROWSER_NAME}: progression d'un autre utilisateur exposée par le mock")
        assert_true(other not in cloud,
                    f"{BROWSER_NAME}: donnée de lecture attribuée au mauvais compte")

        # V34 : une panne réseau ne doit ni effacer la page locale ni exposer
        # un autre compte. À la reconnexion, comparer d'abord les dates.
        network["online"] = False
        first.locator("#reader-page").fill("42")
        first.locator("#reader-page").dispatch_event("change")
        first.wait_for_function(
            "() => document.getElementById('reader-text')?.textContent.includes('Page 42')")
        first.locator("#reader-save-position").click()
        first.wait_for_function(
            "() => document.getElementById('reader-position-status')?.textContent.includes('Synchronisation du compte indisponible')",
            timeout=15_000)
        assert_true(cloud[owner]["last_page"] == 37,
                    f"{BROWSER_NAME}: données distantes modifiées pendant coupure")
        pending = first.evaluate(
            "() => localStorage.getItem('sinjira:liseuse:integrale:la-cendre-du-jugement:ci-fictional-reader-a:pending')")
        assert_true(bool(pending),
                    f"{BROWSER_NAME}: sauvegarde locale en attente absente")
        network["online"] = True
        first.evaluate("window.dispatchEvent(new Event('online'))")
        first.wait_for_function(
            "() => document.getElementById('reader-position-status')?.textContent.includes('Connexion rétablie')",
            timeout=15_000)
        assert_true(cloud[owner]["last_page"] == 42,
                    f"{BROWSER_NAME}: reprise automatique après coupure non synchronisée")
        assert_true(first.evaluate(
            "() => localStorage.getItem('sinjira:liseuse:integrale:la-cendre-du-jugement:ci-fictional-reader-a:pending')") is None,
            f"{BROWSER_NAME}: marqueur de synchronisation non purgé après succès")

        # Compatibilité avec la version serveur qui ne possède que last_page.
        schema["legacy"] = True
        legacy = open_device(owner)
        assert_true(legacy.locator("#reader-page").input_value() == "42",
                    f"{BROWSER_NAME}: ancienne sauvegarde serveur non reprise")
        legacy.locator("#reader-page").fill("39")
        legacy.locator("#reader-page").dispatch_event("change")
        legacy.locator("#reader-save-position").click()
        legacy.wait_for_function(
            "() => document.getElementById('reader-position-status')?.textContent.includes('Page synchronisée avec votre compte')",
            timeout=15_000)
        assert_true(cloud[owner]["last_page"] == 39 and
                    "scroll_ratio" not in cloud[owner],
                    f"{BROWSER_NAME}: fallback V31 n'a pas préservé la sauvegarde serveur")

        # V34 : le compte plus récent ne doit pas être écrasé au retour du réseau.
        network["online"] = False
        legacy.locator("#reader-page").fill("40")
        legacy.locator("#reader-page").dispatch_event("change")
        legacy.wait_for_function(
            "() => document.getElementById('reader-text')?.textContent.includes('Page 40')")
        legacy.locator("#reader-save-position").click()
        legacy.wait_for_function(
            "() => document.getElementById('reader-position-status')?.textContent.includes('Synchronisation du compte indisponible')",
            timeout=15_000)
        cloud[owner] = {**cloud[owner], "last_page": 77,
                        "updated_at": "2099-11-07T20:00:00.000Z"}
        network["online"] = True
        legacy.evaluate("window.dispatchEvent(new Event('online'))")
        legacy.wait_for_function(
            "() => document.getElementById('reader-position-status')?.textContent.includes('Une progression plus récente')",
            timeout=15_000)
        assert_true(cloud[owner]["last_page"] == 77,
                    f"{BROWSER_NAME}: la reconnexion a écrasé une progression serveur plus récente")
    finally:
        for ctx in contexts:
            ctx.close()


def json_ld_graph(page) -> list[dict]:
    nodes: list[dict] = []
    scripts = page.locator('script[type="application/ld+json"]')
    for index in range(scripts.count()):
        raw = scripts.nth(index).text_content() or ""
        if not raw.strip():
            continue
        payload = json.loads(raw)
        if isinstance(payload, dict) and isinstance(payload.get("@graph"), list):
            nodes.extend(node for node in payload["@graph"] if isinstance(node, dict))
        elif isinstance(payload, dict):
            nodes.append(payload)
    return nodes


def assert_no_full_edition_link(page, label: str) -> None:
    hrefs = page.locator("a[href]").evaluate_all("els => els.map(el => el.getAttribute('href') || '')")
    for href in hrefs:
        clean = href.split("#", 1)[0].split("?", 1)[0]
        assert_true(
            not clean.endswith(FULL_BASENAME),
            f"{BROWSER_NAME}: édition intégrale exposée par un lien public ({label}): {href}",
        )


def assert_no_horizontal_overflow(page, label: str) -> None:
    # Mesurer après la finalisation du layout (fonts/styles et deux frames).
    # En cas d'échec production Safari, remonter les éléments hors viewport.
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
    measure = page.evaluate("""() => {
        const width = Math.ceil(window.innerWidth);
        const scrollWidth = document.documentElement.scrollWidth;
        const offenders = [...document.body.querySelectorAll('*')]
          .filter(el => {
            const r = el.getBoundingClientRect();
            return r.width > 0 && (r.right > width + 2 || r.left < -2);
          })
          .slice(0, 8)
          .map(el => {
            const r = el.getBoundingClientRect();
            return {
              tag: el.tagName.toLowerCase(),
              className: typeof el.className === 'string' ? el.className.slice(0, 80) : '',
              left: Math.round(r.left), right: Math.round(r.right),
              scrollWidth: el.scrollWidth,
            };
          });
        return {width, scrollWidth, offenders};
    }""")
    assert_true(
        measure["scrollWidth"] <= measure["width"] + 2,
        f"{BROWSER_NAME}: débordement horizontal sur {label}: {measure}",
    )


def assert_comment_editor_responsive(page, label: str) -> None:
    # Mesurer le formulaire avec un compte simulé uniquement côté DOM :
    # aucune soumission, aucun jeton et aucune requête privée.
    sizing = page.evaluate("""() => {
        const form = document.querySelector('[data-comment-form]');
        const textarea = document.getElementById('sinjira-commentaire-texte');
        const button = form?.querySelector('button[type=submit]');
        if (!form || !textarea || !button) return {ok:false, reason:'elements missing'};
        form.hidden = false;
        const textBox = textarea.getBoundingClientRect();
        const buttonBox = button.getBoundingClientRect();
        const viewport = window.innerWidth;
        return {
            ok: textBox.width >= Math.min(240, viewport * .65) &&
                textBox.height >= (viewport <= 600 ? 168 : 180) &&
                textBox.left >= -1 && textBox.right <= viewport + 1 &&
                Math.abs(buttonBox.width - textBox.width) <= 3 &&
                getComputedStyle(textarea).fontSize === '16px',
            viewport, width: textBox.width, height: textBox.height,
            buttonWidth: buttonBox.width, left: textBox.left,
            right: textBox.right,
            font: getComputedStyle(textarea).fontSize
        };
    }""")
    assert_true(sizing.get("ok"), f"{BROWSER_NAME}: formulaire mal dimensionné sur {label}: {sizing}")


def assert_preorder_public_steps_responsive(browser) -> None:
    """Parcours public à 240–1440 px, même sans JS, session ou backend."""
    targets = ("prix-livre-1", "reception-livre-1", "reservation-livre-1")
    no_js = browser.new_context(
        locale="fr-CA", viewport={"width": 390, "height": 800},
        java_script_enabled=False, reduced_motion="reduce", service_workers="block"
    )
    try:
        page = no_js.new_page()
        for width in (240, 320, 390, 768, 1024, 1440):
            page.set_viewport_size({"width": width, "height": 800})
            response = page.goto(
                urljoin(BASE_URL, "projets/sinjira/romans/precommande.html"),
                wait_until="domcontentloaded", timeout=30_000
            )
            assert_true(response is not None and response.status < 400,
                        f"{BROWSER_NAME}: précommande indisponible à {width}px")
            assert_true(page.locator('body[data-preorder-page="livre-1"]').count() == 1,
                        f"{BROWSER_NAME}: périmètre des styles non activé à {width}px")
            nav = page.locator('nav.sinjira-preorder-steps')
            assert_true(nav.count() == 1 and
                        nav.get_attribute("aria-label") ==
                        "Étapes de la réservation du Livre I",
                        f"{BROWSER_NAME}: sommaire sans nom à {width}px")
            links = nav.locator("a")
            assert_true(links.count() == len(targets),
                        f"{BROWSER_NAME}: nombre d'étapes incorrect à {width}px")
            for i, anchor in enumerate(targets):
                link = links.nth(i)
                assert_true(link.get_attribute("href") == f"#{anchor}",
                            f"{BROWSER_NAME}: destination {anchor} invalide")
                assert_true(page.locator(f'section#{anchor}[aria-labelledby]').count() == 1,
                            f"{BROWSER_NAME}: section {anchor} non accessible")
                assert_true(link.bounding_box()["height"] >= 44,
                            f"{BROWSER_NAME}: zone tactile trop petite à {width}px")
            assert_true(page.locator("a[href$='.pdf'],a[href$='.epub']").count() == 0,
                        f"{BROWSER_NAME}: document privé exposé sur la précommande")
            assert_true(page.locator('[data-preorder-status][role="status"]').count() == 1,
                        f"{BROWSER_NAME}: message de réservation non annoncé")
            assert_true(page.locator('[data-pf-preference-status][role="status"]').count() == 1,
                        f"{BROWSER_NAME}: message de livraison non annoncé")
            assert_true(not page.evaluate(
                "() => document.documentElement.scrollWidth > innerWidth + 2"),
                f"{BROWSER_NAME}: débordement horizontal de précommande à {width}px")
            nav.locator('a[href="#reception-livre-1"]').click()
            assert_true(page.evaluate("location.hash") == "#reception-livre-1",
                        f"{BROWSER_NAME}: ancre Livraison non fonctionnelle à {width}px")
        assert_true(page.locator("[data-main-nav] a").count() == 6,
                    f"{BROWSER_NAME}: navigation principale disparue sans JavaScript")
    finally:
        no_js.close()


def run() -> None:
    assert_true(BROWSER_NAME in SUPPORTED_BROWSERS, f"Navigateur Playwright inconnu: {BROWSER_NAME}")

    with sync_playwright() as p:
        browser = getattr(p, BROWSER_NAME).launch()
        context = browser.new_context(
            locale="fr-CA",
            viewport={"width": 1440, "height": 1000},
            reduced_motion="reduce",
        )
        block_embedded_pdf(context)
        page = context.new_page()
        errors: list[str] = []
        collect_page_errors(page, errors)

        literature_url = urljoin(BASE_URL, LITERATURE_ROUTE)
        response = page.goto(literature_url, wait_until="domcontentloaded", timeout=30_000)
        assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: page Littérature inaccessible")
        assert_true(page.locator("main#contenu").count() == 1, f"{BROWSER_NAME}: main Littérature absent")
        assert_comment_editor_responsive(page, 'ordinateur 1440px')
        assert_true(page.locator("h1").inner_text().strip() == "Littérature.", f"{BROWSER_NAME}: H1 Littérature inattendu")
        assert_true(
            page.locator('link[rel="canonical"]').get_attribute("href") == CANONICAL,
            f"{BROWSER_NAME}: canonical Littérature incorrecte",
        )
        assert_true(
            page.locator('meta[property="og:url"]').get_attribute("content") == CANONICAL,
            f"{BROWSER_NAME}: og:url Littérature incorrect",
        )
        assert_true(
            page.locator('meta[name="twitter:card"]').get_attribute("content") == "summary_large_image",
            f"{BROWSER_NAME}: Twitter Card Littérature absente",
        )
        assert_true(page.locator('nav[aria-label="Navigation principale"]').count() == 1, f"{BROWSER_NAME}: navigation Littérature non nommée")
        assert_true("62 pages" in page.locator("main").inner_text(), f"{BROWSER_NAME}: statut de validation 62 pages absent de la fiche")

        graph = json_ld_graph(page)
        books = [node for node in graph if node.get("@type") == "Book"]
        assert_true(len(books) == 1, f"{BROWSER_NAME}: provenance JSON-LD Book absente ou dupliquée")
        book = books[0]
        assert_true(book.get("name") == BOOK_NAME, f"{BROWSER_NAME}: nom JSON-LD du Livre I incorrect")
        assert_true(book.get("inLanguage") == "fr-CA", f"{BROWSER_NAME}: langue JSON-LD du Livre I incorrecte")
        assert_true(book.get("numberOfPages") == 520, f"{BROWSER_NAME}: édition intégrale JSON-LD différente de 520 pages")
        assert_true(book.get("isbn") == ["978-2-9825371-0-1", "978-2-9825371-1-8"], f"{BROWSER_NAME}: ISBN du Livre I incorrects")
        demo_part = book.get("hasPart") or {}
        assert_true(demo_part.get("isAccessibleForFree") is False, f"{BROWSER_NAME}: démo non publiée déclarée disponible")
        assert_true(demo_part.get("url") == READER_CANONICAL, f"{BROWSER_NAME}: URL JSON-LD de la démo incorrecte")

        assert_true(page.locator('a[href="lire-demo.html"]').count() >= 1,
                    f"{BROWSER_NAME}: page de statut de la démo inaccessible depuis les romans")
        assert_true(page.locator(f'a[href*="{DEMO_BASENAME}"]').count() == 0,
                    f"{BROWSER_NAME}: ancien PDF encore proposé")
        assert_true(page.locator('a[href="/compte/bibliotheque-romans.html"]').count() >= 1,
                    f"{BROWSER_NAME}: lien bibliothèque compte manquant")
        assert_no_full_edition_link(page, "Littérature")

        # L'ancienne édition ne doit plus être servie.
        pdf_head = context.request.head(urljoin(BASE_URL, DEMO_ROUTE), timeout=30_000)
        assert_true(pdf_head.status >= 400,
                    f"{BROWSER_NAME}: l'ancien PDF de 82 pages reste public")

        sitemap_response = context.request.get(urljoin(BASE_URL, SITEMAP_ROUTE), timeout=30_000)
        assert_true(sitemap_response.status < 400, f"{BROWSER_NAME}: sitemap inaccessible (HTTP {sitemap_response.status})")
        sitemap_text = sitemap_response.text()
        reader_loc = f"<loc>{READER_CANONICAL}</loc>"
        assert_true(sitemap_text.count(reader_loc) == 0, f"{BROWSER_NAME}: page noindex de démo encore présente dans le sitemap")
        assert_true(DEMO_BASENAME not in sitemap_text, f"{BROWSER_NAME}: le PDF démo ne doit pas être indexé directement par le sitemap")
        assert_true(FULL_BASENAME not in sitemap_text, f"{BROWSER_NAME}: édition intégrale exposée dans le sitemap")

        reader_url = urljoin(BASE_URL, READER_ROUTE)
        response = page.goto(reader_url, wait_until="domcontentloaded", timeout=30_000)
        assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: lecteur démo inaccessible")
        assert_true(page.locator("main#lecteur").count() == 1, f"{BROWSER_NAME}: main lecteur absent")
        assert_true(page.locator('a.skip-link[href="#lecteur"]').count() == 1, f"{BROWSER_NAME}: lien d’évitement lecteur absent")
        assert_true(
            page.locator('link[rel="canonical"]').get_attribute("href") == READER_CANONICAL,
            f"{BROWSER_NAME}: canonical lecteur incorrecte",
        )
        assert_true(page.locator('body[data-reader-page="demo-pending"]').count() == 1,
                    f"{BROWSER_NAME}: statut de retrait non signalé")
        assert_true(page.locator('meta[name="robots"]').get_attribute("content") == "noindex,follow",
                    f"{BROWSER_NAME}: page temporaire indexable")
        assert_true("62 pages" in page.locator("main").inner_text(),
                    f"{BROWSER_NAME}: nouvelle validation non décrite")
        assert_true(page.locator('iframe[data-pdf-reader]').count() == 0,
                    f"{BROWSER_NAME}: ancien cadre PDF visible")
        assert_true(page.locator(f'a[href*="{DEMO_BASENAME}"]').count() == 0,
                    f"{BROWSER_NAME}: ancien PDF référencé par le lecteur")
        assert_true(page.locator('a[href="/projets/sinjira/romans/"]').count() >= 1,
                    f"{BROWSER_NAME}: retour aux romans inaccessible")
        assert_true(FULL_BASENAME not in page.content(),
                    f"{BROWSER_NAME}: chemin du roman intégral exposé dans la page publique")
        assert_no_full_edition_link(page, "statut démo")

        # La liseuse Web gratuite affiche le retrait au lieu de charger un PDF absent.
        response=page.goto(urljoin(BASE_URL,"compte/liseuse.html?edition=demo"),
                           wait_until="domcontentloaded",timeout=30_000)
        assert_true(response is not None and response.status < 400,
                    f"{BROWSER_NAME}: page compte de la liseuse inaccessible")
        page.locator('#reader-error:not([hidden])').wait_for(timeout=20_000)
        assert_true("temporairement indisponible" in page.locator('#reader-status').inner_text(),
                    f"{BROWSER_NAME}: statut de la démo retirée non annoncé")
        assert_true(page.locator('#reader-content').is_hidden(),
                    f"{BROWSER_NAME}: anciens octets de la démo affichés")
        assert_true(page.locator('#reader-download-demo').is_hidden(),
                    f"{BROWSER_NAME}: ancien lien PDF de secours encore visible")
        assert_no_full_edition_link(page,"liseuse mise en attente")

        # Vérifier le parcours de précommande de façon isolée et sans réseau privé.
        assert_preorder_public_steps_responsive(browser)

        # Protéger aussi l'édition intégrale pendant une déconnexion en vol.
        assert_private_signout_during_load(browser)
        assert_private_cross_device_resume_mock(browser)

        mobile = browser.new_context(
            locale="fr-CA",
            viewport={"width": 390, "height": 844},
            has_touch=True,
            reduced_motion="reduce",
        )
        block_embedded_pdf(mobile)
        mobile_page = mobile.new_page()
        mobile_errors: list[str] = []
        collect_page_errors(mobile_page, mobile_errors)

        for route, label in ((LITERATURE_ROUTE, "Littérature"), (READER_ROUTE, "lecteur démo")):
            response = mobile_page.goto(urljoin(BASE_URL, route), wait_until="domcontentloaded", timeout=30_000)
            assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: {label} inaccessible sur mobile")
            assert_no_horizontal_overflow(mobile_page, label)
            if route == LITERATURE_ROUTE:
                assert_comment_editor_responsive(mobile_page, 'cellulaire 390px')
                mobile_page.set_viewport_size({"width": 320, "height": 720})
                assert_comment_editor_responsive(mobile_page, 'cellulaire 320px')
                mobile_page.set_viewport_size({"width": 390, "height": 844})

        assert_true(mobile_page.locator("iframe[data-pdf-reader]").count() == 0, f"{BROWSER_NAME}: cadre de l'ancien PDF encore visible sur mobile")
        assert_true(mobile_page.locator('a[href="/projets/sinjira/romans/"]').count() >= 1, f"{BROWSER_NAME}: retour mobile inaccessible")

        assert_true(not errors, f"{BROWSER_NAME}: erreurs JavaScript Littérature: " + " | ".join(errors[:5]))
        assert_true(not mobile_errors, f"{BROWSER_NAME}: erreurs JavaScript Littérature mobile: " + " | ".join(mobile_errors[:5]))

        mobile.close()
        context.close()
        browser.close()
        print(f"OK littérature {BROWSER_NAME}: fiche, SEO, sitemap, retrait de l'ancien PDF, frontière intégrale et mobile vérifiés.")


if __name__ == "__main__":
    run()
