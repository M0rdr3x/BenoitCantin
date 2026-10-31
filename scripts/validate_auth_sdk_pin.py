#!/usr/bin/env python3
"""Contrat de provenance du SDK d'authentification exécuté dans le navigateur.

Ne constitue ni une preuve d'intégrité du CDN, ni un test de session production.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK_FILE = Path("assets/js/sinjira-supabase.js")
LOCKED_VERSION = "2.118.0"
LOCKED_URL = f"https://cdn.jsdelivr.net/npm/@supabase/supabase-js@{LOCKED_VERSION}/+esm"
SDK_TOKEN = "@supabase/supabase-js"
EXACT_IMPORT = f"import {{ createClient }} from '{LOCKED_URL}';"

# Les pages et scripts réellement servis au navigateur : pas les docs, outils ou tests.
BROWSER_ROOTS = ("assets/js", "app", "compte", "admin", "Admin", "projets")
BROWSER_SUFFIXES = frozenset({".js", ".mjs", ".html"})


def validate_module(text: str) -> list[str]:
    errors: list[str] = []
    lines = text.splitlines()
    if lines.count(EXACT_IMPORT) != 1:
        errors.append("Import Supabase non épinglé sur la version stable exacte approuvée.")
    if text.count(SDK_TOKEN) != 1:
        errors.append("Une seule référence statique au package Supabase est permise.")
    if re.search(r"(?m)^\s*(?:export\s+)?(?:import|require)\b", text):
        # Le module conserve exactement son import de createClient et son import local.
        imports = [line for line in lines if re.match(r"^\s*import\s", line)]
        if not imports or imports[0] != EXACT_IMPORT:
            errors.append("La première dépendance doit être l'import Supabase verrouillé.")
    if "createClient(SINJIRA_CONFIG.supabaseUrl, SINJIRA_CONFIG.supabasePublishableKey" not in text:
        errors.append("Le client ne prend plus sa clé publiable dans la configuration.")
    if re.search(r"(?i)(?:service_role|sb_secret_)\s*[:=]", text):
        errors.append("Indicateur de clé privilégiée dans le module de session.")
    return errors


def discover_browser_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for dirname in BROWSER_ROOTS:
        folder = root / dirname
        if folder.is_dir():
            result.extend(p for p in folder.rglob("*") if p.is_file() and p.suffix in BROWSER_SUFFIXES)
    return result


def validate_browser_sources(root: Path) -> list[str]:
    errors = []
    for p in discover_browser_files(root):
        rel = p.relative_to(root)
        data = p.read_text("utf-8", errors="replace")
        if rel == SDK_FILE:
            errors.extend(f"{rel}: {err}" for err in validate_module(data))
            continue
        if SDK_TOKEN in data:
            errors.append(f"{rel}: import Supabase secondaire non revu ou version flottante.")
    if not (root / SDK_FILE).is_file():
        errors.append(f"Module client absent : {SDK_FILE}")
    return errors


def self_test() -> None:
    nominal = "\n".join((
        EXACT_IMPORT,
        "import { SINJIRA_CONFIG } from './sinjira-supabase-config.js';",
        "createClient(SINJIRA_CONFIG.supabaseUrl, SINJIRA_CONFIG.supabasePublishableKey);",
    ))
    assert not validate_module(nominal), validate_module(nominal)
    unsafe = (
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm",
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@latest/+esm",
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@^2/+esm",
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.118/+esm",
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.0-canary.4/+esm",
        "https://unpkg.com/@supabase/supabase-js@2.118.0",
        "https://esm.sh/@supabase/supabase-js@2.118.0",
    )
    for url in unsafe:
        assert validate_module(nominal.replace(LOCKED_URL, url)), f"URL non épinglée acceptée : {url}"
    assert validate_module(nominal.replace(EXACT_IMPORT, "")), "Import supprimé accepté."
    assert validate_module(nominal + "\n" + EXACT_IMPORT), "Import dupliqué accepté."
    assert validate_module(nominal.replace("supabasePublishableKey", "supabaseSecretKey")), "Clé privée acceptée."
    print(f"PASS: 11 essais du verrou SDK et scénarios non conformes ({LOCKED_VERSION}).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate_browser_sources(ROOT)
    if errors:
        print(f"ECHEC: {len(errors)} divergence(s) de dépendance auth.")
        for error in errors:
            print("- " + error)
        return 1
    print(f"PASS: client Supabase {LOCKED_VERSION} épinglé; aucun second chargement CDN dans les pages/scripts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
