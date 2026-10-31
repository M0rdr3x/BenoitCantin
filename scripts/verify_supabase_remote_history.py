#!/usr/bin/env python3
"""Comparaison fail-closed de Supabase CLI 'migration list --linked' et du ledger.

Ne consulte aucun secret ni réseau. L'entrée est une sortie CLI déjà obtenue
dans le workspace authentifié et toutes les opérations sont en lecture seule.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "supabase/production-migration-ledger.txt"
VERSION = re.compile(r"^[0-9]{14}$")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def ledger_versions(content: str) -> list[str]:
    versions = []
    for item in content.splitlines():
        line = item.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2 or not VERSION.fullmatch(parts[0]):
            raise ValueError("Registre local mal formé")
        versions.append(parts[0])
    if not versions or versions != sorted(set(versions)):
        raise ValueError("Registre local vide, désordonné ou en doublon")
    return versions


def remote_versions(cli_output: str) -> list[str]:
    versions = []
    for raw in cli_output.splitlines():
        line = ANSI.sub("", raw)
        if "|" not in line:
            continue
        columns = [c.strip() for c in line.split("|")]
        if len(columns) < 3:
            raise ValueError("Colonnes migrations distantes incomplètes")
        remote = columns[1]
        if VERSION.fullmatch(remote):
            versions.append(remote)
        elif remote and remote.lower() != "remote" and not set(remote) <= {"-"}:
            raise ValueError("Version distante non reconnue dans le tableau CLI")
    if not versions or len(versions) != len(set(versions)) or versions != sorted(versions):
        raise ValueError("Tableau distant vide, avec doublon ou non trié")
    return versions


def discrepancies(expected: list[str], actual: list[str]) -> list[str]:
    errors = []
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing:
        errors.append("Versions enregistrées absentes de Supabase: " + ", ".join(missing))
    if extra:
        errors.append("Versions Supabase NON consignées dans le ledger: " + ", ".join(extra))
    if not (missing or extra) and expected != actual:
        errors.append("Ordre distant non conforme au registre")
    return errors


def self_test() -> None:
    fixture = (
        "    Local          | Remote         | Time (UTC)\n"
        "-------------------|----------------|------------------\n"
        "  20260901000000    | 20260901000000 | 2026-09-01\n"
        "                   | 20261001000000 | 2026-10-01\n"
    )
    expected = ["20260901000000", "20261001000000"]
    assert remote_versions(fixture) == expected
    assert ledger_versions("20260901000000 abc\n20261001000000 def\n") == expected
    assert discrepancies(expected, expected) == []
    assert "20261001000000" in str(discrepancies(expected[:-1], expected))
    assert "20261001000000" in str(discrepancies(expected, expected[:-1]))
    for altered in (
        fixture.replace("20261001000000 |", "20260901000000 |"),
        fixture.replace("20261001000000 |", "INVALID-REMOTE |"),
        "Local | Remote | Time (UTC)\n",
    ):
        try:
            remote_versions(altered)
        except ValueError:
            continue
        raise AssertionError("État Supabase divergent accepté")
    print("OK garde historique distant: dérive, doublon, version invalide et sortie vide rejetés")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--supabase-list", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if not args.supabase_list:
        if args.self_test:
            return 0
        parser.error("--supabase-list requis sans --self-test")
    try:
        expected = ledger_versions(LEDGER.read_text("utf-8"))
        actual = remote_versions(args.supabase_list.read_text("utf-8"))
        issues = discrepancies(expected, actual)
    except (OSError, UnicodeError, ValueError) as exc:
        print("BLOQUÉ: impossible de prouver la concordance des migrations:", exc)
        return 1
    if issues:
        print(f"BLOQUÉ: ledger local {len(expected)} migrations / Supabase {len(actual)} migrations.")
        for issue in issues:
            print("- " + issue)
        print("Réconcilier et revoir les migrations avant tout dry-run ou application.")
        return 1
    print(f"OK historique Supabase: {len(expected)} versions distantes exactement identiques au ledger.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
