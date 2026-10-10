#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AUTH_PAGES = {
    "compte/connexion.html": "Navigation d’authentification",
    "compte/inscription.html": "Navigation d’authentification",
    "compte/mot-de-passe-oublie.html": "Navigation d’authentification",
    "compte/reinitialiser-mot-de-passe.html": "Navigation de récupération",
    "compte/mfa.html": "Navigation de sécurité",
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


def check_global_shell(rel: str, html: str, errors: list[str]) -> None:
    robots = robots_value(html)
    if "noindex" not in robots or "nofollow" not in robots:
        errors.append(f"{rel}: noindex/nofollow absent.")
    if 'class="skip-link"' not in html:
        errors.append(f"{rel}: lien d’évitement absent.")
    if not re.search(r'<main\b[^>]*\bid=["\'](?:main-content|contenu)["\']', html, re.I):
        errors.append(f"{rel}: repère main accessible absent.")

    header_match = re.search(r"<header\b[\s\S]*?</header>", html, re.I)
    if not header_match:
        errors.append(f"{rel}: en-tête absent.")
        return
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


def main() -> int:
    errors: list[str] = []

    for rel, subnav_label in AUTH_PAGES.items():
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"Page Auth/MFA absente: {rel}")
            continue
        html = path.read_text("utf-8", errors="strict")
        check_global_shell(rel, html, errors)
        if f'aria-label="{subnav_label}"' not in html:
            errors.append(f"{rel}: sous-navigation contextuelle absente.")

    netlify_path = ROOT / "netlify.toml"
    if not netlify_path.is_file():
        errors.append("netlify.toml absent.")
    else:
        netlify = netlify_path.read_text("utf-8", errors="strict")
        for private_scope in ("/compte/*", "/admin/*", "/Admin/*", "/app/*", "/supabase/*"):
            block_pattern = re.compile(
                rf'\[\[headers\]\]\s*for\s*=\s*["\']{re.escape(private_scope)}["\'][\s\S]*?(?=\n\[\[|\Z)',
                re.I,
            )
            block_match = block_pattern.search(netlify)
            if not block_match:
                errors.append(f"netlify.toml: bloc privé absent pour {private_scope}.")
                continue
            block = block_match.group(0)
            for expected in (
                'Cache-Control = "private, no-store, max-age=0"',
                'Pragma = "no-cache"',
                'Referrer-Policy = "no-referrer"',
            ):
                if expected not in block:
                    errors.append(f"netlify.toml: {private_scope} sans {expected}.")

    security_path = ROOT / "compte/securite.html"
    if not security_path.is_file():
        errors.append("Centre de sécurité absent.")
    else:
        html = security_path.read_text("utf-8", errors="strict")
        check_global_shell("compte/securite.html", html, errors)
        if not re.search(r'<main\b[^>]*\bid=["\']contenu["\']', html, re.I):
            errors.append("compte/securite.html: main#contenu absent.")
        nav_match = re.search(
            r'<nav\b[^>]*class=["\'][^"\']*account-nav[^"\']*["\'][^>]*>[\s\S]*?</nav>',
            html,
            re.I,
        )
        if not nav_match:
            errors.append("compte/securite.html: navigation du compte absente.")
        else:
            nav = nav_match.group(0)
            for href in ACCOUNT_NAV:
                if f'href="{href}"' not in nav and f"href='{href}'" not in nav:
                    errors.append(f"compte/securite.html: destination compte absente: {href}")
            if 'aria-current="page" href="securite.html"' not in nav:
                errors.append("compte/securite.html: entrée Sécurité active absente.")
            if 'data-admin-nav' not in nav or 'data-logout' not in nav:
                errors.append("compte/securite.html: administration conditionnelle ou déconnexion absente.")

    if errors:
        print(f"ECHEC shell Auth/Sécurité: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK shell Auth/Sécurité: 5 pages Auth/MFA et le Centre de sécurité "
        "conservent noindex/nofollow, navigation globale mobile, repères accessibles et en-têtes HTTP no-store."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
