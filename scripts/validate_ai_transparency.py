#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
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
    "native_home": ROOT / "mobile-native/NativeHomeHub.tsx",
    "sw": ROOT / "sw.js",
    "netlify": ROOT / "netlify.toml",
    "assistant": ROOT / "assistant.html",
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
    native_home = compact(contents["native_home"])
    sw = compact(contents["sw"])
    netlify = contents["netlify"]
    assistant = compact(contents["assistant"])

    for marker in (
        "data-ai-transparency",
        "transparence·honnêteté·intégrité",
        "/transparence-ia.html",
        "/assistant.html",
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
        "loadpublicassistant()",
    ):
        if marker not in ai_js:
            fail(f"chatbot public Nova × SINJIRA incomplet: {marker}")

    for marker in (
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://www.bubblav.com",
        "connect-src 'self' https://gpvivleexywljowcqkru.supabase.co wss://gpvivleexywljowcqkru.supabase.co https://www.bubblav.com",
    ):
        if marker not in netlify:
            fail(f"CSP BubblaV incomplète: {marker}")


    for marker in (
        "/assets/css/ai-transparency.css?v=1.1.0",
        "/assets/js/ai-transparency.js?v=1.1.0",
        "data-ai-transparency-style",
        "data-ai-transparency-script",
    ):
        if marker not in site_js:
            fail(f"runtime portail sans transparence IA: {marker}")
        if marker not in nova_js:
            fail(f"runtime Projet Nova sans transparence IA: {marker}")

    for marker in (
        ".ai-transparency-banner",
        ".ai-transparency-values",
        ".ai-transparency-declaration",
    ):
        if marker not in contents["ai_css"]:
            fail(f"style de transparence IA absent: {marker}")

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
    ):
        if marker not in page:
            fail(f"page Transparence IA incomplète: {marker}")

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
        "transparenceia",
        "lesidéesetdécisionsrestenthumaines",
        "idées,visionetdécisions:benoitcantin",
        "validationfinaleetlaresponsabilitéducontenurestenthumaines",
        "onopenpath('/transparence-ia.html')",
    ):
        if marker not in native_home:
            fail(f"application native sans transparence IA: {marker}")

    for marker in (
        "assistantnova×sinjira",
        "aucunspoilerfuturocanoninternenonpublié",
        "neutralitéciviquepourprojetnova",
        "ilnedoitpasdireauxvisiteurscommentvoter",
        "vieprivéepar défaut".replace(" ", ""),
        "/compte",
        "/admin",
        "transparence·honnêteté·intégrité·l'humainavanttout.",
        "/transparence-ia.html",
    ):
        if marker not in assistant:
            fail(f"assistant public incomplet: {marker}")

    for marker in (
        "/assets/css/ai-transparency.css",
        "/assets/js/ai-transparency.js",
        "/a-propos.html",
        "/contact.html",
        "/transparence-ia.html",
        "/confidentialite.html",
        "/gouvernance-vie-privee.html",
        "/avis-legal.html",
        "benoitcantin-v24-4-95-public-3",
    ):
        if marker not in sw:
            fail(f"cache PWA sans transparence IA courante: {marker}")

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
    mutations = [
        ("lien public retiré", "ai_js", "/transparence-ia.html", "/transparence-ia-retiree.html"),
        ("runtime portail retiré", "site_js", "/assets/js/ai-transparency.js?v=1.1.0", "/assets/js/absent.js"),
        ("mention standard retirée", "policy", "Validation finale et responsabilité du contenu", "Validation retirée"),
        ("page Transparence IA hors-ligne retirée", "sw", "/transparence-ia.html", "/transparence-ia-absente.html"),
        ("widget BubblaV retiré", "ai_js", "https://www.bubblav.com/widget.js", "https://www.bubblav.com/widget-retire.js"),
        ("CSP BubblaV retirée", "netlify", " https://www.bubblav.com", ""),
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
