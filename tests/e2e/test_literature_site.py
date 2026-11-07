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
        "**/npm/@supabase/supabase-js@2/+esm*",
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
    context.route('**/npm/@supabase/supabase-js@2/+esm*',
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
    fits = page.evaluate("document.documentElement.scrollWidth <= Math.ceil(window.innerWidth) + 2")
    assert_true(fits, f"{BROWSER_NAME}: débordement horizontal en 390 px sur {label}")


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
        assert_true("82 pages" in page.locator("main").inner_text(), f"{BROWSER_NAME}: pagination de la démo absente de la fiche")

        graph = json_ld_graph(page)
        books = [node for node in graph if node.get("@type") == "Book"]
        assert_true(len(books) == 1, f"{BROWSER_NAME}: provenance JSON-LD Book absente ou dupliquée")
        book = books[0]
        assert_true(book.get("name") == BOOK_NAME, f"{BROWSER_NAME}: nom JSON-LD du Livre I incorrect")
        assert_true(book.get("inLanguage") == "fr-CA", f"{BROWSER_NAME}: langue JSON-LD du Livre I incorrecte")
        assert_true(book.get("numberOfPages") == 520, f"{BROWSER_NAME}: édition intégrale JSON-LD différente de 520 pages")
        assert_true(book.get("isbn") == ["978-2-9825371-0-1", "978-2-9825371-1-8"], f"{BROWSER_NAME}: ISBN du Livre I incorrects")
        demo_part = book.get("hasPart") or {}
        assert_true(demo_part.get("isAccessibleForFree") is True, f"{BROWSER_NAME}: gratuité de la démo non déclarée")
        assert_true(demo_part.get("url") == READER_CANONICAL, f"{BROWSER_NAME}: URL JSON-LD de la démo incorrecte")

        demo_links = page.locator(f'a[href="../documents/{DEMO_BASENAME}"]')
        assert_true(demo_links.count() >= 1, f"{BROWSER_NAME}: lien de téléchargement PDF stable absent")
        download_link = page.locator(f'a[download="{DEMO_BASENAME}"]')
        assert_true(download_link.count() == 1, f"{BROWSER_NAME}: téléchargement PDF nommé absent ou dupliqué")
        assert_true(download_link.get_attribute("type") == "application/pdf", f"{BROWSER_NAME}: type PDF du téléchargement absent")
        assert_true(page.locator('a[href="/compte/liseuse.html?edition=integrale"]').count() == 1, f"{BROWSER_NAME}: accès privé Livre I absent de la fiche")
        assert_true(page.locator('a[href="/compte/liseuse.html?edition=demo"]').count() >= 1,
                    f"{BROWSER_NAME}: lien vers la liseuse gratuite absent")
        assert_no_full_edition_link(page, "Littérature")

        pdf_head = context.request.head(urljoin(BASE_URL, DEMO_ROUTE), timeout=30_000)
        assert_true(pdf_head.status < 400, f"{BROWSER_NAME}: PDF démo public inaccessible (HTTP {pdf_head.status})")

        sitemap_response = context.request.get(urljoin(BASE_URL, SITEMAP_ROUTE), timeout=30_000)
        assert_true(sitemap_response.status < 400, f"{BROWSER_NAME}: sitemap inaccessible (HTTP {sitemap_response.status})")
        sitemap_text = sitemap_response.text()
        reader_loc = f"<loc>{READER_CANONICAL}</loc>"
        assert_true(sitemap_text.count(reader_loc) == 1, f"{BROWSER_NAME}: canonical du lecteur absente ou dupliquée dans le sitemap")
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
        assert_true(
            page.locator('meta[name="twitter:image"]').get_attribute("content") == COVER_URL,
            f"{BROWSER_NAME}: image Twitter du lecteur incorrecte",
        )
        assert_true(
            page.locator('meta[name="twitter:image:alt"]').get_attribute("content") == COVER_ALT,
            f"{BROWSER_NAME}: alternative de l’image Twitter du lecteur absente ou incorrecte",
        )

        reader_graph = json_ld_graph(page)
        reader_works = [
            node for node in reader_graph
            if node.get("@type") == "CreativeWork" and node.get("@id") == f"{READER_CANONICAL}#demo"
        ]
        assert_true(len(reader_works) == 1, f"{BROWSER_NAME}: JSON-LD de la démo lecteur absent ou dupliqué")
        reader_work = reader_works[0]
        assert_true(reader_work.get("name") == READER_WORK_NAME, f"{BROWSER_NAME}: nom JSON-LD du lecteur incorrect")
        assert_true(reader_work.get("url") == READER_CANONICAL, f"{BROWSER_NAME}: URL JSON-LD du lecteur incorrecte")
        assert_true(reader_work.get("inLanguage") == "fr-CA", f"{BROWSER_NAME}: langue JSON-LD du lecteur incorrecte")
        assert_true(reader_work.get("isAccessibleForFree") is True, f"{BROWSER_NAME}: gratuité JSON-LD du lecteur absente")
        author = reader_work.get("author") or {}
        assert_true(author.get("@type") == "Person" and author.get("name") == "Benoit Cantin", f"{BROWSER_NAME}: auteur JSON-LD du lecteur incorrect")
        parent_book = reader_work.get("isPartOf") or {}
        assert_true(parent_book.get("@type") == "Book", f"{BROWSER_NAME}: rattachement JSON-LD du lecteur au Livre I absent")
        assert_true(parent_book.get("name") == BOOK_NAME, f"{BROWSER_NAME}: Livre I parent JSON-LD incorrect")
        assert_true(parent_book.get("url") == CANONICAL, f"{BROWSER_NAME}: URL du Livre I parent incorrecte")
        assert_true(FULL_BASENAME not in page.content(), f"{BROWSER_NAME}: nom du fichier intégral exposé dans le lecteur")

        assert_true(page.locator('body[data-reader-total-pages="82"]').count() == 1, f"{BROWSER_NAME}: pagination canonique 82 pages absente du lecteur")
        assert_true(page.locator('a[href="/compte/liseuse.html?edition=integrale"]').count() == 1, f"{BROWSER_NAME}: accès privé Livre I absent du lecteur")
        assert_true(page.locator('input[data-reader-page-number][aria-label="Numéro de page"]').count() == 1, f"{BROWSER_NAME}: champ de page lecteur non nommé")
        assert_true(page.locator("input[data-reader-page-number]").get_attribute("max") == "82", f"{BROWSER_NAME}: maximum du lecteur différent de 82")
        assert_true(page.locator('[data-reader-resume][aria-live="polite"]').count() == 1, f"{BROWSER_NAME}: reprise lecteur non annoncée aux aides techniques")
        frame = page.locator("iframe[data-pdf-reader]")
        assert_true(frame.count() == 1, f"{BROWSER_NAME}: iframe du lecteur absente")
        assert_true(DEMO_BASENAME in (frame.get_attribute("src") or ""), f"{BROWSER_NAME}: iframe ne pointe plus vers la démo stable")
        assert_true("82 pages" in page.locator("main").inner_text(), f"{BROWSER_NAME}: lecteur ne décrit plus la démo 82 pages")
        assert_no_full_edition_link(page, "lecteur")

        # Nouvelle liseuse Web : aucune URL signée privée, aucune dépendance serveur réelle.
        mock_web_reader(context)
        response=page.goto(urljoin(BASE_URL,"compte/liseuse.html?edition=demo"),
                           wait_until="domcontentloaded",timeout=30_000)
        assert_true(response is not None and response.status < 400,
                    f"{BROWSER_NAME}: nouvelle liseuse inaccessible")
        page.locator("#reader-content:not([hidden])").wait_for(timeout=20_000)
        try:
            page.wait_for_function(
                "() => (document.getElementById('reader-text')?.textContent?.trim().length || 0) > 20",
                timeout=25_000,
            )
        except Exception as exc:
            debug=page.evaluate("""() => ({
              mode:document.getElementById('reader-mode')?.textContent,
              text:document.getElementById('reader-text')?.textContent?.slice(0,220),
              hidden:document.getElementById('reader-text')?.hidden,
              status:document.getElementById('reader-status')?.textContent,
              page:document.getElementById('reader-page')?.value
            })""")
            raise AssertionError(f"{BROWSER_NAME}: texte non affiché; debug={debug}; erreurs={errors[-5:]}") from exc
        initial_text=page.locator("#reader-text").text_content() or ""
        assert_true(len(initial_text.strip())>20,
                    f"{BROWSER_NAME}: texte reformatable absent de la liseuse")
        assert_true(not page.locator("#reader-text").is_hidden(),
                    f"{BROWSER_NAME}: le texte n'est pas le mode de lecture par défaut")
        page.locator("#reader-size").evaluate(
            "(el) => {el.value='28';el.dispatchEvent(new Event('input',{bubbles:true}));}"
        )
        assert_true(page.locator("#reader-size-value").inner_text()=="28 px",
                    f"{BROWSER_NAME}: taille du texte non personnalisable")
        page.locator("#reader-font").select_option("sans")
        assert_true(page.locator("#reader-text").evaluate(
                    "e => getComputedStyle(e).fontFamily.includes('system-ui')"),
                    f"{BROWSER_NAME}: choix de police non appliqué")
        page.locator("#reader-line-height").select_option("2.1")
        page.locator("#reader-theme").select_option("nuit")
        assert_true(page.locator("body").get_attribute("data-read-theme")=="nuit",
                    f"{BROWSER_NAME}: thème de lecture non appliqué")
        initial_page=int(page.locator("#reader-page").input_value())
        page.locator("#reader-next").click()
        next_page=initial_page+1
        assert_true(page.locator("#reader-page").input_value()==str(next_page),
                    f"{BROWSER_NAME}: pagination de la liseuse défectueuse")
        page.wait_for_function(
            "(previous) => {const t=document.getElementById('reader-text')?.textContent || ''; return t.trim().length>20 && t!==previous}",
            arg=initial_text, timeout=15_000,
        )
        assert_true((page.locator("#reader-text").text_content() or "")!=initial_text,
                    f"{BROWSER_NAME}: texte de la page suivante non affiché")
        # V31 : enregistrer explicitement sa position et la retrouver après fermeture.
        page.locator("#reader-viewer").evaluate("(el) => {el.scrollTop=450;el.dispatchEvent(new Event('scroll'))}")
        assert_true(page.locator("#reader-viewer").evaluate("(el) => el.scrollTop > 0"),
                    f"{BROWSER_NAME}: impossible de tester la position intrapage")
        assert_true(page.locator("#reader-save-position").count()==1,
                    f"{BROWSER_NAME}: sauvegarde de lecture absente")
        page.locator("#reader-save-position").click()
        assert_true("Position enregistrée" in page.locator("#reader-position-status").inner_text(),
                    f"{BROWSER_NAME}: accusé de sauvegarde manuelle absent")
        saved_page=int(page.locator("#reader-page").input_value())
        saved_spot=page.evaluate("""() => JSON.parse(localStorage.getItem(
            'sinjira:liseuse:demo:la-cendre-du-jugement:spot'))""")
        assert_true(saved_spot is not None and saved_spot["page"]==saved_page
                    and 0<saved_spot["ratio"]<=1,
                    f"{BROWSER_NAME}: position locale invalide")
        assert_true("text" not in saved_spot and "content" not in saved_spot,
                    f"{BROWSER_NAME}: le texte du roman ne doit pas être sauvegardé")
        page.reload(wait_until="domcontentloaded",timeout=30_000)
        page.locator("#reader-content:not([hidden])").wait_for(timeout=20_000)
        assert_true(page.locator("#reader-page").input_value()==str(saved_page),
                    f"{BROWSER_NAME}: la position n'est pas reprise à la réouverture")
        assert_true("reprise depuis cet appareil" in page.locator("#reader-position-status").inner_text(),
                    f"{BROWSER_NAME}: retour à la dernière position non confirmé")
        page.wait_for_function(
            "() => document.getElementById('reader-viewer')?.scrollTop > 0",
            timeout=15_000)
        assert_true(page.locator("#reader-viewer").evaluate("(el) => el.scrollTop > 0"),
                    f"{BROWSER_NAME}: le défilement intrapage n'a pas été restauré")

        for control in ("reader-voice-play","reader-voice-pause","reader-voice-stop",
                        "reader-voice","reader-speed","reader-voice-auto"):
            assert_true(page.locator("#"+control).count()==1,
                        f"{BROWSER_NAME}: commande vocale absente : "+control)
        assert_no_full_edition_link(page,"nouvelle liseuse")

        # V28 : repères de la démo, mode concentré, recherche et confidentialité.
        for control in ("reader-bookmark-add","reader-highlight-save","reader-note-input",
                        "reader-note-save","reader-marks-list","reader-search-field",
                        "reader-search-submit","reader-search-cancel","reader-search-results",
                        "reader-reading-stats","reader-focus","reader-chapter-next"):
            assert_true(page.locator("#"+control).count()==1,
                        f"{BROWSER_NAME}: commande V28 absente : "+control)
        page.locator(".reader-bookmarks summary").click()
        page.locator("#reader-bookmark-add").click()
        assert_true("Signet" in page.locator("#reader-marks-list").inner_text(),
                    f"{BROWSER_NAME}: marque-page de démo non créé")
        page.locator("#reader-note-input").fill("Mon repère privé de test.")
        page.locator("#reader-note-save").click()
        assert_true("Mon repère privé de test." in page.locator("#reader-marks-list").inner_text(),
                    f"{BROWSER_NAME}: note personnelle non enregistrée")
        saved_marks=page.evaluate("localStorage.getItem('sinjira:liseuse:demo:marks:v28')")
        assert_true("Mon repère privé de test." in (saved_marks or ""),
                    f"{BROWSER_NAME}: la démo ne conserve pas les notes sur cet appareil")
        page.locator("#reader-continuous").click()
        assert_true(page.locator("#reader-continuous").get_attribute("aria-pressed")=="true",
                    f"{BROWSER_NAME}: impossible d'activer le chapitre entier")
        assert_true(not page.locator("#reader-chapter-scroll").is_hidden(),
                    f"{BROWSER_NAME}: chapitre entier masqué")
        page.locator("#reader-continuous").click()
        assert_true(page.locator("#reader-chapter-scroll").is_hidden(),
                    f"{BROWSER_NAME}: impossible de revenir à la lecture par page")
        page.locator("#reader-focus").click()
        assert_true("reader-focus-mode" in (page.locator("body").get_attribute("class") or ""),
                    f"{BROWSER_NAME}: mode lecture concentré inactif")
        page.locator("#reader-focus").click()
        assert_true("reader-focus-mode" not in (page.locator("body").get_attribute("class") or ""),
                    f"{BROWSER_NAME}: impossible de quitter le mode concentré")


        # Protéger aussi l'édition intégrale pendant une déconnexion en vol.
        assert_private_signout_during_load(browser)

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

        assert_true(mobile_page.locator("iframe[data-pdf-reader]").count() == 1, f"{BROWSER_NAME}: iframe lecteur mobile absente")
        assert_true(mobile_page.locator('a[download="SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf"]').count() == 1, f"{BROWSER_NAME}: téléchargement lecteur mobile absent")

        assert_true(not errors, f"{BROWSER_NAME}: erreurs JavaScript Littérature: " + " | ".join(errors[:5]))
        assert_true(not mobile_errors, f"{BROWSER_NAME}: erreurs JavaScript Littérature mobile: " + " | ".join(mobile_errors[:5]))

        mobile.close()
        context.close()
        browser.close()
        print(f"OK littérature {BROWSER_NAME}: fiche, SEO, sitemap, lecteur 82 pages, frontière intégrale et mobile vérifiés.")


if __name__ == "__main__":
    run()
