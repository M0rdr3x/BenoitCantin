#!/usr/bin/env python3
"""Contrat statique : refuser les JWT de sessions révoquées pour les RPC sensibles.

N'exécute AUCUNE fonction SQL, ne lit AUCUN compte et ne se connecte à aucune
base. Un test d'intégration staging avec sessions réelles reste obligatoire.
"""
from __future__ import annotations

import argparse
import hashlib
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
    "(s.not_after IS NULL OR s.not_after > clock_timestamp())",
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


# SHA-256 des définitions actives pg_get_functiondef, avec simple strip()
# en lecture seule au 8 novembre 2026. Toute dérive métier exige revue.
SOURCE_SHA256 = {
    "security_after_password_recovery": "1ced27350a3f05818e3bfebb03ebd5791fc9a5e0e566505a0d4c99ce79596a3a",
    "security_compromise_account": "264a472bdd9f23df25aa9d26adaf00601e2a6a49f852c86bdb4253f3d16d8394",
    "security_report_lost_device": "a8e31f1f9c68a6d4ec06fe78f52ebc81823b69d47f1e67bf227175c93b6b28f4",
    "security_resolve_connection_challenge": "ca24404955fb7ee9a3c0f75e6171beb0e7000f00841e256070802b0d31c09f07",
    "security_resolve_connection_challenge_mfa": "41717bb023f0415f8a986e7cf7b5f704e587e4d8877d39a3bc715f2fe0f35c10",
    "security_revoke_device": "fcdf34e4f92a076cd3e8237a6ec17b4d9a784ed6ae116305a8595a7ab5340bbd",
    "security_set_device_trust": "9993426ee89dff625687c09a529776d1b9f3809412f3affa3945b26a83179c84",
    "security_update_settings": "c11672c4df85e1a1ee3bb9e26b7bdfe46a2fd6776aa5f8062bc8dad5ba3a9dc2",
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
    raw_pieces = source.split("CREATE OR REPLACE FUNCTION sinjira_security_internal.")
    if len(pieces) != len(FUNCTION_NAMES) + 1 or len(raw_pieces) != len(pieces):
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
    for part, raw_part in zip(pieces[1:], raw_pieces[1:]):
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
        if name == "security_set_device_trust" and "and c.request_session_id=v_session" not in part:
            errors.append("Confirmation de confiance non liée à la session demandeuse")
        if "v_user uuid := auth.uid()" not in part:
            errors.append("Identité auth.uid() historique absente : " + name)
        if "RETURNS jsonb" not in part:
            errors.append("Type de retour historique modifié : " + name)

        # Seule l'insertion d'un contrôle de session est autorisée.
        # Reconstituer les octets de pg_get_functiondef à partir du SQL
        # de la PR et comparer le SHA-256 fourni par PostgreSQL en lecture.
        stop = raw_part.find("$function$;")
        if stop < 0:
            errors.append("Fin de fonction absente pour empreinte : " + name)
        else:
            original = (
                "CREATE OR REPLACE FUNCTION sinjira_security_internal."
                + raw_part[:stop] + "$function$"
            )
            original = original.replace("\n  " + SESSION_CALL, "", 1).strip()
            actual_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
            if actual_hash != SOURCE_SHA256[name]:
                errors.append("Corps historique modifié hors garde de session : " + name)

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
        ("absence de date d'expiration", "(s.not_after IS NULL OR s.not_after > clock_timestamp())", "TRUE"),
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
        ("challenge d'une autre session utilisé pour accorder la confiance",
         "and c.request_session_id=v_session", "and c.request_session_id is not null"),
        ("logique métier historique modifiée",
         "where id=p_device_id and user_id=v_user",
         "where user_id=v_user"),
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
