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

LEGACY_REDIRECTS = {
    "projets/sinjira/compte.html": (
        "/compte/",
        "https://www.benoitcantin.com/compte/",
    ),
    "projets/sinjira/personnages/index.html": (
        "/projets/sinjira/registre/",
        "https://www.benoitcantin.com/projets/sinjira/registre/",
    ),
    "projets/sinjira/jeux/le-premier-refuge/index.html": (
        "/projets/sinjira/jeux/reseau-mere-resistance/",
        "https://www.benoitcantin.com/projets/sinjira/jeux/reseau-mere-resistance/",
    ),
    "projets/sinjira/registre/merci.html": (
        "/projets/sinjira/registre/",
        "https://www.benoitcantin.com/projets/sinjira/registre/",
    ),
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

    # Cohérence des contacts SINJIRA : vérifier l'ensemble des pages
    # publiques de l'univers, sans réécrire les champs courriel des comptes,
    # les adresses privées ni le canal indépendant de Projet Nova.
    sinjira_root = ROOT / "projets" / "sinjira"
    official_email = "sinjiraofficiel@gmail.com"
    official_mailto = f'mailto:{official_email}'
    official_youtube = "https://www.youtube.com/@SinjiraOfficiel"
    checked_channels = 0
    for path in sorted(sinjira_root.rglob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        page = path.read_text(encoding="utf-8")
        visible_addresses = re.findall(r"[\\w.+-]+@[\\w.-]+\\.[A-Za-z]{2,}", page)
        for address in visible_addresses:
            if address.lower() != official_email:
                errors.append(f"Courriel public SINJIRA non officiel ({address}) : {rel}")

        footer_match = re.search(r"<footer\\b[\\s\\S]*?</footer>", page, re.I)
        if footer_match and 'href="/contact.html"' in footer_match.group(0):
            checked_channels += 1
            footer = footer_match.group(0)
            if f'href="{official_mailto}"' not in footer:
                errors.append(f"Courriel officiel SINJIRA absent du pied de page : {rel}")
            youtube_tag = find_tag(footer, r'<a\\b[^>]*href="https://www\\.youtube\\.com/@SinjiraOfficiel"[^>]*>')
            if not youtube_tag or 'target="_blank"' not in youtube_tag or (
                "noopener" not in youtube_tag or "noreferrer" not in youtube_tag
            ):
                errors.append(f"Lien YouTube SINJIRA non sécurisé dans le pied de page : {rel}")

    home = (sinjira_root / "index.html").read_text(encoding="utf-8")
    if 'class="sinjira-official-channels"' not in home:
        errors.append("Bloc des canaux officiels absent de l’accueil SINJIRA")
    youtube_icon_link = find_tag(
        home, r'<a\\b[^>]*class="sinjira-official-channel sinjira-official-channel-youtube"[^>]*>',
    )
    if not youtube_icon_link or f'href="{official_youtube}"' not in youtube_icon_link:
        errors.append("Accès prioritaire à la chaîne YouTube SINJIRA absent")
    if not re.search(r'<svg\\b[^>]*class="sinjira-channel-icon"[^>]*>[\\s\\S]*?</svg>', home):
        errors.append("Icône SVG YouTube inaccessible ou absente")
    if f'href="{official_mailto}"' not in home:
        errors.append("Courriel SINJIRA absent de l’accueil")
    if 'sinjira.css?v=24.4.13' not in home:
        errors.append("Feuille de style des canaux SINJIRA non actualisée")

    contact = (ROOT / "contact.html").read_text(encoding="utf-8")
    if contact.count(f'href="{official_mailto}"') < 2:
        errors.append("Adresse officielle SINJIRA insuffisamment visible sur Contact")
    if f'href="{official_youtube}"' not in contact:
        errors.append("Chaîne YouTube SINJIRA absente de Contact")
    if '<option value="SINJIRA" disabled>' not in contact:
        errors.append("Le formulaire personnel pourrait router un message SINJIRA vers le mauvais canal")
    if '<option value="Registre des Consciences" disabled>' not in contact:
        errors.append("Le formulaire personnel pourrait router le Registre vers le mauvais canal")
    if 'href="/projets/projet-nova/contact.html"' not in contact:
        errors.append("Le canal séparé de Projet Nova est absent de Contact")
    nova_contact = (ROOT / "projets" / "projet-nova" / "contact.html").read_text(encoding="utf-8")
    if "officiellenovaparti@gmail.com" not in nova_contact or official_email in nova_contact:
        errors.append("Isolation des contacts Projet Nova / SINJIRA non respectée")

    if checked_channels < 10:
        errors.append("Le contrôle des canaux officiels ne couvre pas assez de pieds de page SINJIRA")

    for rel, (target, canonical) in LEGACY_REDIRECTS.items():
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"Route héritée SINJIRA absente: {rel}")
            continue

        text = path.read_text(encoding="utf-8", errors="strict")
        low = text.lower()
        if 'name="robots" content="noindex,nofollow,noarchive"' not in low:
            errors.append(f"Route héritée non protégée noindex/noarchive: {rel}")
        if f'http-equiv="refresh" content="0; url={target.lower()}"' not in low:
            errors.append(f"Redirection héritée incorrecte vers {target}: {rel}")
        if f'href="{target}"' not in text and f"href='{target}'" not in text:
            errors.append(f"Lien de secours absent vers {target}: {rel}")
        canonical_tag = find_tag(
            text,
            r"<link\b[^>]*rel=[\"']canonical[\"'][^>]*>|<link\b[^>]*href=[\"'][^\"']+[\"'][^>]*rel=[\"']canonical[\"'][^>]*>",
        )
        if not canonical_tag or attribute_value(canonical_tag, "href") != canonical:
            errors.append(f"Canonical de redirection incorrecte: {rel}")
        if '<meta name="viewport"' not in low:
            errors.append(f"Viewport absent de la route héritée: {rel}")

    if errors:
        print(f"ECHEC: {len(errors)} problème(s) dans le shell public SINJIRA.")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK shell public SINJIRA: navigation globale, pieds de page, canonical, "
        "Open Graph, Twitter Cards et JSON-LD vérifiés sur "
        f"{len(PRIMARY_PAGES)} pages et {len(LEGACY_REDIRECTS)} routes héritées."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
