#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.benoitcantin.com"
DOMAIN = "www.benoitcantin.com"
PRIVATE_PREFIXES = ("/compte/", "/admin/", "/Admin/", "/supabase/")

BASIC_KEY_PAGES = [
    ROOT / "index.html",
    ROOT / "a-propos.html",
    ROOT / "contact.html",
    ROOT / "projets" / "sinjira" / "index.html",
]

NOVA_PAGE_NAMES = [
    "comprendre-nova.html",
    "programme.html",
    "documents.html",
    "recrutement.html",
    "transparence.html",
    "comptabilite.html",
    "registre-rencontres.html",
    "registre-conformite.html",
    "equipe.html",
    "propositions.html",
    "presse.html",
    "faq.html",
    "contact.html",
    "avis-legal.html",
    "confidentialite.html",
    "accessibilite.html",
    "actualites.html",
    "manifeste.html",
    "livre-nova.html",
    "transition.html",
    "code-conduite.html",
]

SEO_PAGES = {
    ROOT / "projets" / "sinjira" / "registre" / "index.html": BASE + "/projets/sinjira/registre/",
    ROOT / "projets" / "projet-nova" / "index.html": BASE + "/projets/projet-nova/",
}
for nova_name in NOVA_PAGE_NAMES:
    SEO_PAGES[ROOT / "projets" / "projet-nova" / nova_name] = BASE + "/projets/projet-nova/" + nova_name

PRIVATE_NOINDEX_PAGES = [
    ROOT / "compte" / "index.html",
    ROOT / "compte" / "connexion.html",
    ROOT / "compte" / "reseau-personnage.html",
]


def local_file_for_url(url: str) -> Path:
    path = urlparse(url).path
    if path == "/":
        return ROOT / "index.html"
    if path.endswith("/"):
        return ROOT / path.lstrip("/") / "index.html"
    return ROOT / path.lstrip("/")


def read_sitemap(path: Path, errors: list[str]) -> list[str]:
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        urls = [node.text.strip() for node in root.findall("{*}url/{*}loc") if node.text and node.text.strip()]
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT)} invalide: {exc}")
        return []
    if not urls:
        errors.append(f"{path.relative_to(ROOT)}: aucune URL publique.")
    if len(urls) != len(set(urls)):
        errors.append(f"{path.relative_to(ROOT)}: URL dupliquée.")
    return urls


def meta_content(html: str, *, name: str | None = None, prop: str | None = None) -> str:
    attr = "name" if name is not None else "property"
    value = name if name is not None else prop
    assert value is not None
    patterns = [
        rf"<meta\b(?=[^>]*\b{attr}=[\"']{re.escape(value)}[\"'])[^>]*\bcontent=[\"']([^\"']*)[\"'][^>]*>",
        rf"<meta\b(?=[^>]*\bcontent=[\"']([^\"']*)[\"'])[^>]*\b{attr}=[\"']{re.escape(value)}[\"'][^>]*>",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.I)
        if match:
            return match.group(1).strip()
    return ""


def link_href(html: str, rel: str, hreflang: str | None = None) -> str:
    candidates = re.findall(r"<link\b[^>]*>", html, flags=re.I)
    for tag in candidates:
        rel_match = re.search(r"\brel=[\"']([^\"']+)[\"']", tag, flags=re.I)
        if not rel_match or rel.lower() not in rel_match.group(1).lower().split():
            continue
        if hreflang is not None:
            lang_match = re.search(r"\bhreflang=[\"']([^\"']+)[\"']", tag, flags=re.I)
            if not lang_match or lang_match.group(1).lower() != hreflang.lower():
                continue
        href_match = re.search(r"\bhref=[\"']([^\"']+)[\"']", tag, flags=re.I)
        if href_match:
            return href_match.group(1).strip()
    return ""


def validate_public_url(url: str, sitemap_name: str, errors: list[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != DOMAIN:
        errors.append(f"{sitemap_name}: URL non canonique: {url}")
    if parsed.query or parsed.fragment:
        errors.append(f"{sitemap_name}: query/fragment interdit dans une URL indexée: {url}")
    if any(parsed.path.startswith(prefix) for prefix in PRIVATE_PREFIXES):
        errors.append(f"{sitemap_name}: URL privée indexée: {url}")
    if not local_file_for_url(url).exists():
        errors.append(f"{sitemap_name}: cible locale absente pour {url}")


def validate_basic_page(page: Path, errors: list[str]) -> None:
    if not page.exists():
        errors.append(f"Page SEO critique absente: {page.relative_to(ROOT)}")
        return
    html = page.read_text("utf-8", errors="ignore")
    rel = page.relative_to(ROOT)
    if not re.search(r"<title>\s*[^<]+\s*</title>", html, flags=re.I):
        errors.append(f"{rel}: title absent ou vide.")
    if not meta_content(html, name="description"):
        errors.append(f"{rel}: meta description absente.")
    canonical = link_href(html, "canonical")
    if not canonical:
        errors.append(f"{rel}: URL canonique absente.")
    elif not canonical.startswith(BASE + "/"):
        errors.append(f"{rel}: canonique hors domaine: {canonical}")


def validate_seo_page(page: Path, canonical_expected: str, errors: list[str]) -> None:
    if not page.exists():
        errors.append(f"Page SEO absente: {page.relative_to(ROOT)}")
        return
    html = page.read_text("utf-8", errors="ignore")
    rel = page.relative_to(ROOT)

    title_match = re.search(r"<title>\s*([^<]+?)\s*</title>", html, flags=re.I)
    title = title_match.group(1).strip() if title_match else ""
    description = meta_content(html, name="description")
    canonical = link_href(html, "canonical")

    if not title:
        errors.append(f"{rel}: title absent ou vide.")
    if len(description) < 25:
        errors.append(f"{rel}: meta description absente ou trop courte.")
    if canonical != canonical_expected:
        errors.append(f"{rel}: canonique attendu {canonical_expected}, trouvé {canonical or 'ABSENT'}")
    if link_href(html, "alternate", "fr-CA") != canonical_expected:
        errors.append(f"{rel}: hreflang fr-CA absent ou incohérent.")
    if link_href(html, "alternate", "x-default") != canonical_expected:
        errors.append(f"{rel}: hreflang x-default absent ou incohérent.")

    expected_meta = {
        ("property", "og:locale"): "fr_CA",
        ("property", "og:type"): "website",
        ("property", "og:title"): title,
        ("property", "og:description"): description,
        ("property", "og:url"): canonical_expected,
        ("name", "twitter:title"): title,
        ("name", "twitter:description"): description,
    }
    for (kind, key), expected in expected_meta.items():
        actual = meta_content(html, name=key) if kind == "name" else meta_content(html, prop=key)
        if actual != expected:
            errors.append(f"{rel}: {key} absent ou incohérent.")

    twitter_card = meta_content(html, name="twitter:card")
    og_image = meta_content(html, prop="og:image")
    twitter_image = meta_content(html, name="twitter:image")
    if og_image:
        parsed_image = urlparse(og_image)
        if parsed_image.scheme != "https" or parsed_image.netloc != DOMAIN:
            errors.append(f"{rel}: og:image doit être une URL HTTPS absolue du domaine.")
        if twitter_card != "summary_large_image":
            errors.append(f"{rel}: twitter:card doit être summary_large_image lorsqu’une image est fournie.")
        if twitter_image != og_image:
            errors.append(f"{rel}: twitter:image doit correspondre à og:image.")
    else:
        if twitter_card != "summary":
            errors.append(f"{rel}: twitter:card doit être summary sans image sociale.")
        if twitter_image:
            errors.append(f"{rel}: twitter:image présent sans og:image.")

    schema_match = re.search(
        r"<script\b(?=[^>]*type=[\"']application/ld\+json[\"'])[^>]*>(.*?)</script>",
        html,
        flags=re.I | re.S,
    )
    if not schema_match:
        errors.append(f"{rel}: JSON-LD absent.")
    else:
        try:
            schema = json.loads(schema_match.group(1))
        except Exception as exc:
            errors.append(f"{rel}: JSON-LD invalide: {exc}")
        else:
            if schema.get("@context") != "https://schema.org" or schema.get("@type") != "WebPage":
                errors.append(f"{rel}: type JSON-LD WebPage invalide.")
            if schema.get("url") != canonical_expected:
                errors.append(f"{rel}: URL JSON-LD incohérente.")
            if schema.get("inLanguage") != "fr-CA":
                errors.append(f"{rel}: inLanguage JSON-LD doit être fr-CA.")


def main() -> int:
    errors: list[str] = []

    robots_path = ROOT / "robots.txt"
    robots = robots_path.read_text("utf-8", errors="ignore")
    if "Sitemap: https://www.benoitcantin.com/sitemap.xml" not in robots:
        errors.append("robots.txt: déclaration du sitemap canonique absente.")
    for prefix in PRIVATE_PREFIXES:
        if f"Disallow: {prefix}" not in robots:
            errors.append(f"robots.txt: zone privée non exclue: {prefix}")

    urls = read_sitemap(ROOT / "sitemap.xml", errors)
    nova_urls = read_sitemap(ROOT / "projets" / "projet-nova" / "sitemap.xml", errors)
    for url in urls:
        validate_public_url(url, "sitemap.xml", errors)
    for url in nova_urls:
        validate_public_url(url, "projets/projet-nova/sitemap.xml", errors)

    expected_nova_urls = {BASE + "/projets/projet-nova/"} | {
        BASE + "/projets/projet-nova/" + name for name in NOVA_PAGE_NAMES
    }
    if set(nova_urls) != expected_nova_urls:
        missing = sorted(expected_nova_urls - set(nova_urls))
        extra = sorted(set(nova_urls) - expected_nova_urls)
        if missing:
            errors.append("Sitemap Nova: URL manquantes: " + ", ".join(missing))
        if extra:
            errors.append("Sitemap Nova: URL inattendues: " + ", ".join(extra))
    if BASE + "/projets/projet-nova/index.html" in nova_urls or BASE + "/projets/projet-nova/index.html" in urls:
        errors.append("Projet Nova: index.html ne doit pas concurrencer la canonique de répertoire.")
    for url in expected_nova_urls:
        if url not in urls:
            errors.append(f"sitemap.xml racine: URL Nova absente: {url}")

    registry_url = BASE + "/projets/sinjira/registre/"
    if registry_url not in urls:
        errors.append("sitemap.xml: Registre des Consciences absent de l’index public.")

    for page in BASIC_KEY_PAGES:
        validate_basic_page(page, errors)
    for page, expected in SEO_PAGES.items():
        validate_seo_page(page, expected, errors)
        if expected not in urls:
            errors.append(f"sitemap.xml: canonique SEO absente: {expected}")

    for page in PRIVATE_NOINDEX_PAGES:
        if not page.exists():
            errors.append(f"Page privée critique absente: {page.relative_to(ROOT)}")
            continue
        html = page.read_text("utf-8", errors="ignore")
        robots_meta = meta_content(html, name="robots").lower()
        if "noindex" not in robots_meta:
            errors.append(f"{page.relative_to(ROOT)}: page privée sans noindex.")

    home = (ROOT / "index.html").read_text("utf-8", errors="ignore")
    required_home_markers = [
        'property="og:title"',
        'property="og:description"',
        'property="og:type"',
        'property="og:url"',
        'name="twitter:card"',
        'name="twitter:title"',
        'name="twitter:description"',
        'type="application/ld+json"',
        '"@type":"Person"',
        '"@type":"WebSite"',
    ]
    for marker in required_home_markers:
        if marker not in home:
            errors.append(f"index.html: métadonnée structurée absente: {marker}")

    if errors:
        print(f"ECHEC SEO: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1
    print(
        f"OK SEO: {len(urls)} URL(s) racine, {len(nova_urls)} URL(s) Nova, "
        "canonicalisation, Open Graph, Twitter, JSON-LD, hreflang et zones privées validés."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
