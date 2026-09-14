#!/usr/bin/env python3
"""Fail-closed source guard for the SINJIRA Mode Voyage self-only boundary."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE_MIGRATION = Path("supabase/migrations/20260821222514_sinjira_v24_4_98_account_security_center.sql")
RPC_MIGRATION = Path("supabase/migrations/20260821222615_sinjira_v24_4_98_security_rpc.sql")
SQL_TEST = Path("supabase/tests/security_travel_self_only_v25.test.sql")
WORKFLOW = Path(".github/workflows/sinjira-security-travel-self-only-v25.yml")


def squash(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def extract_function(source: str, signature_start: str) -> str:
    start = source.lower().find(signature_start.lower())
    if start < 0:
        return ""
    next_start = source.lower().find("create or replace function ", start + len(signature_start))
    return source[start:] if next_start < 0 else source[start:next_start]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_text(table_sql: str, rpc_sql: str, test_sql: str, workflow: str) -> list[str]:
    errors: list[str] = []
    table = squash(table_sql)
    test = squash(test_sql)
    flow = squash(workflow)

    require(errors, "create table if not exists public.security_travel_plans" in table,
            "security_travel_plans table definition missing")
    require(errors, "user_id uuid not null references auth.users(id) on delete cascade" in table,
            "travel rows must have a required owner tied to auth.users")
    require(errors, "alter table public.security_travel_plans enable row level security;" in table,
            "RLS must stay enabled on security_travel_plans")
    require(errors, "revoke all on table public.security_travel_plans from public, anon, authenticated;" in table,
            "travel table must remain deny-by-default for browser roles")
    require(errors, "grant select on table public.security_travel_plans to authenticated;" in table,
            "authenticated users need SELECT only, mediated by RLS")
    require(errors, "grant insert on table public.security_travel_plans to authenticated" not in table,
            "authenticated must not receive direct INSERT on travel plans")
    require(errors, "grant update on table public.security_travel_plans to authenticated" not in table,
            "authenticated must not receive direct UPDATE on travel plans")
    require(errors, "grant delete on table public.security_travel_plans to authenticated" not in table,
            "authenticated must not receive direct DELETE on travel plans")
    require(errors, "create policy security_travel_plans_read_own on public.security_travel_plans" in table,
            "self-only travel SELECT policy missing")
    require(errors, "for select to authenticated using ((select auth.uid()) = user_id);" in table,
            "travel SELECT policy must bind auth.uid() to user_id")

    create_fn = squash(extract_function(
        rpc_sql, "create or replace function public.security_create_travel_plan("
    ))
    cancel_fn = squash(extract_function(
        rpc_sql, "create or replace function public.security_cancel_travel_plan("
    ))

    require(errors, bool(create_fn), "security_create_travel_plan RPC missing")
    require(errors, "security definer" in create_fn,
            "travel creation RPC must keep its controlled SECURITY DEFINER boundary")
    require(errors, "set search_path = pg_catalog, public, private" in create_fn,
            "travel creation RPC must keep an explicit safe search_path")
    require(errors, "v_user uuid := auth.uid();" in create_fn,
            "travel creation must derive the owner from auth.uid()")
    require(errors, "if v_user is null then raise exception 'auth_required'" in create_fn,
            "travel creation must reject unauthenticated calls")
    require(errors, "perform private.security_require_aal2_if_available(v_user);" in create_fn,
            "travel creation must preserve MFA step-up when available")
    require(errors, "insert into public.security_travel_plans(user_id,starts_at,ends_at,destinations,multi_country,delete_after)" in create_fn,
            "travel creation insert contract changed")
    require(errors, "values(v_user,p_starts_at,p_ends_at,v_dest,coalesce(p_multi_country,false),p_ends_at+interval '7 days')" in create_fn,
            "travel creation must write auth.uid() as row owner")
    require(errors, "p_user_id" not in create_fn,
            "travel creation must never accept a caller-supplied target user")

    require(errors, bool(cancel_fn), "security_cancel_travel_plan RPC missing")
    require(errors, "security definer" in cancel_fn,
            "travel cancellation RPC must keep its controlled SECURITY DEFINER boundary")
    require(errors, "set search_path = pg_catalog, public, private" in cancel_fn,
            "travel cancellation RPC must keep an explicit safe search_path")
    require(errors, "v_user uuid := auth.uid();" in cancel_fn,
            "travel cancellation must derive the actor from auth.uid()")
    require(errors, "if v_user is null then raise exception 'auth_required'" in cancel_fn,
            "travel cancellation must reject unauthenticated calls")
    require(errors, "perform private.security_require_aal2_if_available(v_user);" in cancel_fn,
            "travel cancellation must preserve MFA step-up when available")
    require(errors, "where id=p_plan_id and user_id=v_user and status='active'" in cancel_fn,
            "travel cancellation must match both plan id and authenticated owner")
    require(errors, "p_user_id" not in cancel_fn,
            "travel cancellation must never accept a caller-supplied target user")

    rpc = squash(rpc_sql)
    require(errors,
            "revoke all on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) from public, anon;" in rpc,
            "anonymous/public execution of travel creation must stay revoked")
    require(errors,
            "grant execute on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) to authenticated;" in rpc,
            "authenticated execution grant for controlled creation RPC missing")
    require(errors,
            "revoke all on function public.security_cancel_travel_plan(uuid) from public, anon;" in rpc,
            "anonymous/public execution of travel cancellation must stay revoked")
    require(errors,
            "grant execute on function public.security_cancel_travel_plan(uuid) to authenticated;" in rpc,
            "authenticated execution grant for controlled cancellation RPC missing")

    required_test_markers = (
        "relrowsecurity",
        "has_table_privilege('authenticated', 'public.security_travel_plans', 'select')",
        "self_only_direct_dml_forbidden",
        "has_table_privilege('anon', 'public.security_travel_plans', 'select')",
        "security_travel_plans_read_own",
        "auth.uid()",
        "has_function_privilege(",
        "self_only_anon_create_rpc_forbidden",
        "self_only_anon_cancel_rpc_forbidden",
        "pg_get_functiondef(",
        "self_only_create_rpc_must_derive_owner_from_auth_uid",
        "self_only_cancel_rpc_must_match_plan_and_caller",
        "rollback;",
    )
    for marker in required_test_markers:
        require(errors, marker in test, f"SQL self-only contract missing marker: {marker}")

    require(errors, "permissions: contents: read" in flow,
            "workflow permissions must stay read-only")
    require(errors, "python3 scripts/validate_security_travel_self_only_v25.py --self-test" in flow,
            "workflow must mutation-test its own guard")
    require(errors, "python3 scripts/validate_security_travel_self_only_v25.py" in flow,
            "workflow must run the self-only validator")
    require(errors, "supabase db push" not in flow and "supabase functions deploy" not in flow,
            "self-only CI must never deploy to Supabase")

    forbidden_precision = ("gps", "latitude", "longitude", "hotel", "flight", "itineraire", "itinéraire")
    # The authoritative migrations may mention forbidden concepts only in explicit privacy comments;
    # the new self-only test/workflow must not introduce fields or processing for them.
    new_guard_text = squash(test_sql + "\n" + workflow)
    for token in forbidden_precision:
        require(errors, token not in new_guard_text,
                f"self-only guard must not introduce precise travel detail: {token}")

    return errors


def load(path: Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def mutate_once(source: str, pattern: str, replacement: str, label: str) -> str:
    mutated, count = re.subn(pattern, replacement, source, count=1, flags=re.IGNORECASE | re.DOTALL)
    if count != 1:
        raise ValueError(f"self-test setup failed; mutation did not match exactly once: {label}")
    return mutated


def run_self_test(table_sql: str, rpc_sql: str, test_sql: str, workflow: str) -> list[str]:
    try:
        rls_disabled = mutate_once(
            table_sql,
            r"alter\s+table\s+public\.security_travel_plans\s+enable\s+row\s+level\s+security\s*;",
            "alter table public.security_travel_plans disable row level security;",
            "RLS disabled",
        )
        policy_widened = mutate_once(
            table_sql,
            r"(create\s+policy\s+security_travel_plans_read_own\s+on\s+public\.security_travel_plans\s+for\s+select\s+to\s+authenticated\s+)using\s*\(\(select\s+auth\.uid\(\)\)\s*=\s*user_id\)\s*;",
            r"\1using (true);",
            "read policy widened",
        )
        create_owner_detached = mutate_once(
            rpc_sql,
            r"(create\s+or\s+replace\s+function\s+public\.security_create_travel_plan\([\s\S]*?v_user\s+uuid\s*:=\s*)auth\.uid\(\)\s*;",
            r"\1gen_random_uuid();",
            "create owner detached",
        )
        cancel_owner_removed = mutate_once(
            rpc_sql,
            r"(create\s+or\s+replace\s+function\s+public\.security_cancel_travel_plan\([\s\S]*?where\s+id\s*=\s*p_plan_id\s+)and\s+user_id\s*=\s*v_user(\s+and\s+status\s*=\s*'active')",
            r"\1\2",
            "cancel owner filter removed",
        )
        anon_create_exposed = mutate_once(
            rpc_sql,
            r"revoke\s+all\s+on\s+function\s+public\.security_create_travel_plan\(timestamptz\s*,\s*timestamptz\s*,\s*text\[\]\s*,\s*boolean\)\s+from\s+public\s*,\s*anon\s*;",
            "grant execute on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) to anon;",
            "anonymous create exposed",
        )
        sql_contract_weakened = mutate_once(
            test_sql,
            r"SELF_ONLY_DIRECT_DML_FORBIDDEN",
            "DIRECT_DML_CHECK_REMOVED",
            "SQL contract weakened",
        )
        workflow_self_test_skipped = mutate_once(
            workflow,
            r"python3\s+scripts/validate_security_travel_self_only_v25\.py\s+--self-test",
            "python3 scripts/validate_security_travel_self_only_v25.py",
            "validator self-test skipped",
        )
    except ValueError as exc:
        return [str(exc)]

    mutations = [
        ("RLS disabled", rls_disabled, rpc_sql, test_sql, workflow),
        ("read policy widened", policy_widened, rpc_sql, test_sql, workflow),
        ("direct INSERT granted", table_sql + "\ngrant insert on table public.security_travel_plans to authenticated;\n",
         rpc_sql, test_sql, workflow),
        ("create owner detached", table_sql, create_owner_detached, test_sql, workflow),
        ("cancel owner filter removed", table_sql, cancel_owner_removed, test_sql, workflow),
        ("anonymous create exposed", table_sql, anon_create_exposed, test_sql, workflow),
        ("SQL contract weakened", table_sql, rpc_sql, sql_contract_weakened, workflow),
        ("validator self-test skipped", table_sql, rpc_sql, test_sql, workflow_self_test_skipped),
    ]
    failures: list[str] = []
    for name, mutated_table, mutated_rpc, mutated_test, mutated_workflow in mutations:
        if not validate_text(mutated_table, mutated_rpc, mutated_test, mutated_workflow):
            failures.append(f"mutation escaped validator: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    table_sql = load(TABLE_MIGRATION)
    rpc_sql = load(RPC_MIGRATION)
    test_sql = load(SQL_TEST)
    workflow = load(WORKFLOW)

    errors = run_self_test(table_sql, rpc_sql, test_sql, workflow) if args.self_test else validate_text(
        table_sql, rpc_sql, test_sql, workflow
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Mode Voyage self-only boundary: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
