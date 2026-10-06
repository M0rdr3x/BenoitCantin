#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_ROOT = (
    "index.html",
    "a-propos.html",
    "avis-legal.html",
    "confidentialite.html",
    "contact.html",
    "gouvernance-vie-privee.html",
    "merci.html",
    "transparence-ia.html",
    "univers.html",
)

GLOBAL_NAV = (
    "/",
    "/projets/sinjira/",
    "/projets/projet-nova/",
    "/a-propos.html",
    "/compte/",
)


def robots_value(html: str) -> str:
    for tag in re.findall(r"<meta\b[^>]*>", html, re.I):
        if re.search(r"\bname=[\"']robots[\"']", tag, re.I):
            m = re.search(r"\bcontent=[\"']([^\"']+)[\"']", tag, re.I)
            if m:
                return m.group(1).lower()
    return ""


def validate_page(rel: str, errors: list[str]) -> None:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"{rel}: page publique absente.")
        return

    html = path.read_text("utf-8", errors="strict")

    if 'class="skip-link"' not in html or 'href="#contenu"' not in html:
        errors.append(f"{rel}: lien d’évitement vers #contenu absent.")
    if not re.search(r'<main\b[^>]*\bid=[\"\']contenu[\"\']', html, re.I):
        errors.append(f"{rel}: main#contenu absent.")

    header = re.search(r"<header\b[\s\S]*?</header>", html, re.I)
    if not header:
        errors.append(f"{rel}: en-tête public absent.")
    else:
        shell = header.group(0)
        for marker in (
            "data-menu-toggle",
            'aria-controls="navigation-principale"',
            'id="navigation-principale"',
            "data-main-nav",
            'aria-label="Navigation principale"',
        ):
            if marker not in shell:
                errors.append(f"{rel}: contrat mobile/public absent: {marker}")
        for href in GLOBAL_NAV:
            if f'href="{href}"' not in shell and f"href='{href}'" not in shell:
                errors.append(f"{rel}: lien public principal absent: {href}")

    if not re.search(r'<link\b[^>]*rel=[\"\']canonical[\"\']', html, re.I):
        errors.append(f"{rel}: canonical absent.")
    if "/assets/css/site.css" not in html:
        errors.append(f"{rel}: CSS public site.css absent.")
    if "browser-compat-v24-4-22.css" not in html:
        errors.append(f"{rel}: socle de compatibilité navigateur absent.")
    if "/assets/js/site.js" not in html:
        errors.append(f"{rel}: runtime public site.js absent.")

    robots = robots_value(html)
    if rel == "merci.html":
        for marker in ("noindex", "nofollow", "noarchive"):
            if marker not in robots:
                errors.append(f"{rel}: page de confirmation indexable, {marker} absent.")
    elif "noindex" in robots:
        errors.append(f"{rel}: page publique principale marquée noindex.")


def main() -> int:
    errors: list[str] = []
    for rel in PUBLIC_ROOT:
        validate_page(rel, errors)

    if errors:
        print(f"ECHEC shell public racine: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK shell public racine: 9 pages actives partagent le menu mobile accessible, "
        "les destinations principales, le canonical et le socle navigateur."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
