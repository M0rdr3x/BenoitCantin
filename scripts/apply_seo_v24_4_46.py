#!/usr/bin/env python3
"""Applique le contrat SEO public V24.4.46 de manière idempotente.

Ce script ne touche qu'aux pages publiques explicitement listées ci-dessous.
Il ne modifie jamais les pages Compte/Admin, afin de préserver leur noindex.
"""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.benoitcantin.com"

PUBLIC_PAGES = {
    "projets/sinjira/registre/index.html": "/projets/sinjira/registre/",
    "projets/projet-nova/index.html": "/projets/projet-nova/",
    "projets/projet-nova/comprendre-nova.html": "/projets/projet-nova/comprendre-nova.html",
    "projets/projet-nova/programme.html": "/projets/projet-nova/programme.html",
    "projets/projet-nova/transparence.html": "/projets/projet-nova/transparence.html",
    "projets/projet-nova/documents.html": "/projets/projet-nova/documents.html",
    "projets/projet-nova/calendrier.html": "/projets/projet-nova/calendrier.html",
    "projets/projet-nova/faq.html": "/projets/projet-nova/faq.html",
    "projets/projet-nova/contact.html": "/projets/projet-nova/contact.html",
}

SITEMAP_PATHS = [
    "/",
    "/a-propos.html",
    "/contact.html",
    "/projets/sinjira/",
    "/projets/sinjira/registre/",
    "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/",
    "/projets/projet-nova/",
    "/projets/projet-nova/comprendre-nova.html",
    "/projets/projet-nova/programme.html",
    "/projets/projet-nova/transparence.html",
    "/projets/projet-nova/documents.html",
    "/projets/projet-nova/calendrier.html",
    "/projets/projet-nova/faq.html",
    "/projets/projet-nova/contact.html",
]


class HeadFacts(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title_parts: list[str] = []
        self.description = ""
        self.og_image = ""

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split()).strip()

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = {str(k).lower(): str(v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "description" and not self.description:
                self.description = attrs_dict.get("content", "").strip()
            if prop == "og:image" and not self.og_image:
                self.og_image = attrs_dict.get("content", "").strip()

    def handle_endtag(self, tag: str):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str):
        if self.in_title:
            self.title_parts.append(data)


def remove_tag_by_attr(source: str, tag: str, attr: str, value: str) -> str:
    pattern = re.compile(
        rf"(?is)<{tag}\b(?=[^>]*\b{attr}\s*=\s*(['\"]){re.escape(value)}\1)[^>]*>\s*"
    )
    return pattern.sub("", source)


def remove_link_rel(source: str, rel_value: str) -> str:
    pattern = re.compile(
        rf"(?is)<link\b(?=[^>]*\brel\s*=\s*(['\"]){re.escape(rel_value)}\1)[^>]*>\s*"
    )
    return pattern.sub("", source)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def absolute_asset(value: str, canonical: str) -> str:
    if not value:
        return ""
    if value.startswith("https://") or value.startswith("http://"):
        return value
    if value.startswith("/"):
        return BASE + value
    # Toutes les images Nova actuellement relatives sont dans /projets/projet-nova/.
    if "/projet-nova/" in canonical:
        return BASE + "/projets/projet-nova/" + value.lstrip("./")
    return BASE + "/" + value.lstrip("./")


def seo_block(title: str, description: str, canonical: str, og_image: str) -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": canonical,
        "inLanguage": "fr-CA",
        "isPartOf": {
            "@type": "WebSite",
            "name": "Benoit Cantin",
            "url": BASE + "/",
        },
    }
    tags = [
        f'<link rel="canonical" href="{esc(canonical)}">',
        f'<link rel="alternate" hreflang="fr-CA" href="{esc(canonical)}">',
        f'<link rel="alternate" hreflang="x-default" href="{esc(canonical)}">',
        '<meta property="og:locale" content="fr_CA">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        f'<meta property="og:url" content="{esc(canonical)}">',
    ]
    if og_image:
        tags.append(f'<meta property="og:image" content="{esc(og_image)}">')
    tags.extend(
        [
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{esc(title)}">',
            f'<meta name="twitter:description" content="{esc(description)}">',
        ]
    )
    if og_image:
        tags.append(f'<meta name="twitter:image" content="{esc(og_image)}">')
    tags.append(
        '<script type="application/ld+json" data-seo-v24-4-46>'
        + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )
    return "\n<!-- SEO V24.4.46 -->\n" + "\n".join(tags) + "\n"


def patch_page(rel_path: str, canonical_path: str) -> bool:
    path = ROOT / rel_path
    if not path.exists():
        raise FileNotFoundError(rel_path)
    source = path.read_text(encoding="utf-8")
    parser = HeadFacts()
    parser.feed(source)
    title = parser.title
    description = parser.description
    if not title:
        raise RuntimeError(f"Titre absent: {rel_path}")
    if not description:
        raise RuntimeError(f"Description absente: {rel_path}")

    canonical = BASE + canonical_path
    og_image = absolute_asset(parser.og_image, canonical)

    cleaned = source
    cleaned = re.sub(r"(?is)\s*<!--\s*SEO V24\.4\.46\s*-->\s*", "\n", cleaned)
    cleaned = re.sub(
        r"(?is)<script\b(?=[^>]*\bdata-seo-v24-4-46\b)[^>]*>.*?</script>\s*",
        "",
        cleaned,
    )
    cleaned = remove_link_rel(cleaned, "canonical")
    cleaned = remove_tag_by_attr(cleaned, "link", "hreflang", "fr-CA")
    cleaned = remove_tag_by_attr(cleaned, "link", "hreflang", "x-default")
    for prop in ("og:locale", "og:type", "og:title", "og:description", "og:url", "og:image"):
        cleaned = remove_tag_by_attr(cleaned, "meta", "property", prop)
    for name in ("twitter:card", "twitter:title", "twitter:description", "twitter:image"):
        cleaned = remove_tag_by_attr(cleaned, "meta", "name", name)

    block = seo_block(title, description, canonical, og_image)
    if re.search(r"(?i)</head>", cleaned) is None:
        raise RuntimeError(f"</head> absent: {rel_path}")
    patched = re.sub(r"(?i)</head>", block + "</head>", cleaned, count=1)
    if patched == source:
        return False
    path.write_text(patched, encoding="utf-8")
    return True


def patch_sitemap() -> bool:
    path = ROOT / "sitemap.xml"
    source = path.read_text(encoding="utf-8")
    entries = "\n".join(f"  <url><loc>{BASE}{p}</loc></url>" for p in SITEMAP_PATHS)
    target = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    if source == target:
        return False
    path.write_text(target, encoding="utf-8")
    return True


def main() -> None:
    changed = []
    for rel_path, canonical_path in PUBLIC_PAGES.items():
        if patch_page(rel_path, canonical_path):
            changed.append(rel_path)
    if patch_sitemap():
        changed.append("sitemap.xml")
    if changed:
        print("SEO V24.4.46 appliqué:")
        for item in changed:
            print(f" - {item}")
    else:
        print("SEO V24.4.46 déjà appliqué — aucune modification.")


if __name__ == "__main__":
    main()
