#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / 'supabase' / 'migrations' / '20260908150000_sinjira_v25_live_social_share_codes.sql'
TEST = ROOT / 'supabase' / 'tests' / 'live_social_share_codes_v25.test.sql'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-live-social-safety-v25.yml'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f'ERREUR codes de partage En direct V25: {message}')


def main() -> int:
    migration = MIGRATION.read_text('utf-8')
    test = TEST.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')
    ml = migration.lower()
    tl = test.lower()
    wl = workflow.lower()

    for marker in (
        'create table if not exists private.social_live_room_share_codes',
        'code_hash text not null unique',
        "check (code_hash ~ '^[a-f0-9]{64}$')",
        "status in ('active','used','revoked','expired')",
        "interval '24 hours'",
        'alter table private.social_live_room_share_codes enable row level security',
        'revoke all on table private.social_live_room_share_codes from public,anon,authenticated,service_role',
        'social_live_share_code_create',
        'social_live_share_code_list',
        'social_live_share_code_revoke',
        'social_live_share_code_redeem',
        "visibility='private'",
        'owner_user_id=v_user',
        'sinjira_age_band',
        'sinjira_can_social_interact',
        'social_is_blocked',
        'social_is_suspended(v_code.creator_user_id)',
        'pg_advisory_xact_lock',
        'for update',
        'gen_random_bytes(32)',
        "digest(v_raw,'sha256')",
        "'display_once',true",
        'social_live_share_code_rate_limit',
        'social_live_share_code_active_limit',
        'insert into public.social_live_room_members',
        'insert into private.social_live_room_invites',
        "set status='used',closed_at=now()",
        'language sql security invoker',
    ):
        require(marker in ml, f'marqueur migration absent: {marker}')

    # Un code de partage ne doit jamais devenir un annuaire social ou une passerelle
    # vers l'identité technique privée.
    redeem_body = ml.split('social_live_share_code_redeem(', 1)[1]
    for forbidden in (
        'social_profiles',
        'account_identities',
        'redeemed_by_user_id',
        'inet_client_addr(',
        'request.headers',
        'latitude',
        'longitude',
        'gps',
    ):
        require(forbidden not in redeem_body, f'collecte/résolution interdite dans le rachat: {forbidden}')

    # Le secret brut et l'identité du rédempteur ne sont jamais des colonnes durables.
    table_def = ml.split('create table if not exists private.social_live_room_share_codes', 1)[1].split(');', 1)[0]
    for forbidden_column in ('\n  code text', '\n  raw_code ', '\n  secret ', '\n  token ', 'redeemed_by_user_id'):
        require(forbidden_column not in table_def, f'colonne sensible interdite: {forbidden_column.strip()}')

    require('select plan(37);' in tl, 'plan pgTAP attendu à 37 assertions')
    for marker in (
        "not has_table_privilege('authenticated','private.social_live_room_share_codes','select')",
        "not has_table_privilege('service_role','private.social_live_room_share_codes','select')",
        "column_name in ('code','raw_code','secret','token')",
        "column_name='redeemed_by_user_id'",
        "not (select prosecdef from pg_proc where oid='public.social_live_share_code_create(uuid)'::regprocedure)",
        "not (select prosecdef from pg_proc where oid='public.social_live_share_code_redeem(text)'::regprocedure)",
        'gen_random_bytes(32)',
        "digest(v_raw,'sha256')",
        'social_live_share_code_unavailable',
        'social_profiles',
        'account_identities',
        'aucun uuid utilisateur',
        'sans persister l identité du rédempteur',
    ):
        require(marker in tl, f'contrat pgTAP absent: {marker}')

    for marker in (
        'python scripts/validate_live_social_share_codes_v25.py',
        'supabase test db supabase/tests/live_social_share_codes_v25.test.sql --local',
    ):
        require(marker in wl, f'workflow sécurité incomplet: {marker}')

    for forbidden in ('--linked', 'supabase_access_token', 'supabase_db_password', 'inputs.apply', 'db push'):
        require(forbidden not in wl, f'workflow ne doit pas viser production: {forbidden}')

    print('OK En direct V25: codes bearer 256 bits, SHA-256 seul en stockage, 24 h, usage unique, strict-no-direct, sans identité de rédempteur/annuaire/UUID/IP/GPS et testés uniquement sur Supabase local.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
