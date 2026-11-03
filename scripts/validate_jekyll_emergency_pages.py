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
    "projets/projet-nova/data/diagnostic-g0-sante-premiere-ligne-2025.json",
    "projets/projet-nova/data/registre-donnees-services-nova-sinjira.json",
    "projets/projet-nova/data/reperes-financiers-nova-sinjira-2026.json",
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
    "projets/sinjira/codex/index.html",
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
)
# Le Codex public possède une seule page HTML approuvée. Un futur export,
# fichier d'inventaire ou aperçu HTML ne doit jamais sortir par défaut.
CODEX_PUBLIC_PAGE = "projets/sinjira/codex/index.html"
CODEX_PREFIX = "projets/sinjira/codex/"

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
        rel = candidate.relative_to(root).as_posix()
        # Vérifier AVANT is_file() : is_file() suit la cible et ignore les
        # liens vers des dossiers ainsi que les liens cassés. Un lien vers
        # un répertoire interne ne doit jamais contourner le confinement.
        if candidate.is_symlink():
            errors.append("Lien symbolique publié : " + rel)
            continue
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() in BLOCKED_EXTS:
            errors.append("Extension technique publiée : " + rel)
        if any(rel.startswith(prefix) for prefix in BLOCKED_DIRS) or (
            rel.startswith(CODEX_PREFIX) and rel != CODEX_PUBLIC_PAGE
        ):
            errors.append("Répertoire technique publié : " + rel)
        if rel.endswith("/README.md"):
            errors.append("README technique publié : " + rel)
    return sorted(set(errors))

def unexpected_against_approved(jekyll: Path, approved: Path) -> list[str]:
    """Any file absent from the reviewed isolated artifact is an exposure.

    Jekyll may render additional Markdown or forgotten JSON/metadata that
    our suffix checks miss. Reject these too (closed file-set comparison).
    """
    if not approved.is_dir() or not jekyll.is_dir():
        return ["Artefact de référence ou sortie Jekyll absent"]
    approved_files = {
        path.relative_to(approved).as_posix()
        for path in approved.rglob("*") if path.is_file()
    }
    observed_files = {
        path.relative_to(jekyll).as_posix()
        for path in jekyll.rglob("*") if path.is_file()
    }
    unexpected = sorted(observed_files - approved_files)
    missing = sorted(approved_files - observed_files)
    if missing:
        # Une absence n'est pas une fuite, mais peut rompre des liens publics.
        # Examiner la liste avant fusion; aucun contenu n'est imprimé.
        print(f"INFO: {len(missing)} fichier(s) publics approuvés absents de Jekyll :")
        for path in missing:
            print("INFO: - " + path)
    # Filenames only. Never print file content or credentials.
    return [f"Fichier hors allowlist isolée: {path}" for path in unexpected]


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
        '- "projets/projet-nova/data/diagnostic-g0-sante-premiere-ligne-2025.json"',
        '- "projets/projet-nova/data/registre-donnees-services-nova-sinjira.json"',
        '- "projets/projet-nova/data/reperes-financiers-nova-sinjira-2026.json"',
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

        # La page publique du Codex doit rester accessible, mais pas une
        # future fiche HTML confidentielle placée dans son répertoire.
        codex = root / "projets/sinjira/codex"
        codex.mkdir(parents=True, exist_ok=True)
        public_codex = codex / "index.html"
        public_codex.write_text("<!doctype html><title>Codex</title>", "utf-8")
        assert validate(root, require_all=False) == [], "Page Codex approuvée refusée"
        for filename in ("private-preview.html", "draft-data.json", "notes.txt"):
            unknown = codex / filename
            unknown.write_text("synthetic", "utf-8")
            violations = validate(root, require_all=False)
            assert any("Répertoire technique publié : projets/sinjira/codex/" +
                       filename in error for error in violations), (
                           "Export Codex non approuvé", filename)
            unknown.unlink()

        # Une redirection de dossier, même cassée, n'est pas un fichier au
        # sens de Path.is_file(). Le contrôle ne doit pas l'ignorer.
        nested = root / "private-temp"
        nested.mkdir()
        (nested / "secret.txt").write_text("synthetic", "utf-8")
        for name, target in (
            ("dossier-lie", nested),
            ("dossier-casse", root / "missing-private-folder"),
            ("fichier-lie", safe),
        ):
            link = root / name
            link.symlink_to(target, target_is_directory=name != "fichier-lie")
            violations = validate(root, require_all=False)
            assert any("Lien symbolique publié : " + name in error
                       for error in violations), ("Lien non détecté", name)
            link.unlink()

        # L'allowlist de chemins doit aussi refuser un nouveau fichier
        # apparemment public (.html/.js) dont le nom n'a pas été approuvé.
        approved = root / "approved-artifact"
        observed = root / "observed-artifact"
        approved.mkdir()
        observed.mkdir()
        (approved / "index.html").write_text("synthetic", "utf-8")
        (observed / "index.html").write_text("synthetic", "utf-8")
        assert unexpected_against_approved(observed, approved) == []
        for suffix in (".html", ".js", ".json"):
            candidate = observed / ("unreviewed" + suffix)
            candidate.write_text("synthetic", "utf-8")
            violations = unexpected_against_approved(observed, approved)
            assert any("Fichier hors allowlist isolée: " + candidate.name in error
                       for error in violations), ("Fichier hors allowlist non détecté", suffix)
            candidate.unlink()
    assert not validate_source(), "Configuration Jekyll incompatible"
    print("PASS: fixtures fail-closed des fichiers techniques et config Jekyll.")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "_jekyll_emergency_site")
    parser.add_argument("--approved", type=Path, help="Répertoire _site isolé approuvé")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate_source() + validate(args.output.resolve())
    if args.approved:
        errors.extend(unexpected_against_approved(args.output.resolve(), args.approved.resolve()))
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
