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
    "nova_home": ROOT / "projets/projet-nova/index.html",
    "native_home": ROOT / "mobile-native/NativeHomeHub.tsx",
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
    nova_home = compact(contents["nova_home"])
    native_home = compact(contents["native_home"])

    for marker in (
        "data-ai-transparency",
        "transparenceia",
        "/transparence-ia.html",
        "idées,visionetdécisions",
        "miseenœuvreassistéepardesoutilsd'intelligenceartificielle",
        "validationfinaleetresponsabilitéducontenu",
    ):
        if marker not in ai_js:
            fail(f"bandeau IA partagé incomplet: {marker}")

    for marker in (
        "/assets/css/ai-transparency.css?v=1.0.0",
        "/assets/js/ai-transparency.js?v=1.0.0",
        "data-ai-transparency-style",
        "data-ai-transparency-script",
    ):
        if marker not in site_js:
            fail(f"runtime portail sans transparence IA: {marker}")
        if marker not in nova_js:
            fail(f"runtime Projet Nova sans transparence IA: {marker}")

    if ".ai-transparency-banner" not in contents["ai_css"]:
        fail("style du bandeau IA absent")

    for marker in (
        "mesidées.unemiseenœuvreassistéeparl'ia.",
        "cequivientdemoi",
        "commentl'iam'aide",
        "responsabilitéhumaine",
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

    for marker in (
        "transparenceia",
        "lesidéesetdécisionsrestenthumaines",
        "idées,visionetdécisions:benoitcantin",
        "validationfinaleetlaresponsabilitéducontenurestenthumaines",
        "onopenpath('/transparence-ia.html')",
    ):
        if marker not in native_home:
            fail(f"application native sans transparence IA: {marker}")

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
    if len(urls) < 10:
        fail("sitemap: liste publique anormalement courte")

    uncovered: list[str] = []
    for url in urls:
        path = sitemap_file_for_url(url)
        if not path.is_file():
            fail(f"sitemap: fichier public introuvable pour {url}")
        html = compact(read(path))
        rel = path.relative_to(ROOT).as_posix()
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

        # Les anciennes URL purement techniques redirigent immédiatement vers une
        # surface active couverte; elles ne constituent pas une page de contenu.
        is_legacy_redirect = (
            "noindex,nofollow" in html
            and ("location.replace(" in html or 'http-equiv="refresh"' in html)
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
        ("runtime portail retiré", "site_js", "/assets/js/ai-transparency.js?v=1.0.0", "/assets/js/absent.js"),
        ("mention standard retirée", "policy", "Validation finale et responsabilité du contenu", "Validation retirée"),
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
