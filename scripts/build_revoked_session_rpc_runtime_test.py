#!/usr/bin/env python3
"""Construit un test pgTAP *local* depuis le candidat P0 sans exécuter de SQL.

Le candidat doit rester ROLLBACK-only. Aucun accès distant ni secret.
Les données fictives et toutes les fonctions temporaires sont annulées.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

from validate_revoked_session_rpc_candidate import SQL, inspect

ROOT = Path(__file__).resolve().parents[1]
ASSERTIONS = ROOT / "security/candidates/sinjira_revoked_auth_session_runtime_assertions.sql"
DEFAULT_OUTPUT = ROOT / "supabase/tests/__sinjira_revoked_session_candidate_generated.test.sql"


def render() -> str:
    candidate = SQL.read_text(encoding="utf-8", errors="strict")
    problems = inspect(candidate)
    if problems:
        raise ValueError("Candidat de sessions non conforme : " + "; ".join(problems))
    if not re.search(r"(?i)\bROLLBACK\s*;\s*$", candidate):
        raise ValueError("Le candidat doit finir par ROLLBACK")
    prelude = re.sub(r"(?i)ROLLBACK\s*;\s*$", "", candidate).rstrip()
    checks = ASSERTIONS.read_text(encoding="utf-8", errors="strict").strip()
    if "BEGIN;" in checks.upper() or "COMMIT;" in checks.upper() or "ROLLBACK;" in checks.upper():
        raise ValueError("Assertions ne doivent contenir aucune transaction")
    if "SELECT * FROM finish()" not in checks:
        raise ValueError("Assertions pgTAP incomplètes")
    return prelude + "\n\n" + checks + "\n\nROLLBACK;\n"


def self_test() -> None:
    sql = render()
    assert sql.startswith("-- CANDIDAT STAGING")
    assert sql.count("\nROLLBACK;") == 1
    assert "CREATE OR REPLACE FUNCTION private.security_require_current_auth_session" in sql
    assert "INSERT INTO auth.users" in sql
    assert "SELECT * FROM finish()" in sql
    assert sql.endswith("\nROLLBACK;\n")
    print("OK : assemblage pgTAP transactionnel, aucun SQL exécuté.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    output = args.output.resolve()
    if output != DEFAULT_OUTPUT.resolve():
        raise SystemExit("Sortie temporaire non approuvée")
    if output.is_symlink():
        raise SystemExit("Refus de sortie via lien symbolique")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(), encoding="utf-8")
    print("OK : fixture pgTAP construite pour Supabase local; aucune base distante utilisée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
