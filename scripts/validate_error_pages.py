#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]

GLOBAL_NAV = (
    "/",
    "/projets/sinjira/",
    "/projets/projet-nova/",
    "/a-propos.html",
    "/contact.html",
)

ERROR_PAGES = {
    "404.html": {
        "title": "Page introuvable",
        "markers": (
            "Erreur 404",
            "Retour à l’accueil",
            "Ouvrir SINJIRA™",
            "Projet Nova",
        ),
    },
    "offline.html": {
        "title": "Hors ligne",
        "markers": (
            "Vous êtes hors ligne.",
            "Réessayer la connexion",
            "Aucune donnée privée",
        ),
    },
}


def local_target(raw: str, base: Path) -> Path | None:
    raw = str(raw or "").strip()
    if not raw or raw.startswith(("#", "//", "data:", "blob:", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc not in {"www.benoitcantin.com", "benoitcantin.com"}:
            return None
        path = unquote(parsed.path)
    else:
        path = unquote(parsed.path)
    if not path:
        return None
    target = ROOT / path.lstrip("/") if path.startswith("/") else base / path
    if path.endswith("/"):
        target = target / "index.html"
    if not target.exists() and target.suffix == "" and (target / "index.html").exists():
        target = target / "index.html"
    return target.resolve()


def robots_value(html: str) -> str:
    for tag in re.findall(r"<meta\b[^>]*>", html, re.I):
        if re.search(r"\bname=[\"']robots[\"']", tag, re.I):
            match = re.search(r"\bcontent=[\"']([^\"']+)[\"']", tag, re.I)
            if match:
                return match.group(1).lower()
    return ""


def validate_page(rel: str, cfg: dict[str, object], errors: list[str]) -> None:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"{rel}: fichier absent.")
        return

    html = path.read_text("utf-8", errors="strict")
    robots = robots_value(html)
    for marker in ("noindex", "nofollow", "noarchive"):
        if marker not in robots:
            errors.append(f"{rel}: robots privé/erreur incomplet, {marker} absent.")

    if str(cfg["title"]).lower() not in html.lower():
        errors.append(f"{rel}: titre attendu absent: {cfg['title']}")

    if 'class="skip-link"' not in html or 'href="#contenu"' not in html:
        errors.append(f"{rel}: lien d’évitement vers #contenu absent.")
    if not re.search(r'<main\b[^>]*\bid=[\"\']contenu[\"\']', html, re.I):
        errors.append(f"{rel}: main#contenu absent.")

    header = re.search(r"<header\b[\s\S]*?</header>", html, re.I)
    if not header:
        errors.append(f"{rel}: en-tête global absent.")
    else:
        shell = header.group(0)
        for marker in (
            "data-menu-toggle",
            'aria-controls="navigation-principale"',
            'id="navigation-principale"',
            "data-main-nav",
        ):
            if marker not in shell:
                errors.append(f"{rel}: contrat menu mobile absent: {marker}")
        for href in GLOBAL_NAV:
            if f'href="{href}"' not in shell and f"href='{href}'" not in shell:
                errors.append(f"{rel}: destination globale absente: {href}")

    if "/assets/js/site.js" not in html:
        errors.append(f"{rel}: runtime global site.js absent.")

    for marker in cfg["markers"]:
        if str(marker).lower() not in html.lower():
            errors.append(f"{rel}: contenu de secours absent: {marker}")

    for raw in re.findall(r'(?:href|src)=[\"\']([^\"\']+)[\"\']', html, re.I):
        target = local_target(raw, path.parent)
        if target is not None and not target.exists():
            errors.append(f"{rel}: ressource/lien local absent: {raw}")

    if rel == "404.html":
        for legacy, target in (
            ("'/sinjira'", "'/projets/sinjira/'"),
            ("'/admin'", "'/admin/sinjira/'"),
        ):
            if legacy not in html or target not in html:
                errors.append(f"{rel}: redirection de compatibilité perdue: {legacy} -> {target}")

    if rel == "offline.html":
        if 'role="status"' not in html or 'aria-live="polite"' not in html:
            errors.append(f"{rel}: annonce accessible de reprise réseau absente.")
        if "location.reload()" not in html:
            errors.append(f"{rel}: action de nouvelle tentative absente.")


def main() -> int:
    errors: list[str] = []
    for rel, cfg in ERROR_PAGES.items():
        validate_page(rel, cfg, errors)

    if errors:
        print(f"ECHEC pages de résilience: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK pages de résilience: 404 et hors-ligne sont noindex, accessibles, "
        "mobiles et reliées au shell public sans dépendance privée."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
