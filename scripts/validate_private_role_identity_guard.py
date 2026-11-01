#!/usr/bin/env python3
"""Audit statique fail-closed d'un candidat SQL SECURITY DEFINER SINJIRA.

Le script ne se connecte PAS à Supabase : il valide un candidat HORS migrations.
Des essais SQL avec des comptes synthétiques restent obligatoires avant release.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "supabase/candidate-migrations/2026-10-31_private_role_identity_guard_REVIEW_ONLY.sql"
FUNCTION_NAMES = ("is_sinjira_admin", "project_access_rank")


def stripped_sql(source: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in source.splitlines())


def errors_in_candidate(source: str) -> list[str]:
    errors: list[str] = []
    sql = stripped_sql(source)
    normalized = re.sub(r"\s+", " ", sql).lower()

    found = re.findall(r"\bcreate\s+or\s+replace\s+function\s+private\.(\w+)\s*\(", sql, re.I)
    if found != list(FUNCTION_NAMES):
        errors.append("Seules les deux fonctions privées attendues sont autorisées")

    functions = re.split(r"(?i)\bCREATE\s+OR\s+REPLACE\s+FUNCTION\s+private\.", sql)
    if len(functions) != 3:
        return errors + ["Structure des deux fonctions non reconnue"]

    admin, rank = functions[1], functions[2]
    for name, body, ret in (
        ("is_sinjira_admin", admin, "boolean"),
        ("project_access_rank", rank, "integer"),
    ):
        low = re.sub(r"\s+", " ", body).lower()
        if not low.startswith(name + "("):
            errors.append("Nom de fonction inattendu")
        if "returns " + ret not in low:
            errors.append("Type de retour non conforme pour " + name)
        for required in (
            "security definer",
            "language sql", "stable",
            "set search_path = pg_catalog, auth, public, private, pg_temp",
            "p_user_id uuid default auth.uid()",
        ):
            if required not in low:
                errors.append("Contrat SQL privilégié manquant : " + name)
        if "$function$" not in low or low.count("$function$") != 2:
            errors.append("Corps SQL non vérifiable : " + name)

    mandatory_admin = (
        "p_user_id is not null",
        "coalesce(auth.jwt()->>'role', '') = 'service_role'",
        "or p_user_id = (select auth.uid())",
        "from public.internal_admin_users as a",
        "where a.user_id = p_user_id",
    )
    for fragment in mandatory_admin:
        if fragment not in re.sub(r"\s+", " ", admin).lower():
            errors.append("Contrôle d'identité administrateur manquant")

    mandatory_rank = (
        "when p_user_id is not null",
        "coalesce(auth.jwt()->>'role', '') <> 'service_role'",
        "p_user_id is distinct from (select auth.uid())",
        "then 0",
        "when private.is_sinjira_admin(p_user_id)",
        "from public.project_access as pa",
        "pa.user_id = p_user_id",
        "from public.projects as p",
        "p.visibility = 'public'",
        "then 1",
        "else 0",
    )
    ranknorm = re.sub(r"\s+", " ", rank).lower()
    for fragment in mandatory_rank:
        if fragment not in ranknorm:
            errors.append("Garde d'accès projet ou niveau public manquant")

    # Le refus d'identité tierce doit être AVANT la moindre interrogation
    # de droits admin et projet (sinon il fuit des informations).
    guard = ranknorm.find("p_user_id is distinct from (select auth.uid())")
    oracle = ranknorm.find("when private.is_sinjira_admin(p_user_id)")
    if guard < 0 or oracle < 0 or not guard < oracle:
        errors.append("Interdiction de consultation des tiers non prioritaire")

    if normalized.count("create or replace function") != 2:
        errors.append("Nombre de modifications DDL inattendu")
    for forbidden in (
        "drop ", "truncate ", "insert ", "delete ", "update ", "grant ",
        "revoke ", "alter ", "create table", "copy ", "set role ",
        "execute ", "pg_read_file(", "pg_ls_dir(", "dblink(",
    ):
        if re.search(r"(?<![a-z_])" + re.escape(forbidden), normalized):
            errors.append("Instruction non autorisée dans le candidat de revue")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    try:
        errors = errors_in_candidate(CANDIDATE.read_text("utf-8"))
    except (OSError, UnicodeError):
        errors = ["Candidat SQL absent ou illisible"]
    if errors:
        print("NO_GO: " + "; ".join(errors), file=sys.stderr)
        return 1
    print("PASS: fonctions privées avec identité de session vérifiée; migration non appliquée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
