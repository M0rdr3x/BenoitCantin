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
    security_ui = read('assets/js/sinjira-security-center-v24-4-98.js')
    config = read('supabase/config.toml')
    migration = read('supabase/migrations/20260902223000_sinjira_v25_0_personal_consciousness_vault.sql')
    continuity = read('supabase/migrations/20260902231500_sinjira_v25_0_conscience_vault_challenge_continuity.sql')
    device_hardening = read('supabase/migrations/20260903213000_sinjira_v25_0_device_key_privacy_and_trust_hardening.sql')
    session_binding = read('supabase/migrations/20260910193000_sinjira_v25_device_challenge_session_binding.sql')

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
        'const { user, service, token } = await requiredVaultUser(req)',
        'const authSessionId = sessionIdFromVerifiedToken(token)',
        "payload?.session_id",
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
        "service.rpc('service_conscience_evaluate_access_session'",
        'p_session_id: authSessionId',
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
        'trusted_device_confirmation',
        "console.warn('[conscience-vault] opération refusée', code)",
    ], 'contrat Edge du Registre personnel')

    forbid(edge, [
        "service.rpc('service_conscience_evaluate_access'",
        "service.rpc('security_evaluate_context'",
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
        'body.session_id',
        'body?.session_id',
        'console.log(body',
        'console.log(parsed',
        'console.log(payload',
        'console.error(error',
        'console.error(error)',
    ], 'aucun contournement, corps non borné, session client ou journal de contenu dans Edge')

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

    require(continuity, [
        'create or replace function public.service_conscience_evaluate_access(',
        'perform private.conscience_vault_require_service_role()',
        'public.security_evaluate_context(',
        "'conscience_vault'",
        "e.action_name='conscience_vault'",
        "v_challenge.status='approved'",
        "v_challenge.status='denied'",
        "v_challenge.status='pending'",
        "interval '30 minutes'",
        'resolver.id=v_challenge.resolved_device_id',
        'resolver.user_id=p_user_id',
        'resolver.id<>v_device.id',
        'resolver.is_trusted',
        'resolver.revoked_at is null',
        "'other_trusted_device_required',true",
        "trusted_device_confirmation_required",
        "approved_recently",
        "denied_recently",
        "'trusted_device_confirmation','pending'",
        "'trusted_device_confirmation','reissued'",
        'revoke all on function public.service_conscience_evaluate_access(uuid,text,text,text,text,text,text)',
        'grant execute on function public.service_conscience_evaluate_access(uuid,text,text,text,text,text,text)',
        'to service_role',
    ], 'continuité historique du challenge appareil fiable')

    require(session_binding, [
        'add column if not exists request_session_id uuid references auth.sessions(id) on delete set null',
        'create or replace function private.security_rebind_service_session(',
        'from auth.sessions s',
        'is_trusted=false',
        'is_primary=false',
        "set status='expired'",
        'create or replace function private.security_challenge_request_session_guard()',
        'new.request_session_id is null',
        "new.status := 'expired'",
        "raise exception 'CHALLENGE_SESSION_REQUIRED'",
        "raise exception 'CHALLENGE_SESSION_MISMATCH'",
        'create trigger security_connection_challenge_session_guard',
        'create or replace function public.service_security_evaluate_context_session(',
        'perform private.security_rebind_service_session(p_user_id,p_device_key,p_session_id)',
        'set request_session_id=p_session_id',
        'create or replace function public.service_conscience_evaluate_access_session(',
        'and c.request_session_id=p_session_id',
        'and last_session_id = p_session_id',
        'revoke execute on function public.service_conscience_evaluate_access(uuid,text,text,text,text,text,text)',
        'from service_role',
        'c.request_session_id=v_session',
    ], 'liaison fail-closed challenge/session V25')

    require(device_hardening, [
        'revoke select on table public.security_devices from authenticated',
        'device_trust_reset_v25',
        'create or replace function sinjira_security_internal.security_list_devices(',
        'create or replace function public.security_list_devices(',
        'security invoker',
        "coalesce(auth.jwt()->>'aal','aal1') <> 'aal2'",
        "raise exception 'AAL2_REQUIRED'",
        'v_row.last_session_id is distinct from v_session',
        "raise exception 'CURRENT_DEVICE_REQUIRED'",
        'v_has_other_trusted',
        "c.status='approved'",
        'resolver.is_trusted',
        "c.resolved_at>now()-interval '30 minutes'",
        "raise exception 'TRUST_CONFIRMATION_REQUIRED'",
        'create or replace function sinjira_security_internal.security_register_device(',
        'create or replace function sinjira_security_internal.security_set_device_trust(',
        'create or replace function sinjira_security_internal.security_revoke_device(',
    ], 'confidentialité device_key et confiance appareil')

    list_block = function_block(
        device_hardening,
        'create or replace function sinjira_security_internal.security_list_devices(',
        'create or replace function public.security_list_devices('
    )
    register_block = function_block(
        device_hardening,
        'create or replace function sinjira_security_internal.security_register_device(',
        '-- Un appareil ne peut devenir fiable'
    )
    trust_block = function_block(
        device_hardening,
        'create or replace function sinjira_security_internal.security_set_device_trust(',
        'create or replace function sinjira_security_internal.security_revoke_device('
    )
    revoke_block = function_block(
        device_hardening,
        'create or replace function sinjira_security_internal.security_revoke_device(',
        '-- Les fonctions internes restent derrière'
    )
    for block, label in [
        (list_block, 'liste appareils'),
        (register_block, 'enregistrement appareil'),
        (trust_block, 'confiance appareil'),
        (revoke_block, 'révocation appareil'),
    ]:
        forbid(block, [
            "'device_key',",
            "'last_session_id',",
            'to_jsonb(v_row)',
        ], f'{label}: aucune clé appareil dans la réponse')

    require(security_ui, [
        "rpc('security_list_devices',{p_current_device_key:meta.device_key})",
        'const current=d.is_current===true',
        'devices.find(d=>d.is_current===true&&!d.revoked_at)',
        "!d.revoked_at&&!d.is_trusted&&current?",
        "message.includes('TRUST_CONFIRMATION_REQUIRED')",
        "message.includes('CURRENT_DEVICE_REQUIRED')",
    ], 'interface sécurité assainie')
    forbid(security_ui, [
        ".from('security_devices')",
        'd.device_key',
        'devices.find(d=>d.device_key',
    ], 'le navigateur ne lit ni ne compare device_key')

    print('OK coffre V25: JWT + AAL2 obligatoire, session JWT liée côté serveur au challenge, corps borné, no-store, identité dérivée, scope conscience_vault, autre appareil fiable et device_key non exposé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
