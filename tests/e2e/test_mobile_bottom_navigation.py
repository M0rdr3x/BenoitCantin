#!/usr/bin/env python3
"""Recette navigateur SINJIRA : barre de navigation mobile, zoom et bandeau PWA.

Fixture privée locale pour les routes de compte : aucune session, donnée,
permission Supabase ou requête vers un service externe n'est utilisée.
"""
import os
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
ENGINE = os.environ.get("BROWSER", "chromium").strip().lower()
ROOT = Path(__file__).resolve().parents[2]
WIDTHS = (240, 320, 390, 768, 1024)
SHELL_MARKUP = """<!doctype html><html lang="fr-CA"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="stylesheet" href="/assets/css/site.css">
<script defer src="/assets/js/sinjira-pwa-install.js?v=24.4.103"></script>
</head><body class="account-page" data-sinjira-ux="v1">
<main id="contenu"><h1>Mon compte : contrôle de navigation</h1><a href="/app/">Fil communautaire</a></main>
</body></html>"""


def verify(condition, message):
    if not condition:
        raise AssertionError(f"{ENGINE}: {message}")


def navigate_account(context, path):
    page = context.new_page()
    try:
        response = page.goto(urljoin(BASE, path), wait_until="domcontentloaded", timeout=30_000)
        verify(response is not None and response.status < 400, f"page fixture absente : {path}")
        if path != "compte/connexion.html":
            page.locator("[data-sinjira-account-mobile-nav]").wait_for(timeout=12_000)
        return page
    except Exception:
        page.close()
        raise


def account_geometry(page):
    return page.evaluate("""() => {
      const nav=document.querySelector('[data-sinjira-account-mobile-nav]');
      const links=[...(nav?.querySelectorAll('a')||[])];
      const box=nav?.getBoundingClientRect();
      const card=document.querySelector('.sinjira-pwa-install[data-sinjira-pwa-install]');
      const cb=card?.getBoundingClientRect();
      const padding=parseFloat(getComputedStyle(document.body).paddingBottom);
      return {width:innerWidth,docOverflow:document.documentElement.scrollWidth>innerWidth+2,
        visible:!!nav && getComputedStyle(nav).display!=='none',
        links:links.map(a=>({text:a.textContent.trim(),href:a.getAttribute('href'),
          height:a.getBoundingClientRect().height,font:parseFloat(getComputedStyle(a).fontSize),
          current:a.getAttribute('aria-current'),section:a.hasAttribute('data-current-section')})),
        navHeight:box?.height||0,navTop:box?.top||0,
        reserved:padding,cssHeight:parseFloat(getComputedStyle(document.body)
          .getPropertyValue('--sinjira-account-mobile-nav-height'))||0,
        cardVisible:!!card && getComputedStyle(card).display!=='none',
        cardBottom:cb?.bottom||0,cardHeight:cb?.height||0,
        navScrollable:!!nav && nav.scrollWidth>nav.clientWidth+2};
    }""")


def assert_account_nav(page, width):
    page.set_viewport_size({"width": width, "height": 700})
    page.wait_for_function("""() => {
      const n=document.querySelector('[data-sinjira-account-mobile-nav]');
      return n && (n.getBoundingClientRect().height===0 ||
        Math.abs(parseFloat(getComputedStyle(document.body)
          .getPropertyValue('--sinjira-account-mobile-nav-height'))-
          n.getBoundingClientRect().height)<3);
    }""")
    state = account_geometry(page)
    verify(not state["docOverflow"], f"débordement horizontal : {state}")
    verify(len(state["links"]) == 5, "cinq destinations de navigation attendues")
    if width <= 820:
        verify(state["visible"], f"dock de compte invisible à {width}px")
        verify(all(a["height"] >= 48 and a["font"] >= 12 for a in state["links"]),
               f"libellés ou cibles trop petits : {state}")
        verify(state["reserved"] >= state["navHeight"] + 8,
               f"contenu masqué sous le dock : {state}")
        verify(abs(state["navHeight"] - state["cssHeight"]) <= 3,
               f"hauteur réelle du dock désynchronisée : {state}")
        if width <= 270:
            verify(state["navScrollable"],
                   f"zoom fort : le dock doit défiler dans sa propre zone : {state}")
        else:
            verify(not state["navScrollable"],
                   f"navigation du compte devrait tenir sur {width}px : {state}")
        if state["cardVisible"]:
            verify(state["cardBottom"] <= state["navTop"] - 7,
                   f"bandeau PWA recouvre la navigation : {state}")
    else:
        verify(not state["visible"], "dock ne doit pas masquer le bureau classique")


def check_zoom(page):
    page.set_viewport_size({"width": 320, "height": 640})
    page.evaluate("document.documentElement.style.fontSize='200%'")
    page.wait_for_function("""() => {
      const n=document.querySelector('[data-sinjira-account-mobile-nav]');
      return n && Math.abs(parseFloat(getComputedStyle(document.body)
        .getPropertyValue('--sinjira-account-mobile-nav-height')) -
        n.getBoundingClientRect().height)<3;
    }""")
    state=account_geometry(page)
    verify(not state["docOverflow"], f"zoom 200 % déclenche un débordement : {state}")
    verify(state["reserved"] >= state["navHeight"] + 8,
           f"dock recouvre le contenu en zoom 200 % : {state}")
    verify(all(a["height"] >= 48 for a in state["links"]),
           "cible tactile inaccessible au zoom 200 %")



def check_keyboard_overlap(context):
    # Un clavier virtuel réduit la hauteur utile; aucune donnée réelle ou
    # contrôle d'authentification n'est chargé par cette fixture de compte.
    page = navigate_account(context, "compte/index.html")
    try:
        page.evaluate("""() => {
          const form=document.createElement('form');
          form.innerHTML='<label for="ux-text">Texte fictif</label>'+
            '<input type="text" id="ux-text" autocomplete="off">'+
            '<label for="ux-area">Saisie longue</label>'+
            '<textarea id="ux-area"></textarea>'+
            '<label for="ux-select">Choix</label>'+
            '<select id="ux-select"><option>Fictif</option></select>'+
            '<label for="ux-check"><input type="checkbox" id="ux-check"> Option</label>'+
            '<button type="button" id="ux-button">Terminé</button>';
          document.getElementById('contenu').appendChild(form);
        }""")
        nav = page.locator('[data-sinjira-account-mobile-nav]')
        for width in (240, 320, 390, 768):
            page.set_viewport_size({"width":width, "height":360})
            page.locator('#ux-text').focus()
            page.wait_for_function(
                "() => document.body.classList.contains('sinjira-account-typing')")
            verify(not account_geometry(page)["visible"],
                   f"le dock couvre la saisie à {width}px")
            state = account_geometry(page)
            verify(state["reserved"]<=16 and not state["docOverflow"],
                   f"la marge du dock empêche la saisie à {width}px: {state}")
            verify(not state["cardVisible"],
                   f"l'invitation PWA couvre la saisie à {width}px")
            page.locator('#ux-text').fill("Valeur fictive maintenue")
            page.locator('#ux-area').focus()
            verify(not account_geometry(page)["visible"],
                   f"le dock revient entre deux champs à {width}px")
            page.locator('#ux-select').focus()
            verify(not account_geometry(page)["visible"],
                   f"le sélecteur natif est recouvert à {width}px")
            page.locator('#ux-check').focus()
            page.wait_for_function(
                "() => !document.body.classList.contains('sinjira-account-typing')")
            verify(account_geometry(page)["visible"],
                   f"le dock ne revient pas après la saisie à {width}px")
            verify(page.locator('#ux-text').input_value()=="Valeur fictive maintenue",
                   f"le contenu du champ a été perdu à {width}px")
            page.locator('#ux-text').focus()
            page.locator('#ux-button').focus()
            page.wait_for_function(
                "() => !document.body.classList.contains('sinjira-account-typing')")
            verify(nav.is_visible(),
                   f"la navigation ne revient pas après le bouton à {width}px")
        # Sur ordinateur, le comportement natif des pages de compte reste inchangé.
        page.set_viewport_size({"width":1024,"height":700})
        page.locator('#ux-text').focus()
        verify(account_geometry(page)["reserved"]<100,
               "le clavier fictif ne doit pas créer une marge mobile sur PC")
        page.locator('#ux-button').focus()
    finally:
        page.close()


def check_routes(context):
    page = navigate_account(context, "compte/index.html")
    try:
        for width in WIDTHS:
            assert_account_nav(page, width)
        check_zoom(page)
    finally:
        page.close()

    # Les destinations apparentées ne doivent pas être annoncées comme la page exacte.
    for path, expected_current, expected_section in [
        ("compte/monde-parallele.html", "/compte/monde-parallele.html", None),
        ("compte/securite.html", None, "/compte/profil.html"),
    ]:
        page=navigate_account(context, path)
        try:
            page.set_viewport_size({"width": 390, "height": 700})
            state=account_geometry(page)
            for link in state["links"]:
                if expected_current and link["href"] == expected_current:
                    verify(link["current"] == "page", "page exacte non annoncée")
                elif expected_section and link["href"] == expected_section:
                    verify(link["current"] is None and link["section"],
                           "sous-page incorrectement annoncée comme page active")
                else:
                    verify(link["current"] is None, "plusieurs pages annoncées comme actives")
        finally:
            page.close()


    # Écran très étroit, au premier affichage : l'onglet Profil est à
    # l'extrémité du dock et doit devenir visible sans glissement préalable.
    page = context.new_page()
    try:
        page.set_viewport_size({"width": 240, "height": 700})
        response = page.goto(urljoin(BASE, "compte/securite.html"),
                             wait_until="domcontentloaded", timeout=30_000)
        verify(response is not None and response.status < 400,
               "fixture Sécurité indisponible pour le dock 240 px")
        dock = page.locator("[data-sinjira-account-mobile-nav]")
        dock.wait_for(state="visible", timeout=12_000)
        page.wait_for_function("""() => {
          const nav=document.querySelector('[data-sinjira-account-mobile-nav]');
          const selected=nav?.querySelector('a[data-current-section]');
          if(!nav||!selected) return false;
          const a=selected.getBoundingClientRect(), b=nav.getBoundingClientRect();
          return nav.scrollLeft>15 && a.left>=b.left-2 && a.right<=b.right+2;
        }""", timeout=6_000)
        verify(dock.locator('a[href="/compte/profil.html"]').get_attribute(
            "data-current-section") is not None,
            "l'onglet Profil ne correspond plus à la section Sécurité")
        # Le geste manuel est respecté tant que l'utilisateur ne redimensionne pas.
        dock.evaluate("(el) => {el.scrollLeft=0;}")
        page.wait_for_timeout(150)
        verify(dock.evaluate("(el) => el.scrollLeft") <= 2,
               "la navigation reprend le contrôle contre le glissement de l'utilisateur")
        # Une variation de hauteur seule (barre d'adresse/clavier) doit
        # conserver le balayage manuel au lieu de recentrer sur Profil.
        for height in (360, 840, 700):
            page.set_viewport_size({"width":240,"height":height})
            page.evaluate("() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
            verify(dock.evaluate("(el)=>el.scrollLeft")<=2,
                   f"dock recentré après changement de hauteur {height}px")
        # Une rotation 240 -> 390 -> 240 révèle de nouveau l'onglet actif.
        page.set_viewport_size({"width": 390, "height": 700})
        page.wait_for_function("() => document.querySelector('[data-sinjira-account-mobile-nav]').clientWidth>=380") 
        page.evaluate("() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
        page.set_viewport_size({"width": 240, "height": 700})
        page.wait_for_function("""() => {
          const nav=document.querySelector('[data-sinjira-account-mobile-nav]');
          const selected=nav?.querySelector('a[data-current-section]');
          if(!nav||!selected) return false;
          const a=selected.getBoundingClientRect(), b=nav.getBoundingClientRect();
          return nav.scrollLeft>15 && a.left>=b.left-2 && a.right<=b.right+2;
        }""", timeout=6_000)
    finally:
        page.close()

    page=navigate_account(context, "compte/connexion.html")
    try:
        verify(page.locator("[data-sinjira-account-mobile-nav]").count() == 0,
               "la navigation privée ne doit pas apparaître sur la connexion")
    finally:
        page.close()


def check_app(playwright):
    # Application sociale réelle, en HTML/CSS uniquement; aucun compte ni appel privé.
    browser = getattr(playwright, ENGINE).launch()
    try:
        context=browser.new_context(java_script_enabled=False, locale="fr-CA",
                                    viewport={"width": 320, "height": 700})
        try:
            page=context.new_page()
            response=page.goto(urljoin(BASE, "app/"), wait_until="domcontentloaded", timeout=30_000)
            verify(response is not None and response.status < 400, "application sociale introuvable")
            verify(page.locator(".mobile-app-bottom-nav a").count() == 5,
                   "navigation de l'app incomplète")
            verify(page.locator(".mobile-app-brand img").get_attribute("src") ==
                   "/assets/icons/sinjira-officiel-20261120.png",
                   "emblème officiel SINJIRA manquant")
            # Le débordement global peut être masqué par overflow-x:hidden.
            # Vérifier aussi les rectangles des commandes et du formulaire.
            def verify_composer_layout(width, height, zoom):
                page.set_viewport_size({"width":width,"height":height})
                page.evaluate("(zoom) => document.documentElement.style.fontSize=zoom", zoom)
                geometry=page.evaluate("""() => {
                  const rect = selector => document.querySelector(selector).getBoundingClientRect();
                  const within = r => r.left >= -2 && r.right <= innerWidth+2;
                  const top=rect('.mobile-app-topbar'), brand=rect('.mobile-app-brand');
                  const actions=rect('.mobile-app-top-actions'), main=rect('.mobile-app-main');
                  const composer=rect('.mobile-app-composer'), field=rect('.mobile-app-composer textarea');
                  const submit=rect('.mobile-app-composer-actions button');
                  return { within:[brand,actions,composer,field,submit].every(within),
                    separate: brand.right<=actions.left+2 || brand.bottom<=actions.top+2,
                    mainClear: main.top>=top.bottom-2,
                    fieldContained: field.left>=composer.left-2 && field.right<=composer.right+2,
                    submitContained: submit.left>=composer.left-2 && submit.right<=composer.right+2,
                    submitHeight:submit.height };
                }""")
                verify(all(geometry[k] for k in ("within","separate","mainClear",
                    "fieldContained","submitContained")) and geometry["submitHeight"]>=47.5,
                    f"entête ou publication mal disposés à {width}x{height}, zoom {zoom}: {geometry}")

            for width, height, zoom in ((240,700,"100%"),(320,700,"200%"),
                                         (390,360,"100%"),(768,360,"100%")):
                verify_composer_layout(width,height,zoom)
            page.evaluate("document.documentElement.style.fontSize=''")
            for width in WIDTHS:
                page.set_viewport_size({"width":width,"height":700})
                state=page.evaluate("""() => {
                  const nav=document.querySelector('.mobile-app-bottom-nav');
                  const links=[...nav.querySelectorAll('a')];
                  return {
                    overflow:document.documentElement.scrollWidth>innerWidth+2,
                    links:links.map(a=>({height:a.getBoundingClientRect().height,
                      font:parseFloat(getComputedStyle(a).fontSize)})),
                    scrollable:nav.scrollWidth>nav.clientWidth+2,
                    top:[...document.querySelectorAll('.mobile-app-top-actions a')]
                      .map(a=>a.getBoundingClientRect().height)
                  };
                }""")
                verify(not state["overflow"], f"app sociale déborde à {width}px : {state}")
                verify(all(x["height"]>=48 and x["font"]>=12 for x in state["links"]),
                       f"cibles ou étiquettes du dock app trop petites : {state}")
                verify(all(h>=44 for h in state["top"]),
                       "actions du haut non tactiles")
                if width<=270:
                    verify(state["scrollable"],"dock de l'app illisible en zoom élevé")
        finally:
            context.close()
    finally:
        browser.close()


def run():
    verify(ENGINE in {"chromium","firefox","webkit"}, "navigateur non autorisé")
    with sync_playwright() as playwright:
        browser=getattr(playwright, ENGINE).launch()
        try:
            context=browser.new_context(
                locale="fr-CA",user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
                viewport={"width":390,"height":700},
                reduced_motion="reduce",service_workers="block"
            )
            # Réponse factice uniquement pour les quatre routes de test. Toute
            # navigation à un compte réel est exclue de cette recette.
            for path in ("compte/index.html","compte/monde-parallele.html",
                         "compte/securite.html","compte/connexion.html"):
                context.route("**/"+path, lambda route:route.fulfill(
                    status=200,content_type="text/html; charset=utf-8",body=SHELL_MARKUP))
            try:
                check_routes(context)
                check_keyboard_overlap(context)
            finally:
                context.close()
        finally:
            browser.close()
        check_app(playwright)
    print(f"OK {ENGINE}: dock et PWA mobiles, zoom, ARIA, site social, sans authentification")


if __name__=="__main__":
    run()
