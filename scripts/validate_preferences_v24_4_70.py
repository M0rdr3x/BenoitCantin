#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819001526_sinjira_v24_4_70_self_only_preferences.sql'
CONV=ROOT/'supabase/migrations/20260819003353_sinjira_v24_4_70_preferences_schema_convergence.sql'
JS=ROOT/'assets/js/v24-preferences.js'
EXPORT=ROOT/'assets/js/v24-data-control.js'
PAGE=ROOT/'compte/parametres.html'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'


def require(text,markers,label):
    missing=[m for m in markers if m not in text]
    if missing: raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text,markers,label):
    found=[m for m in markers if m in text]
    if found: raise AssertionError(f'{label}: marqueurs interdits: {found}')


def main():
    migration=MIG.read_text('utf-8',errors='ignore')
    convergence=CONV.read_text('utf-8',errors='ignore')
    js=JS.read_text('utf-8',errors='ignore')
    export=EXPORT.read_text('utf-8',errors='ignore')
    page=PAGE.read_text('utf-8',errors='ignore')
    ledger=LEDGER.read_text('utf-8',errors='ignore')

    require(migration,[
        'create table if not exists public.privacy_settings',
        'create table if not exists public.notification_preferences',
        'alter table public.privacy_settings enable row level security',
        'alter table public.notification_preferences enable row level security',
        'revoke all on table public.privacy_settings from public, anon, authenticated',
        'revoke all on table public.notification_preferences from public, anon, authenticated',
        'privacy_settings_self_select','privacy_settings_self_insert','privacy_settings_self_update',
        'notification_preferences_self_select','notification_preferences_self_insert','notification_preferences_self_update',
        'allow_ai_personal_data boolean not null default false check (allow_ai_personal_data = false)',
        "digest_frequency in ('never','daily','weekly')"
    ],'migration préférences')
    forbid(migration,[
        'grant insert on table public.privacy_settings',
        'grant update on table public.privacy_settings',
        'grant delete',
        ' to anon;'
    ],'ACL préférences')

    require(convergence,[
        'add column if not exists created_at',
        "alter table public.privacy_settings alter column show_avatar_public set default false",
        "alter table public.privacy_settings alter column show_online_status set default false",
        "alter table public.privacy_settings alter column allow_messages_from set default 'nobody'",
        "alter table public.notification_preferences alter column security_email set default false",
        "alter table public.notification_preferences alter column market_activity set default false",
        "alter table public.notification_preferences alter column digest_frequency set default 'never'",
        'privacy_settings_allow_ai_personal_data_check',
        'drop policy if exists privacy_settings_own',
        'drop policy if exists notification_preferences_own',
        'revoke all on table public.privacy_settings from public, anon, authenticated',
        'revoke all on table public.notification_preferences from public, anon, authenticated'
    ],'convergence préférences')

    require(js,[
        "await bind('privacy_settings'",
        "await bind('notification_preferences'",
        '.insert({user_id:user.id,...payload})',
        ".update({...payload,updated_at:new Date().toISOString()}).eq('user_id',user.id)",
        'let exists=Boolean(data)'
    ],'runtime préférences')
    forbid(js,['.upsert(', 'user_id:user.id,...payload,updated_at'], 'runtime préférences')

    require(export,[
        "privacy_settings:()=>s.from('privacy_settings')",
        "notification_preferences:()=>s.from('notification_preferences')",
        'complete:errors.length===0'
    ],'export V24.4.70+')
    if "format:'SINJIRA_USER_EXPORT_V24_4_70'" not in export and "format:'SINJIRA_USER_EXPORT_V24_4_83'" not in export:
        raise AssertionError('export V24.4.70+: format canonique V70 ou V83 absent')

    require(page,[
        'settings-v70',
        'v24-preferences.js?v=24.4.70',
        'Elles ne déclenchent aucun courriel, SMS, push ni service payant',
        'name="allow_ai_personal_data"',
        'disabled="" name="allow_ai_personal_data"'
    ],'page paramètres')
    if 'v24-data-control.js?v=24.4.70' not in page and 'v24-data-control.js?v=24.4.83' not in page:
        raise AssertionError('page paramètres: runtime contrôle des données V70+ absent')

    require(ledger,[
        '20260819001526 sinjira_v24_4_70_self_only_preferences',
        '20260819003353 sinjira_v24_4_70_preferences_schema_convergence'
    ],'ledger production')
    print('OK préférences V24.4.70+: stockage self-only, export canonique actuel, RLS, moindre privilège, IA personnelle forcée off et aucun canal payant actif.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
