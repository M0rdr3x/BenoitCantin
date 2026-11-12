#!/usr/bin/env python3
"""Interdire un SDK Supabase de version flottante dans les pages exécutables.

L'intégrité totale demande un bundle audité et distribué localement : un
numéro npm exact bloque seulement les mises à niveau majeures/mineures
silencieuses, pas une compromission du CDN.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK_VERSION = "2.119.0"
SDK_URL = f"https://cdn.jsdelivr.net/npm/@supabase/supabase-js@{SDK_VERSION}/+esm"
CLIENT_FILE = ROOT / "assets/js/sinjira-supabase.js"
SCOPES = ("assets/js", "compte", "projets/sinjira")
SUFFIXES = frozenset((".js", ".mjs", ".html", ".htm"))
MAX_SOURCE_BYTES = 2 * 1024 * 1024

SDK_CDN = re.compile(
    r"""https?://(?:cdn\.jsdelivr\.net/npm/|esm\.sh/|unpkg\.com/)
        (?:@supabase/supabase-js|%40supabase%2Fsupabase-js)
        [^\s'"<>\x60)]*""",
    re.I | re.X,
)


def scan_module(rel: str, source: str) -> list[str]:
    errors: list[str] = []
    for found in SDK_CDN.finditer(source):
        url = found.group(0)
        if url != SDK_URL:
            # Ne pas imprimer l'URL : une future chaîne source peut contenir
            # une query-string avec des informations non nécessaires aux logs.
            errors.append(f"{rel}: SDK Supabase non épinglé à {SDK_VERSION}")
    return errors


def source_files() -> list[Path]:
    selected: set[Path] = set()
    for scope in SCOPES:
        root = ROOT / scope
        if not root.is_dir():
            raise RuntimeError(f"Répertoire de code public absent: {scope}")
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUFFIXES:
                selected.add(path)
    return sorted(selected)


def inspect_repo() -> list[str]:
    errors: list[str] = []
    if not CLIENT_FILE.is_file():
        return ["Module partagé d'authentification SINJIRA absent"]
    client = CLIENT_FILE.read_text(encoding="utf-8")
    expected = f"import {{ createClient }} from '{SDK_URL}';"
    if client.count(expected) != 1:
        errors.append("Import Supabase de session absent ou modifié, version immuable requise")
    if "SINJIRA_CONFIG.supabasePublishableKey" not in client:
        errors.append("Le client doit rester sur la clé publique prévue, sans clé privilégiée")

    checked = 0
    for path in source_files():
        rel = path.relative_to(ROOT).as_posix()
        if path.stat().st_size > MAX_SOURCE_BYTES:
            errors.append(f"{rel}: source executable trop volumineuse pour le contrôle")
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="strict")
        except UnicodeError:
            errors.append(f"{rel}: UTF-8 illisible")
            continue
        errors.extend(scan_module(rel, source))
        checked += 1
    if not checked:
        errors.append("Aucun module public analysé")
    return errors


def self_test() -> None:
    good = f"import {{ createClient }} from '{SDK_URL}';"
    assert scan_module("test", good) == []
    assert scan_module("test", "import './other.js'") == []
    for url in (
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm",
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@latest/+esm",
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@^2/+esm",
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@~2.119/+esm",
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm",
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119/+esm",
        "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.118.0/+esm",
        "https://esm.sh/@supabase/supabase-js@2",
        "https://unpkg.com/@supabase/supabase-js@2",
        "http://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.0/+esm",
        SDK_URL + "?module",
    ):
        assert scan_module("test", "import '" + url + "'"), f"URL non verrouillée: {url}"
    assert not scan_module("test", "https://cdn.jsdelivr.net/npm/another-package@1.2.3/+esm")
    print("OK supply chain navigateur : 11 dérives/version flottante rejetées, URL npm immuable reconnue.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = inspect_repo()
    for error in errors:
        print("ECHEC : " + error)
    if errors:
        return 1
    print("OK : tous les imports SDK Supabase des modules/pages publics scannés sont épinglés à 2.119.0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
