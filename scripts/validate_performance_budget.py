#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlparse
import re

ROOT = Path(__file__).resolve().parents[1]
TEXT_LIMITS = {".js": 550_000, ".css": 550_000, ".html": 650_000}
IMAGE_LIMIT = 1_500_000
EXCLUDED_DIRS = {".git", "node_modules", ".venv", "dist", "build"}
CRITICAL_PAGES = [
    ROOT / "index.html",
    ROOT / "projets" / "sinjira" / "index.html",
    ROOT / "projets" / "sinjira" / "registre" / "index.html",
    ROOT / "projets" / "projet-nova" / "index.html",
]


def iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def resolve_asset(page: Path, value: str) -> Path | None:
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or value.startswith("data:"):
        return None
    clean = parsed.path
    if clean.startswith("/"):
        return ROOT / clean.lstrip("/")
    return (page.parent / clean).resolve()


def main() -> int:
    errors = []

    # Les budgets texte s’appliquent à tout le runtime versionné.
    for path in iter_files():
        limit = TEXT_LIMITS.get(path.suffix.lower())
        if limit and path.stat().st_size > limit:
            errors.append(
                f"{path.relative_to(ROOT)}: {path.stat().st_size:,} octets dépasse le budget de {limit:,}."
            )

    # Pour les images, on contrôle les actifs réellement chargés par les pages
    # critiques plutôt que des archives/documentations qui ne pénalisent pas le web.
    image_refs = set()
    for page in CRITICAL_PAGES:
        if not page.exists():
            continue
        html = page.read_text("utf-8", errors="ignore")
        for value in re.findall(r"<img\b[^>]*\bsrc=[\"']([^\"']+)", html, flags=re.I):
            asset = resolve_asset(page, value)
            if asset and asset.suffix.lower() in {".webp", ".avif", ".png", ".jpg", ".jpeg"}:
                image_refs.add(asset)
    for asset in sorted(image_refs):
        if not asset.exists():
            errors.append(f"Actif image critique absent: {asset.relative_to(ROOT)}")
        elif asset.stat().st_size > IMAGE_LIMIT:
            errors.append(
                f"{asset.relative_to(ROOT)}: {asset.stat().st_size:,} octets dépasse le budget image critique de {IMAGE_LIMIT:,}."
            )

    home = (ROOT / "index.html").read_text("utf-8", errors="ignore")
    script_count = len(re.findall(r"<script\b", home, flags=re.I))
    stylesheet_count = len(re.findall(r"<link\b[^>]*rel=[\"']stylesheet[\"']", home, flags=re.I))
    if script_count > 6:
        errors.append(f"index.html: {script_count} scripts; budget maximal 6.")
    if stylesheet_count > 8:
        errors.append(f"index.html: {stylesheet_count} feuilles de style; budget maximal 8.")

    cards = re.findall(r'<a class="home-project".*?</a>', home, flags=re.I | re.S)
    if len(cards) != 3:
        errors.append(f"index.html: 3 cartes principales attendues, trouvé {len(cards)}.")
    else:
        for idx, card in enumerate(cards, start=1):
            image = re.search(r"<img\b[^>]*>", card, flags=re.I)
            if not image:
                errors.append(f"index.html: carte {idx} sans image.")
                continue
            tag = image.group(0)
            if 'loading="lazy"' not in tag:
                errors.append(f"index.html: image de la carte {idx} sans loading=lazy.")
            if 'decoding="async"' not in tag:
                errors.append(f"index.html: image de la carte {idx} sans decoding=async.")

    if errors:
        print(f"ECHEC budgets performance: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1
    print(f"OK performance: {len(image_refs)} image(s) critiques, budgets texte et chargement différé de l’accueil sont sous contrôle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
