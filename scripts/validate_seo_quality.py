#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlparse
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "www.benoitcantin.com"
PRIVATE_PREFIXES = ("/compte/", "/admin/", "/Admin/", "/supabase/")
KEY_PAGES = [
    ROOT / "index.html",
    ROOT / "a-propos.html",
    ROOT / "contact.html",
    ROOT / "projets" / "sinjira" / "index.html",
    ROOT / "projets" / "projet-nova" / "index.html",
]


def local_file_for_url(url: str) -> Path:
    path = urlparse(url).path
    if path == "/":
        return ROOT / "index.html"
    if path.endswith("/"):
        return ROOT / path.lstrip("/") / "index.html"
    return ROOT / path.lstrip("/")


def has_meta(html: str, attr: str, value: str) -> bool:
    pattern = rf"<meta\b[^>]*{attr}=[\"']{re.escape(value)}[\"'][^>]*>"
    return bool(re.search(pattern, html, flags=re.I))


def main() -> int:
    errors = []
    robots = (ROOT / "robots.txt").read_text("utf-8", errors="ignore")
    if "Sitemap: https://www.benoitcantin.com/sitemap.xml" not in robots:
        errors.append("robots.txt: déclaration du sitemap canonique absente.")
    for prefix in PRIVATE_PREFIXES:
        if f"Disallow: {prefix}" not in robots:
            errors.append(f"robots.txt: zone privée non exclue: {prefix}")

    sitemap_path = ROOT / "sitemap.xml"
    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        urls = [node.text.strip() for node in root.findall("{*}url/{*}loc") if node.text]
    except Exception as exc:
        errors.append(f"sitemap.xml invalide: {exc}")
        urls = []

    if not urls:
        errors.append("sitemap.xml: aucune URL publique.")
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != DOMAIN:
            errors.append(f"sitemap.xml: URL non canonique: {url}")
        if any(parsed.path.startswith(prefix) for prefix in PRIVATE_PREFIXES):
            errors.append(f"sitemap.xml: URL privée indexée: {url}")
        if not local_file_for_url(url).exists():
            errors.append(f"sitemap.xml: cible locale absente pour {url}")

    canonicals = set()
    for page in KEY_PAGES:
        if not page.exists():
            errors.append(f"Page SEO critique absente: {page.relative_to(ROOT)}")
            continue
        html = page.read_text("utf-8", errors="ignore")
        rel = page.relative_to(ROOT)
        if not re.search(r"<title>\s*[^<]+\s*</title>", html, flags=re.I):
            errors.append(f"{rel}: title absent ou vide.")
        if not has_meta(html, "name", "description"):
            errors.append(f"{rel}: meta description absente.")
        canonical = re.search(r"<link\b[^>]*rel=[\"']canonical[\"'][^>]*href=[\"']([^\"']+)", html, flags=re.I)
        if not canonical:
            canonical = re.search(r"<link\b[^>]*href=[\"']([^\"']+)[\"'][^>]*rel=[\"']canonical[\"']", html, flags=re.I)
        if not canonical:
            errors.append(f"{rel}: URL canonique absente.")
        else:
            url = canonical.group(1)
            if not url.startswith("https://www.benoitcantin.com/"):
                errors.append(f"{rel}: canonique hors domaine: {url}")
            if url in canonicals:
                errors.append(f"{rel}: canonique dupliquée: {url}")
            canonicals.add(url)

    # Le Registre est une application publique interactive déjà listée dans le sitemap;
    # sa canonical statique sera ajoutée lors de sa prochaine refonte de formulaire, mais
    # elle doit rester indexable et ne jamais basculer dans les zones privées.
    registry_url = "https://www.benoitcantin.com/projets/sinjira/registre/"
    if registry_url not in urls:
        errors.append("sitemap.xml: Registre des Consciences absent de l’index public.")

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
    print(f"OK SEO: {len(urls)} URL(s) publiques, canonicals critiques, robots, Open Graph, Twitter Card et JSON-LD vérifiés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
