#!/usr/bin/env python3
"""Contrat fail-closed pour un candidat SQL PRIVÉ (aucune écriture Supabase)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "supabase/candidate-migrations/2026-10-31_private_mfa_identity_oracle_guard_REVIEW_ONLY.sql"


def normalize(source: str) -> str:
    # Le contrat ne doit jamais être satisfait par des commentaires SQL.
    clean = "\n".join(line.split("--", 1)[0] for line in source.splitlines())
    return re.sub(r"\s+", " ", clean).strip().lower()


def validate(source: str) -> list[str]:
    sql = normalize(source)
    errors: list[str] = []
    if sql.count("create or replace function") != 1:
        errors.append("un seul CREATE OR REPLACE FUNCTION autorisé")

    expected_signature = (
        "create or replace function private.security_require_aal2_if_available(p_user_id uuid) "
        "returns void language plpgsql stable security definer "
        "set search_path to 'pg_catalog', 'auth', 'private' "
        "as $function$ begin"
    )
    if not sql.startswith(expected_signature):
        errors.append("signature/retour/droits/search_path/entrée SQL modifiés")

    if not sql.endswith("end; $function$;"):
        errors.append("le SQL doit finir après la fonction ciblée")

    # Vérification PREALABLE au contrôle MFA: les deux branches
    # doivent apparaître dans le corps, avant le premier accès aux facteurs.
    null_guard = (
        "if p_user_id is null then "
        "raise exception 'auth_required' using errcode = '42501'; end if;"
    )
    identity_guard = (
        "if coalesce(auth.jwt()->>'role', '') <> 'service_role' "
        "and p_user_id is distinct from auth.uid() then "
        "raise exception 'auth_context_mismatch' using errcode = '42501'; end if;"
    )
    factor_check = (
        "if private.security_verified_mfa_exists(p_user_id) "
        "and coalesce(auth.jwt()->>'aal','aal1') <> 'aal2' then "
        "raise exception 'aal2_required' using errcode = '42501'; end if;"
    )
    boundaries = [sql.find(x) for x in (null_guard, identity_guard, factor_check)]
    if any(x < 0 for x in boundaries):
        errors.append("séquence des protections ou exceptions obligatoires altérée")
    elif not boundaries[0] < boundaries[1] < boundaries[2]:
        errors.append("l'identité doit être vérifiée AVANT l'accès MFA")

    if sql.count("private.security_verified_mfa_exists(") != 1:
        errors.append("une unique lecture MFA après autorisation est requise")
    if sql.count("auth.uid()") != 1:
        errors.append("une seule comparaison de sujet JWT est autorisée")

    forbidden = (
        "drop ", "truncate ", "insert ", "delete ", "update ",
        "alter ", "grant ", "revoke ", "create table", "set role",
        "execute ", "dblink(", "pg_read_file(", "pg_ls_dir(",
        "disable row level security", "current_setting(", "dynamic sql"
    )
    for item in forbidden:
        if item in sql:
            errors.append("opération non autorisée dans un candidat de revue: " + item)

    # Les trois branches sont censées occuper TOUT le corps, pas seulement
    # servir de texte témoin avant un effet de bord caché.
    if all(x >= 0 for x in boundaries):
        expected_body = " ".join((null_guard, identity_guard, factor_check))
        between = sql.split("as $function$ begin", 1)
        if len(between) != 2 or between[1] != " " + expected_body + " end; $function$;":
            errors.append("corps SQL divergent du comportement strictement revu")

    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    try:
        errors = validate(CANDIDATE.read_text("utf-8"))
    except (OSError, UnicodeError):
        errors = ["candidat de revue absent ou illisible"]
    if errors:
        print("NO_GO: " + "; ".join(errors), file=sys.stderr)
        return 1
    print("PASS: identité vérifiée avant MFA, service_role conservé; candidat hors production.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
