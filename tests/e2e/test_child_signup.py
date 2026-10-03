#!/usr/bin/env python3
import os
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def run() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            locale="fr-CA",
            viewport={"width": 1280, "height": 900},
            reduced_motion="reduce",
        )
        page = context.new_page()
        page_errors = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        # Le test ne communique jamais avec Supabase production. Il remplace uniquement
        # l'import public du client par un état local déterministe : session parent active,
        # puis session libre après la déconnexion locale.
        page.route(
            "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm",
            lambda route: route.fulfill(
                status=200,
                content_type="application/javascript",
                headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-store"},
                body="""
let active = true;
export function createClient(){
  return {
    auth: {
      getSession: async () => {
        await new Promise(resolve => setTimeout(resolve, 500));
        return {data:{session:active ? {user:{id:'parent-test'}} : null},error:null};
      },
      signOut: async () => { active = false; return {error:null}; },
      signUp: async (payload) => {
        globalThis.__SINJIRA_TEST_SIGNUP_PAYLOAD = payload;
        return {data:{session:null},error:null};
      }
    }
  };
}
""",
            ),
        )

        response = page.goto(
            urljoin(BASE_URL, "compte/inscription.html"),
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        assert_true(response is not None and response.status < 400, "Page d'inscription enfant inaccessible")

        warning = page.locator("[data-signup-session-warning]")
        signout = page.locator("[data-signup-session-signout]")
        submit = page.locator('[data-signup-form] [type="submit"]')
        assert_true(submit.is_disabled(), "Le bouton de création est actif avant la vérification de la frontière de session")
        page.wait_for_function(
            """() => {
                const warning = document.querySelector('[data-signup-session-warning]');
                const submit = document.querySelector('[data-signup-form] [type="submit"]');
                return warning && !warning.hidden && submit && submit.disabled;
            }""",
            timeout=10_000,
        )
        assert_true(warning.is_visible(), "Une session parent active n'affiche pas l'avertissement")
        assert_true(submit.is_disabled(), "La création reste possible pendant une session parent active")

        signout.click()
        page.wait_for_function(
            """() => {
                const warning = document.querySelector('[data-signup-session-warning]');
                const submit = document.querySelector('[data-signup-form] [type="submit"]');
                return warning && warning.hidden && submit && !submit.disabled;
            }""",
            timeout=10_000,
        )
        assert_true(warning.is_hidden(), "L'avertissement de session reste affiché après la déconnexion locale")
        assert_true(not submit.is_disabled(), "La création ne se réouvre pas après séparation confirmée des sessions")

        child_birth = page.evaluate(
            """() => {
                const d = new Date();
                d.setFullYear(d.getFullYear() - 11);
                const y = d.getFullYear();
                const m = String(d.getMonth() + 1).padStart(2, '0');
                const day = String(d.getDate()).padStart(2, '0');
                return `${y}-${m}-${day}`;
            }"""
        )
        page.locator("#signup-birth-date").fill(child_birth)
        page.wait_for_function(
            """() => {
                const guide = document.querySelector('[data-child-guardian-guide]');
                const wrap = document.querySelector('[data-guardian-code-wrap]');
                const code = document.querySelector('[data-guardian-code]');
                const contributor = document.querySelector('[data-contributor-panel]');
                return guide && !guide.hidden && wrap && !wrap.hidden && code && code.required === true && contributor && contributor.hidden;
            }""",
            timeout=10_000,
        )

        assert_true(page.locator("[data-child-guardian-guide]").is_visible(), "Guide parental absent à exactement 11 ans")
        assert_true(page.locator("[data-guardian-code-wrap]").is_visible(), "Champ code parental absent à exactement 11 ans")
        assert_true(page.locator("[data-guardian-code]").get_attribute("required") is not None, "Code parental non obligatoire à exactement 11 ans")
        assert_true(page.locator("[data-contributor-panel]").is_hidden(), "Programme Contributeur visible pour un enfant de 11 ans")

        # Le parcours visible doit réellement transmettre le code au hook Auth.
        # Cette preuve ferme l'écart entre « champ présent » et « donnée envoyée au serveur ».
        page.locator("#signup-name").fill("Enfant navigateur 11")
        page.locator("#signup-email").fill("child-browser-11@example.test")
        page.locator("#signup-password").fill("Child-Browser-11-2026!")
        page.locator("#signup-confirm").fill("Child-Browser-11-2026!")
        page.locator("#signup-gender").select_option(label="Homme")
        page.locator("[data-guardian-code]").fill("youth-abcd123456")
        page.locator('[data-signup-form] input[type="checkbox"][required]').check()
        submit.click()

        page.wait_for_function(
            "() => Boolean(window.__SINJIRA_TEST_SIGNUP_PAYLOAD)",
            timeout=10_000,
        )
        signup_payload = page.evaluate("() => window.__SINJIRA_TEST_SIGNUP_PAYLOAD")
        metadata = signup_payload.get("options", {}).get("data", {})

        assert_true(metadata.get("guardian_code") == "YOUTH-ABCD123456", "Le code parental saisi n'est pas transmis ou normalisé dans signUp")
        assert_true(metadata.get("birth_date") == child_birth, "La date de naissance 11 ans n'est pas transmise au serveur")
        assert_true(metadata.get("date_of_birth") == child_birth, "Le champ de compatibilité date_of_birth diverge")
        assert_true(metadata.get("account_age_band") == "child_11_12", "Le payload navigateur ne marque pas la bande enfant 11–12")
        assert_true(metadata.get("guardian_controls_required") is True, "Le payload ne marque pas la supervision comme obligatoire")
        assert_true(metadata.get("initial_contributor_opt_in") is False, "Le navigateur tente d'activer la contribution pour un enfant")
        assert_true(metadata.get("initial_share_free_text") is False, "Le navigateur tente d'activer le texte libre pour un enfant")
        assert_true(not page_errors, "Erreur JavaScript dans le parcours enfant: " + " | ".join(page_errors[:5]))

        context.close()
        browser.close()
        print("OK navigateur enfant 11 ans: session séparée, code requis et réellement transmis à signUp, bande child_11_12 et contribution neutralisée.")


if __name__ == "__main__":
    run()
