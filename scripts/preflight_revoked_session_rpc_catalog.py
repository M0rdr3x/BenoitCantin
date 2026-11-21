#!/usr/bin/env python3
"""Contrôle read-only AVANT/APRÈS promotion des huit RPC d'appareils SINJIRA.

N'exécute aucune requête SQL : émet une sélection de métadonnées pg_catalog
ou vérifie un JSON de catalogue exporté en lecture seule. Ne demande aucun
secret, compte, jeton ou contenu des tables auth.sessions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from validate_revoked_session_rpc_candidate import FUNCTION_NAMES, SOURCE_SHA256

# Noms issus du contrat gelé du candidat, jamais d'une entrée non fiable.
assert len(FUNCTION_NAMES) == len(set(FUNCTION_NAMES)) == 8
assert all(re.fullmatch(r"security_[a-z_]+", name) for name in FUNCTION_NAMES)

SQL = r"""
SELECT COALESCE(jsonb_agg(to_jsonb(c) ORDER BY c.function_name), '[]'::jsonb) AS snapshot
FROM (
  SELECT p.proname AS function_name,
         n.nspname AS schema_name,
         encode(extensions.digest(
           btrim(pg_get_functiondef(p.oid), E' \n\r\t'), 'sha256'
         ), 'hex') AS definition_sha256,
         p.prosecdef AS security_definer,
         has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_execute,
         has_function_privilege('authenticated', p.oid, 'EXECUTE') AS authenticated_execute,
         (position('private.security_require_current_auth_session('
                   IN pg_get_functiondef(p.oid)) > 0) AS session_guard_present,
         (
           SELECT count(*) = 3
           FROM pg_catalog.pg_attribute a
           WHERE a.attrelid = 'auth.sessions'::regclass
             AND a.attnum > 0 AND NOT a.attisdropped
             AND (
               (a.attname = 'id' AND a.atttypid = 'uuid'::regtype)
               OR (a.attname = 'user_id' AND a.atttypid = 'uuid'::regtype)
               OR (a.attname = 'not_after' AND a.atttypid = 'timestamptz'::regtype)
             )
         ) AS session_contract_ok
  FROM pg_catalog.pg_proc p
  JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'sinjira_security_internal'
    AND p.proname IN (
      'security_after_password_recovery',
      'security_compromise_account',
      'security_report_lost_device',
      'security_resolve_connection_challenge',
      'security_resolve_connection_challenge_mfa',
      'security_revoke_device',
      'security_set_device_trust',
      'security_update_settings'
    )
) AS c;
""".strip()


def check_snapshot(rows: object, *, postflight: bool = False) -> list[str]:
    """Fail closed on missing/doubled RPCs, drift, privileges, or missing session guard."""
    if isinstance(rows, dict) and set(rows) == {"snapshot"}:
        rows = rows["snapshot"]
    if not isinstance(rows, list):
        return ["Format incorrect : une liste JSON de huit fonctions est requise."]
    if len(rows) != len(FUNCTION_NAMES):
        return [f"Nombre de fonctions incorrect : {len(rows)}/8."]
    by_name: dict[str, dict] = {}
    errors: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            errors.append("Entrée non structurée dans le catalogue.")
            continue
        name = row.get("function_name")
        if not isinstance(name, str) or name not in SOURCE_SHA256:
            errors.append("Fonction étrangère ou nom invalide.")
            continue
        if name in by_name:
            errors.append(f"Fonction en double : {name}.")
            continue
        by_name[name] = row

    for name in FUNCTION_NAMES:
        if name not in by_name:
            errors.append(f"Fonction attendue absente : {name}.")
            continue
        row = by_name[name]
        if row.get("schema_name") != "sinjira_security_internal":
            errors.append(f"Schéma RPC inattendu : {name}.")
        if row.get("security_definer") is not True:
            errors.append(f"SECURITY DEFINER absent : {name}.")
        if row.get("anon_execute") is not False:
            errors.append(f"Le rôle anon a une permission inattendue : {name}.")
        if row.get("authenticated_execute") is not True:
            errors.append(f"Contrat authenticated modifié : {name}.")
        if row.get("session_contract_ok") is not True:
            errors.append(f"Colonnes auth.sessions id/user_id/not_after incompatibles : {name}.")
        digest = row.get("definition_sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append(f"Empreinte SHA-256 absente ou malformée : {name}.")
        elif not postflight and digest != SOURCE_SHA256[name]:
            errors.append(f"Dérive de la définition SQL avant promotion : {name}.")
        if row.get("session_guard_present") is not postflight:
            errors.append(
                ("Garde de révocation absent après promotion : "
                 if postflight else "Garde déjà présent : revalider la promotion : ") + name + "."
            )
    return errors


def sample(*, postflight: bool = False) -> list[dict]:
    return [{
        "function_name": name,
        "schema_name": "sinjira_security_internal",
        "definition_sha256": "f" * 64 if postflight else SOURCE_SHA256[name],
        "security_definer": True,
        "anon_execute": False,
        "authenticated_execute": True,
        "session_guard_present": postflight,
        "session_contract_ok": True,
    } for name in FUNCTION_NAMES]


def self_test() -> None:
    assert not check_snapshot(sample())
    assert not check_snapshot({"snapshot": sample()})
    assert not check_snapshot(sample(postflight=True), postflight=True)

    def reject(label: str, rows: list[dict], *, postflight: bool = False) -> None:
        errors = check_snapshot(rows, postflight=postflight)
        if not errors:
            raise AssertionError("Mutation dangereuse acceptée : " + label)

    reject("une RPC manquante", sample()[:-1])
    reject("RPC dupliquée", sample()[:-1] + [sample()[0]])
    for field, value in (
        ("function_name", "security_unknown"),
        ("schema_name", "public"),
        ("definition_sha256", "0" * 64),
        ("security_definer", False),
        ("anon_execute", True),
        ("authenticated_execute", False),
        ("session_guard_present", True),
        ("session_contract_ok", False),
    ):
        rows = sample()
        rows[0][field] = value
        reject("dérive " + field, rows)

    for field, value in (
        ("session_guard_present", False),
        ("security_definer", False),
        ("anon_execute", True),
        ("session_contract_ok", False),
    ):
        rows = sample(postflight=True)
        rows[0][field] = value
        reject("postflight " + field, rows, postflight=True)

    # Le contrôle est une lecture de catalogue, jamais un script de déploiement.
    assert "FROM pg_catalog.pg_proc" in SQL
    assert "pg_get_functiondef" in SQL
    assert "FROM pg_catalog.pg_attribute" in SQL
    assert "auth.sessions'::regclass" in SQL
    assert "jsonb_agg" in SQL
    assert not re.search(r"(?im)^\s*(?:UPDATE|DELETE|INSERT|CREATE|DROP|ALTER|GRANT|REVOKE|COPY)\b", SQL)
    print("PASS : 16 mutations de catalogue refusées, audit SQL read-only, contrôle avant/après.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Préflight de huit RPC sensibles en lecture seule")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--emit-sql", action="store_true", help="Imprimer le SELECT du catalogue")
    group.add_argument("--self-test", action="store_true", help="Tests locaux sans accès réseau")
    group.add_argument("--verify-json", type=Path, help="JSON de résultat du SELECT")
    parser.add_argument("--postflight", action="store_true",
                        help="Après déploiement, exiger la présence du nouveau garde")
    args = parser.parse_args()
    if args.emit_sql:
        print(SQL)
        return 0
    if args.self_test:
        self_test()
        return 0
    path: Path = args.verify_json
    try:
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 100_000:
            raise ValueError("Le rapport doit être un fichier JSON local régulier de moins de 100 Ko")
        rows = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ECHEC preflight : {exc}", file=sys.stderr)
        return 1
    errors = check_snapshot(rows, postflight=args.postflight)
    if errors:
        for error in errors:
            print("ECHEC preflight : " + error, file=sys.stderr)
        return 1
    phase = "après" if args.postflight else "avant"
    print(f"PASS : 8/8 RPC autorisées, signatures structurelles intactes ({phase} promotion).")
    if args.postflight:
        print("ATTENTION : ce contrôle ne remplace pas la comparaison des corps SQL ni les tests MFA/JWT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
