#!/usr/bin/env python3
"""Contrat V47 : prévol liseuse en lecture seule, fidèle à la migration V32.

Aucun accès réseau ni lecture de lignes de romans ou d'utilisateurs.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts/audits/sinjira_reader_v47_preflight_readonly.sql"
V32 = ROOT / "supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql"

EXPECTED_CHECKS = frozenset({
    "reader_table_present",
    "reader_rls_enabled",
    "reader_single_owner_policy",
    "reader_primary_key",
    "reader_legacy_bounds",
    "reader_existing_fields",
    "reader_authenticated_read_write",
    "reader_anon_direct_grants",
    "reader_scroll_ratio_column",
    "reader_scroll_ratio_range",
    "reader_release_decision",
})
ALLOWED_SOURCES = frozenset({
    "t", "columns", "constraints", "policies", "checks",
    "pg_class", "pg_namespace", "pg_constraint",
    "pg_policies", "information_schema.columns",
})
DISALLOWED = re.compile(
    r"\b(?:ALTER|CREATE|DROP|INSERT|UPDATE|DELETE|TRUNCATE|REVOKE|GRANT|"
    r"COPY|CALL|DO|EXECUTE|VACUUM|PERFORM|MERGE|REFRESH|COMMIT|"
    r"ROLLBACK|SET|RESET)\b",
    re.I,
)


def strip_literals_and_comments(sql: str) -> str:
    """Neutralise commentaires et chaînes pour inspecter les instructions SQL."""
    def replace(match: re.Match[str]) -> str:
        return "''" if match.group(0).startswith("'") else " "
    return re.sub(r"'(?:''|[^'])*'|--[^\n]*|/\*[\s\S]*?\*/", replace, sql)


def validate_sources(preflight: str, migration: str) -> list[str]:
    errors: list[str] = []
    sql = strip_literals_and_comments(preflight).strip()
    if not sql.upper().startswith("WITH "):
        errors.append("NOT_CATALOGUE_SELECT")
    if sql.count(";") != 1 or not sql.endswith(";"):
        errors.append("MULTI_STATEMENT")
    if DISALLOWED.search(sql):
        errors.append("MUTATION_SQL_PRESENT")
    sources = set(re.findall(r"\b(?:FROM|JOIN)\s+([a-z_][\w.]*)", sql, re.I))
    if not sources or not sources <= ALLOWED_SOURCES:
        errors.append("NON_METADATA_SOURCE")

    checks = re.findall(r"\bSELECT\s+'(reader_[a-z_]+)'", preflight, re.I)
    if len(checks) != len(EXPECTED_CHECKS) or set(checks) != EXPECTED_CHECKS:
        errors.append("RELEASE_CHECK_INVENTORY_CHANGED")
    if "CASE WHEN EXISTS(SELECT 1 FROM checks WHERE status='BLOCK')" not in preflight:
        errors.append("NO_FAIL_CLOSED_GATE")
    if "THEN 'NO_GO' ELSE 'REVIEW_REQUIRED'" not in preflight:
        errors.append("UNSUPPORTED_GO_STATUS")
    if "reader_anon_direct_grants" not in preflight or "THEN 'REVIEW'" not in preflight:
        errors.append("ANON_GRANT_REVIEW_REMOVED")
    for expected in (
        "sinjira_reader_library", "pg_policies", "relrowsecurity",
        "has_table_privilege('anon'", "has_table_privilege('authenticated'",
        "reader_single_owner_policy", "auth.uid", "reader_scroll_ratio_column",
        "reader_scroll_ratio_range", "numeric", "is_nullable='YES'",
        "sinjira_reader_library_scroll_ratio_range", "reader_legacy_bounds",
    ):
        if expected not in preflight:
            errors.append("MISSING_CHECK:" + expected)

    if not re.search(
        r"add\s+column\s+if\s+not\s+exists\s+scroll_ratio\s+numeric\s*\(5\s*,\s*4\s*\)",
        migration, flags=re.I,
    ):
        errors.append("V32_MIGRATION_DRIFT")
    if not re.search(
        r"check\s*\(scroll_ratio\s+is\s+null\s+or\s*\("
        r"scroll_ratio\s*>=\s*0\s+and\s+scroll_ratio\s*<=\s*1\)\)",
        migration, flags=re.I,
    ):
        errors.append("V32_BOUNDS_DRIFT")

    if re.search(r"\b(?:supabase db push|service_role_key|postgresql://)\b",preflight,re.I):
        errors.append("PRODUCTION_CONNECTION_ARTIFACT")
    return errors


def validate_files() -> list[str]:
    return validate_sources(
        PREFLIGHT.read_text(encoding="utf-8"),
        V32.read_text(encoding="utf-8"),
    )


if __name__ == "__main__":
    errors = validate_files()
    for error in errors:
        print("V47-ERROR:", error)
    if errors:
        raise SystemExit(1)
    print("V47-PASS — prévol catalogue unique, fail-closed, V32 conforme, aucun accès distant.")
