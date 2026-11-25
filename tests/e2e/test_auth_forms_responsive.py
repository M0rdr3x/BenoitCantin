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
            <label for="b">Confirmation</label>
            <input id="b" type="password" autocomplete="new-password" value="EXEMPLE-UNIQUEMENT">
          </form></body></html>""")
        page.add_script_tag(url=urljoin(BASE, "assets/js/sinjira-password-visibility-v1.js"))
        buttons = page.locator("[data-password-visibility]")
        assert_ok(buttons.count() == 2, "boutons Afficher/Masquer manquants dans le formulaire reset")
        assert_ok(buttons.first.get_attribute("type") == "button",
                  "une révélation du mot de passe ne doit pas soumettre le formulaire")
        buttons.first.click()
        assert_ok(page.locator("#a").get_attribute("type") == "text",
                  "affichage du nouveau mot de passe inopérant")
        assert_ok(buttons.first.get_attribute("aria-pressed") == "true",
                  "état accessible du bouton non synchronisé")
        page.evaluate("() => window.dispatchEvent(new Event('pagehide'))")
        assert_ok(page.locator("#a").get_attribute("type") == "password",
                  "le mot de passe doit être masqué en quittant la page")
        assert_ok(buttons.first.get_attribute("aria-pressed") == "false",
                  "bouton de révélation non réinitialisé")
        assert_ok(page.locator("#a").input_value() == "EXEMPLE-UNIQUEMENT",
                  "le masquage ne doit pas effacer la saisie")
    finally:
        page.close()


def assert_preferences_save_feedback(browser):
    # Le module officiel est exécuté avec un client synthétique, sans compte
    # ni trafic externe, et des réponses volontairement différées.
    context=browser.new_context(service_workers="block")
    try:
        page=context.new_page()
        context.route("**/*",lambda route: route.continue_() if route.request.url.startswith(BASE) else route.abort())
        context.route("**/preferences-test.html",lambda route: route.fulfill(
            content_type="text/html",body="""<form data-privacy-settings-form inert aria-busy="true">
              <input type="checkbox" name="public_profile"><input type="checkbox" name="allow_ai_personal_data" disabled>
              <button type="submit" disabled>Enregistrer</button></form><p data-privacy-settings-status></p>
              <script type="module" src="/assets/js/v24-preferences.js"></script>"""))
        context.route("**/assets/js/sinjira-supabase.js",lambda route: route.fulfill(
            content_type="text/javascript",body="""export async function requireUser(){return {id:'fixture-user'}}
              window.writes=[];window.pending=[];
              export function setStatus(node,msg,type){node.textContent=msg;node.dataset.type=type;}
              export function getSupabase(){return {from(table){return {
                select(){return {eq(){return {maybeSingle:async()=>({data:{public_profile:false,allow_ai_personal_data:false},error:null})}}}},
                update(payload){return {eq(key,id){window.writes.push({table,payload,key,id});return new Promise((resolve,reject)=>window.pending.push({resolve,reject}));}}},
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
        page.evaluate("window.pending.shift().resolve({error:null})")
        page.wait_for_function("() => !document.querySelector('button').disabled")
        assert_ok("plus récentes" in status.inner_text(),"modification récente annoncée comme enregistrée")
        assert_ok(not checkbox.is_checked(),"saisie écrasée")
        button.click()
        page.evaluate("window.pending.shift().reject(new Error('fixture réseau'))")
        page.wait_for_function("() => !document.querySelector('button').disabled")
        assert_ok("saisie est conservée" in status.inner_text(),"erreur réseau non signalée")
        button.click()
        page.evaluate("window.pending.shift().resolve({error:null})")
        page.wait_for_function("() => !document.querySelector('button').disabled")
        assert_ok("enregistrées dans votre compte" in status.inner_text(),"relance non confirmée")
        assert_ok(page.evaluate("window.writes.every(w=>w.key==='user_id'&&w.id==='fixture-user'&&!('allow_ai_personal_data' in w.payload))"),"périmètre d’écriture modifié")
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
                assert_preferences_save_feedback(browser)
                print(f"OK {ENGINE}: quatre formulaires Auth à 240–1440px + révélation locale sûre")
            finally:
                context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    run()
