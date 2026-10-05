#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PRIMARY_PAGES = {
    "projets/sinjira/index.html": "https://www.benoitcantin.com/projets/sinjira/",
    "projets/sinjira/romans/index.html": "https://www.benoitcantin.com/projets/sinjira/romans/",
    "projets/sinjira/jeux/index.html": "https://www.benoitcantin.com/projets/sinjira/jeux/",
    "projets/sinjira/registre/index.html": "https://www.benoitcantin.com/projets/sinjira/registre/",
    "projets/sinjira/communaute/index.html": "https://www.benoitcantin.com/projets/sinjira/communaute/",
    "projets/sinjira/monde-parallele/index.html": "https://www.benoitcantin.com/projets/sinjira/monde-parallele/",
    "projets/sinjira/codex/index.html": "https://www.benoitcantin.com/projets/sinjira/codex/",
    "projets/sinjira/marche/index.html": "https://www.benoitcantin.com/projets/sinjira/marche/",
}

GLOBAL_NAV_HREFS = (
    "/",
    "/projets/sinjira/",
    "/projets/projet-nova/",
    "/a-propos.html",
    "/compte/",
)

FOOTER_HREFS = (
    "/projets/sinjira/romans/",
    "/projets/sinjira/jeux/",
    "/projets/sinjira/registre/",
    "/projets/sinjira/communaute/",
    "/projets/sinjira/monde-parallele/",
    "/projets/sinjira/codex/",
    "/contact.html",
    "/transparence-ia.html",
    "/confidentialite.html",
    "/gouvernance-vie-privee.html",
    "/avis-legal.html",
)


def attribute_value(tag: str, name: str) -> str | None:
    match = re.search(rf"\b{name}=[\"']([^\"']+)[\"']", tag, re.I)
    return match.group(1) if match else None


def find_tag(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.I)
    return match.group(0) if match else None


def main() -> int:
    errors: list[str] = []

    for rel, canonical in PRIMARY_PAGES.items():
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"Page publique SINJIRA absente: {rel}")
            continue

        text = path.read_text(encoding="utf-8", errors="strict")

        header_match = re.search(r"<header\b[\s\S]*?</header>", text, re.I)
        if not header_match:
            errors.append(f"En-tête public absent: {rel}")
        else:
            header = header_match.group(0)
            if 'data-menu-toggle' not in header:
                errors.append(f"Bouton menu mobile absent: {rel}")
            if 'aria-controls="navigation-principale"' not in header:
                errors.append(f"aria-controls navigation absent: {rel}")
            nav_match = re.search(r"<nav\b[^>]*class=[\"'][^\"']*main-nav[^\"']*[\"'][\s\S]*?</nav>", header, re.I)
            if not nav_match:
                errors.append(f"Navigation principale absente: {rel}")
            else:
                nav = nav_match.group(0)
                for href in GLOBAL_NAV_HREFS:
                    if f'href="{href}"' not in nav and f"href='{href}'" not in nav:
                        errors.append(f"Lien global {href} absent de {rel}")

        footer_match = re.search(r"<footer\b[\s\S]*?</footer>", text, re.I)
        if not footer_match:
            errors.append(f"Pied de page public absent: {rel}")
        else:
            footer = footer_match.group(0)
            for href in FOOTER_HREFS:
                if f'href="{href}"' not in footer and f"href='{href}'" not in footer:
                    errors.append(f"Lien pied de page {href} absent de {rel}")

        canonical_tag = find_tag(text, r"<link\b[^>]*rel=[\"']canonical[\"'][^>]*>|<link\b[^>]*href=[\"'][^\"']+[\"'][^>]*rel=[\"']canonical[\"'][^>]*>")
        if not canonical_tag or attribute_value(canonical_tag, "href") != canonical:
            errors.append(f"Canonical incorrecte: {rel}")

        og_url_tag = find_tag(text, r"<meta\b[^>]*property=[\"']og:url[\"'][^>]*>|<meta\b[^>]*content=[\"'][^\"']+[\"'][^>]*property=[\"']og:url[\"'][^>]*>")
        if not og_url_tag or attribute_value(og_url_tag, "content") != canonical:
            errors.append(f"og:url incorrecte: {rel}")

        required_markers = (
            'property="og:title"',
            'property="og:description"',
            'property="og:image"',
            'name="twitter:card"',
            'name="twitter:title"',
            'name="twitter:description"',
            'name="twitter:image"',
            'application/ld+json',
        )
        for marker in required_markers:
            if marker not in text:
                errors.append(f"Métadonnée {marker} absente: {rel}")

    if errors:
        print(f"ECHEC: {len(errors)} problème(s) dans le shell public SINJIRA.")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK shell public SINJIRA: navigation globale, pieds de page, canonical, "
        "Open Graph, Twitter Cards et JSON-LD vérifiés sur "
        f"{len(PRIMARY_PAGES)} pages."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
