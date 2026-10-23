#!/usr/bin/env python3
"""Garde de publication: alias historiques de main et confinement Netlify.

Lire les redirections de la branche officielle main, mais NE JAMAIS
reprendre son build.publish='.' (publication du dépôt entier).
"""
from __future__ import annotations

import argparse
import subprocess
import tomllib
from pathlib import Path, PurePosixPath

from build_netlify_public import relative_path_allowed

ROOT = Path(__file__).resolve().parents[1]
RELEASE_CONFIG = ROOT / "netlify.toml"
CANONICAL_MAIN_REF = "refs/remotes/origin/main"
TECHNICAL_DENIALS = (
    "/supabase/*", "/scripts/*", "/docs/*", "/.github/*",
    "/tests/*", "/mobile-native/*", "/.git/*", "/.env*",
    "/.gitignore", "/netlify.toml", "/projets/projet-nova/.gitignore",
    "/projets/projet-nova/.nojekyll",
)


def load_main_config() -> dict:
    p = subprocess.run(
        ["git", "show", f"{CANONICAL_MAIN_REF}:netlify.toml"],
        cwd=ROOT, capture_output=True, check=False,
    )
    if p.returncode:
        raise RuntimeError("Impossible de lire le netlify.toml de main: "
                           + p.stderr.decode("utf-8", "replace")[:300])
    return tomllib.loads(p.stdout.decode("utf-8"))


def redirects_by_source(config: dict) -> tuple[dict[str, dict], list[str]]:
    redirects: dict[str, dict] = {}
    errors: list[str] = []
    for item in config.get("redirects", ()):
        if not isinstance(item, dict) or not isinstance(item.get("from"), str):
            errors.append("Redirection Netlify invalide.")
            continue
        source = item["from"]
        if source in redirects:
            errors.append(f"Redirection Netlify dupliquée: {source}")
        redirects[source] = item
    return redirects, errors


def validate(main: dict, candidate: dict, *, check_files: bool = True) -> list[str]:
    errors: list[str] = []
    build = candidate.get("build", {})
    if build.get("publish") != "_site":
        errors.append("NO_GO : publier uniquement l'artefact isolé _site.")
    if build.get("command") != "python3 scripts/build_netlify_public.py":
        errors.append("NO_GO : le builder public Netlify est obligatoire.")

    historic, historic_errors = redirects_by_source(main)
    release, candidate_errors = redirects_by_source(candidate)
    errors.extend(historic_errors)
    errors.extend(candidate_errors)
    for source, item in sorted(historic.items()):
        current = release.get(source)
        if current is None:
            errors.append(f"Alias historique manquant: {source}")
            continue
        for field in ("to", "status", "force"):
            if field in item and item[field] != current.get(field):
                errors.append(f"Alias historique modifié: {source} ({field}).")
        # L'ajout d'un 'force' sur un alias de main n'est pas neutre.
        if "force" not in item and bool(current.get("force", False)):
            errors.append(f"Alias historique rendu forcé: {source}")

    for source in TECHNICAL_DENIALS:
        deny = release.get(source)
        if deny is None or deny.get("status") != 404 or not deny.get("force"):
            errors.append(f"Refus technique 404 forcé manquant: {source}")
        elif deny.get("to") != "/404.html":
            errors.append(f"Refus technique vers mauvaise destination: {source}")

    order = [d.get("from") for d in candidate.get("redirects", ())]
    if len(order) < len(TECHNICAL_DENIALS) or tuple(order[:len(TECHNICAL_DENIALS)]) != TECHNICAL_DENIALS:
        errors.append("Les 12 refus techniques doivent précéder les alias publics.")

    if check_files:
        for source, item in sorted(historic.items()):
            if item.get("status") != 301:
                continue
            target = item.get("to")
            if not isinstance(target, str) or not target.startswith("/"):
                errors.append(f"Alias {source}: cible interne attendue.")
                continue
            if ":splat" in target:
                continue  # Alias historique à capture générique.
            if ":" in target or "?" in target or "#" in target:
                errors.append(f"Alias {source}: destination inattendue.")
                continue
            path = PurePosixPath(target)
            if ".." in path.parts:
                errors.append(f"Alias {source}: traversal interdit.")
                continue
            rel = Path(target.lstrip("/"))
            if target.endswith("/"):
                rel /= "index.html"
            full = ROOT / rel
            if not full.is_file():
                errors.append(f"Alias {source}: destination non existante: {target}")
            elif not relative_path_allowed(rel):
                errors.append(f"Alias {source}: destination exclue du build: {target}")
    return errors


def self_test() -> list[str]:
    errors: list[str] = []
    main = {"build": {"publish": "."}, "redirects": [
        {"from": "/vieux", "to": "/page.html", "status": 301}
    ]}
    release = {"build": {"publish": "_site",
                         "command": "python3 scripts/build_netlify_public.py"},
               "redirects": [
                   *({"from": path, "to": "/404.html", "status": 404, "force": True}
                     for path in TECHNICAL_DENIALS),
                   {"from": "/vieux", "to": "/page.html", "status": 301},
               ]}
    if validate(main, release, check_files=False):
        errors.append("Auto-test positif de réconciliation Netlify échoué.")
    broken = {"build": {"publish": "."}, "redirects": release["redirects"]}
    if not any("artefact isolé" in x for x in validate(main, broken, check_files=False)):
        errors.append("Le test n'a pas refusé publish='.'.")
    changed = {"build": release["build"],
               "redirects": [*release["redirects"][:-1],
                             {"from": "/vieux", "to": "/autre.html", "status": 301}]}
    if not any("historique modifié" in x for x in validate(main, changed, check_files=False)):
        errors.append("Le test n'a pas refusé la perte d'un alias historique.")
    lost_deny = {"build": release["build"],
                 "redirects": release["redirects"][1:]}
    if not any("Refus technique" in x for x in validate(main, lost_deny, check_files=False)):
        errors.append("Le test n'a pas refusé la disparition d'un 404 technique.")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        problems = self_test()
    else:
        try:
            main = load_main_config()
            release = tomllib.loads(RELEASE_CONFIG.read_text(encoding="utf-8"))
        except (RuntimeError, ValueError, OSError) as exc:
            raise SystemExit(f"NO_GO : configuration Netlify non vérifiable: {exc}")
        problems = validate(main, release)
    for problem in problems:
        print("ECHEC:", problem)
    if problems:
        raise SystemExit(1)
    print("OK : alias historiques de main préservés, 12 refus techniques prioritaires, "
          "cibles publiques vérifiées et publication isolée _site.")
