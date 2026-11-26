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


def inspect_member_forms(browser):
    # Recette de présentation : aucun module applicatif, aucune session ni
    # soumission. Les valeurs et autorisations du serveur ne sont pas testées.
    context=browser.new_context(java_script_enabled=False,service_workers="block",
        locale="fr-CA",reduced_motion="reduce",viewport={"width":390,"height":844})
    try:
        page=context.new_page()
        for path in ("compte/profil.html","compte/parametres.html"):
            response=page.goto(urljoin(BASE,path),wait_until="domcontentloaded",timeout=30_000)
            assert_ok(response is not None and response.ok,"page membre inaccessible")
            if path.endswith("profil.html"):
                page.locator("[data-optional-private-profile] summary").click()
                assert_ok(page.locator("[data-optional-private-profile]").get_attribute("open") is not None,
                          "réglages facultatifs inaccessibles")
            for width,zoom in ((240,"100%"),(320,"200%"),(390,"100%"),(768,"100%"),(1440,"100%")):
                page.set_viewport_size({"width":width,"height":844})
                page.evaluate("(zoom)=>document.documentElement.style.fontSize=zoom",zoom)
                state=page.evaluate("""() => {
                  const controls=[...document.querySelectorAll('main .account-form .field input:not([type=hidden]),main .account-form select,main .account-form textarea,main .btn,main summary,main .account-check')].filter(e=>e.getBoundingClientRect().width>0);
                  return {count:controls.length,overflow:document.documentElement.scrollWidth>innerWidth+2,
                    offenders:controls.filter(e=>{const r=e.getBoundingClientRect();return r.left<-2||r.right>innerWidth+2||r.height<47.5}).map(e=>e.id||e.className||e.tagName),
                    status:[...document.querySelectorAll('main .account-status')].every(e=>e.getAttribute('role')==='status'&&e.getAttribute('aria-live')==='polite')};
                }""")
                assert_ok(state["count"]>=5 and not state["overflow"] and not state["offenders"] and state["status"],
                          f"formulaire {path}, {width}px / {zoom}: {state}")
            page.evaluate("document.documentElement.style.fontSize=''")
            if path.endswith("parametres.html"):
                assert_ok(page.locator('[name="allow_ai_personal_data"]').is_disabled(),
                          "option IA privée doit rester désactivée")
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
                inspect_member_forms(browser)
                print(f"OK {ENGINE}: quatre formulaires Auth à 240–1440px + révélation locale sûre")
            finally:
                context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    run()
