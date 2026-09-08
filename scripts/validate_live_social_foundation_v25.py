#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / 'supabase' / 'migrations' / '20260908120000_sinjira_v25_live_social_foundation.sql'
REALTIME_MIGRATION = ROOT / 'supabase' / 'migrations' / '20260908121000_sinjira_v25_live_social_realtime_eligibility.sql'
HELPER_MIGRATION = ROOT / 'supabase' / 'migrations' / '20260908122000_sinjira_v25_live_social_helper_invoker.sql'
TEST = ROOT / 'supabase' / 'tests' / 'live_social_foundation_v25.test.sql'
REALTIME_TEST = ROOT / 'supabase' / 'tests' / 'live_social_realtime_eligibility_v25.test.sql'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-live-social-foundation-v25.yml'
COMMUNITY = ROOT / 'compte' / 'communaute.html'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f'ERREUR En direct V25: {message}')


def main() -> int:
    migration = MIGRATION.read_text('utf-8')
    realtime_migration = REALTIME_MIGRATION.read_text('utf-8')
    helper_migration = HELPER_MIGRATION.read_text('utf-8')
    test = TEST.read_text('utf-8')
    realtime_test = REALTIME_TEST.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')
    community = COMMUNITY.read_text('utf-8')
    low = migration.lower()

    for marker in (
        'create table if not exists public.social_live_rooms',
        'create table if not exists public.social_live_room_members',
        'create table if not exists public.social_live_messages',
        'alter table public.social_live_rooms enable row level security',
        'alter table public.social_live_room_members enable row level security',
        'alter table public.social_live_messages enable row level security',
        'default auth.uid()',
        'default public.sinjira_my_age_band()',
        'public.social_live_is_room_member(p_room_id uuid)',
        'or public.social_live_is_room_member(id)',
        'social_live_rooms_read',
        'social_live_members_public_join',
        'social_live_messages_read',
        'social_live_messages_insert',
        'public.sinjira_can_social_interact',
        'public.social_is_blocked',
        'public.social_is_suspended',
        'public.has_accepted_community_rules',
        'pg_advisory_xact_lock',
        'social_live_rate_limit_burst',
        'social_live_rate_limit_minute',
        'social_live_duplicate_message',
        'social_live_author_mismatch',
        'realtime.send(',
        "'sinjira-live:'||new.room_id::text",
        'on realtime.messages as restrictive',
        "realtime.messages.extension='presence'",
        "realtime.messages.extension in ('broadcast','presence')",
    ):
        require(marker.lower() in low, f'marqueur migration absent: {marker}')

    require('social_live_presence' not in low, 'Presence ne doit pas devenir une table persistante')
    require('grant insert(owner_user_id' not in low, 'owner_user_id ne doit jamais être injectable')
    require('grant insert(audience' not in low, 'audience ne doit jamais être injectable')
    require('grant insert(room_id,user_id' not in low, 'user_id adhésion ne doit jamais être injectable')
    require('grant insert(room_id,user_id,body' not in low, 'user_id message ne doit jamais être injectable')
    for forbidden in ('inet_client_addr(', 'request.headers', 'latitude', 'longitude', 'gps'):
        require(forbidden not in low, f'collecte interdite dans En direct: {forbidden}')

    realtime_low = realtime_migration.lower()
    for marker in (
        'has_accepted_community_rules',
        'social_is_suspended',
        'sinjira_my_age_band',
        'social_is_blocked',
        'on realtime.messages as restrictive',
    ):
        require(marker in realtime_low, f'durcissement Realtime absent: {marker}')

    helper_low = helper_migration.lower()
    require('alter function public.social_live_is_room_member(uuid) security invoker' in helper_low,
            'le helper membership doit finir en SECURITY INVOKER')
    require('grant execute on function public.social_live_is_room_member(uuid) to authenticated,service_role' in helper_low,
            'le helper invoker doit être exécutable uniquement par les rôles attendus')

    fn_start = low.index('create or replace function public.social_live_notify_message_insert()')
    fn_end = low.index('revoke all on function public.social_live_notify_message_insert()', fn_start)
    notify = low[fn_start:fn_end]
    require("'message_id'" in notify, 'Broadcast doit transporter message_id')
    require("'body'" not in notify, 'Broadcast ne doit jamais transporter le corps')
    require(',\n    true\n  );' in migration[fn_start:fn_end], 'Broadcast doit rester privé')

    for marker in (
        'select plan(46);',
        "to_regclass('public.social_live_presence') is null",
        "not has_column_privilege('authenticated','public.social_live_rooms','owner_user_id','insert')",
        "not has_column_privilege('authenticated','public.social_live_messages','user_id','insert')",
        "qual ilike '%social_live_is_room_member%'",
        "permissive='restrictive'",
        "with_check not ilike '%broadcast%'",
    ):
        require(marker.lower() in test.lower(), f'contrat pgTAP absent: {marker}')

    for marker in (
        'select plan(6);',
        "not (select prosecdef from pg_proc where oid='public.social_live_is_room_member(uuid)'::regprocedure)",
        "has_function_privilege('authenticated','public.social_live_is_room_member(uuid)','execute')",
    ):
        require(marker.lower() in realtime_test.lower(), f'contrat helper/Realtime absent: {marker}')

    for marker in (
        'python scripts/validate_live_social_foundation_v25.py',
        'python scripts/validate_social_home_v25.py',
        'python scripts/validate_supabase.py',
        'supabase start',
        'supabase test db supabase/tests/live_social_foundation_v25.test.sql --local',
        'supabase test db supabase/tests/live_social_realtime_eligibility_v25.test.sql --local',
        'supabase stop --no-backup',
    ):
        require(marker in workflow, f'workflow local incomplet: {marker}')
    for forbidden in ('--linked', 'SUPABASE_ACCESS_TOKEN', 'SUPABASE_DB_PASSWORD', 'inputs.apply', 'db push'):
        require(forbidden not in workflow, f'workflow En direct ne doit jamais viser la production: {forbidden}')

    require('Prochaine étape · Realtime sécurisé' in community, 'la carte #249 doit rester en aperçu avant preuve CI/runtime')
    require('Cette carte n’affiche pas de faux statut en direct' in community, 'aucun faux temps réel avant activation du runtime')

    print('OK En direct V25: fondation RLS fail-closed, helper self-only SECURITY INVOKER, identité serveur, anti-spam par compte, Broadcast minimal et Presence privée; production non touchée.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
