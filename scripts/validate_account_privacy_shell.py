#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PRIVATE_PAGES = {
    "compte/confidentialite-joueur.html": "Navigation confidentialité",
    "compte/vie-privee.html": "Navigation vie privée",
    "compte/signaler-deces.html": "Navigation héritage numérique",
}

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


def main() -> int:
    errors: list[str] = []

    for rel, subnav_label in PRIVATE_PAGES.items():
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"Page privée absente: {rel}")
            continue
        html = path.read_text("utf-8", errors="strict")
        robots = robots_value(html)
        if "noindex" not in robots or "nofollow" not in robots:
            errors.append(f"{rel}: noindex/nofollow absent.")
        if 'class="skip-link"' not in html or 'href="#contenu"' not in html:
            errors.append(f"{rel}: lien d’évitement vers #contenu absent.")
        if not re.search(r'<main\b[^>]*\bid=["\']contenu["\']', html, re.I):
            errors.append(f"{rel}: repère main#contenu absent.")

        header_match = re.search(r"<header\b[\s\S]*?</header>", html, re.I)
        if not header_match:
            errors.append(f"{rel}: en-tête absent.")
        else:
            header = header_match.group(0)
            for marker in (
                'data-menu-toggle',
                'aria-controls="navigation-principale"',
                'id="navigation-principale"',
                'data-main-nav',
            ):
                if marker not in header:
                    errors.append(f"{rel}: contrat menu mobile absent: {marker}")
            for href in GLOBAL_NAV:
                if f'href="{href}"' not in header and f"href='{href}'" not in header:
                    errors.append(f"{rel}: lien global absent: {href}")

        if f'aria-label="{subnav_label}"' not in html:
            errors.append(f"{rel}: sous-navigation contextuelle absente.")

    legacy = ROOT / "compte/mes-personnages.html"
    if not legacy.is_file():
        errors.append("Route héritée mes-personnages absente.")
    else:
        html = legacy.read_text("utf-8", errors="strict")
        low = html.lower()
        if 'name="robots" content="noindex,nofollow,noarchive"' not in low:
            errors.append("mes-personnages: contrat noindex/noarchive absent.")
        if 'http-equiv="refresh" content="0; url=/compte/mon-personnage.html"' not in low:
            errors.append("mes-personnages: redirection directe incorrecte.")
        if 'rel="canonical" href="https://www.benoitcantin.com/compte/mon-personnage.html"' not in low:
            errors.append("mes-personnages: canonical actuelle absente.")
        if 'href="/compte/mon-personnage.html"' not in html:
            errors.append("mes-personnages: lien de secours absent.")

    if errors:
        print(f"ECHEC shell confidentialité: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK shell confidentialité: 3 pages privées accessibles et une route héritée "
        "noindex/noarchive avec redirection canonique."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
