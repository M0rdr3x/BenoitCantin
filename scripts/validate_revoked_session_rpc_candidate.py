#!/usr/bin/env python3
"""Contrat statique : refuser les JWT de sessions révoquées pour les RPC sensibles.

N'exécute AUCUNE fonction SQL, ne lit AUCUN compte et ne se connecte à aucune
base. Un test d'intégration staging avec sessions réelles reste obligatoire.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "security/candidates/sinjira_revoked_auth_session_device_rpcs.sql"

FUNCTION_NAMES = (
    "security_after_password_recovery",
    "security_compromise_account",
    "security_report_lost_device",
    "security_resolve_connection_challenge",
    "security_resolve_connection_challenge_mfa",
    "security_revoke_device",
    "security_set_device_trust",
    "security_update_settings",
)
AUTH_CHECK = "if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;"
SESSION_CALL = "perform private.security_require_current_auth_session(v_user);"
IMMEDIATE_GUARD = "  " + AUTH_CHECK + "\n  " + SESSION_CALL

HELPER_REQUIREMENTS = (
    "CREATE OR REPLACE FUNCTION private.security_require_current_auth_session(p_user uuid)",
    "RETURNS void",
    "LANGUAGE plpgsql",
    "VOLATILE",
    "SECURITY DEFINER",
    "SET search_path TO 'pg_catalog'",
    "p_user IS NULL OR p_user IS DISTINCT FROM auth.uid()",
    "v_session := NULLIF(auth.jwt()->>'session_id','')::uuid;",
    "EXCEPTION WHEN invalid_text_representation THEN",
    "v_session IS NULL OR NOT EXISTS(",
    "FROM auth.sessions s",
    "s.id = v_session",
    "s.user_id = p_user",
    "(s.not_after IS NULL OR s.not_after > now())",
    "RAISE EXCEPTION 'AUTH_SESSION_INVALID' USING ERRCODE='42501'",
    "REVOKE ALL ON FUNCTION private.security_require_current_auth_session(uuid)",
    "FROM PUBLIC, anon, authenticated;",
)

SIGNATURES = {
    "security_after_password_recovery": "(p_device_key text DEFAULT NULL::text)",
    "security_compromise_account": "(p_current_device_key text DEFAULT NULL::text)",
    "security_report_lost_device": "(p_device_id uuid)",
    "security_resolve_connection_challenge": "(p_challenge_id uuid, p_device_key text, p_decision text)",
    "security_resolve_connection_challenge_mfa": "(p_challenge_id uuid, p_device_key text)",
    "security_revoke_device": "(p_device_id uuid)",
    "security_set_device_trust": "(p_device_id uuid, p_trusted boolean, p_primary boolean DEFAULT false)",
    "security_update_settings": (
        "(p_remember_usual_region boolean DEFAULT NULL::boolean, "
        "p_sensitive_step_up boolean DEFAULT NULL::boolean, "
        "p_notify_new_device boolean DEFAULT NULL::boolean, "
        "p_notify_high_risk boolean DEFAULT NULL::boolean, "
        "p_notify_security_changes boolean DEFAULT NULL::boolean)"
    ),
}


def remove_comments(source: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in source.splitlines())


def inspect(source: str) -> list[str]:
    errors: list[str] = []
    code = remove_comments(source).strip()
    if not re.match(r"^BEGIN\s*;", code, re.I):
        errors.append("BEGIN transactionnel explicite absent")
    if not re.search(r"ROLLBACK\s*;\s*$", code, re.I):
        errors.append("ROLLBACK final obligatoire : ne jamais déployer ce candidat")
    if re.search(r"(?im)^\s*(?:COMMIT|GRANT|ALTER|DROP|TRUNCATE|SAVEPOINT)\b", code):
        errors.append("Instruction de promotion/droits interdite dans le candidat")
    if len(re.findall(r"(?im)^\s*ROLLBACK\s*;", code)) != 1:
        errors.append("ROLLBACK doit apparaître une seule fois, à la fin")
    if len(re.findall(r"(?im)^\s*CREATE OR REPLACE FUNCTION\s+", code)) != len(FUNCTION_NAMES) + 1:
        errors.append("Le candidat doit contenir exactement neuf définitions de fonctions")

    pieces = code.split("CREATE OR REPLACE FUNCTION sinjira_security_internal.")
    if len(pieces) != len(FUNCTION_NAMES) + 1:
        errors.append("Nombre de RPC SINJIRA sensibles incorrect")
        return errors
    helper = pieces[0]
    for required in HELPER_REQUIREMENTS:
        if required not in helper:
            errors.append("Vérification de session absente : " + required)
    if helper.count("$session_guard$") != 2 or "$session_guard$;" not in helper:
        errors.append("Délimiteurs de la nouvelle fonction de session incorrects")
    if "REVOKE ALL ON FUNCTION" not in helper or re.search(
        r"(?im)^\s*GRANT\s+", code
    ):
        errors.append("La fonction de sécurité ne doit pas être accordée aux rôles clients")

    names_seen = []
    for part in pieces[1:]:
        found = re.match(r"([a-z_]+)\(", part)
        if not found:
            errors.append("Signature RPC non reconnaissable")
            continue
        name = found.group(1)
        names_seen.append(name)
        if name not in SIGNATURES:
            errors.append("RPC inconnue : " + name)
            continue
        if not part.startswith(name + SIGNATURES[name]):
            errors.append("Signature RPC historique modifiée : " + name)
        if part.count("$function$") != 2 or "$function$;" not in part:
            errors.append("Bloc SQL RPC mal terminé : " + name)
        if "SECURITY DEFINER" not in part or "SET search_path TO" not in part:
            errors.append("Garde privilèges/search_path historique absent : " + name)
        if part.count(AUTH_CHECK) != 1 or part.count(SESSION_CALL) != 1:
            errors.append("Contrôle de session non unique : " + name)
        if IMMEDIATE_GUARD not in part:
            errors.append("Contrôle de session non immédiat après AUTH_REQUIRED : " + name)
        if "v_user uuid := auth.uid()" not in part:
            errors.append("Identité auth.uid() historique absente : " + name)
        if "RETURNS jsonb" not in part:
            errors.append("Type de retour historique modifié : " + name)

    if tuple(names_seen) != FUNCTION_NAMES:
        errors.append("Liste ou ordre des RPC différent du catalogue attendu")
    if code.count("REVOKE ALL ON FUNCTION") != 1:
        errors.append("Modification inattendue des droits existants")
    return errors


def self_test(source: str) -> None:
    problems = inspect(source)
    if problems:
        raise AssertionError("La base valide du candidat a échoué : " + "; ".join(problems))
    mutations = (
        ("retrait du rollback", "ROLLBACK;", "COMMIT;"),
        ("absence de session", "FROM auth.sessions s", "FROM auth.users s"),
        ("session appartenant à un tiers", "s.user_id = p_user", "s.user_id IS NOT NULL"),
        ("absence de date d'expiration", "(s.not_after IS NULL OR s.not_after > now())", "TRUE"),
        ("session_id falsifié", "auth.jwt()->>'session_id'", "auth.jwt()->>'untrusted_id'"),
        ("liaison à l'appelant retirée", "p_user IS DISTINCT FROM auth.uid()", "false"),
        ("helper sans definer", "VOLATILE\nSECURITY DEFINER", "VOLATILE\nSECURITY INVOKER"),
        ("helper rendu public", "FROM PUBLIC, anon, authenticated;", "FROM anon;"),
        ("garde de RPC retiré", SESSION_CALL, "perform 1;"),
        ("garde de RPC trop tardif", IMMEDIATE_GUARD,
         "  " + AUTH_CHECK + "\n  perform 1;\n  " + SESSION_CALL),
        ("grants publics introduits", "ROLLBACK;",
         "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA private TO PUBLIC;\nROLLBACK;"),
        ("double rollback", "ROLLBACK;", "ROLLBACK;\nROLLBACK;"),
    )
    for label, original, replacement in mutations:
        if original not in source:
            raise AssertionError("Fixture de mutation manquante : " + label)
        modified = source.replace(original, replacement, 1)
        if not inspect(modified):
            raise AssertionError("Mutation dangereuse acceptée : " + label)
    print(f"OK : {len(mutations)} mutations de sessions et privilèges rejetées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not SQL.is_file() or SQL.is_symlink():
        print("ECHEC : candidat SQL absent ou lien symbolique")
        return 1
    if SQL.stat().st_size > 100_000:
        print("ECHEC : SQL trop volumineux")
        return 1
    try:
        source = SQL.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError):
        print("ECHEC : SQL illisible")
        return 1

    if args.self_test:
        try:
            self_test(source)
            return 0
        except AssertionError as exc:
            print("ECHEC : " + str(exc))
            return 1
    errors = inspect(source)
    if errors:
        for error in errors:
            print("ECHEC : " + error)
        return 1
    print("OK : huit RPC sensibles protégées par vérification de session, candidat ROLLBACK-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
