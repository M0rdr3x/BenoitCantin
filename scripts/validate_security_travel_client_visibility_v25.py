#!/usr/bin/env python3
"""Fail-closed guard for the SINJIRA Mode Voyage client visibility boundary."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = Path("supabase/migrations/20260914223000_sinjira_v25_travel_mode_client_visibility_boundary.sql")
SQL_TEST = Path("supabase/tests/security_travel_client_visibility_v25.test.sql")
WORKFLOW = Path(".github/workflows/sinjira-security-travel-client-visibility-v25.yml")
REVIEWED = Path("supabase/production-reviewed-migration-batch.txt")
MIGRATION_ID = "20260914223000 sinjira_v25_travel_mode_client_visibility_boundary"


def squash(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def git_blob_sha(text: str) -> str:
    data = text.encode("utf-8")
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


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


def validate(migration: str, test_sql: str, workflow: str, reviewed: str) -> list[str]:
    errors: list[str] = []
    mig = squash(migration)
    test = squash(test_sql)
    flow = squash(workflow)
    policy = policy_expression(migration)
    create_fn = squash(extract_function(
        migration, "create or replace function public.security_create_travel_plan("
    ))
    cancel_fn = squash(extract_function(
        migration, "create or replace function public.security_cancel_travel_plan("
    ))

    require(errors,
            "alter table public.security_travel_plans enable row level security;" in mig,
            "RLS must remain enabled on security_travel_plans")
    require(errors,
            "revoke all on table public.security_travel_plans from public, anon, authenticated;" in mig,
            "browser roles must be reset deny-by-default")
    require(errors,
            "grant select on table public.security_travel_plans to authenticated;" in mig,
            "authenticated must receive SELECT only")
    require(errors,
            "grant insert on table public.security_travel_plans to authenticated" not in mig
            and "grant update on table public.security_travel_plans to authenticated" not in mig
            and "grant delete on table public.security_travel_plans to authenticated" not in mig,
            "authenticated must not receive direct travel writes")
    require(errors,
            "grant select on table public.security_travel_plans to anon" not in mig,
            "anon must never receive travel read access")
    require(errors,
            "drop policy if exists security_travel_plans_read_own" in mig,
            "legacy broad travel policy must be replaced explicitly")
    require(errors,
            "create policy security_travel_plans_read_own" in mig and "to authenticated" in mig,
            "canonical travel SELECT policy must target authenticated explicitly")
    require(errors, bool(policy), "travel SELECT policy expression missing")
    require(errors,
            "(select auth.uid()) = user_id" in policy,
            "travel SELECT policy must remain self-only")
    require(errors,
            "status = 'active'" in policy,
            "cancelled travel rows must be hidden from browser reads")
    require(errors,
            "ends_at >= statement_timestamp()" in policy,
            "expired travel rows must be hidden using server time")
    require(errors,
            "delete_after" not in policy,
            "retention deadline must never authorize browser visibility")

    require(errors, bool(create_fn), "public travel creation wrapper missing")
    require(errors,
            "security invoker" in create_fn and "set search_path = ''" in create_fn,
            "public travel creation wrapper must remain SECURITY INVOKER with empty search_path")
    require(errors,
            "sinjira_security_internal.security_create_travel_plan($1,$2,$3,$4)" in create_fn,
            "public travel creation wrapper must delegate to the internal implementation")
    require(errors,
            "jsonb_build_object" in create_fn,
            "public travel creation wrapper must build an explicit response")
    for key in ("id", "status", "starts_at", "ends_at", "destinations"):
        require(errors,
                f"'{key}', result->'{key}'" in create_fn,
                f"public travel creation response must include only required key: {key}")
    for key in ("delete_after", "user_id", "created_at", "updated_at", "cancelled_at", "multi_country"):
        require(errors,
                f"result->'{key}'" not in create_fn,
                f"public travel creation response must not expose internal key: {key}")
    require(errors,
            "revoke all on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) from public, anon;" in mig,
            "anonymous/public creation RPC execution must stay revoked")
    require(errors,
            "grant execute on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) to authenticated, service_role;" in mig,
            "creation RPC grant must stay limited to authenticated and service_role")

    require(errors, bool(cancel_fn), "public travel cancellation wrapper missing")
    require(errors,
            "security invoker" in cancel_fn and "set search_path = ''" in cancel_fn,
            "public travel cancellation wrapper must remain SECURITY INVOKER with empty search_path")
    require(errors,
            "sinjira_security_internal.security_cancel_travel_plan($1)" in cancel_fn,
            "public travel cancellation wrapper must delegate to the internal implementation")
    require(errors,
            "jsonb_build_object" in cancel_fn
            and "'id', result->'id'" in cancel_fn
            and "'status', result->'status'" in cancel_fn,
            "public travel cancellation wrapper must return only an explicit acknowledgement")
    for key in ("delete_after", "user_id", "created_at", "updated_at", "cancelled_at", "destinations", "starts_at", "ends_at"):
        require(errors,
                f"result->'{key}'" not in cancel_fn,
                f"public travel cancellation response must not expose internal key: {key}")
    require(errors,
            "revoke all on function public.security_cancel_travel_plan(uuid) from public, anon;" in mig,
            "anonymous/public cancellation RPC execution must stay revoked")
    require(errors,
            "grant execute on function public.security_cancel_travel_plan(uuid) to authenticated, service_role;" in mig,
            "cancellation RPC grant must stay limited to authenticated and service_role")

    required_test_markers = (
        "select plan(22)",
        "relrowsecurity",
        "has_table_privilege('authenticated', 'public.security_travel_plans', 'select')",
        "has_table_privilege('anon', 'public.security_travel_plans', 'select')",
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
        "jsonb_build_object",
        "has_function_privilege('anon'",
        "has_function_privilege('authenticated'",
        "select * from finish()",
        "rollback;",
    )
    for marker in required_test_markers:
        require(errors, marker in test, f"SQL visibility contract missing marker: {marker}")

    require(errors,
            "permissions: contents: read" in flow,
            "workflow permissions must stay read-only")
    for path in (str(MIGRATION), str(SQL_TEST), str(WORKFLOW), str(REVIEWED)):
        require(errors, path.lower() in flow, f"workflow must watch {path}")
    require(errors,
            "python3 scripts/validate_security_travel_client_visibility_v25.py --self-test" in flow,
            "workflow must mutation-test the visibility guard")
    require(errors,
            "python3 scripts/validate_security_travel_client_visibility_v25.py" in flow,
            "workflow must run the visibility validator")
    require(errors,
            "supabase db push" not in flow and "supabase functions deploy" not in flow,
            "visibility CI must never deploy")

    expected_review = f"{MIGRATION_ID} {git_blob_sha(migration)}"
    require(errors,
            expected_review in reviewed,
            "reviewed migration batch must contain the exact Git blob fingerprint")
    require(errors,
            reviewed.count(MIGRATION_ID) == 1,
            "reviewed migration batch must contain exactly one visibility migration entry")

    return errors


def load(path: Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"self-test setup failed for {label}: expected one exact match")
    return source.replace(old, new, 1)


def self_test(migration: str, test_sql: str, workflow: str, reviewed: str) -> list[str]:
    try:
        mutations = [
            ("RLS disabled", replace_once(
                migration,
                "alter table public.security_travel_plans enable row level security;",
                "alter table public.security_travel_plans disable row level security;",
                "RLS disabled"), test_sql, workflow, reviewed),
            ("owner boundary removed", replace_once(
                migration,
                "(select auth.uid()) = user_id",
                "true",
                "owner boundary"), test_sql, workflow, reviewed),
            ("cancelled rows exposed", replace_once(
                migration,
                "and status = 'active'",
                "",
                "status filter"), test_sql, workflow, reviewed),
            ("retained expired rows exposed", replace_once(
                migration,
                "and ends_at >= statement_timestamp()",
                "and delete_after >= statement_timestamp()",
                "expiry boundary"), test_sql, workflow, reviewed),
            ("anonymous read granted", migration + "\ngrant select on table public.security_travel_plans to anon;\n",
             test_sql, workflow, reviewed),
            ("direct update granted", migration + "\ngrant update on table public.security_travel_plans to authenticated;\n",
             test_sql, workflow, reviewed),
            ("creation response leaks retention", replace_once(
                migration,
                "    'destinations', result->'destinations'\n",
                "    'destinations', result->'destinations',\n    'delete_after', result->'delete_after'\n",
                "creation response leak"), test_sql, workflow, reviewed),
            ("SQL contract weakened", migration, replace_once(
                test_sql,
                "statement_timestamp()",
                "clock_timestamp()",
                "SQL policy clock assertion"), workflow, reviewed),
            ("review fingerprint corrupted", migration, test_sql, workflow, replace_once(
                reviewed,
                f"{MIGRATION_ID} {git_blob_sha(migration)}",
                f"{MIGRATION_ID} {'0' * 40}",
                "review fingerprint")),
            ("migration path unwatched", migration, test_sql, replace_once(
                workflow,
                f"      - '{MIGRATION}'",
                "      - 'supabase/migrations/UNWATCHED.sql'",
                "workflow migration path"), reviewed),
            ("validator self-test skipped", migration, test_sql, replace_once(
                workflow,
                "python3 scripts/validate_security_travel_client_visibility_v25.py --self-test",
                "python3 scripts/validate_security_travel_client_visibility_v25.py --help",
                "workflow self-test"), reviewed),
        ]
    except ValueError as exc:
        return [str(exc)]

    failures: list[str] = []
    for name, mutated_migration, mutated_test, mutated_workflow, mutated_reviewed in mutations:
        if not validate(mutated_migration, mutated_test, mutated_workflow, mutated_reviewed):
            failures.append(f"mutation escaped validator: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    migration = load(MIGRATION)
    test_sql = load(SQL_TEST)
    workflow = load(WORKFLOW)
    reviewed = load(REVIEWED)
    errors = self_test(migration, test_sql, workflow, reviewed) if args.self_test else validate(
        migration, test_sql, workflow, reviewed
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Mode Voyage retained-row client visibility and RPC response boundary: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
