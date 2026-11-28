#!/usr/bin/env python3
"""Recette UX des écrans de compte SINJIRA : responsive et contrôle local des mots de passe.

N'utilise aucun compte réel, aucun mot de passe réel, aucune écriture backend.
La révélation volontaire est testée sur une fixture isolée qui charge le script officiel.
"""
import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
ENGINE = os.environ.get("BROWSER", "chromium").lower().strip()
PAGES = (
    "compte/connexion.html",
    "compte/inscription.html",
    "compte/mot-de-passe-oublie.html",
    "compte/reinitialiser-mot-de-passe.html",
)
WIDTHS = (240, 280, 320, 390, 540, 768, 1440)
LOGO = "/assets/icons/sinjira-officiel-20261120.png"


def assert_ok(condition, message):
    if not condition:
        raise AssertionError(f"{ENGINE}: {message}")


def inspect_route(page, path, width):
    page.set_viewport_size({"width": width, "height": 844})
    response = page.goto(urljoin(BASE, path), wait_until="domcontentloaded", timeout=30_000)
    assert_ok(response is not None and response.status < 400, f"route introuvable : {path}")
    result = page.evaluate("""() => {
      const form = document.querySelector('main form.account-form');
      const inputs = [...(form?.querySelectorAll('input:not([type=checkbox]),select,textarea')||[])];
      const submit = form?.querySelector('button[type=submit]');
      const logo = document.querySelector('.site-header .brand img');
      const main = document.querySelector('main');
      return {
        overflow: document.documentElement.scrollWidth > innerWidth + 2,
        formExists: !!form,
        mainTabindex: main?.getAttribute('tabindex'),
        backendRole: document.querySelector('[data-backend-state]')?.getAttribute('role'),
        mainWidth: main?.getBoundingClientRect().width,
        mainRight: main?.getBoundingClientRect().right,
        elements: inputs.map(input => {
          const rect = input.getBoundingClientRect();
          return {id:input.id, width:rect.width, height:rect.height,
            left:rect.left,right:rect.right,
            labelled:!!document.querySelector('label[for="'+input.id+'"]')};
        }),
        button:submit?.getBoundingClientRect().height || 0,
        logo:logo?.getAttribute('src'),
        ux:document.body.dataset.sinjiraFormUx,
        css:[...document.querySelectorAll('link[rel=stylesheet]')]
          .some(n => n.getAttribute('href')?.startsWith('/assets/css/sinjira-forms-ux-v1.css')),
      };
    }""")
    assert_ok(result["formExists"] and result["ux"] == "v1" and result["css"],
              f"CSS des formulaires indisponible sur {path} à {width}px: {result}")
    assert_ok(result["mainTabindex"] == "-1" and result["backendRole"] == "status",
              f"navigation clavier ou annonce de service inaccessible : {path}")
    assert_ok(result["logo"] == LOGO, f"logo non officiel sur {path}")
    assert_ok(not result["overflow"], f"défilement horizontal sur {path} à {width}px")
    assert_ok(result["mainRight"] <= width + 2, f"main coupé sur {path} à {width}px")
    assert_ok(result["button"] >= 44, f"bouton principal trop petit sur {path} à {width}px")
    assert_ok(bool(result["elements"]), f"aucun contrôle sur {path}")
    for field in result["elements"]:
        assert_ok(field["labelled"], f"champ non étiqueté : {path}/{field['id']}")
        assert_ok(field["height"] >= 44, f"champ trop petit : {path}/{field['id']}")
        assert_ok(field["left"] >= -2 and field["right"] <= width + 2,
                  f"champ hors écran : {path}/{field['id']}")


def assert_password_script_is_safe(context):
    # Fixture isolée : pas d'Auth, pas de requête réseau privée, aucun secret utilisateur.
    page = context.new_page()
    try:
        page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)
        page.set_content("""<!doctype html><html lang="fr-CA"><body>
          <form data-reset-form>
            <label for="a">Nouveau mot de passe</label>
            <input id="a" type="password" autocomplete="new-password" value="EXEMPLE-UNIQUEMENT">
            <fieldset id="locked" disabled>
            <label for="b">Confirmation</label>
            <input id="b" type="password" autocomplete="new-password" value="EXEMPLE-UNIQUEMENT">
            </fieldset>
          </form></body></html>""")
        page.add_script_tag(url=urljoin(BASE, "assets/js/sinjira-password-visibility-v1.js"))
        buttons = page.locator("[data-password-visibility]")
        assert_ok(buttons.count() == 2, "boutons Afficher/Masquer manquants dans le formulaire reset")
        assert_ok(buttons.first.get_attribute("type") == "button",
                  "une révélation du mot de passe ne doit pas soumettre le formulaire")
        assert_ok(buttons.last.is_disabled(), "commande active sur un champ verrouillé")
        page.locator("#locked").evaluate("(el) => { el.disabled = false; }")
        page.wait_for_function("() => !document.querySelector('[aria-controls=b]').disabled")
        buttons.first.click()
        assert_ok(page.locator("#a").get_attribute("type") == "text",
                  "affichage du nouveau mot de passe inopérant")
        assert_ok(buttons.first.get_attribute("aria-pressed") == "true",
                  "état accessible du bouton non synchronisé")
        page.locator("#a").evaluate("(el) => { el.disabled = true; }")
        page.wait_for_function("() => document.querySelector('#a').type === 'password' && document.querySelector('[aria-controls=a]').disabled")
        assert_ok(buttons.first.get_attribute("aria-pressed") == "false",
                  "un champ verrouillé reste révélé")
        page.locator("#a").evaluate("(el) => { el.disabled = false; }")
        page.wait_for_function("() => !document.querySelector('[aria-controls=a]').disabled")
        buttons.first.click()
        page.evaluate("() => window.dispatchEvent(new Event('pagehide'))")
        assert_ok(page.locator("#a").get_attribute("type") == "password",
                  "le mot de passe doit être masqué en quittant la page")
        assert_ok(buttons.first.get_attribute("aria-pressed") == "false",
                  "bouton de révélation non réinitialisé")
        assert_ok(page.locator("#a").input_value() == "EXEMPLE-UNIQUEMENT",
                  "le masquage ne doit pas effacer la saisie")
    finally:
        page.close()


def assert_inline_feedback(context):
    # Validation native uniquement, sans accès aux services Auth.
    page = context.new_page()
    try:
        page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)
        page.set_content("""<!doctype html><html lang="fr-CA"><body>
          <form data-login-form>
            <label for="email">Courriel</label><input id="email" type="email" required aria-describedby="help">
            <small id="help">Votre courriel.</small>
            <button type="submit">Continuer</button>
          </form></body></html>""")
        page.add_script_tag(url=urljoin(BASE, "assets/js/sinjira-form-feedback-v1.js"))
        field = page.locator("#email")
        page.locator('button[type=submit]').click()
        error = page.locator(".sinjira-field-error")
        assert_ok(error.count() == 1 and error.is_visible(), "erreur native non persistante")
        assert_ok(field.get_attribute("aria-invalid") == "true", "champ invalide non annoncé")
        assert_ok("help" in field.get_attribute("aria-describedby").split(), "aide d'origine perdue")
        field.fill("invalide")
        assert_ok(error.is_visible(), "erreur effacée avant correction")
        field.fill("exemple@example.invalid")
        assert_ok(error.count() == 0, "erreur non retirée après correction")
        assert_ok(field.get_attribute("aria-invalid") is None, "état invalide résiduel")
        assert_ok(field.get_attribute("aria-describedby") == "help", "aide d'origine non restaurée")
        field.fill("")
        page.locator('button[type=submit]').click()
        page.locator("form").evaluate("(el) => el.reset()")
        page.wait_for_function("() => !document.querySelector('.sinjira-field-error')")
        assert_ok(field.get_attribute("aria-describedby") == "help", "aide non restaurée après reset")
        field.evaluate("(el) => { el.required = true; el.reportValidity(); el.required = false; }")
        page.wait_for_function("() => !document.querySelector('.sinjira-field-error')")
        assert_ok(field.get_attribute("aria-invalid") is None, "erreur résiduelle après retrait de required")
        page.locator("form").evaluate("""(form) => {
          const label = document.createElement('label');
          label.innerHTML = '<input id="consent" type="checkbox" required> Consentement fictif';
          form.appendChild(label);
        }""")
        checkbox = page.locator("#consent")
        checkbox.evaluate("(el) => el.reportValidity()")
        assert_ok(error.count() == 1, "erreur de consentement absente")
        assert_ok(checkbox.evaluate("(el) => el.closest('label').nextElementSibling.classList.contains('sinjira-field-error')"),
                  "erreur intégrée au nom accessible du consentement")
        checkbox.check()
        assert_ok(error.count() == 0, "erreur de consentement non retirée")
        checkbox.uncheck()
        checkbox.evaluate("(el) => { el.reportValidity(); el.disabled = true; }")
        page.wait_for_function("() => !document.querySelector('.sinjira-field-error')")
        assert_ok(checkbox.get_attribute("aria-invalid") is None, "erreur sur un champ désactivé")
    finally:
        page.close()


def assert_processing_feedback(context):
    page = context.new_page()
    try:
        page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)
        page.set_content("""<!doctype html><html lang="fr-CA"><body>
          <form data-login-form aria-busy="true">
            <label for="email">Courriel</label><input id="email" type="email">
            <button type="submit">Continuer</button>
          </form><div data-account-status hidden></div></body></html>""")
        # Contrôler les transitions réseau et la temporisation sans réseau réel.
        page.evaluate("""() => {
          window.fakeOnline=true;
          Object.defineProperty(navigator,'onLine',{configurable:true,get:()=>window.fakeOnline});
          const set=window.setTimeout.bind(window), clear=window.clearTimeout.bind(window);
          window.slowCallbacks=new Map();
          let next=-100;
          window.setTimeout=(cb,ms,...args)=>{
            if(ms!==10000)return set(cb,ms,...args);
            const id=next--;window.slowCallbacks.set(id,()=>cb(...args));return id;
          };
          window.clearTimeout=id=>{if(window.slowCallbacks.has(id))window.slowCallbacks.delete(id);else clear(id);};
          window.simulateSlow=()=>{
            const callbacks=[...window.slowCallbacks.values()];
            window.slowCallbacks.clear();callbacks.forEach(cb=>cb());
          };
        }""")
        page.add_script_tag(url=urljoin(BASE, "assets/js/sinjira-form-feedback-v1.js"))
        page.evaluate("""() => {
          const form=document.querySelector('form');
          window.attempts=0;
          form.addEventListener('submit', e => {
            e.preventDefault();window.attempts++;
            form.setAttribute('aria-busy','true');
          });
        }""")
        form=page.locator("form")
        feedback=page.locator(".sinjira-form-processing")
        assert_ok(feedback.get_attribute("role") == "status", "attente non accessible")
        assert_ok(feedback.inner_text() == "", "verrou initial présenté comme une requête")
        submit="el => el.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))"
        form.evaluate(submit)
        assert_ok(page.evaluate("window.attempts") == 0, "envoi accepté pendant le verrou")
        form.evaluate("el => el.setAttribute('aria-busy','false')")
        form.evaluate(submit)
        page.wait_for_function("() => document.querySelector('.sinjira-form-processing').textContent.includes('Traitement')")
        form.evaluate(submit)
        assert_ok(page.evaluate("window.attempts") == 1, "soumission répétée non bloquée")
        page.evaluate("() => {window.fakeOnline=false;window.dispatchEvent(new Event('offline'));}")
        assert_ok("hors ligne" in feedback.inner_text(), "interruption réseau non annoncée")
        page.evaluate("() => window.simulateSlow()")
        page.evaluate("() => {window.fakeOnline=true;window.dispatchEvent(new Event('online'));}")
        assert_ok("plus de temps" in feedback.inner_text(), "attente prolongée non annoncée")
        assert_ok(page.evaluate("window.attempts") == 1, "relance automatique interdite")
        assert_ok(form.get_attribute("aria-busy") == "true", "verrou levé par le réseau")
        form.evaluate("el => el.setAttribute('aria-busy','false')")
        page.wait_for_function("() => !document.querySelector('.sinjira-form-processing').textContent")
        form.evaluate(submit)
        page.wait_for_function("() => document.querySelector('.sinjira-form-processing').textContent.includes('Traitement')")
        assert_ok(page.evaluate("window.attempts") == 2, "nouvelle tentative légitime bloquée")
        page.locator("[data-account-status]").evaluate("el => {el.textContent='Terminé';el.hidden=false;}")
        page.wait_for_function("() => !document.querySelector('.sinjira-form-processing').textContent")
        assert_ok(form.get_attribute("aria-busy") == "true", "verrou Auth modifié par l'UX")
        assert_ok(page.evaluate("window.slowCallbacks.size") == 0, "temporisation résiduelle après résultat")
        page.evaluate("() => {window.fakeOnline=false;window.dispatchEvent(new Event('offline'));}")
        assert_ok(feedback.inner_text() == "", "ancienne requête réaffichée après résultat")
    finally:
        page.close()


def inspect_member_forms(browser):
    # Recette de présentation : aucun module applicatif, aucune session ni
    # soumission. Les valeurs et autorisations du serveur ne sont pas testées.
    context=browser.new_context(java_script_enabled=False,service_workers="block",
        locale="fr-CA",reduced_motion="reduce",viewport={"width":390,"height":844})
    try:
        context.route("**/*", lambda route: route.continue_() if route.request.url.startswith(BASE) else route.abort())
        page=context.new_page()
        for path in ("compte/profil.html","compte/parametres.html"):
            response=page.goto(urljoin(BASE,path),wait_until="load",timeout=30_000)
            assert_ok(response is not None and response.ok,"page membre inaccessible")
            if path.endswith("profil.html"):
                page.locator("[data-optional-private-profile] summary").click()
                assert_ok(page.locator("[data-optional-private-profile]").get_attribute("open") is not None,
                          "réglages facultatifs inaccessibles")
            for width,zoom in ((240,"100%"),(320,"200%"),(390,"100%"),(768,"100%"),(1440,"100%")):
                page.set_viewport_size({"width":width,"height":844})
                # Avec JavaScript désactivé, ne pas attendre une animation asynchrone.
                # Le calcul de géométrie force une mise en page synchrone après le zoom.
                state=page.evaluate("""(zoom) => {
                  document.documentElement.style.fontSize=zoom;
                  const rootWidth=document.documentElement.scrollWidth;
                  const controls=[...document.querySelectorAll('main .account-form .field input:not([type=hidden]),main .account-form select,main .account-form textarea,main .btn,main summary,main .account-check')].filter(e=>e.getBoundingClientRect().width>0);
                  return {count:controls.length,overflow:rootWidth>innerWidth+2,
                    offenders:controls.filter(e=>{const r=e.getBoundingClientRect();return r.left<-2||r.right>innerWidth+2||r.height<47.5}).map(e=>{const r=e.getBoundingClientRect();return {control:e.id||e.className||e.tagName,left:r.left,right:r.right,height:r.height,width:r.width}}),
                    status:[...document.querySelectorAll('main .account-status')].every(e=>e.getAttribute('role')==='status'&&e.getAttribute('aria-live')==='polite')};
                }""",zoom)
                assert_ok(state["count"]>=5 and not state["overflow"] and not state["offenders"] and state["status"],
                          f"formulaire {path}, {width}px / {zoom}: {state}")
            page.evaluate("document.documentElement.style.fontSize=''")
            if path.endswith("parametres.html"):
                assert_ok(page.locator('[name="allow_ai_personal_data"]').is_disabled(),
                          "option IA privée doit rester désactivée")
    finally:
        context.close()


def assert_preferences_save_feedback(browser):
    # Le module officiel est exécuté avec un client synthétique, sans compte
    # ni trafic externe, et des réponses volontairement différées.
    context=browser.new_context(service_workers="block")
    try:
        page=context.new_page()
        context.route("**/*",lambda route: route.continue_() if route.request.url.startswith(BASE) else route.abort())
        context.route("**/preferences-test.html*",lambda route: route.fulfill(
            content_type="text/html",body="""<form data-privacy-settings-form inert aria-busy="true">
              <input type="checkbox" name="public_profile"><input type="checkbox" name="allow_ai_personal_data" disabled>
              <button type="submit" disabled>Enregistrer</button></form><p data-privacy-settings-status></p>
              <script type="module" src="/assets/js/v24-preferences.js"></script>"""))
        context.route("**/assets/js/sinjira-supabase.js",lambda route: route.fulfill(
            content_type="text/javascript",body="""export async function requireUser(){if(location.search==='?session-error')throw Error('fixture session');return {id:'fixture-user'}}
              window.writes=[];window.pending=[];
              export function setStatus(node,msg,type){node.textContent=msg;node.dataset.type=type;}
              export function getSupabase(){return {from(table){return {
                select(){return {eq(){return {maybeSingle:async()=>({data:{user_id:'fixture-user',public_profile:false,allow_ai_personal_data:false},error:null})}}}},
                update(payload){return {eq(key,id){window.writes.push({table,payload,key,id});return {select(){return {maybeSingle(){return new Promise((resolve,reject)=>window.pending.push({resolve,reject}));}}}};}}},
                insert(){throw Error('insertion inattendue')}
              }}}}"""))
        page.goto(urljoin(BASE,"preferences-test.html"),wait_until="domcontentloaded")
        form=page.locator("[data-privacy-settings-form]")
        button=form.locator("button")
        checkbox=form.locator('[name="public_profile"]')
        status=page.locator("[data-privacy-settings-status]")
        page.wait_for_function("() => !document.querySelector('form').inert")
        checkbox.check()
        button.click()
        page.evaluate("document.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))")
        assert_ok(page.evaluate("window.writes.length")==1,"double soumission")
        assert_ok(button.is_disabled() and form.get_attribute("aria-busy")=="true","état occupé absent")
        checkbox.uncheck()
        page.evaluate("window.pending.shift().resolve({data:{user_id:'fixture-user'},error:null})")
        page.wait_for_function("() => !document.querySelector('button').disabled")
        assert_ok("plus récentes" in status.inner_text(),"modification récente annoncée comme enregistrée")
        assert_ok(not checkbox.is_checked(),"saisie écrasée")
        button.click()
        page.evaluate("window.pending.shift().reject(new Error('fixture réseau'))")
        page.wait_for_function("() => !document.querySelector('button').disabled")
        assert_ok("saisie est conservée" in status.inner_text(),"erreur réseau non signalée")
        button.click()
        page.evaluate("window.pending.shift().resolve({data:{user_id:'fixture-user'},error:null})")
        page.wait_for_function("() => !document.querySelector('button').disabled")
        assert_ok("enregistrées dans votre compte" in status.inner_text(),"relance non confirmée")
        checkbox.check()
        button.click()
        page.evaluate("window.pending.shift().resolve({data:null,error:null})")
        page.wait_for_function("() => !document.querySelector('button').disabled")
        assert_ok("Impossible de confirmer" in status.inner_text() and checkbox.is_checked(),"zéro ligne annoncé comme succès")
        button.click()
        page.evaluate("window.pending.shift().resolve({data:{user_id:'fixture-user'},error:null})")
        page.wait_for_function("() => !document.querySelector('button').disabled")
        assert_ok("enregistrées dans votre compte" in status.inner_text(),"confirmation après zéro ligne absente")
        assert_ok(page.evaluate("window.writes.every(w=>w.key==='user_id'&&w.id==='fixture-user'&&!('allow_ai_personal_data' in w.payload))"),"périmètre d’écriture modifié")
        page.goto(urljoin(BASE,"preferences-test.html?session-error"),wait_until="domcontentloaded")
        page.wait_for_function("document.querySelector('form').getAttribute('aria-busy')==='false'")
        assert_ok(form.get_attribute("inert") is not None and button.is_disabled(),"session non vérifiée mais formulaire disponible")
        assert_ok("Impossible de vérifier" in status.inner_text(),"échec de session non expliqué")
        assert_ok(page.evaluate("window.writes.length===0"),"écriture malgré échec de session")
    finally:
        context.close()


def run():
    assert_ok(ENGINE in {"chromium", "firefox", "webkit"}, "moteur navigateur inconnu")
    with sync_playwright() as playwright:
        browser = getattr(playwright, ENGINE).launch()
        try:
            context = browser.new_context(locale="fr-CA", viewport={"width": 390, "height": 844},
                                          reduced_motion="reduce", service_workers="block")
            # Tests uniquement locaux : aucune requête Supabase externe n'est requise.
            context.route("**/*.supabase.co/**", lambda route: route.abort())
            try:
                page = context.new_page()
                for path in PAGES:
                    for width in WIDTHS:
                        inspect_route(page, path, width)
                assert_password_script_is_safe(context)
                assert_inline_feedback(context)
                assert_processing_feedback(context)
                inspect_member_forms(browser)
                assert_preferences_save_feedback(browser)
                print(f"OK {ENGINE}: quatre formulaires Auth à 240–1440px + révélation locale sûre")
            finally:
                context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    run()
