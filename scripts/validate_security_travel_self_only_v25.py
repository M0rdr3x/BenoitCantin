#!/usr/bin/env python3
"""Fail-closed source guard for the effective SINJIRA Mode Voyage self-only boundary."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE_MIGRATION = Path("supabase/migrations/20260821222514_sinjira_v24_4_98_account_security_center.sql")
BASE_RPC_MIGRATION = Path("supabase/migrations/20260821222615_sinjira_v24_4_98_security_rpc.sql")
BOUNDARY_MIGRATION = Path("supabase/migrations/20260822201257_sinjira_v24_5_10_security_rpc_boundary.sql")
CREATE_V25_MIGRATION = Path("supabase/migrations/20260911001000_sinjira_v25_travel_mode_country_normalization.sql")
VISIBILITY_MIGRATION = Path("supabase/migrations/20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql")
HARDENING_MIGRATION = Path("supabase/migrations/20260921005000_sinjira_v25_travel_mode_internal_response_minimization.sql")
SQL_TEST = Path("supabase/tests/security_travel_self_only_v25.test.sql")
WORKFLOW = Path(".github/workflows/sinjira-security-travel-self-only-v25.yml")


def squash(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value.lower())


def extract_function(source: str, signature_start: str) -> str:
    lower = source.lower()
    start = lower.find(signature_start.lower())
    if start < 0:
        return ""
    next_start = lower.find("create or replace function ", start + len(signature_start))
    return source[start:] if next_start < 0 else source[start:next_start]


def extract_named_policy(source: str, policy_name: str) -> str:
    lower = source.lower()
    marker = f"create policy {policy_name.lower()} "
    start = lower.find(marker)
    if start < 0:
        return ""
    next_policy = lower.find("drop policy if exists ", start + len(marker))
    return source[start:] if next_policy < 0 else source[start:next_policy]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_text(
    table_sql: str,
    base_rpc_sql: str,
    boundary_sql: str,
    create_v25_sql: str,
    hardening_sql: str,
    test_sql: str,
    workflow: str,
) -> list[str]:
    errors: list[str] = []
    table = squash(table_sql)
    boundary = squash(boundary_sql)
    create_v25 = squash(create_v25_sql)
    hardening = squash(hardening_sql)
    test = squash(test_sql)
    flow = squash(workflow)
    travel_policy = squash(extract_named_policy(table_sql, "security_travel_plans_read_own"))

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
    require(errors, bool(travel_policy), "self-only travel SELECT policy missing")
    require(errors, "for select to authenticated using ((select auth.uid()) = user_id);" in travel_policy,
            "travel SELECT policy must bind auth.uid() to user_id")

    base_cancel = squash(extract_function(
        base_rpc_sql, "create or replace function public.security_cancel_travel_plan("
    ))
    require(errors, bool(base_cancel), "base security_cancel_travel_plan implementation missing")
    require(errors, "security definer" in base_cancel,
            "travel cancellation implementation must start from a controlled SECURITY DEFINER function")
    require(errors, "v_user uuid := auth.uid();" in base_cancel,
            "travel cancellation must derive the actor from auth.uid()")
    require(errors, "perform private.security_require_aal2_if_available(v_user);" in base_cancel,
            "travel cancellation must preserve MFA step-up")
    require(errors, "where id=p_plan_id and user_id=v_user and status='active'" in base_cancel,
            "travel cancellation must match both plan id and authenticated owner")
    require(errors, "p_user_id" not in base_cancel,
            "travel cancellation must never accept a caller-supplied target user")

    require(errors, "create schema if not exists sinjira_security_internal;" in boundary,
            "internal security RPC schema boundary missing")
    require(errors, "security_cancel_travel_plan" in boundary and "security_create_travel_plan" in boundary,
            "Mode Voyage RPCs must remain in the V24.5.10 internalization target set")
    require(errors, "alter function public.%i(%s) set schema sinjira_security_internal" in boundary,
            "security RPC implementations must be moved out of the public API schema")
    require(errors, "language sql security invoker set search_path = ''" in boundary,
            "public security RPC wrappers must remain SECURITY INVOKER")
    require(errors, "revoke all on function public.%i(%s) from public, anon" in boundary,
            "public/anonymous execution must remain revoked on wrappers")
    require(errors, "grant execute on function public.%i(%s) to authenticated, service_role" in boundary,
            "controlled wrapper execution grant missing")

    normalized_create = squash(extract_function(
        create_v25_sql, "create or replace function sinjira_security_internal.security_create_travel_plan("
    ))
    public_create = squash(extract_function(
        create_v25_sql, "create or replace function public.security_create_travel_plan("
    ))
    require(errors, bool(normalized_create), "V25 normalized travel creation implementation missing")
    require(errors, "not private.security_is_iso_country_code_v25(x)" in normalized_create,
            "V25 travel creation must reject non-ISO country values")
    require(errors, "select distinct upper(trim(x)) as code" in normalized_create,
            "V25 travel creation must normalize and deduplicate country codes")
    require(errors, "cardinality(coalesce(v_dest,'{}'::text[])) not between 1 and 12" in normalized_create,
            "V25 travel creation must keep the 1..12 country limit")

    visibility_sql = load(VISIBILITY_MIGRATION)
    visibility_create = squash(extract_function(
        visibility_sql, "create or replace function sinjira_security_internal.security_create_travel_plan("
    ))
    visibility_cancel = squash(extract_function(
        visibility_sql, "create or replace function sinjira_security_internal.security_cancel_travel_plan("
    ))
    require(errors, bool(visibility_create),
            "A3 travel creation implementation must already be redefined internally")
    require(errors, "v_user uuid := auth.uid();" in visibility_create,
            "A3 travel creation must still derive ownership from auth.uid()")
    require(errors, "p_user_id" not in visibility_create,
            "A3 travel creation must not accept a caller-supplied target user")
    require(errors, "return pg_catalog.jsonb_build_object(" in visibility_create
            and "return to_jsonb(v_row)" not in visibility_create,
            "A3 travel creation must already return a minimized JSON object")
    require(errors, bool(visibility_cancel),
            "A3 travel cancellation implementation must already be redefined internally")
    require(errors, "whereid=p_plan_idanduser_id=v_userandstatus='active'" in compact(visibility_cancel),
            "A3 travel cancellation must remain self-only")
    require(errors, "p_user_id" not in visibility_cancel,
            "A3 travel cancellation must not accept a caller-supplied target user")
    require(errors, "return pg_catalog.jsonb_build_object(" in visibility_cancel
            and "return to_jsonb(v_row)" not in visibility_cancel,
            "A3 travel cancellation must already return a minimized JSON object")

    effective_create = squash(extract_function(
        hardening_sql, "create or replace function sinjira_security_internal.security_create_travel_plan("
    ))
    effective_cancel = squash(extract_function(
        hardening_sql, "create or replace function sinjira_security_internal.security_cancel_travel_plan("
    ))

    require(errors, bool(effective_create), "effective internal travel creation implementation missing")
    require(errors, "security definer" in effective_create,
            "effective internal travel creation must remain SECURITY DEFINER")
    require(errors, "v_user uuid := auth.uid();" in effective_create,
            "effective travel creation must derive row ownership from auth.uid()")
    require(errors, "if v_user is null then" in effective_create and "auth_required" in effective_create,
            "effective travel creation must reject unauthenticated callers")
    require(errors, "perform private.security_require_aal2_if_available(v_user);" in effective_create,
            "effective travel creation must preserve MFA step-up")
    require(errors, "not private.security_is_iso_country_code_v25(x)" in effective_create,
            "effective travel creation must preserve ISO country validation")
    require(errors, "select distinct upper(trim(x)) as code" in effective_create,
            "effective travel creation must preserve country normalization/deduplication")
    require(errors, "cardinality(coalesce(v_dest,'{}'::text[])) not between 1 and 12" in effective_create,
            "effective travel creation must keep the 1..12 country limit")
    require(errors, "values(v_user," in compact(effective_create),
            "effective travel creation must persist auth.uid() as row owner")
    require(errors, "p_user_id" not in effective_create,
            "effective travel creation must never accept a caller-supplied target user")
    require(errors, "return pg_catalog.jsonb_build_object(" in effective_create
            and "return to_jsonb(v_row)" not in effective_create,
            "effective travel creation must return a minimized JSON object")

    require(errors, bool(effective_cancel), "effective internal travel cancellation implementation missing")
    require(errors, "security definer" in effective_cancel,
            "effective internal travel cancellation must remain SECURITY DEFINER")
    require(errors, "v_user uuid := auth.uid();" in effective_cancel,
            "effective travel cancellation must derive the actor from auth.uid()")
    require(errors, "perform private.security_require_aal2_if_available(v_user);" in effective_cancel,
            "effective travel cancellation must preserve MFA step-up")
    require(errors, "whereid=p_plan_idanduser_id=v_userandstatus='active'" in compact(effective_cancel),
            "effective travel cancellation must match both plan id and authenticated owner")
    require(errors, "p_user_id" not in effective_cancel,
            "effective travel cancellation must never accept a caller-supplied target user")
    require(errors, "return pg_catalog.jsonb_build_object(" in effective_cancel
            and "return to_jsonb(v_row)" not in effective_cancel,
            "effective travel cancellation must return a minimized JSON object")

    require(errors, bool(public_create), "V25 public travel creation wrapper missing")
    require(errors, "security invoker" in public_create,
            "V25 public travel creation wrapper must remain SECURITY INVOKER")
    require(errors, "select sinjira_security_internal.security_create_travel_plan($1,$2,$3,$4)" in public_create,
            "V25 public create wrapper must delegate only to the internal implementation")
    require(errors,
            "revoke all on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) from public, anon;" in create_v25,
            "anonymous/public execution of V25 travel creation must stay revoked")
    require(errors,
            "grant execute on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) to authenticated, service_role;" in create_v25,
            "authenticated/service_role execution grant for V25 create wrapper missing")

    required_test_markers = (
        "select plan(20)",
        "relrowsecurity",
        "security_travel_plans_read_own",
        "self_only_direct_dml_forbidden",
        "self_only_anon_create_rpc_forbidden",
        "self_only_anon_cancel_rpc_forbidden",
        "sinjira_security_internal.security_create_travel_plan",
        "sinjira_security_internal.security_cancel_travel_plan",
        "self_only_create_rpc_must_derive_owner_from_auth_uid",
        "self_only_cancel_rpc_must_match_plan_and_caller",
        "select * from finish()",
        "rollback;",
    )
    for marker in required_test_markers:
        require(errors, marker in test, f"SQL self-only contract missing marker: {marker}")

    for watched in (
        str(TABLE_MIGRATION),
        str(BASE_RPC_MIGRATION),
        str(BOUNDARY_MIGRATION),
        str(CREATE_V25_MIGRATION),
        str(VISIBILITY_MIGRATION),
        str(HARDENING_MIGRATION),
        str(SQL_TEST),
    ):
        require(errors, flow.count(watched.lower()) >= 2,
                f"workflow must watch authoritative self-only source on PR and push: {watched}")

    require(errors, "permissions: contents: read" in flow,
            "workflow permissions must stay read-only")
    require(errors, "python3 scripts/validate_security_travel_self_only_v25.py --self-test" in flow,
            "workflow must mutation-test its own guard")
    require(errors, "python3 scripts/validate_security_travel_self_only_v25.py" in flow,
            "workflow must run the self-only validator")
    require(errors, "supabase db push" not in flow and "supabase functions deploy" not in flow,
            "self-only CI must never deploy to Supabase")

    return errors


def load(path: Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def mutate_once(source: str, pattern: str, replacement: str, label: str) -> str:
    mutated, count = re.subn(pattern, replacement, source, count=1, flags=re.IGNORECASE | re.DOTALL)
    if count != 1:
        raise ValueError(f"self-test setup failed; mutation did not match exactly once: {label}")
    return mutated


def run_self_test(
    table_sql: str,
    base_rpc_sql: str,
    boundary_sql: str,
    create_v25_sql: str,
    hardening_sql: str,
    test_sql: str,
    workflow: str,
) -> list[str]:
    try:
        mutations = [
            ("RLS disabled",
             mutate_once(table_sql,
                         r"alter\s+table\s+public\.security_travel_plans\s+enable\s+row\s+level\s+security\s*;",
                         "alter table public.security_travel_plans disable row level security;", "RLS"),
             base_rpc_sql, boundary_sql, create_v25_sql, hardening_sql, test_sql, workflow),
            ("read policy widened",
             mutate_once(table_sql,
                         r"(create\s+policy\s+security_travel_plans_read_own[\s\S]*?)using\s*\(\(select\s+auth\.uid\(\)\)\s*=\s*user_id\)\s*;",
                         r"\1using (true);", "read policy"),
             base_rpc_sql, boundary_sql, create_v25_sql, hardening_sql, test_sql, workflow),
            ("direct INSERT granted",
             table_sql + "\ngrant insert on table public.security_travel_plans to authenticated;\n",
             base_rpc_sql, boundary_sql, create_v25_sql, hardening_sql, test_sql, workflow),
            ("base cancel owner filter removed", table_sql,
             mutate_once(base_rpc_sql,
                         r"where\s+id\s*=\s*p_plan_id\s+and\s+user_id\s*=\s*v_user\s+and\s+status\s*=\s*'active'",
                         "where id=p_plan_id and status='active'", "base cancel owner filter"),
             boundary_sql, create_v25_sql, hardening_sql, test_sql, workflow),
            ("effective create owner detached", table_sql, base_rpc_sql, boundary_sql, create_v25_sql,
             mutate_once(hardening_sql,
                         r"v_user\s+uuid\s*:=\s*auth\.uid\(\)\s*;",
                         "v_user uuid := gen_random_uuid();", "effective create owner"),
             test_sql, workflow),
            ("effective cancel owner filter removed", table_sql, base_rpc_sql, boundary_sql, create_v25_sql,
             mutate_once(hardening_sql,
                         r"and\s+user_id\s*=\s*v_user",
                         "", "effective cancel owner filter"),
             test_sql, workflow),
            ("effective response widened", table_sql, base_rpc_sql, boundary_sql, create_v25_sql,
             mutate_once(hardening_sql,
                         r"return\s+pg_catalog\.jsonb_build_object\(",
                         "return to_jsonb(v_row); -- ", "effective minimized response"),
             test_sql, workflow),
            ("internalization target removed", table_sql, base_rpc_sql,
             mutate_once(boundary_sql, r"'security_cancel_travel_plan'\s*,", "", "cancel target"),
             create_v25_sql, hardening_sql, test_sql, workflow),
            ("SQL contract weakened", table_sql, base_rpc_sql, boundary_sql, create_v25_sql, hardening_sql,
             mutate_once(test_sql,
                         r"SELF_ONLY_CREATE_RPC_MUST_DERIVE_OWNER_FROM_AUTH_UID",
                         "CREATE_OWNER_CHECK_REMOVED", "SQL create-owner assertion"),
             workflow),
            ("visibility source unwatched", table_sql, base_rpc_sql, boundary_sql, create_v25_sql, hardening_sql, test_sql,
             mutate_once(workflow,
                         re.escape(str(VISIBILITY_MIGRATION)),
                         "supabase/migrations/UNWATCHED_travel_visibility.sql", "workflow visibility watch")),
            ("hardening source unwatched", table_sql, base_rpc_sql, boundary_sql, create_v25_sql, hardening_sql, test_sql,
             mutate_once(workflow,
                         re.escape(str(HARDENING_MIGRATION)),
                         "supabase/migrations/UNWATCHED_travel_hardening.sql", "workflow hardening watch")),
            ("validator self-test skipped", table_sql, base_rpc_sql, boundary_sql, create_v25_sql, hardening_sql, test_sql,
             mutate_once(workflow,
                         r"python3\s+scripts/validate_security_travel_self_only_v25\.py\s+--self-test",
                         "python3 scripts/validate_security_travel_self_only_v25.py", "workflow self-test")),
        ]
    except ValueError as exc:
        return [str(exc)]

    failures: list[str] = []
    for name, t, base, boundary, create_v25, hardening, test, flow in mutations:
        if not validate_text(t, base, boundary, create_v25, hardening, test, flow):
            failures.append(f"mutation escaped validator: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    values = (
        load(TABLE_MIGRATION),
        load(BASE_RPC_MIGRATION),
        load(BOUNDARY_MIGRATION),
        load(CREATE_V25_MIGRATION),
        load(HARDENING_MIGRATION),
        load(SQL_TEST),
        load(WORKFLOW),
    )
    errors = run_self_test(*values) if args.self_test else validate_text(*values)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Mode Voyage effective self-only boundary: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
