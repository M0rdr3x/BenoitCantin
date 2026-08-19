#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260819001526_sinjira_v24_4_70_self_only_preferences.sql'
JS=ROOT/'assets/js/v24-preferences.js'
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
    js=JS.read_text('utf-8',errors='ignore')
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

    require(js,[
        "await bind('privacy_settings'",
        "await bind('notification_preferences'",
        '.insert({user_id:user.id,...payload})',
        ".update({...payload,updated_at:new Date().toISOString()}).eq('user_id',user.id)",
        'let exists=Boolean(data)'
    ],'runtime préférences')
    forbid(js,['.upsert(', 'user_id:user.id,...payload,updated_at'], 'runtime préférences')

    require(page,[
        'settings-v70',
        'v24-preferences.js?v=24.4.70',
        'Elles ne déclenchent aucun courriel, SMS, push ni service payant',
        'name="allow_ai_personal_data"',
        'disabled="" name="allow_ai_personal_data"'
    ],'page paramètres')

    require(ledger,['20260819001526 sinjira_v24_4_70_self_only_preferences'],'ledger production')
    print('OK préférences V24.4.70: stockage self-only, RLS, moindre privilège, IA personnelle forcée off et aucun canal payant actif.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
