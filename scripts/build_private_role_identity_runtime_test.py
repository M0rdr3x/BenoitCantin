#!/usr/bin/env python3
"""Assemblage d'un test pgTAP strictement local depuis le candidat SQL #843.

Ne modifie aucune BD : retire le ROLLBACK final en mémoire uniquement, ajoute
des assertions fictives, puis rétablit un ROLLBACK unique pour pg_prove local.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

from validate_private_role_identity_candidate import CANDIDATE, inspect_sql

ROOT = Path(__file__).resolve().parents[1]
ASSERTIONS = ROOT / "security/candidates/private_role_identity_runtime_assertions.sql"
OUTPUT = ROOT / "supabase/tests/__sinjira_private_role_identity_generated.test.sql"


def render() -> str:
    source = CANDIDATE.read_text(encoding="utf-8", errors="strict")
    errors = inspect_sql(source)
    if errors:
        raise ValueError("Candidat SQL invalide : " + "; ".join(errors))
    if not re.search(r"(?i)\bROLLBACK\s*;\s*$", source):
        raise ValueError("Candidat non rollback-only")
    checks = ASSERTIONS.read_text(encoding="utf-8", errors="strict").strip()
    if not re.search(r"(?m)^SELECT plan\(28\);$", checks):
        raise ValueError("Plan pgTAP local incohérent")
    if len(re.findall(r"(?m)^SELECT (?:ok|is)\(", checks)) != 28:
        raise ValueError("Couverture de 28 assertions modifiée")
    if re.search(r"(?im)^\s*(?:BEGIN|COMMIT|ROLLBACK)\s*;", checks):
        raise ValueError("Transaction interdite dans les assertions")
    if not checks.endswith("SELECT * FROM finish();"):
        raise ValueError("finish() absent des assertions pgTAP")
    candidate_prefix = re.sub(r"(?i)\bROLLBACK\s*;\s*$", "", source).rstrip()
    return candidate_prefix + "\n\nSET LOCAL application_name = 'sinjira-local-rls-pgtap';\n" + checks + "\n\nROLLBACK;\n"


def self_test() -> None:
    sql = render()
    assert sql.count("\nROLLBACK;") == 1
    assert sql.endswith("ROLLBACK;\n")
    assert "CREATE OR REPLACE FUNCTION private.is_sinjira_admin" in sql
    assert "CREATE OR REPLACE FUNCTION private.project_access_rank" in sql
    assert "INSERT INTO auth.users" in sql
    assert "SET LOCAL ROLE" in sql
    assert "SELECT plan(28);" in sql
    assert "SET LOCAL application_name = 'sinjira-local-rls-pgtap'" in sql
    assert "SINJIRA_PGTAP_LOCAL_ASSEMBLY_REQUIRED" in sql
    print("OK : 28 assertions préparées dans une transaction rollback-only.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    output = args.output.resolve()
    if output != OUTPUT.resolve() or output.is_symlink():
        raise SystemExit("Refus de sortie hors de la fixture locale approuvée")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(), encoding="utf-8")
    print("OK : fixture SQL produite pour le conteneur Supabase local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
