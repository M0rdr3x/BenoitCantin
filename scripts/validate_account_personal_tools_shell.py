#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGES = {
    "compte/registre-personnel.html": None,
    "compte/histoire-de-vie.html": None,
    "compte/mon-ia.html": None,
    "compte/contributions.html": None,
    "compte/playtests.html": None,
    "compte/regles-communaute.html": "communaute.html",
}

GLOBAL_NAV = (
    "/",
    "/projets/sinjira/",
    "/projets/projet-nova/",
    "/a-propos.html",
    "/compte/",
)

ACCOUNT_NAV = (
    "index.html",
    "bibliotheque.html",
    "licences.html",
    "mes-lectures.html",
    "mes-achats.html",
    "notifications.html",
    "mon-personnage.html",
    "communaute.html",
    "messages.html",
    "profil.html",
    "securite.html",
    "parametres.html",
)


def robots_value(html: str) -> str:
    for tag in re.findall(r"<meta\b[^>]*>", html, re.I):
        if re.search(r"\bname=[\"']robots[\"']", tag, re.I):
            match = re.search(r"\bcontent=[\"']([^\"']+)[\"']", tag, re.I)
            if match:
                return match.group(1).lower()
    return ""


def main() -> int:
    errors: list[str] = []

    for rel, current in PAGES.items():
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"Page personnelle privée absente: {rel}")
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

        nav_match = re.search(
            r'<nav\b[^>]*class=["\'][^"\']*account-nav[^"\']*["\'][^>]*>[\s\S]*?</nav>',
            html,
            re.I,
        )
        if not nav_match:
            errors.append(f"{rel}: navigation du compte absente.")
        else:
            nav = nav_match.group(0)
            if 'aria-label="Navigation du compte"' not in nav:
                errors.append(f"{rel}: libellé accessible de navigation du compte absent.")
            for href in ACCOUNT_NAV:
                if f'href="{href}"' not in nav and f"href='{href}'" not in nav:
                    errors.append(f"{rel}: destination compte absente: {href}")
            if current and f'aria-current="page" href="{current}"' not in nav:
                errors.append(f"{rel}: aria-current incorrect pour {current}.")
            if 'data-admin-nav' not in nav or 'data-logout' not in nav:
                errors.append(f"{rel}: administration conditionnelle ou déconnexion absente.")

    if errors:
        print(f"ECHEC shell outils personnels: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK shell outils personnels: 6 pages privées avec noindex/nofollow, "
        "navigation globale mobile, navigation compte stable et repères accessibles."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
