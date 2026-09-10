#!/usr/bin/env python3
"""Contrat statique V25: une device_key ne transporte jamais la confiance entre sessions."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_REL = "supabase/migrations/20260910150000_sinjira_v25_device_trust_session_rebind_security_hardening.sql"
SMOKE_REL = "scripts/smoke_device_trust_session_rebind_local.py"
VALIDATOR_REL = "scripts/validate_device_trust_session_rebind.py"
CLIENT_WORKFLOW_REL = ".github/workflows/sinjira-device-challenge-client-boundary-v25.yml"
CONTINUITY_WORKFLOW_REL = ".github/workflows/sinjira-device-challenge-continuity-v25.yml"


def errors_for(migration: str, smoke: str, client: str, continuity: str) -> list[str]:
    errors: list[str] = []

    migration_required = (
        "create or replace function sinjira_security_internal.security_register_device(",
        "auth.jwt()->>'session_id'",
        "where user_id=v_user and device_key=p_device_key\n  for update;",
        "v_rebound_trust := (v_row.is_trusted or v_row.is_primary)",
        "v_session is null or v_row.last_session_id is distinct from v_session",
        "is_trusted=case when v_rebound_trust then false else is_trusted end",
        "is_primary=case when v_rebound_trust then false else is_primary end",
        "last_session_id=v_session",
        "'device_trust_session_rebind'",
        "revoke all on function sinjira_security_internal.security_register_device(text,text,text,text) from public, anon;",
        "grant execute on function sinjira_security_internal.security_register_device(text,text,text,text) to authenticated, service_role;",
    )
    for marker in migration_required:
        if marker not in migration:
            errors.append(f"migration rebind incomplète: {marker}")
    if "create or replace function public.security_register_device(" in migration:
        errors.append("la migration rebind ne doit pas recréer une implémentation privilégiée dans public")
    if "is_trusted=true" in migration or "is_primary=true" in migration:
        errors.append("la migration rebind ne doit jamais accorder directement de confiance")
    for forbidden in ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD", "service_role_key", "--linked"):
        if forbidden.lower() in migration.lower():
            errors.append(f"surface production/secrète interdite dans la migration: {forbidden}")

    smoke_required = (
        "aal1_b = sign_in(email, password)",
        'jwt_claims(aal1_b).get("aal") == "aal1"',
        'rebound.get("is_trusted") is False',
        'rebound.get("is_primary") is False',
        '"CURRENT_DEVICE_REQUIRED"',
        '"AAL2_REQUIRED"',
        "aal2_b = verify_totp(aal1_b, factor_id, secret)",
        'recovered.get("is_trusted") is True and recovered.get("is_primary") is True',
        '"device_key" not in recovered and "last_session_id" not in recovered',
    )
    for marker in smoke_required:
        if marker not in smoke:
            errors.append(f"smoke rebind incomplet: {marker}")
    for forbidden in ("SUPABASE_SERVICE_ROLE_KEY", "SERVICE_ROLE_KEY", "SUPABASE_ACCESS_TOKEN", "gpvivleexywljowcqkru", "/auth/v1/admin/", "--no-verify-jwt"):
        if forbidden in smoke:
            errors.append(f"surface privilégiée/production interdite dans le smoke: {forbidden}")
    if "127.0.0.1" not in smoke or "localhost" not in smoke:
        errors.append("le smoke rebind doit rester strictement borné à Supabase local")

    migration_trigger = f"      - '{MIGRATION_REL}'"
    validator_trigger = f"      - '{VALIDATOR_REL}'"
    smoke_trigger = f"      - '{SMOKE_REL}'"
    if client.count(migration_trigger) != 2:
        errors.append("la migration rebind doit déclencher le workflow frontière client sur PR et push")
    if client.count(validator_trigger) != 2:
        errors.append("le validateur rebind doit déclencher le workflow frontière client sur PR et push")
    for command in (
        "python3 scripts/validate_device_trust_session_rebind.py --self-test",
        "python3 scripts/validate_device_trust_session_rebind.py",
    ):
        if command not in client:
            errors.append(f"workflow frontière client sans contrôle rebind: {command}")

    if continuity.count(smoke_trigger) != 2:
        errors.append("le smoke rebind doit déclencher le workflow de continuité sur PR et push")
    if continuity.count(validator_trigger) != 2:
        errors.append("le validateur rebind doit déclencher le workflow de continuité sur PR et push")
    if continuity.count("      - 'supabase/migrations/**security**.sql'") != 2:
        errors.append("les migrations security doivent continuer à déclencher la continuité sur PR et push")
    if "python3 scripts/validate_device_trust_session_rebind.py" not in continuity:
        errors.append("workflow continuité sans validation statique du rebind")
    if "python3 scripts/smoke_device_trust_session_rebind_local.py" not in continuity:
        errors.append("workflow continuité sans smoke HTTP du rebind")
    for text, label in ((client, "frontière client"), (continuity, "continuité")):
        for forbidden in ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD", "environment: production", "supabase db push", "--linked"):
            if forbidden in text:
                errors.append(f"{label}: primitive distante/production interdite: {forbidden}")

    return errors


def load() -> tuple[str, str, str, str]:
    paths = [ROOT / MIGRATION_REL, ROOT / SMOKE_REL, ROOT / CLIENT_WORKFLOW_REL, ROOT / CONTINUITY_WORKFLOW_REL]
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("ERREUR rebind appareil: fichiers manquants: " + ", ".join(missing))
    return tuple(path.read_text("utf-8") for path in paths)  # type: ignore[return-value]


def self_test(migration: str, smoke: str, client: str, continuity: str) -> None:
    mutations = {
        "verrou SQL retiré": (migration.replace("\n  for update;", ";", 1), smoke, client, continuity),
        "mismatch session retiré": (migration.replace("v_row.last_session_id is distinct from v_session", "v_row.last_session_id = v_session", 1), smoke, client, continuity),
        "reset trusted retiré": (migration.replace("is_trusted=case when v_rebound_trust then false else is_trusted end", "is_trusted=is_trusted", 1), smoke, client, continuity),
        "reset primary retiré": (migration.replace("is_primary=case when v_rebound_trust then false else is_primary end", "is_primary=is_primary", 1), smoke, client, continuity),
        "événement retiré": (migration.replace("'device_trust_session_rebind'", "'device_seen'", 1), smoke, client, continuity),
        "preuve AAL1 retirée": (migration, smoke.replace('rebound.get("is_trusted") is False', 'rebound.get("is_trusted") is True', 1), client, continuity),
        "preuve AAL2 retirée": (migration, smoke.replace('"AAL2_REQUIRED"', '"AUTH_REQUIRED"', 1), client, continuity),
        "trigger migration client retiré": (migration, smoke, client.replace(f"      - '{MIGRATION_REL}'\n", "", 1), continuity),
        "trigger smoke continuité retiré": (migration, smoke, client, continuity.replace(f"      - '{SMOKE_REL}'\n", "", 1)),
        "smoke runtime continuité retiré": (migration, smoke, client, continuity.replace("python3 scripts/smoke_device_trust_session_rebind_local.py", "echo rebind-retire", 1)),
    }
    for label, texts in mutations.items():
        if not errors_for(*texts):
            raise SystemExit(f"ERREUR rebind appareil: mutation critique non détectée: {label}")
    print(f"OK: {len(mutations)} mutations critiques rebind appareil détectées")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    migration, smoke, client, continuity = load()
    if args.self_test:
        self_test(migration, smoke, client, continuity)
        return 0
    errors = errors_for(migration, smoke, client, continuity)
    if errors:
        print("Contrat rebind appareil V25: ÉCHEC")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Contrat rebind appareil V25: OK")
    print("- une device_key réutilisée sous une autre session perd trusted/primary sous verrou de ligne")
    print("- l'ancienne session ne peut pas reprendre la confiance; la nouvelle exige AAL2")
    print("- la récupération humaine après TOTP reste possible")
    print("- CI PR/push entièrement locale, sans secrets ni opérations Supabase liées")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
