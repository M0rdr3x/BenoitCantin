#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORE_PAGES = {
    "compte/index.html": "index.html",
    "compte/bibliotheque.html": "bibliotheque.html",
    "compte/licences.html": "licences.html",
    "compte/mes-lectures.html": "mes-lectures.html",
    "compte/mes-achats.html": "mes-achats.html",
    "compte/notifications.html": "notifications.html",
    "compte/profil.html": "profil.html",
    "compte/parametres.html": "parametres.html",
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


def main() -> int:
    errors: list[str] = []

    for rel, current in CORE_PAGES.items():
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"Page coeur du compte absente: {rel}")
            continue

        html = path.read_text("utf-8", errors="strict")
        low = html.lower()

        if 'name="robots" content="noindex,nofollow,noarchive"' not in low:
            errors.append(f"{rel}: noindex/nofollow/noarchive absent.")

        if 'class="skip-link"' not in html or 'href="#contenu"' not in html:
            errors.append(f"{rel}: lien d'évitement vers #contenu absent.")
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
            for href in ACCOUNT_NAV:
                if f'href="{href}"' not in nav and f"href='{href}'" not in nav:
                    errors.append(f"{rel}: destination compte absente: {href}")
            if f'aria-current="page" href="{current}"' not in nav and f"href='{current}' aria-current='page'" not in nav:
                errors.append(f"{rel}: aria-current incorrect pour {current}.")
            if 'data-admin-nav' not in nav or 'data-logout' not in nav:
                errors.append(f"{rel}: administration conditionnelle ou déconnexion absente.")

    if errors:
        print(f"ECHEC shell compte: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK shell compte: 8 pages coeur privées avec noindex/noarchive, "
        "navigation globale mobile, navigation compte cohérente et accessibilité clavier."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
