#!/usr/bin/env python3
"""Contrat fail-closed : pas d'EXECUTE public sur les triggers internes.

Valide les fichiers candidats uniquement : ne prétend pas prouver la production.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/candidate-migrations/20261031094000_sinjira_private_trigger_execute_acl_hardening.sql"
TAP = ROOT / "supabase/tests/private_trigger_execute_acl_hardening.test.sql"
FUNCTIONS = (
    "private.privacy_incident_retention_guard()",
    "private.safety_create_escalation_case()",
)
EXPECTED_TABLES = (
    "private.privacy_incident_register",
    "public.social_reports",
)


def uncommented(text: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in text.splitlines()).lower()


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", uncommented(text)).strip()


def inspect(migration: str, tap: str) -> list[str]:
    errors: list[str] = []
    clean = normalized(migration)
    test = normalized(tap)
    if not clean.startswith("begin;") or not clean.endswith("commit;"):
        errors.append("Migration non transactionnelle.")
    if re.search(r"\b(?:grant|create|drop|alter|truncate|delete|insert|update)\b", clean):
        errors.append("Migration élargie au-delà de REVOKE/DO de validation.")
    if re.search(r"\bcascade\b", clean):
        errors.append("CASCADE interdit.")
    if clean.count("revoke execute on function ") != len(FUNCTIONS):
        errors.append("Le nombre de restrictions EXECUTE doit rester exactement deux.")
    for name in FUNCTIONS:
        statement = f"revoke execute on function {name} from public, anon, authenticated;"
        if statement not in clean:
            errors.append(f"REVOKE complet absent : {name}")
        if clean.count(f"'{name}'::regprocedure") < 2:
            errors.append(f"Vérification de la définition/du déclencheur absente : {name}")
        if clean.count(f"has_function_privilege('anon','{name}','execute')") != 1:
            errors.append(f"Postcondition anon absente : {name}")
        if clean.count(f"has_function_privilege('authenticated','{name}','execute')") != 1:
            errors.append(f"Postcondition authenticated absente : {name}")
        for role in ("anon", "authenticated"):
            if f"not has_function_privilege('{role}','{name}','execute')" not in test:
                errors.append(f"Test pgtap manquant : {role}/{name}")
    for table in EXPECTED_TABLES:
        if f"'{table}'::regclass" not in clean or f"'{table}'::regclass" not in test:
            errors.append(f"Liaison à la table du trigger non prouvée : {table}")
    if clean.count("raise exception") < 5:
        errors.append("Préconditions ou postconditions SQL retirées.")
    if "select plan(8);" not in test or "select * from finish();" not in test:
        errors.append("Plan pgtap ou clôture absent.")
    if "rollback;" not in test:
        errors.append("Le test SQL doit rester sans effet permanent.")
    return errors


def self_test() -> None:
    good = MIGRATION.read_text("utf-8")
    tap = TAP.read_text("utf-8")
    assert not inspect(good, tap), inspect(good, tap)
    changes = {
        "missing_revoke": good.replace("revoke execute on function " + FUNCTIONS[0], "-- revoke execute on function " + FUNCTIONS[0]),
        "missing_anon": good.replace("from public, anon, authenticated;", "from public, authenticated;"),
        "missing_authenticated": good.replace("from public, anon, authenticated;", "from public, anon;"),
        "broken_trigger": good.replace("'public.social_reports'::regclass", "'public.profiles'::regclass"),
        "removed_postflight": good.replace("raise exception 'PRIVATE_TRIGGER_EXECUTE_ACL_STILL_EXPOSED';", "null;"),
        "nontransactional": good.replace("\ncommit;\n", ""),
        "dangerous_drop": good + "\ndrop table private.privacy_incident_register;",
        "forbidden_grant": good + "\ngrant execute on function private.safety_create_escalation_case() to anon;",
    }
    for name, mutated in changes.items():
        assert inspect(mutated, tap), f"Mutation dangereuse acceptée : {name}"
    broken_tap = tap.replace("not has_function_privilege('anon','private.safety_create_escalation_case()','EXECUTE')", "true")
    assert inspect(good, broken_tap), "Test négatif pgtap manquant accepté."
    print("PASS: contrat minimal + 9 mutations dangereuses rejetées.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = inspect(MIGRATION.read_text("utf-8"), TAP.read_text("utf-8"))
    if errors:
        for error in errors:
            print("- " + error)
        return 1
    print("PASS: ACL exactes, préconditions triggers, postconditions et pgtap présents.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
