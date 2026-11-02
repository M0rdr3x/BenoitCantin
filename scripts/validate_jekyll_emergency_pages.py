#!/usr/bin/env python3
"""Fail-closed smoke of the emergency GitHub Pages Jekyll output.

This does not replace the isolated _site builder or a controlled Pages source
migration. GitHub Actions runs Jekyll in a sandbox on a PR, then audits the
actual resulting directory with NO deployment, credentials, or remote scans.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]

BLOCKED = (
    "supabase/config.toml",
    "tests/e2e/test_public_site.py",
    "mobile-native/App.tsx",
    "scripts/build_netlify_public.py",
    "docs/README.md",
    ".github/workflows/validate-site.yml",
    "netlify.toml",
    "vercel.json",
    "package.json",
    "_config.yml",
    "projets/projet-nova/official/versions/V322/V322_CURRENT_STATE.json",
    "projets/projet-nova/official/versions/V316/README.md",
    "projets/projet-nova/data/modele_comptabilite.csv",
    "projets/projet-nova/CNAME_APRES_NAMECHEAP.txt",
    "assets/icons/README.md",
    "projets/sinjira/codex/livre-i-delivery-contract.json",
    "projets/sinjira/romans/livre-1-release.json",
)
REQUIRED = (
    "index.html",
    "404.html",
    "CNAME",
    "robots.txt",
    "sitemap.xml",
    ".well-known/security.txt",
    "projets/projet-nova/index.html",
    "projets/projet-nova/script.js",
    "projets/projet-nova/data/boussole-partis-2026.json",
    "projets/sinjira/romans/index.html",
    "projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf",
    "assets/js/site.js",
    "compte/index.html",
    "admin/index.html",
)
BLOCKED_EXTS = {
    ".py", ".pyc", ".ts", ".tsx", ".sql", ".toml", ".yaml", ".yml",
    ".pem", ".key", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db",
    ".log", ".bak", ".backup", ".map", ".lock", ".csv", ".zip",
    ".7z", ".rar", ".tar", ".gz",
}
BLOCKED_DIRS = (
    "supabase/", "tests/", "mobile-native/", "scripts/", "docs/",
    ".github/", ".git/", "projets/projet-nova/official/versions/",
    "projets/sinjira/codex/",
)

def validate(root: Path, require_all: bool = True) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return ["Artefact Jekyll de vérification absent"]
    for name in BLOCKED:
        if (root / name).exists():
            errors.append("Fichier privé ou technique publié : " + name)
    for name in REQUIRED:
        if require_all and not (root / name).is_file():
            errors.append("Page/fichier public manquant : " + name)
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        rel = candidate.relative_to(root).as_posix()
        if candidate.is_symlink():
            errors.append("Lien symbolique publié : " + rel)
        if candidate.suffix.lower() in BLOCKED_EXTS:
            errors.append("Extension technique publiée : " + rel)
        if any(rel.startswith(prefix) for prefix in BLOCKED_DIRS):
            errors.append("Répertoire technique publié : " + rel)
        if rel.endswith("/README.md"):
            errors.append("README technique publié : " + rel)
    return sorted(set(errors))

def validate_source() -> list[str]:
    errors = []
    if (ROOT / ".nojekyll").exists():
        errors.append(".nojekyll désactive totalement les exclusions Jekyll")
    config = ROOT / "_config.yml"
    if not config.is_file():
        errors.append("_config.yml absent")
        return errors
    source = config.read_text("utf-8")
    for key in (
        "exclude:", "include:", "- \"supabase\"", "- \"scripts\"",
        "- \"tests\"", "- \"mobile-native\"", "- \"docs\"",
        "- \"projets/projet-nova/official/versions\"",
        "- \"**/*.csv\"", "- \"**/*.ts\"", "- \"**/*.tsx\"",
        "- \"**/*.py\"", "- \"**/*.toml\"",
        "- \".well-known/security.txt\"",
    ):
        if key not in source:
            errors.append("Protection de configuration manquante : " + key)
    if re.search(r"(?m)^\s*(?:source|destination):", source):
        errors.append("Redirection de source/destination Jekyll interdite")
    return errors

def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="sinjira-jekyll-boundary-") as folder:
        root = Path(folder)
        for item in BLOCKED:
            if item.startswith(".git/"):
                continue
            path = root / item
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic", "utf-8")
            errors = validate(root, require_all=False)
            assert any(item in x for x in errors), ("Exposition non détectée", item)
            path.unlink()
        safe = root / "index.html"
        safe.write_text("<!doctype html><title>Site test</title>", "utf-8")
        assert validate(root, require_all=False) == [], "Page de test légitime refusée"
    assert not validate_source(), "Configuration Jekyll incompatible"
    print("PASS: fixtures fail-closed des fichiers techniques et config Jekyll.")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "_jekyll_emergency_site")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate_source() + validate(args.output.resolve())
    if errors:
        for error in errors:
            print("FAIL:", error)
        print(f"ECHEC: {len(errors)} écart(s) détecté(s).")
        return 1
    count = sum(1 for file in args.output.rglob("*") if file.is_file())
    print(f"PASS: Jekyll urgence : {count} fichiers contrôlés, aucun artefact technique énuméré.")
    print("ATTENTION: l'artefact Jekyll est un confinement temporaire; préférer _site + Pages Actions.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
