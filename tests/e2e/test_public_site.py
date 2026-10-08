#!/usr/bin/env python3
import json
import os
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:4173/").rstrip("/") + "/"
BROWSER_NAME = os.environ.get("BROWSER", "chromium").strip().lower()
SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
ASSISTANT_VERSION = "24.4.48"
PUBLIC_ROUTES = [
    "",
    "a-propos.html",
    "contact.html",
    "projets/sinjira/",
    "projets/sinjira/registre/",
    "projets/sinjira/communaute/",
    "projets/sinjira/monde-parallele/",
    "projets/projet-nova/",
    "projets/projet-nova/boussole-electorale.html",
    "projets/sinjira/jeux/",
    "projets/sinjira/jeux/fracture-du-reseau-mere/",
]
AUTH_ROUTES = [
    "compte/connexion.html",
    "compte/inscription.html",
    "compte/mot-de-passe-oublie.html",
    "compte/reinitialiser-mot-de-passe.html",
]
EXPECTED_DOORS = {
    "/projets/sinjira/",
    "/projets/sinjira/registre/",
    "/projets/projet-nova/",
    "/projets/projet-nova/boussole-electorale.html",
}
IS_LOCAL = (urlparse(BASE_URL).hostname or "").lower() in {"127.0.0.1", "localhost"}


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def register_error_capture(page, target):
    page.on("pageerror", lambda error: target.append(f"pageerror: {error}"))


def wait_for_assistant(page):
    if page.locator('html[data-disable-sinjira-assistant="true"]').count():
        page.wait_for_load_state("load")
        page.evaluate("window.dispatchEvent(new Event('pointerdown'))")
    page.wait_for_function(
        "([version]) => window.__SINJIRA_ASSISTANT__ && window.__SINJIRA_ASSISTANT__.version === version",
        arg=[ASSISTANT_VERSION],
        timeout=10_000,
    )


def run() -> None:
    assert_true(BROWSER_NAME in SUPPORTED_BROWSERS, f"Navigateur Playwright inconnu: {BROWSER_NAME}")

    with sync_playwright() as p:
        browser_type = getattr(p, BROWSER_NAME)
        browser = browser_type.launch()

        context = browser.new_context(
            locale="fr-CA",
            viewport={"width": 1440, "height": 1000},
            reduced_motion="reduce",
        )
        page = context.new_page()
        page_errors = []
        register_error_capture(page, page_errors)

        for route in PUBLIC_ROUTES:
            url = urljoin(BASE_URL, route)
            response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            assert_true(response is not None, f"Aucune réponse navigateur pour {url}")
            assert_true(response.status < 400, f"HTTP {response.status} pour {url}")
            assert_true(page.locator("main").count() >= 1, f"Repère main absent: {url}")
            assert_true(page.locator("h1").count() >= 1, f"H1 absent: {url}")
            assert_true(bool(page.title().strip()), f"Titre absent: {url}")

        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_function(
            "document.querySelector('link[data-sinjira-browser-compat]') !== null",
            timeout=10_000,
        )
        compat_href = page.locator("link[data-sinjira-browser-compat]").get_attribute("href") or ""
        assert_true("browser-compat-v24-4-22.css" in compat_href, "Couche CSS de compatibilité non chargée")

        runtime_version = page.evaluate("window.__SINJIRA_RUNTIME__ && window.__SINJIRA_RUNTIME__.version")
        assert_true(runtime_version == "24.4.22", f"Runtime public inattendu: {runtime_version!r}")

        cards = page.locator("a.home-project")
        assert_true(cards.count() == 4, f"Accueil: 4 accès attendus, trouvé {cards.count()}")
        hrefs = {cards.nth(i).get_attribute("href") for i in range(cards.count())}
        assert_true(hrefs == EXPECTED_DOORS, f"Accueil: portes inattendues: {hrefs}")
        orbit_nodes = page.locator(".home-cosmos a.orbit-node")
        assert_true(orbit_nodes.count() == 4, f"Accueil: 4 portes orbitales attendues, trouvé {orbit_nodes.count()}")
        compass_orbit = page.locator(".home-cosmos .node-boussole-home")
        assert_true(compass_orbit.count() == 1, f"{BROWSER_NAME}: porte orbitale Boussole absente")
        assert_true(
            compass_orbit.get_attribute("href") == "/projets/projet-nova/boussole-electorale.html",
            f"{BROWSER_NAME}: cible de la porte orbitale Boussole incorrecte",
        )
        assert_true(
            compass_orbit.locator('img[src="/assets/media/nova-boussole-electorale-v2.webp"]').count() == 1,
            f"{BROWSER_NAME}: visuel officiel absent de la porte Boussole",
        )
        assert_true(
            page.locator('a[href="/projets/projet-nova/boussole-electorale.html"]').count() >= 4,
            f"{BROWSER_NAME}: accès directs à la Boussole insuffisants sur l’accueil principal",
        )

        for selector, min_width in (
            (".node-registre-home img", 120),
            (".node-sinjira-home img", 120),
            (".node-nova-home img", 120),
            (".node-boussole-home img", 125),
        ):
            icon = page.locator(selector)
            box = icon.bounding_box()
            assert_true(box is not None and box["width"] >= min_width, f"{BROWSER_NAME}: icône principale trop petite: {selector}")

        page.goto(urljoin(BASE_URL, "projets/projet-nova/"), wait_until="domcontentloaded", timeout=30_000)
        assert_true(
            page.locator('a[href="boussole-electorale.html"]').count() >= 3,
            f"{BROWSER_NAME}: la Boussole doit avoir au moins trois accès depuis l’accueil Nova",
        )
        nova_compass_entry = page.locator(".nova-compass-entry .nova-compass-entry-link")
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
            const response = await fetch("data/boussole-preuves-2026.json", {cache:"no-store"});
            if(!response.ok) throw new Error("Corpus de preuves indisponible");
            const corpus = await response.json();
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
        page.locator("#compass-start").click()
        page.locator("#compass-question-stage .compass-question").wait_for(state="visible", timeout=10_000)
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
        assert_true(project.locator('option[value="Projet Nova"]').count() == 0, f"{BROWSER_NAME}: Projet Nova encore routé par le formulaire personnel")
        project.select_option("SINJIRA")
        assert_true(form.get_attribute("action") is None, f"{BROWSER_NAME}: endpoint personnel actif avant configuration")
        assert_true(form.get_attribute("method") is None, f"{BROWSER_NAME}: POST personnel actif avant configuration")
        assert_true(form.get_attribute("data-personal-formspree-state") == "pending-separate-endpoint", f"{BROWSER_NAME}: état fail-closed Formspree absent")
        assert_true(submit.is_disabled(), f"{BROWSER_NAME}: bouton personnel actif avant endpoint distinct")
        assert_true("désactivé" in route.inner_text().lower(), f"{BROWSER_NAME}: message fail-closed absent")
        assert_true(page.locator('a[href="/projets/projet-nova/contact.html"]').count() >= 1, f"{BROWSER_NAME}: lien contact officiel Nova absent")
        contact_html = page.content().lower()
        assert_true("formspree.io/f/xdenkzrv" not in contact_html, f"{BROWSER_NAME}: ancien endpoint personnel encore exposé")
        assert_true("formspree.io/f/xkolwjdg" not in contact_html, f"{BROWSER_NAME}: endpoint Nova encore exposé dans le contact personnel")
        assert_true("kingtyrano@gmail.com" not in contact_html, "Adresse privée embarquée dans le formulaire de contact")

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

            assistant_toggle = page.locator(".sinjira-assistant-toggle")
            assert_true(assistant_toggle.count() == 1, f"{BROWSER_NAME}: bouton Aide IA absent")
            assistant_toggle.click()
            panel = page.locator("#sinjira-assistant-panel")
            assert_true(panel.is_visible(), f"{BROWSER_NAME}: panneau assistant ne s’ouvre pas")
            assert_true(assistant_toggle.get_attribute("aria-expanded") == "true", f"{BROWSER_NAME}: aria-expanded assistant invalide")

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

            page.goto(urljoin(BASE_URL, "projets/sinjira/registre/"), wait_until="domcontentloaded", timeout=30_000)
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
            # Simuler une indisponibilité réelle du questionnaire JSON.
            # Le registre utilise le même fichier : les deux reprises doivent
            # rester indépendantes, sans recharger la page ni lever l'erreur.
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
        )
        mobile_page = mobile.new_page()
        mobile_errors = []
        register_error_capture(mobile_page, mobile_errors)
        response = mobile_page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        assert_true(response is not None and response.status < 400, f"{BROWSER_NAME}: accueil mobile inaccessible")

        overflow = mobile_page.evaluate("document.documentElement.scrollWidth <= Math.ceil(window.innerWidth) + 2")
        assert_true(overflow, f"{BROWSER_NAME}: débordement horizontal détecté en 390 px")

        toggle = mobile_page.locator("[data-menu-toggle]")
        assert_true(toggle.count() == 1, f"{BROWSER_NAME}: bouton de menu mobile absent")
        toggle.click()
        assert_true(toggle.get_attribute("aria-expanded") == "true", f"{BROWSER_NAME}: menu mobile n’annonce pas son état ouvert")
        nav_class = mobile_page.locator("[data-main-nav]").get_attribute("class") or ""
        assert_true("open" in nav_class.split(), f"{BROWSER_NAME}: menu mobile ne s’ouvre pas")
        toggle.click()
        assert_true(toggle.get_attribute("aria-expanded") == "false", f"{BROWSER_NAME}: menu mobile ne se referme pas")

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
            mobile_page.keyboard.press("Escape")

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
            not mobile_page.locator("#compass-start").is_disabled(),
            f"{BROWSER_NAME}: Boussole mobile indisponible",
        )
        for viewport_width in (390, 320):
            mobile_page.set_viewport_size({"width": viewport_width, "height": 844})
            mobile_overflow = mobile_page.evaluate("""() => {
                const width = window.innerWidth;
                return {
                    width,
                    scrollWidth: document.documentElement.scrollWidth,
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
        browser.close()
        auth_note = f", {len(AUTH_ROUTES)} pages Auth locales + assistant V{ASSISTANT_VERSION} contextuel" if IS_LOCAL else ""
        print(
            f"OK E2E {BROWSER_NAME}: {len(PUBLIC_ROUTES)} routes publiques{auth_note}, "
            f"accueil desktop/mobile, contact, compatibilité CSS/runtime et frontière compte vérifiés sur {BASE_URL}"
        )


if __name__ == "__main__":
    run()
