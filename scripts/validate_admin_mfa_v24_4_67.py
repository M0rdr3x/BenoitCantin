#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_ADMIN = [
    'admin-analytics',
    'admin-console',
    'admin-license-codes',
    'admin-reports',
    'admin-sinjira-v18',
    'admin-social-v20',
    'admin-users',
]


def read(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        raise AssertionError(f'Fichier absent: {path}')
    return p.read_text('utf-8', errors='ignore')


def require(text: str, markers: list[str], label: str) -> None:
    missing = [m for m in markers if m not in text]
    if missing:
        raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text: str, markers: list[str], label: str) -> None:
    found = [m for m in markers if m in text]
    if found:
        raise AssertionError(f'{label}: marqueurs interdits: {found}')


def main() -> int:
    auth = read('supabase/functions/_shared/auth.ts')
    users = read('supabase/functions/admin-users/index.ts')
    literary = read('supabase/functions/admin-sinjira-v18/index.ts')
    browser = read('assets/js/sinjira-supabase.js')
    health = read('assets/js/v24-admin-health.js')

    for name in ACTIVE_ADMIN:
        require(auth, [f"'{name}'"], 'inventaire endpoints admin')

    require(auth, [
        'ACTIVE_ADMIN_FUNCTIONS',
        'edgeFunctionName(req)',
        'assertAdminMfa(context)',
        "service.rpc('is_sinjira_admin'",
        'getAuthenticatorAssuranceLevel(token)',
        "aal.nextLevel === 'aal2'",
        "aal.currentLevel !== 'aal2'",
        "throw new Error('MFA_REQUIRED')",
        "throw new Error('MFA_STATE_UNAVAILABLE')",
        'export async function requiredAdmin',
    ], 'garde serveur administrateur')

    require(users, [
        "import { requiredAdmin } from '../_shared/auth.ts'",
        'await requiredAdmin(req)',
        "code:'MFA_REQUIRED'",
        "code:'MFA_STATE_UNAVAILABLE'",
    ], 'admin-users partagé')
    forbid(users, [
        "createClient } from 'npm:@supabase/supabase-js@2'",
        'function serviceClient()',
        "Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')",
    ], 'admin-users ne doit plus dupliquer auth')

    require(browser, [
        "v24-admin-health.js?v=24.4.67",
        'MFA_STATE_UNAVAILABLE',
    ], 'chargeur garde admin navigateur')
    require(health, [
        "ADMIN_SECURITY_VERSION='24.4.67'",
        'await requireUser()',
        "import {getSupabase,getCurrentUser,isSinjiraOwner,escapeHtml,requireUser}",
    ], 'garde navigateur administration')

    require(literary, [
        "if(a==='generate_character')",
        "code:'REMOTE_AI_DISABLED_FREE_ONLY'",
        'remote_ai:false',
        'free_only:true',
        "code:'MFA_REQUIRED'",
        "code:'MFA_STATE_UNAVAILABLE'",
    ], 'administration littéraire gratuite')
    forbid(literary, [
        "Deno.env.get('OPENAI_API_KEY')",
        'api.openai.com',
        "fetch('https://api.openai.com",
        "factorType:'phone'",
        'twilio',
        'stripe',
    ], 'aucun chemin payant actif dans admin-sinjira-v18')

    print('OK admin V24.4.67: 7 endpoints centralisés, MFA AAL2 progressif fail-closed et IA distante verrouillée en mode gratuit.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
