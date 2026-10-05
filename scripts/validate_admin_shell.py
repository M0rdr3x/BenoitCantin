#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ACTIVE = {
    "admin/sinjira/index.html": "/admin/sinjira/",
    "admin/sinjira/licences.html": "/admin/sinjira/licences.html",
    "admin/sinjira/precommandes.html": "/admin/sinjira/precommandes.html",
    "admin/sinjira/precommandes-readiness.html": "/admin/sinjira/precommandes-readiness.html",
    "admin/sinjira/heritage.html": "/admin/sinjira/heritage.html",
}

REDIRECTS = {
    "admin/index.html": (
        "/admin/sinjira/",
        "https://www.benoitcantin.com/admin/sinjira/",
    ),
    "admin/sinjira-analytics.html": (
        "/admin/sinjira/",
        "https://www.benoitcantin.com/admin/sinjira/",
    ),
    "Admin/sinjira-analytics.html": (
        "/admin/sinjira-analytics.html",
        "https://www.benoitcantin.com/admin/sinjira-analytics.html",
    ),
    "Admin/sinjira/index.html": (
        "/admin/sinjira/",
        "https://www.benoitcantin.com/admin/sinjira/",
    ),
    "Admin/sinjira/licences.html": (
        "/admin/sinjira/licences.html",
        "https://www.benoitcantin.com/admin/sinjira/licences.html",
    ),
}

GLOBAL_NAV = (
    "/",
    "/projets/sinjira/",
    "/projets/projet-nova/",
    "/a-propos.html",
    "/compte/",
)

ADMIN_NAV = tuple(ACTIVE.values())

PAGE_CONTRACTS = {
    "admin/sinjira/index.html": (
        "data-admin-tab=",
        "data-admin-panel=",
        "sinjira-admin-console.js",
        "sinjira-admin-v18.js",
        "sinjira-admin-social-v20.js",
    ),
    "admin/sinjira/licences.html": (
        "v24-admin-licenses.js",
    ),
    "admin/sinjira/precommandes.html": (
        "sinjira-admin-preorders-v24-5-4.js",
        "sinjira-admin-preorder-workflow-v24-5-36.js",
        "sinjira-admin-preorder-commercial-v24-5-5.js",
        "sinjira-admin-preorder-fulfillment-v24-5-6.js",
    ),
    "admin/sinjira/precommandes-readiness.html": (
        "sinjira-admin-preorder-readiness-v24-5-41.js",
        "data-readiness-grid",
        "data-readiness-blockers",
        "data-readiness-locks",
    ),
    "admin/sinjira/heritage.html": (
        "sinjira-admin-life-story-v24-5-2.js",
        "Héritage numérique",
    ),
}

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.I,
)
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b")


def robots_value(html: str) -> str:
    for tag in re.findall(r"<meta\b[^>]*>", html, re.I):
        if re.search(r"\bname=[\"']robots[\"']", tag, re.I):
            m = re.search(r"\bcontent=[\"']([^\"']+)[\"']", tag, re.I)
            if m:
                return m.group(1).lower()
    return ""


def html_inventory() -> set[str]:
    result: set[str] = set()
    for base in ("admin", "Admin"):
        root = ROOT / base
        if root.is_dir():
            for path in root.rglob("*.html"):
                result.add(path.relative_to(ROOT).as_posix())
    return result


def validate_active(rel: str, current: str, errors: list[str]) -> None:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"Page Admin active absente: {rel}")
        return

    html = path.read_text("utf-8", errors="strict")
    robots = robots_value(html)
    if "noindex" not in robots or "nofollow" not in robots:
        errors.append(f"{rel}: noindex/nofollow absent.")

    if 'class="skip-link"' not in html or 'href="#contenu"' not in html:
        errors.append(f"{rel}: lien d’évitement vers #contenu absent.")
    if not re.search(r'<main\b[^>]*\bid=[\"\']contenu[\"\']', html, re.I):
        errors.append(f"{rel}: main#contenu absent.")

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
        r'<nav\b[^>]*aria-label=[\"\']Navigation administration[\"\'][^>]*>[\s\S]*?</nav>',
        html,
        re.I,
    )
    if not nav_match:
        errors.append(f"{rel}: navigation Admin dédiée absente.")
    else:
        nav = nav_match.group(0)
        for href in ADMIN_NAV:
            if f'href="{href}"' not in nav and f"href='{href}'" not in nav:
                errors.append(f"{rel}: destination Admin absente: {href}")
        if f'aria-current="page" href="{current}"' not in nav:
            errors.append(f"{rel}: page Admin active incorrecte: {current}")

    if not re.search(r'<script\b[^>]*src=[\"\']/assets/js/site\.js', html, re.I):
        errors.append(f"{rel}: runtime du menu mobile site.js absent.")

    for marker in PAGE_CONTRACTS.get(rel, ()):
        if marker not in html:
            errors.append(f"{rel}: contrat fonctionnel perdu: {marker}")

    if EMAIL_RE.search(html):
        errors.append(f"{rel}: adresse courriel statique détectée dans l’HTML Admin.")
    if UUID_RE.search(html):
        errors.append(f"{rel}: UUID statique détecté dans l’HTML Admin.")
    if JWT_RE.search(html):
        errors.append(f"{rel}: jeton JWT statique détecté dans l’HTML Admin.")


def validate_redirect(rel: str, target: str, canonical: str, errors: list[str]) -> None:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"Route Admin de redirection absente: {rel}")
        return

    html = path.read_text("utf-8", errors="strict")
    robots = robots_value(html)
    for marker in ("noindex", "nofollow", "noarchive"):
        if marker not in robots:
            errors.append(f"{rel}: robots privé incomplet, {marker} absent.")

    if not re.search(
        rf'http-equiv=[\"\']refresh[\"\'][^>]*content=[\"\']0;\s*url={re.escape(target)}[\"\']',
        html,
        re.I,
    ):
        errors.append(f"{rel}: redirection meta incorrecte vers {target}.")
    if f'rel="canonical" href="{canonical}"' not in html:
        errors.append(f"{rel}: canonical incorrecte.")
    if f'href="{target}"' not in html:
        errors.append(f"{rel}: lien de secours absent vers {target}.")
    if f"location.replace('{target}'+location.search+location.hash)" not in html:
        errors.append(f"{rel}: redirection JS ne conserve pas query/hash.")


def main() -> int:
    errors: list[str] = []

    actual = html_inventory()
    expected = set(ACTIVE) | set(REDIRECTS)
    missing_classification = sorted(actual - expected)
    missing_files = sorted(expected - actual)
    if missing_classification:
        errors.append(
            "Inventaire Admin: pages HTML non classées: "
            + ", ".join(missing_classification)
        )
    if missing_files:
        errors.append(
            "Inventaire Admin: classifications sans fichier: "
            + ", ".join(missing_files)
        )
    if len(actual) != 10:
        errors.append(f"Inventaire Admin: 10 pages HTML attendues, {len(actual)} trouvées.")

    for rel, current in ACTIVE.items():
        validate_active(rel, current, errors)
    for rel, (target, canonical) in REDIRECTS.items():
        validate_redirect(rel, target, canonical, errors)

    if errors:
        print(f"ECHEC shell Admin SINJIRA: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK Admin SINJIRA: 5 pages actives accessibles/mobile, 5 redirections privées "
        "canoniques et 10 pages HTML classées sans donnée sensible statique."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
