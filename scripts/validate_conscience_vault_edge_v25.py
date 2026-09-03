#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        raise AssertionError(f'Fichier absent: {path}')
    return target.read_text('utf-8', errors='strict')


def require(text: str, markers: list[str], label: str) -> None:
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text: str, markers: list[str], label: str) -> None:
    found = [marker for marker in markers if marker in text]
    if found:
        raise AssertionError(f'{label}: marqueurs interdits: {found}')


def function_block(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise AssertionError(f'Bloc absent: {start_marker}')
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        raise AssertionError(f'Fin de bloc absente: {end_marker}')
    return text[start:end]


def main() -> int:
    auth = read('supabase/functions/_shared/auth.ts')
    edge = read('supabase/functions/conscience-vault/index.ts')
    config = read('supabase/config.toml')
    migration = read('supabase/migrations/20260902223000_sinjira_v25_0_personal_consciousness_vault.sql')

    require(auth, [
        'getAuthenticatorAssuranceLevel(token)',
        'export async function requiredVaultUser',
        'await assertVaultMfa(context)',
        'return { ...context, aal }',
    ], 'contexte authentifié du coffre')

    vault_auth = function_block(
        auth,
        'async function assertVaultMfa',
        'export async function optionalUser'
    )
    require(vault_auth, [
        'await assuranceLevel(context)',
        "aal.nextLevel !== 'aal2'",
        "aal.currentLevel !== 'aal2'",
        "throw new Error('MFA_SETUP_REQUIRED')",
        "throw new Error('MFA_REQUIRED')",
    ], 'AAL2 obligatoire du coffre')
    forbid(vault_auth, [
        'sensitiveStepUpEnabled(context)',
        ".from('security_user_settings')",
    ], 'AAL2 du coffre ne dépend pas des préférences')

    require(edge, [
        "import { requiredVaultUser } from '../_shared/auth.ts'",
        'await requiredVaultUser(req)',
        'async function readBoundedJson(req: Request)',
        "contentType !== 'application/json'",
        'req.body.getReader()',
        'total > MAX_REQUEST_BYTES',
        "throw new Error('REQUEST_TOO_LARGE')",
        "new TextDecoder('utf-8', { fatal: true })",
        "'Cache-Control': 'private, no-store, max-age=0'",
        "'X-Content-Type-Options': 'nosniff'",
        "'Referrer-Policy': 'no-referrer'",
        "['user_id', 'target_user_id', 'subject_user_id']",
        "throw new Error('CLIENT_IDENTITY_FORBIDDEN')",
        "p_action: 'conscience_vault'",
        "security?.risk_model_version !== 'v25.0'",
        'security?.mandatory_step_up !== true',
        'security?.requires_step_up !== true',
        "p_risk_action: 'conscience_vault'",
        "p_risk_model_version: 'v25.0'",
        "service.rpc('service_conscience_open_session'",
        "service.rpc('service_conscience_list_entries'",
        "service.rpc('service_conscience_create_entry'",
        "service.rpc('service_conscience_update_entry'",
        "service.rpc('service_conscience_delete_entry'",
        "service.rpc('service_conscience_revoke_session'",
        "Deno.env.get('SINJIRA_TRUST_GEO_HEADERS') !== 'true'",
        "req.headers.get('cf-ipcountry')",
        "req.headers.get('x-sinjira-region')",
        'client_geo_accepted: false',
        'raw_ip_stored: false',
        'gps_used: false',
        "console.warn('[conscience-vault] opération refusée', code)",
    ], 'contrat Edge du Registre personnel')

    forbid(edge, [
        'requiredSensitiveUser',
        ".schema('private')",
        ".from('conscience_entries')",
        ".from('conscience_vault_sessions')",
        ".from('conscience_vault_audit')",
        'await req.json()',
        'body.user_id',
        'body?.user_id',
        'body.target_user_id',
        'body?.target_user_id',
        'body.country_code',
        'body?.country_code',
        'body.region_code',
        'body?.region_code',
        'console.log(body',
        'console.log(parsed',
        'console.log(payload',
        'console.error(error',
        'console.error(error)',
    ], 'aucun contournement, corps non borné ou journal de contenu dans Edge')

    config_block = function_block(
        config,
        '[functions.conscience-vault]',
        '[functions.life-story-export]'
    )
    require(config_block, ['verify_jwt = true'], 'JWT Supabase obligatoire pour conscience-vault')
    forbid(config_block, ['verify_jwt = false'], 'conscience-vault ne peut jamais être public')

    require(migration, [
        'revoke all on table private.conscience_entries from public, anon, authenticated, service_role',
        "p_risk_action is distinct from 'conscience_vault'",
        "raise exception 'RISK_SCOPE_REQUIRED'",
        "risk_model_version = 'v25.0'",
        "check (expires_at <= issued_at + interval '10 minutes')",
    ], 'barrières SQL du coffre')

    print('OK coffre V25: JWT + AAL2 obligatoire, corps borné, no-store, identité dérivée, risque conscience_vault et RPC étroites sans accès direct au schéma private.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
