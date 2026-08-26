#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOVA = ROOT / "projets" / "projet-nova"
DEFAULT_IMAGE = "https://www.benoitcantin.com/projets/projet-nova/assets/nova-banner-officielle.webp"

PAGES = [
    "index.html", "comprendre-nova.html", "programme.html", "documents.html",
    "recrutement.html", "transparence.html", "comptabilite.html",
    "registre-rencontres.html", "registre-conformite.html", "equipe.html",
    "propositions.html", "presse.html", "faq.html", "contact.html",
    "avis-legal.html", "confidentialite.html", "accessibilite.html",
    "actualites.html", "manifeste.html", "livre-nova.html", "transition.html",
    "code-conduite.html", "constitution.html", "document-a1.html",
]


def meta_content(text: str, name: str) -> str:
    m = re.search(
        rf'<meta\b(?=[^>]*\bname=["\']{re.escape(name)}["\'])[^>]*\bcontent=["\']([^"\']*)["\'][^>]*>',
        text, re.I,
    )
    return html.unescape(m.group(1).strip()) if m else ""


def title_of(text: str) -> str:
    m = re.search(r"<title>\s*([^<]+?)\s*</title>", text, re.I | re.S)
    return html.unescape(m.group(1).strip()) if m else "Projet Nova"


def canonical_of(text: str, name: str) -> str:
    m = re.search(r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*\bhref=["\']([^"\']+)["\'][^>]*>', text, re.I)
    if m:
        return html.unescape(m.group(1).strip())
    if name == "index.html":
        return "https://www.benoitcantin.com/projets/projet-nova/"
    return f"https://www.benoitcantin.com/projets/projet-nova/{name}"


def strip_generated(text: str) -> str:
    patterns = [
        r'\s*<link\b[^>]*\brel=["\']alternate["\'][^>]*\bhreflang=["\'](?:fr-CA|x-default)["\'][^>]*>',
        r'\s*<meta\b[^>]*\bproperty=["\']og:(?:locale|type|title|description|url|image)["\'][^>]*>',
        r'\s*<meta\b[^>]*\bname=["\']twitter:(?:card|title|description|image)["\'][^>]*>',
        r'\s*<script\b(?=[^>]*type=["\']application/ld\+json["\'])(?=[^>]*data-seo-v24-4-46)[^>]*>.*?</script>',
    ]
    for pat in patterns:
        text = re.sub(pat, "", text, flags=re.I | re.S)
    return text


def esc_attr(value: str) -> str:
    return html.escape(value, quote=True)


def normalize(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="strict")
    title = title_of(original)
    description = meta_content(original, "description")
    canonical = canonical_of(original, path.name)
    if not description:
        raise RuntimeError(f"{path}: meta description absente")

    text = strip_generated(original)
    # Canonique : conserver une seule balise et la corriger si nécessaire.
    canonical_tag = f'<link rel="canonical" href="{esc_attr(canonical)}">'
    if re.search(r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*>', text, re.I):
        text = re.sub(r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*>', canonical_tag, text, count=1, flags=re.I)
    else:
        text = text.replace("</title>", f"</title>\n{canonical_tag}", 1)

    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": canonical,
        "inLanguage": "fr-CA",
        "isPartOf": {"@type": "WebSite", "name": "Benoit Cantin", "url": "https://www.benoitcantin.com/"},
    }
    block = "\n".join([
        f'<link rel="alternate" hreflang="fr-CA" href="{esc_attr(canonical)}">',
        f'<link rel="alternate" hreflang="x-default" href="{esc_attr(canonical)}">',
        '<meta property="og:locale" content="fr_CA">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{esc_attr(title)}">',
        f'<meta property="og:description" content="{esc_attr(description)}">',
        f'<meta property="og:url" content="{esc_attr(canonical)}">',
        f'<meta property="og:image" content="{DEFAULT_IMAGE}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc_attr(title)}">',
        f'<meta name="twitter:description" content="{esc_attr(description)}">',
        f'<meta name="twitter:image" content="{DEFAULT_IMAGE}">',
        '<script type="application/ld+json" data-seo-v24-4-46>' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")) + '</script>',
    ])
    text = text.replace("</head>", block + "\n</head>", 1)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = []
    for name in PAGES:
        path = NOVA / name
        if not path.is_file():
            continue
        if normalize(path):
            changed.append(name)
    print(f"SEO Nova normalisé : {len(changed)} page(s)")
    for name in changed:
        print(f"- {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
