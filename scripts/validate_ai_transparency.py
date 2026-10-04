#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_RUNTIME_PREFIXES = (
    "admin/",
    "Admin/",
    "app/",
    "compte/",
    "histoire-de-vie/",
)
STANDARD = (
    "Idées, vision et décisions : Benoit Cantin. "
    "Mise en œuvre assistée par des outils d'intelligence artificielle. "
    "Validation finale et responsabilité du contenu : Benoit Cantin."
)

FILES = {
    "ai_js": ROOT / "assets/js/ai-transparency.js",
    "ai_css": ROOT / "assets/css/ai-transparency.css",
    "site_js": ROOT / "assets/js/site.js",
    "nova_js": ROOT / "projets/projet-nova/script.js",
    "page": ROOT / "transparence-ia.html",
    "policy": ROOT / "AI_TRANSPARENCY.md",
    "readme": ROOT / "README.md",
    "sitemap": ROOT / "sitemap.xml",
    "home": ROOT / "index.html",
    "about": ROOT / "a-propos.html",
    "nova_home": ROOT / "projets/projet-nova/index.html",
    "sw": ROOT / "sw.js",
    "netlify": ROOT / "netlify.toml",
    "assistant": ROOT / "assistant.html",
    "privacy": ROOT / "confidentialite.html",
    "assistant_governance": ROOT / "ASSISTANT_GOVERNANCE.md",
    "assistant_data_minimization": ROOT / "docs/BUBBLAV_PUBLIC_ASSISTANT_DATA_MINIMIZATION.md",
}

def compact(value: str) -> str:
    return "".join(value.lower().replace("’", "'").replace(" ", " ").split())

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def fail(message: str) -> None:
    raise ValueError(message)

def validate_core(contents: dict[str, str]) -> None:
    ai_js = compact(contents["ai_js"])
    site_js = compact(contents["site_js"])
    nova_js = compact(contents["nova_js"])
    page = compact(contents["page"])
    policy = compact(contents["policy"])
    readme = compact(contents["readme"])
    home = compact(contents["home"])
    about = compact(contents["about"])
    nova_home = compact(contents["nova_home"])
    sw = compact(contents["sw"])
    netlify = contents["netlify"]
    assistant = compact(contents["assistant"])
    privacy = compact(contents["privacy"])
    assistant_governance = compact(contents["assistant_governance"])
    assistant_data_minimization = compact(contents["assistant_data_minimization"])

    for marker in (
        "data-ai-transparency",
        "transparence·honnêteté·intégrité",
        "/transparence-ia.html",
        "jetravailleavecl'aidedel'intelligenceartificielle",
        "lesidées,lavisionetlesdécisionsfinalesrestentlesmiennes",
        "l'humainavanttout",
    ):
        if marker not in ai_js:
            fail(f"bandeau IA partagé incomplet: {marker}")

    for marker in (
        "https://www.bubblav.com/widget.js",
        "data-site-id",
        "ca77cd98-bd32-459c-ad55-fdad4fb85316",
        "data-bubblav-widget",
        "path==='/compte'",
        "path.indexof('/compte/')===0",
        "path==='/admin'",
        "path.indexof('/admin/')===0",
        "path==='/app'",
        "path.indexof('/app/')===0",
        "isnoindexsurface",
        "meta[name=\"robots\"]",
        "noindex",
        "loadpublicassistant()",
        "window.location.hostname",
        "host==='www.benoitcantin.com'",
        "if(!isofficialhost||isprivatesurface||isnoindexsurface)return;",
        "data-public-assistant-launcher",
        "ouvrirl'assistantnova×sinjira,servicebubblav",
        "chargéseulementaprèsvotreclic",
        "launcher.addeventlistener('click'",
        "launcher.setattribute('aria-busy','true')",
        "varpublicassistantformsminimized=true;",
        "varpublicassistantdomainsrestricted=true;",
        "varpublicassistantnetworkvalidated=false;",
        "if(!publicassistantformsminimized||!publicassistantdomainsrestricted||!publicassistantnetworkvalidated)return;",
    ):
        if marker not in ai_js:
            fail(f"chatbot public Nova × SINJIRA incomplet: {marker}")

    if "host==='benoitcantin.com'" in ai_js:
        fail("chatbot public: l’apex ne doit pas être autorisé comme origine BubblaV")

    click_index = ai_js.find("launcher.addeventlistener('click'")
    third_party_index = ai_js.find("script.src='https://www.bubblav.com/widget.js'")
    if click_index < 0 or third_party_index < 0 or third_party_index < click_index:
        fail("chatbot public: BubblaV ne doit être créé qu'après une action explicite")

    if "https://www.bubblav.com" in netlify:
        fail("CSP BubblaV doit rester bloquée tant que la validation réseau/CSP du widget n’est pas terminée")

    for directive in ("script-src", "connect-src"):
        match = re.search(rf"{directive}\s+([^;]+)", netlify)
        if not match:
            fail(f"CSP sans directive {directive}")
        tokens = match.group(1).split()
        if "*" in tokens or "https:" in tokens:
            fail(f"CSP trop permissive dans {directive}")
        if "https://www.bubblav.com" in tokens:
            fail(f"CSP BubblaV réactivée par erreur dans {directive}")

    for marker in (
        "/assets/css/ai-transparency.css?v=1.2.0",
        "/assets/js/ai-transparency.js?v=1.5.0",
        "data-ai-transparency-style",
        "data-ai-transparency-script",
    ):
        if marker not in site_js:
            fail(f"runtime portail sans transparence IA: {marker}")

    for marker in (
        "/assets/css/ai-transparency.css?v=1.2.0",
        "/assets/js/ai-transparency.js?v=1.5.0",
        "data-ai-transparency-style",
        "data-ai-transparency-script",
    ):
        if marker not in nova_js:
            fail(f"runtime Projet Nova sans transparence IA: {marker}")

    for marker in (
        "isofficialhost",
        "isprivatesurface",
        "isnoindexsurface",
        "if(isofficialhost&&!isprivatesurface&&!isnoindexsurface)return;",
    ):
        if marker not in site_js:
            fail(f"runtime portail: séparation assistant local/public absente: {marker}")

    for marker in (
        "isofficialhost",
        "isnoindexsurface",
        "if(isofficialhost&&!isnoindexsurface)return;",
    ):
        if marker not in nova_js:
            fail(f"runtime Projet Nova: séparation assistant local/public absente: {marker}")

    for marker in (
        ".ai-transparency-banner",
        ".ai-transparency-values",
        ".ai-transparency-declaration",
        ".public-assistant-launcher",
        ".public-assistant-launcher__privacy",
    ):
        if marker not in contents["ai_css"]:
            fail(f"style de transparence IA absent: {marker}")

    for surface in ("home", "page", "assistant", "nova_home"):
        if "/assets/css/ai-transparency.css?v=1.2.0" not in compact(contents[surface]):
            fail(f"cache transparence IA obsolète sur {surface}: version 1.2.0 requise")
        if "ai-transparency.css?v=1.1.0" in compact(contents[surface]):
            fail(f"cache transparence IA obsolète sur {surface}: 1.1.0 interdit")


    for marker in (
        '<meta property="og:title" content="Transparence IA | Benoit Cantin">',
        '<meta property="og:description" content="Déclaration publique de Benoit Cantin sur l\'utilisation de l\'intelligence artificielle, fondée sur la transparence, l\'honnêteté, l\'intégrité et la responsabilité humaine.">',
        '<meta property="og:type" content="website">',
        '<meta property="og:url" content="https://www.benoitcantin.com/transparence-ia.html">',
    ):
        if marker not in contents["page"]:
            fail(f"page Transparence IA sans métadonnée sociale: {marker}")

    for marker in (
        "jechoisisdedireclairementcommentl'iam'aide.",
        "troisvaleursquidoiventrestervisibles.",
        "transparence",
        "honnêteté",
        "intégrité",
        "cequivientdemoi",
        "commentl'iam'aide",
        "responsabilitéhumaine",
        "déclarationofficielle",
        "uneaidetechnologiquedéclarée.uneresponsabilitéhumaineassumée.",
        "l'humainavanttout.",
        "projetscitoyensetpositionspubliques",
        "ellenechoisitpasunepositionpolitique",
        "découvrirl'assistantnova×sinjira",
        "/assistant.html",
    ):
        if marker not in page:
            fail(f"page Transparence IA incomplète: {marker}")

    for marker in (
        "assistantnova×sinjira",
        "assistant_governance.md",
        "/assistant.html",
        "/confidentialite.html",
        "frontièreanti-spoiler",
        "/compte",
        "/admin",
        "/app",
        "informeretorientersansdevenirunesecondevoiepourlaconnexion",
        "renvoyercesactionsverslesparcoursofficielsdusite",
        "étatactuel:bubblavestdésactivécôtésite.",
        "publicassistantformsminimized=true",
        "publicassistantdomainsrestricted=true",
        "publicassistantnetworkvalidated=false",
    ):
        if marker not in policy:
            fail(f"politique IA sans gouvernance assistant: {marker}")

    standard_compact = compact(STANDARD)
    if standard_compact not in page:
        fail("mention standard absente de la page Transparence IA")
    if standard_compact not in policy:
        fail("mention standard absente de AI_TRANSPARENCY.md")
    if standard_compact not in readme:
        fail("mention standard absente du README")

    for key, content in (("accueil", home), ("Projet Nova", nova_home)):
        if "data-ai-transparency" not in content:
            fail(f"{key}: bandeau IA statique absent")
        if "/transparence-ia.html" not in content:
            fail(f"{key}: lien vers la déclaration IA absent")
        for marker in ("transparence·honnêteté·intégrité", "l'humainavanttout"):
            if marker not in content:
                fail(f"{key}: valeurs publiques de transparence IA absentes: {marker}")

    for marker in (
        "/transparence-ia.html",
        "transparence.honnêteté.intégrité.",
        "transparence:",
        "honnêteté:",
        "intégrité:",
        "l'humainavanttout.",
    ):
        if marker not in about:
            fail(f"À propos: engagement de transparence IA incomplet: {marker}")

    for marker in (
        "assistantnova×sinjira",
        "aucunspoilerfuturoucanoninternenonpublié",
        "neutralitéciviquepourprojetnova",
        "ilnedoitpasdireauxvisiteurscommentvoter",
        "vieprivéepar défaut".replace(" ", ""),
        "/compte",
        "/admin",
        "/app",
        "transparence·honnêteté·intégrité·l'humainavanttout.",
        "/transparence-ia.html",
        "ilsertàinformeretàorienter",
        "lesautresactionsliéesàuncomptedoiventpasserparlesparcoursofficielsdusite",
    ):
        if marker not in assistant:
            fail(f"assistant public incomplet: {marker}")

    for marker in (
        "gouvernancedel'assistantnova×sinjira",
        "frontièreanti-spoilersinjira",
        "neutralitéciviquedeprojetnova",
        "yolo_mode=false",
        "/compte/*",
        "/admin/*",
        "/app/*",
        "toutepageportantunedirective`noindex`",
        "https://www.bubblav.com/widget.js",
        "lechargeurdoitrester**opt-in**",
        "aprèsunclicexplicite",
        "outil d'information et d'orientation".replace(" ", ""),
        "ilnedoitpasdevenirunesecondevoiefonctionnelle",
        "formulairesfournisseurlimitésauxbesoinspublicsréellementnécessaires",
        "docs/bubblav_public_assistant_data_minimization.md",
        "issue**#443**",
        "issue**#444**",
        "bubblavestdésactivécôtésite",
        "publicassistantformsminimized=true",
        "publicassistantdomainsrestricted=true",
        "publicassistantnetworkvalidated=false",
        "bubblavdoitresterabsentde",
        "responsabilitéhumaine",
    ):
        if marker not in assistant_governance:
            fail(f"gouvernance assistant incomplète: {marker}")

    for marker in (
        "bubblav—minimisationdesformulairesduchatbotpublic",
        "retiréetconfirmécôtéfournisseur",
        "seconnecteràsoncompte",
        "ilsontensuiteétésupprimésindividuellement",
        "chaquesuppressionayantrépondu`deleted:true`",
        "total=2",
        "allow_all_domains=false",
        "allowed_domains=[\"www.benoitcantin.com\"]",
        "lecturedesflowsresteindisponible",
        "submission_count=0",
        "aucunesoumissionouhistoriqueexistantn'aétésupprimé",
    ):
        if marker not in assistant_data_minimization:
            fail(f"revue minimisation BubblaV incomplète: {marker}")

    for marker in (
        "assistantpublicnova×sinjiraetbubblav",
        "bubblav",
        "lewidgetfournisseurestactuellementdésactivé",
        "aucunlanceur,scriptouappelréseaububblavn'estinitialiséparlesite",
        "sileserviceestréactivéultérieurement",
        "surlessurfacespubliquesindexablesdudomaineofficiel",
        "<code>/app</code>",
        "stockagelocaldunavigateur",
        "lechatbotpublicsertàinformeretàorienter",
        "lesautresactionsdecomptedoiventutiliserlesparcoursofficielsdusite",
        "/assistant.html",
        "30septembre2026",
        "toutepagemarquée<code>noindex</code>",
    ):
        if marker not in privacy:
            fail(f"déclaration vie privée BubblaV incomplète: {marker}")

    for marker in (
        "/assets/css/ai-transparency.css",
        "/assets/js/ai-transparency.js",
        "/a-propos.html",
        "/contact.html",
        "/transparence-ia.html",
        "/assistant.html",
        "/confidentialite.html",
        "/gouvernance-vie-privee.html",
        "/avis-legal.html",
    ):
        if marker not in sw:
            fail(f"cache PWA sans transparence IA courante: {marker}")
    if not re.search(r"constcache=['\"]benoitcantin-v24-4-95-public-\d+['\"];", sw):
        fail("cache PWA: version publique explicite absente")

def sitemap_file_for_url(url: str) -> Path:
    path = urlparse(url).path
    if path == "/":
        return ROOT / "index.html"
    rel = path.lstrip("/")
    if rel.endswith("/"):
        rel += "index.html"
    return ROOT / rel

def validate_public_pages(sitemap: str) -> None:
    urls = re.findall(r"<loc>(https://www\.benoitcantin\.com/[^<]*)</loc>", sitemap)
    if "https://www.benoitcantin.com/transparence-ia.html" not in urls:
        fail("sitemap: page Transparence IA absente")
    if "https://www.benoitcantin.com/assistant.html" not in urls:
        fail("sitemap: page Assistant Nova × SINJIRA absente")
    if len(urls) < 10:
        fail("sitemap: liste publique anormalement courte")

    uncovered: list[str] = []
    for url in urls:
        path = sitemap_file_for_url(url)
        if not path.is_file():
            fail(f"sitemap: fichier public introuvable pour {url}")
        html_raw = read(path)
        html = compact(html_raw)
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("projets/sinjira/") and "site.js?v=" in html_raw:
            if "site.js?v=24.4.23" not in html_raw:
                fail(
                    f"surface SINJIRA avec cache site.js obsolète: {rel}"
                )

        if rel == "transparence-ia.html":
            continue
        if "data-ai-transparency" in html:
            continue
        if rel.startswith("projets/projet-nova/"):
            if "script.js" not in html:
                uncovered.append(rel)
        elif "site.js" not in html:
            uncovered.append(rel)

    if uncovered:
        fail("pages publiques sans mécanisme de transparence IA: " + ", ".join(uncovered))

def validate_all_html_surfaces() -> None:
    uncovered: list[str] = []
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(PRIVATE_RUNTIME_PREFIXES):
            continue
        html_raw = read(path)
        html = compact(html_raw)

        # Les URL purement techniques qui redirigent immédiatement vers une
        # surface active couverte ne constituent pas une page de contenu. On
        # reconnaît uniquement les redirections instantanées explicites.
        is_legacy_redirect = (
            "location.replace(" in html
            or re.search(
                r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]+content=["\']?0\s*;',
                html_raw,
                flags=re.IGNORECASE,
            ) is not None
            or re.search(
                r'<meta[^>]+content=["\']?0\s*;[^>]+http-equiv=["\']?refresh',
                html_raw,
                flags=re.IGNORECASE,
            ) is not None
        )
        if is_legacy_redirect:
            continue

        if rel == "transparence-ia.html":
            continue
        if "data-ai-transparency" in html:
            continue
        if "site.js" in html:
            continue
        if rel.startswith("projets/projet-nova/") and "script.js" in html:
            continue

        uncovered.append(rel)

    if uncovered:
        fail(
            "surfaces HTML actives sans mécanisme de transparence IA: "
            + ", ".join(uncovered)
        )

def self_test(contents: dict[str, str]) -> None:
    # La baseline doit être valide avant toute mutation; sinon une erreur
    # préexistante pourrait faire passer artificiellement tous les cas négatifs.
    validate_core(contents)

    mutations = [
        ("lien public retiré", "ai_js", "/transparence-ia.html", "/transparence-ia-retiree.html"),
        ("lien Assistant retiré de Transparence IA", "page", "/assistant.html", "/assistant-retire.html"),
        ("runtime portail retiré", "site_js", "/assets/js/ai-transparency.js?v=1.5.0", "/assets/js/absent.js"),
        ("mention standard retirée", "policy", "Validation finale et responsabilité du contenu", "Validation retirée"),
        ("page Transparence IA hors-ligne retirée", "sw", "/transparence-ia.html", "/transparence-ia-absente.html"),
        ("widget BubblaV retiré", "ai_js", "https://www.bubblav.com/widget.js", "https://www.bubblav.com/widget-retire.js"),
        ("garde noindex retiré", "ai_js", "if (!isOfficialHost || isPrivateSurface || isNoindexSurface) return;", "if (!isOfficialHost || isPrivateSurface) return;"),
        ("garde domaine officiel retirée", "ai_js", "if (!isOfficialHost || isPrivateSurface || isNoindexSurface) return;", "if (isPrivateSurface || isNoindexSurface) return;"),
        ("apex réautorisé pour BubblaV", "ai_js", "host === 'www.benoitcantin.com'", "host === 'www.benoitcantin.com' || host === 'benoitcantin.com'"),
        ("garde /app retirée", "ai_js", "path === '/app' ||\n      path.indexOf('/app/') === 0;", "path === '/app-retire' ||\n      path.indexOf('/app-retire/') === 0;"),
        ("activation volontaire retirée", "ai_js", "launcher.addEventListener('click'", "launcher.addEventListener('mouseover'"),
        ("preuve formulaires régressée", "ai_js", "var publicAssistantFormsMinimized = true;", "var publicAssistantFormsMinimized = false;"),
        ("preuve domaines régressée", "ai_js", "var publicAssistantDomainsRestricted = true;", "var publicAssistantDomainsRestricted = false;"),
        ("gate réseau réactivé", "ai_js", "var publicAssistantNetworkValidated = false;", "var publicAssistantNetworkValidated = true;"),
        ("triple verrou fournisseur affaibli", "ai_js", "if (!publicAssistantFormsMinimized || !publicAssistantDomainsRestricted || !publicAssistantNetworkValidated) return;", "if (!publicAssistantFormsMinimized || !publicAssistantDomainsRestricted) return;"),
        ("libellé accessible du lanceur retiré", "ai_js", "Ouvrir l’assistant Nova × SINJIRA, service BubblaV", "Ouvrir le chatbot"),
        ("cache IA accueil rétrogradé", "home", "/assets/css/ai-transparency.css?v=1.2.0", "/assets/css/ai-transparency.css?v=1.1.0"),
        ("cache IA page Transparence rétrogradé", "page", "/assets/css/ai-transparency.css?v=1.2.0", "/assets/css/ai-transparency.css?v=1.1.0"),
        ("cache IA accueil Nova rétrogradé", "nova_home", "/assets/css/ai-transparency.css?v=1.2.0", "/assets/css/ai-transparency.css?v=1.1.0"),
        ("séparation assistant public retirée", "site_js", "if (isOfficialHost && !isPrivateSurface && !isNoindexSurface) return;", "if (false) return;"),
        ("séparation assistant Nova retirée", "nova_js", "if(isOfficialHost&&!isNoindexSurface)return;", "if(false)return;"),
        ("CSP BubblaV réactivée script", "netlify", "https://cdn.jsdelivr.net; worker-src", "https://cdn.jsdelivr.net https://www.bubblav.com; worker-src"),
        ("CSP BubblaV réactivée connect", "netlify", "wss://gpvivleexywljowcqkru.supabase.co; frame-src", "wss://gpvivleexywljowcqkru.supabase.co https://www.bubblav.com; frame-src"),
        ("déclaration BubblaV retirée", "privacy", "Assistant public Nova × SINJIRA et BubblaV", "Assistant public retiré"),
        ("gouvernance assistant retirée", "assistant_governance", "Frontière anti-spoiler SINJIRA", "Frontière retirée"),
        ("frontière actions publiques retirée", "assistant", "Il sert à informer et à orienter.", "Il peut aussi agir dans le compte."),
        ("garde parcours officiels retirée", "assistant_governance", "Il ne doit pas devenir une seconde voie fonctionnelle", "Il peut devenir une seconde voie fonctionnelle"),
        ("garde formulaires fournisseur retirée", "assistant_governance", "formulaires fournisseur limités aux besoins publics réellement nécessaires", "formulaires fournisseur sans limite"),
        ("preuve suppression formulaires retirée", "assistant_data_minimization", "Ils ont ensuite été supprimés individuellement", "état fournisseur inconnu"),
        ("frontière /app politique IA retirée", "policy", "espaces privés `/compte`, `/admin` et `/app`", "espaces privés `/compte` et `/admin`"),
        ("frontière actions politique IA retirée", "policy", "informer et orienter sans devenir une seconde voie", "agir directement dans les comptes"),
        ("état fournisseur politique IA retiré", "policy", "**État actuel : BubblaV est désactivé côté site.**", "**État actuel : BubblaV peut être chargé côté site.**"),
        ("référence assistant IA retirée", "policy", "ASSISTANT_GOVERNANCE.md", "ASSISTANT_GOUVERNANCE_RETIRÉE.md"),
    ]
    detected = 0
    for name, key, old, new in mutations:
        mutated = dict(contents)
        if old not in mutated[key]:
            fail(f"auto-test invalide: marqueur absent avant mutation: {name}")
        mutated[key] = mutated[key].replace(old, new, 1)
        try:
            validate_core(mutated)
        except ValueError:
            detected += 1
        else:
            fail(f"auto-test: dérive non détectée: {name}")
    print(f"OK transparence IA auto-test: {detected}/{len(mutations)} dérives détectées")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    contents = {key: read(path) for key, path in FILES.items()}
    if args.self_test:
        self_test(contents)
        return

    validate_core(contents)
    validate_public_pages(contents["sitemap"])
    validate_all_html_surfaces()
    print("OK transparence IA: déclaration publique, bandeaux, politique, sitemap et surfaces HTML actives validés.")

if __name__ == "__main__":
    main()
