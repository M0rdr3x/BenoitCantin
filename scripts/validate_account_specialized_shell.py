#!/usr/bin/env python3
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CATEGORIES = {
    "auth": {
        "compte/connexion.html",
        "compte/inscription.html",
        "compte/mot-de-passe-oublie.html",
        "compte/reinitialiser-mot-de-passe.html",
        "compte/mfa.html",
    },
    "coeur": {
        "compte/index.html",
        "compte/bibliotheque.html",
        "compte/licences.html",
        "compte/mes-lectures.html",
        "compte/mes-achats.html",
        "compte/notifications.html",
        "compte/profil.html",
        "compte/parametres.html",
    },
    "secondaire": {
        "compte/mes-parties.html",
        "compte/documents.html",
        "compte/mon-personnage.html",
        "compte/communaute.html",
        "compte/monde-parallele.html",
        "compte/emploi.html",
        "compte/marche.html",
        "compte/jetons.html",
    },
    "social": {
        "compte/relations.html",
        "compte/messages.html",
        "compte/messages-reels.html",
        "compte/messages-personnage.html",
        "compte/reseau-personnage.html",
        "compte/rencontres.html",
        "compte/blocages.html",
        "compte/mes-commentaires.html",
    },
    "personnel": {
        "compte/registre-personnel.html",
        "compte/histoire-de-vie.html",
        "compte/mon-ia.html",
        "compte/contributions.html",
        "compte/playtests.html",
        "compte/regles-communaute.html",
    },
    "confidentialite": {
        "compte/confidentialite-joueur.html",
        "compte/vie-privee.html",
        "compte/signaler-deces.html",
    },
    "securite": {
        "compte/securite.html",
    },
    "alias-redirection": {
        "compte/mes-personnages.html",
    },
    "specialisee": {
        "compte/projet.html",
        "compte/moderation.html",
    },
}

SPECIALIZED_PAGES = {
    "compte/projet.html": "bibliotheque.html",
    "compte/moderation.html": "moderation.html",
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


def validate_inventory(errors: list[str]) -> None:
    compte_dir = ROOT / "compte"
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in compte_dir.glob("*.html")
        if path.is_file()
    }

    classified_list = [
        path
        for pages in CATEGORIES.values()
        for path in pages
    ]
    counts = Counter(classified_list)
    duplicates = sorted(path for path, count in counts.items() if count != 1)
    classified = set(classified_list)

    if duplicates:
        errors.append(
            "Inventaire compte: pages classées plusieurs fois: "
            + ", ".join(duplicates)
        )

    missing = sorted(actual - classified)
    stale = sorted(classified - actual)
    if missing:
        errors.append(
            "Inventaire compte: pages HTML non classées: " + ", ".join(missing)
        )
    if stale:
        errors.append(
            "Inventaire compte: classifications sans fichier: " + ", ".join(stale)
        )

    if len(actual) != 42:
        errors.append(
            f"Inventaire compte: 42 pages HTML attendues, {len(actual)} trouvées."
        )
    if len(classified) != 42:
        errors.append(
            f"Inventaire compte: 42 pages classées attendues, {len(classified)} déclarées."
        )


def validate_specialized_shell(rel: str, current: str, errors: list[str]) -> None:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"Page spécialisée absente: {rel}")
        return

    html = path.read_text("utf-8", errors="strict")
    robots = robots_value(html)
    if "noindex" not in robots or "nofollow" not in robots:
        errors.append(f"{rel}: noindex/nofollow absent.")

    if 'class="skip-link"' not in html or 'href="#contenu"' not in html:
        errors.append(f"{rel}: lien d’évitement vers #contenu absent.")
    if not re.search(r'<main\b[^>]*\bid=[\"\']contenu[\"\']', html, re.I):
        errors.append(f"{rel}: repère main#contenu absent.")

    header_match = re.search(r"<header\b[\s\S]*?</header>", html, re.I)
    if not header_match:
        errors.append(f"{rel}: en-tête absent.")
    else:
        header = header_match.group(0)
        for marker in (
            "data-menu-toggle",
            'aria-controls="navigation-principale"',
            'id="navigation-principale"',
            "data-main-nav",
        ):
            if marker not in header:
                errors.append(f"{rel}: contrat menu mobile absent: {marker}")
        for href in GLOBAL_NAV:
            if f'href="{href}"' not in header and f"href='{href}'" not in header:
                errors.append(f"{rel}: lien global absent: {href}")

    nav_match = re.search(
        r'<nav\b[^>]*class=[\"\'][^\"\']*account-nav[^\"\']*[\"\'][^>]*>[\s\S]*?</nav>',
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
        if f'aria-current="page" href="{current}"' not in nav:
            errors.append(f"{rel}: aria-current incorrect pour {current}.")
        if "data-admin-nav" not in nav or "data-logout" not in nav:
            errors.append(
                f"{rel}: administration conditionnelle ou déconnexion absente."
            )

    if rel == "compte/projet.html":
        for marker in (
            'data-library-page="project"',
            "data-project-name",
            "data-project-documents",
            "data-project-playtests",
            "data-library-status",
            "sinjira-library.js",
        ):
            if marker not in html:
                errors.append(f"{rel}: contrat bibliothèque perdu: {marker}")

    if rel == "compte/moderation.html":
        for marker in (
            "Mes décisions de modération et mes appels",
            "appel interne est <strong>gratuit</strong>",
            "révision humaine",
            "data-moderation-list",
            "sinjira-moderation-appeals-v24-4-90.js",
        ):
            if marker.lower() not in html.lower():
                errors.append(f"{rel}: contrat modération perdu: {marker}")


def main() -> int:
    errors: list[str] = []

    validate_inventory(errors)
    for rel, current in SPECIALIZED_PAGES.items():
        validate_specialized_shell(rel, current, errors)

    if errors:
        print(f"ECHEC inventaire/shell spécialisé du compte: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK Compte SINJIRA: 42 pages HTML classées explicitement; "
        "projet et modération utilisent le shell privé stable sans perdre leurs contrats."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
