#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LIMITS = {
    ".js": 550_000,
    ".css": 550_000,
    ".html": 650_000,
    ".webp": 1_500_000,
    ".avif": 1_500_000,
    ".png": 3_000_000,
    ".jpg": 3_000_000,
    ".jpeg": 3_000_000,
}
EXCLUDED_DIRS = {".git", "node_modules", ".venv", "dist", "build"}


def iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def main() -> int:
    errors = []
    for path in iter_files():
        limit = LIMITS.get(path.suffix.lower())
        if limit and path.stat().st_size > limit:
            errors.append(
                f"{path.relative_to(ROOT)}: {path.stat().st_size:,} octets dépasse le budget de {limit:,}."
            )

    home = (ROOT / "index.html").read_text("utf-8", errors="ignore")
    script_count = len(re.findall(r"<script\b", home, flags=re.I))
    stylesheet_count = len(re.findall(r"<link\b[^>]*rel=[\"']stylesheet[\"']", home, flags=re.I))
    if script_count > 6:
        errors.append(f"index.html: {script_count} scripts; budget maximal 6.")
    if stylesheet_count > 8:
        errors.append(f"index.html: {stylesheet_count} feuilles de style; budget maximal 8.")

    # Les trois cartes situées sous le premier écran doivent être différées.
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
    print("OK performance: poids des actifs, budget de dépendances et chargement différé de l’accueil sont sous contrôle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
