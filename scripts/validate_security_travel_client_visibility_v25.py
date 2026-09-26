#!/usr/bin/env python3
"""Fail-closed guard for SINJIRA V25 Mode Voyage client visibility convergence."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = Path("supabase/migrations/20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql")
HARDENING_MIGRATION = Path("supabase/migrations/20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql")
SQL_TEST = Path("supabase/tests/security_travel_client_visibility_v25.test.sql")
WORKFLOW = Path(".github/workflows/sinjira-security-travel-client-visibility-v25.yml")
LEDGER = Path("supabase/production-migration-ledger.txt")
STAMP = "20260914223000"
HARDENING_STAMP = "20260921005000"
EXPECTED_BLOB_SHA = "2d7b8ccbfc79fed6a03208086a138618779d6e2d"


def squash(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def git_blob_sha(text: str) -> str:
    data = text.encode("utf-8")
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def function(source: str, marker: str) -> str:
    start = source.lower().find(marker.lower())
    if start < 0:
        return ""
    nxt = source.lower().find("create or replace function ", start + len(marker))
    return source[start:] if nxt < 0 else source[start:nxt]


def validate(
    migration: str,
    hardening: str,
    test_sql: str,
    workflow: str,
    ledger: str,
) -> list[str]:
    errors: list[str] = []
    mig = squash(migration)
    hard = squash(hardening)
    test = squash(test_sql)
    flow = workflow.lower()

    if git_blob_sha(migration) != EXPECTED_BLOB_SHA:
        errors.append("migration visibility: empreinte A1 inattendue")

    required_migration = (
        "alter table public.security_travel_plans enable row level security;",
        "revoke all on table public.security_travel_plans from public, anon, authenticated;",
        "grant select on table public.security_travel_plans to authenticated;",
        "create policy security_travel_plans_read_own",
        "to authenticated",
        "(select auth.uid()) = user_id",
        "status = 'active'",
        "ends_at >= statement_timestamp()",
    )
    for needle in required_migration:
        if needle not in mig:
            errors.append(f"migration visibilité: invariant absent: {needle}")

    policy = re.search(
        r"create\s+policy\s+security_travel_plans_read_own[\s\S]*?using\s*\(([\s\S]*?)\)\s*;",
        migration,
        flags=re.IGNORECASE,
    )
    policy_text = squash(policy.group(1)) if policy else ""
    if not policy_text:
        errors.append("politique SELECT Mode Voyage absente")
    elif "delete_after" in policy_text:
        errors.append("la rétention ne doit jamais autoriser une lecture client")

    for verb in ("insert", "update", "delete"):
        if f"grant {verb} on table public.security_travel_plans to authenticated" in mig:
            errors.append(f"écriture directe authenticated interdite: {verb}")
    if "grant select on table public.security_travel_plans to anon" in mig:
        errors.append("anon ne doit jamais lire les voyages")

    create_fn = squash(function(migration, "create or replace function public.security_create_travel_plan("))
    cancel_fn = squash(function(migration, "create or replace function public.security_cancel_travel_plan("))

    if "security invoker" not in create_fn or "set search_path = ''" not in create_fn:
        errors.append("wrapper création: SECURITY INVOKER/search_path requis")
    if "sinjira_security_internal.security_create_travel_plan($1,$2,$3,$4)" not in create_fn:
        errors.append("wrapper création: délégation interne absente")
    for key in ("id", "status", "starts_at", "ends_at", "destinations"):
        if f"'{key}', result->'{key}'" not in create_fn:
            errors.append(f"wrapper création: clé requise absente: {key}")
    for key in ("delete_after", "user_id", "created_at", "updated_at", "cancelled_at", "multi_country"):
        if f"result->'{key}'" in create_fn:
            errors.append(f"wrapper création: métadonnée interne exposée: {key}")

    if "security invoker" not in cancel_fn or "set search_path = ''" not in cancel_fn:
        errors.append("wrapper annulation: SECURITY INVOKER/search_path requis")
    if "sinjira_security_internal.security_cancel_travel_plan($1)" not in cancel_fn:
        errors.append("wrapper annulation: délégation interne absente")
    if "'id', result->'id'" not in cancel_fn or "'status', result->'status'" not in cancel_fn:
        errors.append("wrapper annulation: accusé minimal absent")
    for key in ("delete_after", "user_id", "created_at", "updated_at", "cancelled_at", "destinations", "starts_at", "ends_at"):
        if f"result->'{key}'" in cancel_fn:
            errors.append(f"wrapper annulation: métadonnée interne exposée: {key}")

    intro_internal_create = squash(function(
        migration,
        "create or replace function sinjira_security_internal.security_create_travel_plan(",
    ))
    intro_internal_cancel = squash(function(
        migration,
        "create or replace function sinjira_security_internal.security_cancel_travel_plan(",
    ))

    for label, block in (("création interne A3", intro_internal_create), ("annulation interne A3", intro_internal_cancel)):
        if not block:
            errors.append(f"{label}: définition absente dès 20260914223000")
            continue
        if "security definer" not in block:
            errors.append(f"{label}: SECURITY DEFINER requis")
        if "as $" not in block or "$;" not in block:
            errors.append(f"{label}: délimiteur PL/pgSQL $ invalide")
        if "return pg_catalog.jsonb_build_object(" not in block:
            errors.append(f"{label}: réponse minimale jsonb_build_object absente")
        if "return to_jsonb(v_row)" in block:
            errors.append(f"{label}: retour de ligne complète interdit")
        if "from public, anon" not in block or "to authenticated, service_role" not in block:
            errors.append(f"{label}: ACL directe interne inattendue")

    for key in ("id", "status", "starts_at", "ends_at"):
        if f"'{key}',v_row.{key}" not in intro_internal_create:
            errors.append(f"création interne A3: clé minimale absente: {key}")
    if "'destinations',to_jsonb(v_row.destinations)" not in intro_internal_create:
        errors.append("création interne A3: clé minimale absente: destinations")
    for key in ("user_id", "delete_after", "created_at", "updated_at", "cancelled_at", "multi_country"):
        if f"'{key}'," in intro_internal_create:
            errors.append(f"création interne A3: clé serveur exposée: {key}")

    if "'id',v_row.id" not in intro_internal_cancel or "'status',v_row.status" not in intro_internal_cancel:
        errors.append("annulation interne A3: accusé minimal id/status absent")
    for key in ("user_id", "delete_after", "created_at", "updated_at", "cancelled_at", "destinations", "starts_at", "ends_at"):
        if f"'{key}'," in intro_internal_cancel:
            errors.append(f"annulation interne A3: clé serveur exposée: {key}")

    internal_create = squash(function(
        hardening,
        "create or replace function sinjira_security_internal.security_create_travel_plan(",
    ))
    internal_cancel = squash(function(
        hardening,
        "create or replace function sinjira_security_internal.security_cancel_travel_plan(",
    ))

    for label, block in (("création interne", internal_create), ("annulation interne", internal_cancel)):
        if not block:
            errors.append(f"{label}: définition absente")
            continue
        if "security definer" not in block:
            errors.append(f"{label}: SECURITY DEFINER requis")
        if "return pg_catalog.jsonb_build_object(" not in block:
            errors.append(f"{label}: réponse minimale jsonb_build_object absente")
        if "return to_jsonb(v_row)" in block:
            errors.append(f"{label}: retour de ligne complète interdit")
        if "from public, anon" not in block or "to authenticated, service_role" not in block:
            errors.append(f"{label}: ACL directe interne inattendue")

    for key in ("id", "status", "starts_at", "ends_at"):
        if f"'{key}',v_row.{key}" not in internal_create:
            errors.append(f"création interne: clé minimale absente: {key}")
    if "'destinations',to_jsonb(v_row.destinations)" not in internal_create:
        errors.append("création interne: clé minimale absente: destinations")
    for key in ("user_id", "delete_after", "created_at", "updated_at", "cancelled_at", "multi_country"):
        if f"'{key}'," in internal_create:
            errors.append(f"création interne: clé serveur exposée: {key}")

    if "'id',v_row.id" not in internal_cancel or "'status',v_row.status" not in internal_cancel:
        errors.append("annulation interne: accusé minimal id/status absent")
    for key in ("user_id", "delete_after", "created_at", "updated_at", "cancelled_at", "destinations", "starts_at", "ends_at"):
        if f"'{key}'," in internal_cancel:
            errors.append(f"annulation interne: clé serveur exposée: {key}")

    for marker in (
        "select plan(28)",
        "relrowsecurity",
        "security_travel_plans_read_own",
        "auth.uid()",
        "status",
        "active",
        "ends_at",
        "statement_timestamp()",
        "delete_after",
        "service_role",
        "security_create_travel_plan(timestamptz,timestamptz,text[],boolean)",
        "security_cancel_travel_plan(uuid)",
        "sinjira_security_internal.security_create_travel_plan",
        "sinjira_security_internal.security_cancel_travel_plan",
        "return to_jsonb(v_row)",
        "jsonb_build_object",
        "select * from finish()",
        "rollback;",
    ):
        if marker not in test:
            errors.append(f"contrat pgTAP visibilité incomplet: {marker}")

    for watched in (
        MIGRATION,
        HARDENING_MIGRATION,
        SQL_TEST,
        LEDGER,
        Path("scripts/validate_security_travel_client_visibility_v25.py"),
        WORKFLOW,
    ):
        if flow.count(str(watched).lower()) < 2:
            errors.append(f"workflow: chemin critique non surveillé sur PR + push: {watched}")

    for command in (
        "python3 scripts/validate_security_travel_client_visibility_v25.py --self-test",
        "python3 scripts/validate_security_travel_client_visibility_v25.py",
        "supabase test db supabase/tests/security_travel_client_visibility_v25.test.sql --local",
    ):
        if command not in workflow:
            errors.append(f"workflow: commande absente: {command}")

    if "permissions:\n  contents: read" not in workflow:
        errors.append("workflow: permissions lecture seule requises")
    if "production-reviewed-migration-batch.txt" in flow:
        errors.append("workflow: le lot production reviewed doit rester hors convergence")
    if "supabase db push" in flow or "supabase functions deploy" in flow:
        errors.append("workflow: tout déploiement Supabase est interdit")

    if re.search(rf"^{STAMP}\s+", ledger, flags=re.MULTILINE):
        errors.append("ledger production: migration de visibilité marquée déployée")
    if re.search(rf"^{HARDENING_STAMP}\s+", ledger, flags=re.MULTILINE):
        errors.append("ledger production: minimisation interne Mode Voyage marquée déployée")

    return errors


def load(path: Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"mutation attendue une fois: {old}")
    return source.replace(old, new, 1)


def self_test(values: tuple[str, str, str, str, str]) -> list[str]:
    migration, hardening, test_sql, workflow, ledger = values
    try:
        cases = [
            (
                replace_once(
                    migration,
                    "alter table public.security_travel_plans enable row level security;",
                    "alter table public.security_travel_plans disable row level security;",
                ),
                hardening, test_sql, workflow, ledger,
            ),
            (
                replace_once(migration, "(select auth.uid()) = user_id", "true"),
                hardening, test_sql, workflow, ledger,
            ),
            (
                replace_once(
                    migration,
                    "    'destinations',to_jsonb(v_row.destinations)",
                    "    'delete_after',v_row.delete_after",
                ),
                hardening, test_sql, workflow, ledger,
            ),
            (
                replace_once(migration, "and status = 'active'", ""),
                hardening, test_sql, workflow, ledger,
            ),
            (
                replace_once(
                    migration,
                    "and ends_at >= statement_timestamp()",
                    "and delete_after >= statement_timestamp()",
                ),
                hardening, test_sql, workflow, ledger,
            ),
            (
                migration + "\ngrant select on table public.security_travel_plans to anon;\n",
                hardening, test_sql, workflow, ledger,
            ),
            (
                migration + "\ngrant update on table public.security_travel_plans to authenticated;\n",
                hardening, test_sql, workflow, ledger,
            ),
            (
                replace_once(
                    migration,
                    "    'destinations', result->'destinations'\n",
                    "    'destinations', result->'destinations',\n    'delete_after', result->'delete_after'\n",
                ),
                hardening, test_sql, workflow, ledger,
            ),
            (
                migration,
                replace_once(
                    hardening,
                    "  return pg_catalog.jsonb_build_object(\n    'id',v_row.id,\n    'status',v_row.status,\n    'starts_at',v_row.starts_at,",
                    "  return to_jsonb(v_row);\n  -- 'starts_at',v_row.starts_at,",
                ),
                test_sql, workflow, ledger,
            ),
            (
                migration, hardening,
                replace_once(test_sql, "statement_timestamp()", "clock_timestamp()"),
                workflow, ledger,
            ),
            (
                migration + "\n-- mutation non revue\n",
                hardening, test_sql, workflow, ledger,
            ),
            (
                migration, hardening, test_sql,
                workflow.replace(
                    "      - 'supabase/migrations/20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql'",
                    "      - 'supabase/migrations/UNWATCHED.sql'",
                    1,
                ),
                ledger,
            ),
            (
                migration, hardening, test_sql,
                workflow.replace(
                    "      - 'supabase/migrations/20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql'",
                    "      - 'supabase/migrations/UNWATCHED_INTERNAL.sql'",
                    1,
                ),
                ledger,
            ),
            (
                migration, hardening, test_sql,
                replace_once(
                    workflow,
                    "python3 scripts/validate_security_travel_client_visibility_v25.py --self-test",
                    "python3 scripts/validate_security_travel_client_visibility_v25.py --help",
                ),
                ledger,
            ),
            (
                migration, hardening, test_sql, workflow,
                ledger + "\n20260914223000 sinjira_v25_travel_mode_client_visibility_boundary\n",
            ),
            (
                migration, hardening, test_sql, workflow,
                ledger + "\n20260921005000 sinjira_v25_travel_mode_internal_response_minimization\n",
            ),
        ]
    except ValueError as exc:
        return [str(exc)]

    failures = []
    for index, mutated in enumerate(cases, start=1):
        if not validate(*mutated):
            failures.append(f"mutation {index} non détectée")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    values = (
        load(MIGRATION),
        load(HARDENING_MIGRATION),
        load(SQL_TEST),
        load(WORKFLOW),
        load(LEDGER),
    )
    errors = self_test(values) if args.self_test else validate(*values)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Mode Voyage client visibility: wrappers et appels internes minimisés, production intacte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
