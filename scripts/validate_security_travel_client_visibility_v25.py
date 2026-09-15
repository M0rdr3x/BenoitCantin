#!/usr/bin/env python3
"""Fail-closed guard for SINJIRA V25 Mode Voyage client visibility convergence."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = Path("supabase/migrations/20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql")
SQL_TEST = Path("supabase/tests/security_travel_client_visibility_v25.test.sql")
WORKFLOW = Path(".github/workflows/sinjira-security-travel-client-visibility-v25.yml")
LEDGER = Path("supabase/production-migration-ledger.txt")
MIGRATION_ID = "20260914223000 sinjira_v25_travel_mode_client_visibility_boundary"
EXPECTED_BLOB_SHA = "b08af7275d0d89b122505da413458fa9a24d2603"


def squash(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def git_blob_sha(text: str) -> str:
    data = text.encode("utf-8")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def policy_expression(migration: str) -> str:
    match = re.search(
        r"create\s+policy\s+security_travel_plans_read_own[\s\S]*?using\s*\(([\s\S]*?)\)\s*;",
        migration,
        flags=re.IGNORECASE,
    )
    return squash(match.group(1)) if match else ""


def extract_function(source: str, signature_start: str) -> str:
    start = source.lower().find(signature_start.lower())
    if start < 0:
        return ""
    next_start = source.lower().find("create or replace function ", start + len(signature_start))
    return source[start:] if next_start < 0 else source[start:next_start]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate(migration: str, test_sql: str, workflow: str, ledger: str) -> list[str]:
    errors: list[str] = []
    mig = squash(migration)
    test = squash(test_sql)
    flow = squash(workflow)
    policy = policy_expression(migration)
    create_fn = squash(extract_function(migration, "create or replace function public.security_create_travel_plan("))
    cancel_fn = squash(extract_function(migration, "create or replace function public.security_cancel_travel_plan("))

    require(errors, git_blob_sha(migration) == EXPECTED_BLOB_SHA,
            "migration visibility: empreinte A1 inattendue")
    require(errors, "alter table public.security_travel_plans enable row level security;" in mig,
            "RLS doit rester activée")
    require(errors, "revoke all on table public.security_travel_plans from public, anon, authenticated;" in mig,
            "la table doit rester deny-by-default")
    require(errors, "grant select on table public.security_travel_plans to authenticated;" in mig,
            "authenticated doit recevoir SELECT uniquement")
    require(errors,
            all(f"grant {verb} on table public.security_travel_plans to authenticated" not in mig for verb in ("insert", "update", "delete")),
            "aucune écriture directe authenticated n'est permise")
    require(errors, "grant select on table public.security_travel_plans to anon" not in mig,
            "anon ne doit jamais lire les voyages")
    require(errors, bool(policy), "politique SELECT Mode Voyage absente")
    require(errors, "(select auth.uid()) = user_id" in policy,
            "la politique doit rester self-only")
    require(errors, "status = 'active'" in policy,
            "les voyages annulés doivent être invisibles")
    require(errors, "ends_at >= statement_timestamp()" in policy,
            "les voyages expirés doivent être invisibles selon l'heure serveur")
    require(errors, "delete_after" not in policy,
            "la rétention ne doit jamais autoriser une lecture client")

    require(errors, bool(create_fn), "wrapper public de création absent")
    require(errors, "security invoker" in create_fn and "set search_path = ''" in create_fn,
            "le wrapper de création doit rester SECURITY INVOKER")
    require(errors, "sinjira_security_internal.security_create_travel_plan($1,$2,$3,$4)" in create_fn,
            "la création doit déléguer à l'implémentation interne")
    for key in ("id", "status", "starts_at", "ends_at", "destinations"):
        require(errors, f"'{key}', result->'{key}'" in create_fn,
                f"réponse création: clé requise absente: {key}")
    for key in ("delete_after", "user_id", "created_at", "updated_at", "cancelled_at", "multi_country"):
        require(errors, f"result->'{key}'" not in create_fn,
                f"réponse création: métadonnée interne exposée: {key}")

    require(errors, bool(cancel_fn), "wrapper public d'annulation absent")
    require(errors, "security invoker" in cancel_fn and "set search_path = ''" in cancel_fn,
            "le wrapper d'annulation doit rester SECURITY INVOKER")
    require(errors, "sinjira_security_internal.security_cancel_travel_plan($1)" in cancel_fn,
            "l'annulation doit déléguer à l'implémentation interne")
    require(errors, "'id', result->'id'" in cancel_fn and "'status', result->'status'" in cancel_fn,
            "l'annulation doit retourner uniquement un accusé explicite")
    for key in ("delete_after", "user_id", "created_at", "updated_at", "cancelled_at", "destinations", "starts_at", "ends_at"):
        require(errors, f"result->'{key}'" not in cancel_fn,
                f"réponse annulation: métadonnée interne exposée: {key}")

    required_test_markers = (
        "select plan(22)", "relrowsecurity", "security_travel_plans_read_own", "auth.uid()",
        "status", "active", "ends_at", "statement_timestamp()", "delete_after", "service_role",
        "security_create_travel_plan(timestamptz,timestamptz,text[],boolean)",
        "security_cancel_travel_plan(uuid)", "jsonb_build_object", "select * from finish()", "rollback;",
    )
    for marker in required_test_markers:
        require(errors, marker in test, f"contrat pgTAP visibilité incomplet: {marker}")

    for path in (str(MIGRATION), str(SQL_TEST), str(LEDGER), "scripts/validate_security_travel_client_visibility_v25.py", str(WORKFLOW)):
        require(errors, flow.count(path.lower()) == 2,
                f"workflow: chemin critique non surveillé sur PR + push: {path}")
    require(errors, "permissions: contents: read" in flow,
            "workflow: permissions lecture seule requises")
    require(errors, "production-reviewed-migration-batch.txt" not in flow,
            "workflow: le lot production reviewed doit rester hors convergence")
    require(errors, "python3 scripts/validate_security_travel_client_visibility_v25.py --self-test" in flow,
            "workflow: auto-test du garde absent")
    require(errors, "python3 scripts/validate_security_travel_client_visibility_v25.py" in flow,
            "workflow: validation du garde absente")
    require(errors, "supabase test db supabase/tests/security_travel_client_visibility_v25.test.sql --local" in flow,
            "workflow: pgTAP local de visibilité absent")
    require(errors, "supabase db push" not in flow and "supabase functions deploy" not in flow,
            "workflow: tout déploiement Supabase est interdit")

    require(errors, not re.search(r"^20260914223000\s+", ledger, flags=re.MULTILINE),
            "ledger production: la migration de visibilité ne doit pas être marquée déployée")
    return errors


def load(path: Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"self-test setup failed for {label}: expected one exact match")
    return source.replace(old, new, 1)


def replace_one_of_two(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 2:
        raise ValueError(f"self-test setup failed for {label}: expected two exact matches")
    return source.replace(old, new, 1)


def self_test(migration: str, test_sql: str, workflow: str, ledger: str) -> list[str]:
    try:
        mutations = [
            ("RLS disabled", replace_once(migration,
                "alter table public.security_travel_plans enable row level security;",
                "alter table public.security_travel_plans disable row level security;", "RLS"), test_sql, workflow, ledger),
            ("owner boundary removed", replace_once(migration,
                "(select auth.uid()) = user_id", "true", "owner boundary"), test_sql, workflow, ledger),
            ("cancelled rows exposed", replace_once(migration,
                "and status = 'active'", "", "status filter"), test_sql, workflow, ledger),
            ("expired retained rows exposed", replace_once(migration,
                "and ends_at >= statement_timestamp()", "and delete_after >= statement_timestamp()", "expiry filter"), test_sql, workflow, ledger),
            ("anonymous read granted", migration + "\ngrant select on table public.security_travel_plans to anon;\n", test_sql, workflow, ledger),
            ("direct update granted", migration + "\ngrant update on table public.security_travel_plans to authenticated;\n", test_sql, workflow, ledger),
            ("creation leaks retention", replace_once(migration,
                "    'destinations', result->'destinations'\n",
                "    'destinations', result->'destinations',\n    'delete_after', result->'delete_after'\n", "retention leak"), test_sql, workflow, ledger),
            ("SQL contract weakened", migration, replace_once(test_sql,
                "statement_timestamp()", "clock_timestamp()", "SQL clock"), workflow, ledger),
            ("migration fingerprint changed", migration + "\n-- mutation non revue\n", test_sql, workflow, ledger),
            ("migration path unwatched", migration, test_sql, replace_one_of_two(workflow,
                "      - 'supabase/migrations/20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql'",
                "      - 'supabase/migrations/UNWATCHED.sql'", "workflow migration watch"), ledger),
            ("validator self-test skipped", migration, test_sql, replace_once(workflow,
                "python3 scripts/validate_security_travel_client_visibility_v25.py --self-test",
                "python3 scripts/validate_security_travel_client_visibility_v25.py --help", "workflow self-test"), ledger),
            ("false production deployment", migration, test_sql, workflow,
                ledger + "\n20260914223000 sinjira_v25_travel_mode_client_visibility_boundary\n"),
        ]
    except ValueError as exc:
        return [str(exc)]

    failures: list[str] = []
    for name, mut_migration, mut_test, mut_workflow, mut_ledger in mutations:
        if not validate(mut_migration, mut_test, mut_workflow, mut_ledger):
            failures.append(f"mutation escaped validator: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    values = (load(MIGRATION), load(SQL_TEST), load(WORKFLOW), load(LEDGER))
    errors = self_test(*values) if args.self_test else validate(*values)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Mode Voyage client visibility: A1 fail-closed, empreinte verrouillée, production intacte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
