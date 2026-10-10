#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALIASES = (
    "accessibilite.html",
    "actualites.html",
    "code-conduite.html",
    "comprendre-nova.html",
    "comptabilite.html",
    "constitution.html",
    "documents.html",
    "equipe.html",
    "faq.html",
    "formulaire-soutien.html",
    "livre-nova.html",
    "lois-administratives.html",
    "lois-ordinaires.html",
    "lois-organiques.html",
    "manifeste.html",
    "merci-formulaire.html",
    "mises-a-jour.html",
    "mission.html",
    "participer.html",
    "presse.html",
    "programme.html",
    "propositions.html",
    "recrutement.html",
    "registre-conformite.html",
    "registre-rencontres.html",
    "reglements.html",
    "transparence.html",
    "transition.html",
    "vision.html",
    "visionneuse.html",
)

BASE = "/projets/projet-nova/"
CANONICAL_BASE = "https://www.benoitcantin.com/projets/projet-nova/"


def robots_value(html: str) -> str:
    for tag in re.findall(r"<meta\b[^>]*>", html, re.I):
        if re.search(r"\bname=[\"']robots[\"']", tag, re.I):
            match = re.search(r"\bcontent=[\"']([^\"']+)[\"']", tag, re.I)
            if match:
                return match.group(1).lower()
    return ""


def validate_alias(name: str, errors: list[str]) -> None:
    source = ROOT / name
    target = ROOT / "projets" / "projet-nova" / name
    if not source.is_file():
        errors.append(f"Alias Nova absent: {name}")
        return
    if not target.is_file():
        errors.append(f"Destination Nova absente pour {name}: {target.relative_to(ROOT)}")
        return

    html = source.read_text("utf-8", errors="strict")
    robots = robots_value(html)
    for marker in ("noindex", "nofollow", "noarchive"):
        if marker not in robots:
            errors.append(f"{name}: robots incomplet, {marker} absent.")

    destination = BASE + name
    canonical = CANONICAL_BASE + name

    if f'rel="canonical" href="{canonical}"' not in html:
        errors.append(f"{name}: canonical exacte absente.")
    if not re.search(
        rf'http-equiv=[\"\']refresh[\"\'][^>]*content=[\"\']0;\s*url={re.escape(destination)}[\"\']',
        html,
        re.I,
    ):
        errors.append(f"{name}: meta refresh exacte absente vers {destination}.")
    if f'href="{destination}"' not in html:
        errors.append(f"{name}: lien de secours exact absent.")
    if f"const target='{destination}'+location.search+location.hash" not in html:
        errors.append(f"{name}: redirection JS ne conserve pas query/hash.")

    if "location.pathname" in html:
        errors.append(f"{name}: redirection générique dynamique encore présente.")


def main() -> int:
    errors: list[str] = []
    for name in ALIASES:
        validate_alias(name, errors)

    discovered = {
        path.name
        for path in ROOT.glob("*.html")
        if "Projet Nova — redirection" in path.read_text("utf-8", errors="ignore")
    }
    expected = set(ALIASES)
    if discovered != expected:
        missing = sorted(expected - discovered)
        extra = sorted(discovered - expected)
        if missing:
            errors.append("Alias Nova attendus sans stub reconnu: " + ", ".join(missing))
        if extra:
            errors.append("Alias Nova non classés dans le validateur: " + ", ".join(extra))

    netlify = (ROOT / "netlify.toml").read_text("utf-8", errors="strict")
    for name in ALIASES:
        from_line = f'from = "/{name}"'
        to_line = f'to = "{BASE}{name}"'
        if from_line not in netlify or to_line not in netlify:
            errors.append(f"netlify.toml: redirection 301 absente pour {name}.")

    if errors:
        print(f"ECHEC routes legacy Projet Nova: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        f"OK routes legacy Projet Nova: {len(ALIASES)} alias racine redirigent "
        "déterministement vers des destinations existantes, canoniques et non indexables."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
