#!/usr/bin/env python3
"""Parcours réel 18+ Projet Nova, Chromium/Firefox/WebKit, aucun envoi live."""
import os
from playwright.sync_api import sync_playwright
from nova_network_stall_helpers import check_stalled_fetch

BROWSER = os.environ.get("BROWSER", "chromium")
URL = "http://127.0.0.1:4173/projets/projet-nova/sondage.html"


def require(condition, message):
    if not condition:
        raise AssertionError(f"{BROWSER}: {message}")


def main():
    require(BROWSER in {"chromium", "firefox", "webkit"}, "moteur non autorisé")
    with sync_playwright() as playwright:
        browser = getattr(playwright, BROWSER).launch()
        page = browser.new_page(
            locale="fr-CA", viewport={"width": 390, "height": 844},
            reduced_motion="reduce",
        )
        sent = []
        page.on("request", lambda request:
                sent.append(request.url) if request.method == "POST" else None)
        try:
            # L'accueil Nova doit exposer les trois parcours dans une section
            # unique, y compris sur mobile, sans renvoyer vers une URL cassée.
            entry = browser.new_page(
                locale="fr-CA", viewport={"width": 390, "height": 844},
                reduced_motion="reduce",
            )
            entry_posts = []
            entry.on("request", lambda req: entry_posts.append(req.url)
                     if req.method == "POST" else None)
            entry.goto("http://127.0.0.1:4173/projets/projet-nova/",
                       wait_until="domcontentloaded", timeout=30_000)
            directory = entry.locator("#consultations")
            require(directory.is_visible(), "Annuaire Nova des trois parcours invisible")
            cards = directory.locator(".nova-survey-directory-card")
            require(cards.count() == 3, "Trois cartes attendues sur l'accueil Nova")
            require(entry.evaluate(
                "document.documentElement.scrollWidth <= innerWidth + 2"
            ), "Débordement mobile de l'annuaire des sondages/Boussole")
            for button_id, route, heading, image in [
                ("nova-survey-directory-40", "consultation-40.html", "#sondage-titre",
                 "assets/nova-sondage-icone.webp"),
                ("nova-survey-directory-64", "sondage.html", "#sondage-titre",
                 "assets/nova-sondage-icone.webp"),
                ("nova-survey-directory-compass", "boussole-electorale.html",
                 "#compass-start", "../../assets/media/nova-boussole-electorale-v2.webp"),
            ]:
                link = directory.locator("#" + button_id)
                require(link.is_visible(), "Bouton d'accès masqué : " + button_id)
                require(link.get_attribute("href") == route, "URL incorrecte : " + button_id)
                icon = directory.locator(
                    'a[href="' + route + '"] img[src="' + image + '"]'
                )
                require(icon.count() == 1, "Image officielle absente : " + button_id)
                icon.scroll_into_view_if_needed()
                require(icon.evaluate(
                    "(img) => img.complete && img.naturalWidth > 0"
                ), "Image officielle non chargée : " + button_id)
                link.click()
                require(entry.url.endswith("/projets/projet-nova/" + route),
                        "Navigation d'accueil incorrecte : " + button_id)
                entry.locator(heading).wait_for(state="visible", timeout=15_000)
                entry.goto("http://127.0.0.1:4173/projets/projet-nova/",
                           wait_until="domcontentloaded")
            require(entry_posts == [], "La navigation d'accueil envoie des opinions")
            # Le registre public doit rester visible et contrôlable sans
            # révéler le moindre bulletin, même quand la collecte est fermée.
            results_link = directory.locator("#nova-public-results-link")
            require(results_link.count() == 1 and
                    results_link.get_attribute("href") == "resultats-sondages.html",
                    "Accès aux résultats anonymisés absent de l'accueil Nova")
            results = browser.new_page(
                locale="fr-CA", viewport={"width": 390, "height": 844},
                reduced_motion="reduce",
            )
            result_posts = []
            results.on("request", lambda req: result_posts.append(req.url)
                       if req.method == "POST" else None)
            results.goto(
                "http://127.0.0.1:4173/projets/projet-nova/resultats-sondages.html",
                wait_until="domcontentloaded", timeout=30_000)
            results.wait_for_function(
                "() => document.querySelectorAll('#results-question-list li').length === 40",
                timeout=15_000,
            )
            require("Aucun résultat publié" in results.locator("#results-state").inner_text(),
                    "Faux résultats ou état de collecte trompeur sur 40 questions")
            require(results.locator(".nova-results-bar-item").count() == 0,
                    "Des décomptes figurent dans l'état public fermé")
            results.locator("#results-show-64").click()
            results.wait_for_function(
                "() => document.querySelectorAll('#results-question-list li').length === 64",
                timeout=15_000,
            )
            require(results.locator("#results-show-64").get_attribute("aria-pressed") == "true",
                    "Basculement accessible vers les 64 propositions indisponible")
            require(results.locator(".nova-results-bar-item").count() == 0,
                    "La page des 64 questions affiche des résultats non autorisés")
            require(results.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
                    "Débordement mobile sur les résultats anonymisés")
            require(result_posts == [], "Le registre public a envoyé une opinion")
            results.close()
            # Premier chargement en panne puis récupération via bouton accessible :
            # aucune réponse réelle ni chiffre ne peut être reconstitué.
            temporary = browser.new_page(
                locale="fr-CA", viewport={"width": 390, "height": 844},
                reduced_motion="reduce",
            )
            temporary_posts = []
            temporary.on("request", lambda req: temporary_posts.append(req.url)
                         if req.method == "POST" else None)
            intercepted = {"count": 0}
            def interrupt_first_registry(route):
                intercepted["count"] += 1
                if intercepted["count"] == 1:
                    route.abort("failed")
                else:
                    route.continue_()
            temporary.route("**/resultats-sondages-publics-v1.json", interrupt_first_registry)
            temporary.goto(
                "http://127.0.0.1:4173/projets/projet-nova/resultats-sondages.html",
                wait_until="domcontentloaded", timeout=30_000)
            retry = temporary.locator("#results-retry")
            retry.wait_for(state="visible", timeout=15_000)
            require(temporary.evaluate(
                "document.documentElement.scrollWidth <= innerWidth + 2"),
                "Le bouton Réessayer déborde de l'écran mobile")
            require("indisponibles ou non validées" in
                    temporary.locator("#results-state").inner_text(),
                    "Registre en panne : état de vérification trompeur")
            require(temporary.locator(".nova-results-bar-item").count() == 0,
                    "Registre en panne : des comptes ont été affichés")
            temporary.locator("#results-show-64").click()
            retry.click()
            temporary.wait_for_function(
                "() => document.querySelectorAll('#results-question-list li').length === 64"
                " && document.querySelector('#results-retry').hidden",
                timeout=15_000)
            require(intercepted["count"] == 2,
                    "Le bouton Réessayer n'a pas relancé le registre public")
            require("Aucun résultat publié" in
                    temporary.locator("#results-state").inner_text(),
                    "Après reprise, le registre fermé affiche de faux résultats")
            require(temporary.locator("#results-show-64").get_attribute(
                    "aria-pressed") == "true",
                    "La reprise a perdu la sélection des 64 propositions")
            require(temporary.locator(".nova-results-bar-item").count() == 0,
                    "Une reprise réseau a révélé des statistiques interdites")
            require(temporary_posts == [], "Une reprise réseau a envoyé une opinion")
            temporary.close()
            # Contrats navigateur : une source figée est interrompue, et
            # aucun chiffre fictif ni démarrage de sondage n'est possible.
            check_stalled_fetch(browser,
                "http://127.0.0.1:4173/projets/projet-nova/resultats-sondages.html",
                "resultats-sondages-publics-v1.json", "results", "Registre public bloqué")
            check_stalled_fetch(browser, URL,
                "sondage-questions-v1.json", "survey", "Questionnaire 64 bloqué")
            entry.close()
            response = page.goto(URL, wait_until="domcontentloaded", timeout=30_000)
            require(response is not None and response.status in (200, 304),
                    "page de sondage non disponible localement")
            require("Cette case ne constitue pas un consentement à une future collecte." in
                    page.locator("label:has(#sondage-consent)").inner_text(),
                    "La démonstration exige un nouvel accord de collecte pour une future activation")
            require(page.locator("#sondage-form").get_attribute("autocomplete") == "off",
                    "Autocomplétion du questionnaire non désactivée")
            require(page.locator("#sondage-consent").get_attribute("autocomplete") == "off",
                    "Autocomplétion de l'accord de démonstration non désactivée")
            # Les réponses ne doivent être saisissables qu'une fois le
            # manifeste chargé et les deux cases vérifiées.
            require("Une fois une contribution agrégée" in page.locator("#sondage-privacy-warning").inner_text(),
                    "Avertissement de retrait des agrégats absent")
            page.locator("#sondage-age").check()
            page.locator("#sondage-consent").uncheck()
            require(page.locator("#sondage-start").is_disabled(),
                    "Consentement non exigé avant démarrage")
            page.locator("#sondage-age").uncheck()
            page.locator("#sondage-consent").check()
            require(page.locator("#sondage-start").is_disabled(),
                    "Contrôle 18 ans contournable")
            page.locator("#sondage-age").check()
            page.locator("#sondage-start").wait_for(state="attached")
            page.wait_for_function(
                "() => !document.getElementById('sondage-start').disabled",
                timeout=15_000,
            )
            page.locator("#sondage-start").click()
            require(not page.locator("#sondage-questionnaire").is_hidden(),
                    "Première question non affichée")
            require(page.locator("#sondage-choices input[type=radio]").first.get_attribute("autocomplete") == "off",
                    "Le navigateur ne doit pas mémoriser automatiquement les choix politiques")
            require(page.locator("#sondage-choices input[type=radio]").count() == 8,
                    "Échelle -3..+3 et Sans opinion non disponible")
            page.locator("#sondage-choices input[value='1']").check()
            page.locator("#sondage-next").click()
            require("Question 2 sur 64" in page.locator("#sondage-position").inner_text(),
                    "Progression de la question 2 incorrecte")
            page.locator("#sondage-choices input[value='skip']").check()
            page.locator("#sondage-back").click()
            require(page.locator("#sondage-choices input[value='1']").is_checked(),
                    "Retour à la question 1 : choix perdu")
            page.locator("#sondage-next").click()
            require(page.locator("#sondage-choices input[value='skip']").is_checked(),
                    "Retour à la question 2 : Sans opinion perdu")
            page.locator("#sondage-next").click()
            for position in range(3, 65):
                require(
                    f"Question {position} sur 64" in page.locator("#sondage-position").inner_text(),
                    f"Question {position} non présentée individuellement",
                )
                page.locator("#sondage-choices input[value='skip']").check()
                page.locator("#sondage-next").click()
            require(not page.locator("#sondage-finish").is_hidden(),
                    "Écran final absent après 64 questions")
            require(page.locator("#sondage-review-list li").count() == 64,
                    "Récapitulatif des 64 choix absent")
            require("Votre choix : Plutôt d’accord" in
                    page.locator("#sondage-review-list li").first.inner_text(),
                    "Première réponse non affichée")
            require("Sans opinion" in page.locator("#sondage-review-list li").last.inner_text(),
                    "La réponse Sans opinion n'apparaît pas dans le récapitulatif")
            require(page.locator("#sondage-submit").is_disabled(),
                    "Envoi politique non approuvé activé par erreur")
            require("non ouverte" in page.locator("#sondage-submit-status").inner_text(),
                    "État réel de la collecte masqué")
            require(sent == [], f"Une réponse a quitté le navigateur : {sent}")
            page.locator("#sondage-review-list li").first.locator("button").click()
            require("Question 1 sur 64" in page.locator("#sondage-position").inner_text(),
                    "Modification directe impossible")
            require(page.locator("#sondage-choices input[value='1']").is_checked(),
                    "Réponse originale perdue")
            page.locator("#sondage-choices input[value='-2']").check()
            page.locator("#sondage-next").click()
            require(not page.locator("#sondage-finish").is_hidden(),
                    "Retour au récapitulatif impossible après correction")
            require("Votre choix : En désaccord" in
                    page.locator("#sondage-review-list li").first.inner_text(),
                    "Réponse corrigée non reflétée")
            require("Sans opinion" in page.locator("#sondage-review-list li").last.inner_text(),
                    "Dernière réponse perdue pendant la correction")
            page.locator("#sondage-review").click()
            require(not page.locator("#sondage-questionnaire").is_hidden(),
                    "Relecture des questions impossible")
            require("Question 1 sur 64" in page.locator("#sondage-position").inner_text(),
                    "La relecture ne démarre pas à la première question")
            require(page.locator("#sondage-choices input[value='-2']").is_checked(),
                    "Réponse corrigée perdue")
            require(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
                    "Débordement horizontal en 390 px")
            page.once("dialog", lambda dialog: dialog.accept())
            page.locator("#sondage-reset-question").click()
            require(not page.locator("#sondage-introduction").is_hidden(),
                    "Retour au consentement après effacement impossible")
            require(not page.locator("#sondage-age").is_checked(),
                    "Attestation 18 ans non réinitialisée")
            require(not page.locator("#sondage-consent").is_checked(),
                    "Consentement non réinitialisé")
            require(page.locator("#sondage-start").is_disabled(),
                    "Démarrage encore autorisé après retrait du consentement")
            page.locator("#sondage-age").check()
            page.locator("#sondage-consent").check()
            page.locator("#sondage-start").click()
            require(page.locator("#sondage-next").is_disabled(),
                    "Des opinions sont restées dans la mémoire après effacement")
            require(not page.locator("#sondage-choices input[value='1']").is_checked(),
                    "Ancienne réponse retrouvée après purge")
            require(sent == [], f"Des réponses ont été envoyées malgré la collecte fermée : {sent}")
            page.locator("#sondage-choices input[value='1']").check()
            # La purge doit être immédiate sur pagehide, avant même une
            # restauration d'historique (bfcache) ou un nouveau pageshow.
            page.evaluate("window.dispatchEvent(new Event('pagehide'))")
            require(page.locator("#sondage-introduction").is_visible() and
                    page.locator("#sondage-questionnaire").is_hidden(),
                    "Départ de page : questionnaire personnel encore visible")
            require(not page.locator("#sondage-age").is_checked() and
                    not page.locator("#sondage-consent").is_checked() and
                    page.locator("#sondage-choices").locator("input").count() == 0,
                    "Départ de page : réponses personnelles ou consentement conservés")
            require(page.locator("#sondage-start").is_disabled(),
                    "Départ de page : parcours réactivable sans accord")
            page.goto("http://127.0.0.1:4173/projets/projet-nova/", wait_until="domcontentloaded")
            page.go_back(wait_until="domcontentloaded")
            require(not page.locator("#sondage-introduction").is_hidden(),
                    "Retour historique : le sondage ne revient pas à l'introduction")
            require(not page.locator("#sondage-age").is_checked()
                    and not page.locator("#sondage-consent").is_checked(),
                    "Retour historique : attestation 18+ ou accord de démonstration conservé")
            require(page.locator("#sondage-start").is_disabled(),
                    "Retour historique : démarrage sans nouvelle attestation")
            page.reload(wait_until="domcontentloaded")
            require(not page.locator("#sondage-introduction").is_hidden()
                    and not page.locator("#sondage-age").is_checked()
                    and not page.locator("#sondage-consent").is_checked(),
                    "Rechargement : confirmation d'âge ou accord restauré")
            require(page.locator("#sondage-start").is_disabled(),
                    "Rechargement : questionnaire lancé sans attestation")
            require(sent == [], "Historique/rechargement : requête de collecte non autorisée")
            page.set_viewport_size({"width": 1440, "height": 900})
            require(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),
                    "Débordement horizontal sur ordinateur")
            # Test négatif réel : le manifeste 64 conserve 64 questions et un
            # JSON valide, mais sa première formulation est modifiée en transit.
            # L'empreinte SHA-256 doit bloquer le parcours avant toute saisie.
            tampered = browser.new_page(locale="fr-CA")
            def modified_survey(route):
                import json
                corpus = json.loads(route.fetch().body())
                corpus["questions"][0]["text"] += " (texte non approuvé)"
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps(corpus, ensure_ascii=False))
            tampered.route("**/sondage-questions-v1.json", modified_survey)
            tampered.goto(URL, wait_until="domcontentloaded", timeout=30_000)
            tampered.locator("#sondage-introduction [role='alert']").wait_for(
                state="visible", timeout=10_000)
            require(tampered.locator("#sondage-start").is_disabled(),
                    "Sondage 64 démarrable malgré un manifeste falsifié")
            tampered.close()
            # Un cache/CDN désynchronisé entre le sondage et sa source 64
            # doit bloquer le démarrage, pas poser une question altérée.
            altered = browser.new_page(locale="fr-CA")
            def modified_compass(route):
                upstream = route.fetch()
                import json
                corpus = json.loads(upstream.body())
                corpus["questions"][0]["text"] += " VERSION ALTÉRÉE"
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps(corpus, ensure_ascii=False))
            altered.route("**/boussole-electorale-v2.json", modified_compass)
            altered.goto(URL, wait_until="domcontentloaded", timeout=30_000)
            altered.locator("#sondage-introduction [role='alert']").wait_for(state="visible", timeout=10_000)
            require(altered.locator("#sondage-start").is_disabled(),
                    "Sondage 64 démarrable malgré une question divergente de la Boussole")
            altered.close()
            # Métadonnées modifiées mais textes strictement identiques :
            # le questionnaire citoyen doit refuser le fichier source.
            altered_metadata=browser.new_page(locale="fr-CA")
            def wrong_source_metadata(route):
                import json
                corpus=json.loads(route.fetch().body())
                corpus["published"]="2026-10-07"
                route.fulfill(status=200,content_type="application/json",
                              body=json.dumps(corpus,ensure_ascii=False))
            altered_metadata.route("**/boussole-electorale-v2.json",wrong_source_metadata)
            altered_metadata.goto(URL,wait_until="domcontentloaded",timeout=30_000)
            altered_metadata.locator("#sondage-introduction [role='alert']").wait_for(
                state="visible",timeout=10_000)
            require(altered_metadata.locator("#sondage-start").is_disabled(),
                    "Les métadonnées Boussole ont changé sans nouvelle empreinte")
            altered_metadata.close()
            # L'empreinte Boussole verrouille AUSSI les métadonnées : des
            # formulations identiques ne suffisent pas.
            def corrupt_compass_metadata(route):
                import json
                source=json.loads(route.fetch().body())
                source["published"]="2026-10-07"
                route.fulfill(status=200,content_type="application/json",
                              body=json.dumps(source,ensure_ascii=False))
            tampered=browser.new_page(locale="fr-CA")
            tampered.route("**/boussole-electorale-v2.json",corrupt_compass_metadata)
            tampered.goto(
                "http://127.0.0.1:4173/projets/projet-nova/boussole-electorale.html",
                wait_until="domcontentloaded",timeout=30_000)
            tampered.locator("#compass-questionnaire-retry").wait_for(
                state="visible",timeout=10_000)
            require(tampered.locator("#compass-start").is_disabled(),
                    "Boussole démarrable malgré un corpus modifié")
            tampered.locator("#compass-evidence-retry").wait_for(
                state="visible",timeout=10_000)
            tampered.unroute("**/boussole-electorale-v2.json",corrupt_compass_metadata)
            tampered.locator("#compass-questionnaire-retry").click()
            tampered.wait_for_function(
                "!document.querySelector('#compass-start').disabled")
            tampered.locator("#compass-evidence-retry").click()
            tampered.locator(
                "#compass-evidence-parties .compass-evidence-card").first.wait_for(
                state="visible",timeout=10_000)
            tampered.close()
            # Recette Boussole indépendante de la CI générale (souvent ignorée
            # sur PR brouillon) : exécuter chaque navigateur de l'aperçu Nova.
            compass_context = browser.new_context(
                locale="fr-CA", viewport={"width": 390, "height": 844},
                reduced_motion="reduce", service_workers="block",
            )
            compass = compass_context.new_page()
            import json
            compass_posts = []
            compass.on("request", lambda request:
                       compass_posts.append(request.url) if request.method == "POST" else None)
            evidence_pattern = "**/boussole-preuves-2026.json"
            def unsafe_evidence(route):
                source = json.loads(route.fetch().body())
                source["evidenceRecords"][0]["sourceUrl"] = "javascript:alert(1)"
                route.fulfill(status=200, content_type="application/json",
                              body=json.dumps(source, ensure_ascii=False))
            compass.route(evidence_pattern, unsafe_evidence)
            compass.goto("http://127.0.0.1:4173/projets/projet-nova/boussole-electorale.html",
                         wait_until="domcontentloaded", timeout=30_000)
            compass.locator("#compass-evidence-retry").wait_for(state="visible", timeout=10_000)
            require(compass.locator("#compass-evidence-parties .compass-evidence-card").count() == 0,
                    "Lien documentaire non HTTPS accepté par la Boussole")
            compass.unroute(evidence_pattern, unsafe_evidence)
            compass.locator("#compass-evidence-retry").click()
            compass.locator("#compass-evidence-parties .compass-evidence-card").first.wait_for(
                state="visible", timeout=10_000)
            require(compass.locator("#compass-evidence-parties .compass-evidence-card").count() == 22,
                    "Reprise de l'explorateur documentaire incomplète")
            # Une modification de registre ou de sources qui conserve la
            # structure JSON doit bloquer l'explorateur entier (échec fermé).
            for file_name in ("boussole-partis-2026.json",
                              "boussole-sources-partis-2026.json"):
                altered_document = browser.new_page(locale="fr-CA")
                pattern = "**/" + file_name
                def mutate_document(route):
                    document = json.loads(route.fetch().body())
                    document["version"] = "NON_APPROUVEE"
                    route.fulfill(status=200, content_type="application/json",
                                  body=json.dumps(document, ensure_ascii=False))
                altered_document.route(pattern, mutate_document)
                altered_document.goto(
                    "http://127.0.0.1:4173/projets/projet-nova/boussole-electorale.html",
                    wait_until="domcontentloaded", timeout=30_000)
                altered_document.locator("#compass-evidence-retry").wait_for(
                    state="visible", timeout=10_000)
                require(altered_document.locator(
                    "#compass-evidence-parties .compass-evidence-card").count() == 0,
                    "Corpus documentaire falsifié présenté : " + file_name)
                altered_document.unroute(pattern, mutate_document)
                altered_document.locator("#compass-evidence-retry").click()
                altered_document.locator(
                    "#compass-evidence-parties .compass-evidence-card").first.wait_for(
                        state="visible", timeout=10_000)
                altered_document.close()
            compass.wait_for_function("!document.getElementById('compass-start').disabled")
            compass.locator("#compass-start").click()
            full = compass.evaluate("""() => {
                for(let i=0;i<64;i++){
                    const radio=document.querySelector('#compass-question-stage input[type=radio]');
                    if(!radio) return false;
                    radio.click();
                    document.querySelector('#compass-next').click();
                }
                return !document.querySelector('#compass-results').hidden &&
                    document.querySelectorAll('#compass-results-grid .compass-result-card').length === 16;
            }""")
            require(full, "Parcours complet de la Boussole (64 propositions) non terminé")
            share = compass.evaluate("""async () => {
                const calls=[];
                Object.defineProperty(navigator,'clipboard',{
                    configurable:true,value:{writeText:async value=>calls.push(value)}
                });
                const b=document.querySelector('#compass-copy-result');
                b.click();await Promise.resolve();b.click();await Promise.resolve();
                return calls.length===2 && calls[0]===calls[1] &&
                    document.querySelector('#compass-status').textContent.includes('Résumé copié');
            }""")
            require(share, "Le partage répété de la Boussole est en échec")
            compass.locator("#compass-reset").click()
            cleared = compass.evaluate("""() =>
                document.querySelector('#compass-results').hidden &&
                !document.querySelector('#compass-question-stage').childElementCount &&
                !document.querySelector('#compass-results-grid').childElementCount &&
                !document.querySelector('#compass-radar').childElementCount &&
                !document.querySelector('#compass-summary').textContent &&
                document.querySelector('#compass-share-email').getAttribute('href')==='mailto:'
            """)
            require(cleared, "La réinitialisation de la Boussole laisse des opinions dans le DOM")
            compass.locator("#compass-start").click()
            partial = compass.evaluate("""() => {
                for(let i=0;i<64;i++){
                    const radio=document.querySelector(
                        '#compass-question-stage input[value="'+(i===0?'-3':'skip')+'"]');
                    if(!radio) return false;
                    radio.click();document.querySelector('#compass-next').click();
                }
                return !document.querySelector('#compass-results').hidden &&
                    [...document.querySelectorAll('#compass-results-grid .compass-result-head strong')]
                      .every(x=>x.textContent.trim()==='—') &&
                    document.querySelector('#compass-radar').textContent.includes('pas encore assez');
            }""")
            require(partial, "Axe avec une seule réponse présenté comme un score fiable")
            compass.evaluate("window.dispatchEvent(new Event('pagehide'))")
            require(compass.evaluate("""() =>
                document.querySelector('#compass-results').hidden &&
                !document.querySelector('#compass-results-grid').childElementCount &&
                !document.querySelector('#compass-question-stage').childElementCount
            """), "La navigation conserve un profil sensible dans la page")
            require(compass_posts == [], "La Boussole a transmis des réponses politiques")
            compass_context.close()
            print(f"OK {BROWSER}: Nova 18+, consentement, 64 questions, "
                  "relecture, aucun POST et collecte désactivée")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
