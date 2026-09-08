#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'supabase' / 'migrations' / '20260908130000_sinjira_v25_live_social_moderation.sql'
INV = ROOT / 'supabase' / 'migrations' / '20260908131000_sinjira_v25_live_social_private_invites.sql'
CONVERGENCE = ROOT / 'supabase' / 'migrations' / '20260908132000_sinjira_v25_live_social_safety_convergence.sql'
MOD_TEST = ROOT / 'supabase' / 'tests' / 'live_social_moderation_v25.test.sql'
INV_TEST = ROOT / 'supabase' / 'tests' / 'live_social_private_invites_v25.test.sql'
GLOBAL_TEST = ROOT / 'supabase' / 'tests' / 'global_safety_compliance_v24_4_83.test.sql'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-live-social-safety-v25.yml'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f'ERREUR sécurité En direct V25: {message}')


def main() -> int:
    moderation = MOD.read_text('utf-8')
    invites = INV.read_text('utf-8')
    convergence = CONVERGENCE.read_text('utf-8')
    mod_test = MOD_TEST.read_text('utf-8')
    inv_test = INV_TEST.read_text('utf-8')
    global_test = GLOBAL_TEST.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')
    ml = moderation.lower()
    il = invites.lower()
    cl = convergence.lower()
    gl = global_test.lower()

    for marker in (
        "check (network in ('real','character','live'))",
        "check (network in ('real','character','dating','account','live'))",
        'sinjira_social_user_internal.social_report_content',
        "p_network='live'",
        'public.social_live_messages',
        'public.social_live_room_members',
        "'snapshot_source','server'",
        "'identity_data_included',false",
        "public.moderation_content_visible('live','message',id)",
        'security invoker',
    ):
        require(marker in ml, f'marqueur modération absent: {marker}')

    for marker in (
        'private.sinjira_report_reason_allowed',
        'priority_safety',
        'private.sinjira_live_message_content_policy_guard',
        "private.sinjira_content_policy_code(new.body,new.user_id,null,'message')",
        'create trigger sinjira_content_policy_guard',
        'revoke all on table private.social_live_room_invites from service_role',
    ):
        require(marker in cl, f'convergence sécurité absente: {marker}')
    require('has_accepted_community_rules' not in cl.split('create or replace function private.sinjira_live_message_content_policy_guard()',1)[0],
            'le signalement de danger ne doit pas dépendre de l acceptation des règles')

    require('create table if not exists private.social_live_room_invites' in il, 'table invitations privée absente')
    for marker in (
        'alter table private.social_live_room_invites enable row level security',
        'revoke all on table private.social_live_room_invites from public,anon,authenticated',
        'social_live_invite_create',
        'social_live_my_invites',
        'social_live_invite_respond',
        'social_live_invite_revoke',
        "visibility='private'",
        'owner_user_id=v_user',
        'sinjira_age_band',
        'sinjira_can_social_interact',
        'social_is_blocked',
        'pg_advisory_xact_lock',
        'social_live_invite_rate_limit',
        'social_live_invite_pending_limit',
        "interval '7 days'",
        'insert into public.social_live_room_members',
        'language sql security invoker',
    ):
        require(marker in il, f'marqueur invitation absent: {marker}')

    for forbidden in ('inet_client_addr(', 'request.headers', 'latitude', 'longitude', 'gps'):
        require(forbidden not in ml, f'collecte interdite dans modération live: {forbidden}')
        require(forbidden not in il, f'collecte interdite dans invitations live: {forbidden}')
        require(forbidden not in cl, f'collecte interdite dans convergence live: {forbidden}')

    require('select plan(21);' in mod_test.lower(), 'plan pgTAP modération inattendu')
    require('select plan(30);' in inv_test.lower(), 'plan pgTAP invitations inattendu')
    require("not (select prosecdef from pg_proc where oid='public.social_report_content" in mod_test.lower(), 'test wrapper signalement invoker absent')
    require('priority_safety' in mod_test.lower(), 'test priorité sécurité V24.4.82 absent')
    require('has_accepted_community_rules' in mod_test.lower(), 'test indépendance signalement/règles absent')
    require("not (select prosecdef from pg_proc where oid='public.social_live_invite_create" in inv_test.lower(), 'test wrapper invitation invoker absent')
    require("not has_table_privilege('authenticated','private.social_live_room_invites','select')" in inv_test.lower(), 'test absence CRUD direct invitations absent')
    require("not has_table_privilege('service_role','private.social_live_room_invites','select')" in inv_test.lower(), 'test strict_no_direct service_role absent')
    require("tgname='sinjira_content_policy_guard'" in gl and ",15," in gl, 'conformité globale doit compter la 15e garde En direct')
    require('les 15 gardes v24.4.82 + en direct restent actives' in gl, 'libellé conformité globale En direct absent')

    for marker in (
        'python scripts/validate_live_social_safety_v25.py',
        'python scripts/validate_live_social_foundation_v25.py',
        'python scripts/validate_production_schema_manifest.py',
        'python scripts/validate_production_migration_ledger.py',
        'supabase start',
        'supabase test db supabase/tests/live_social_moderation_v25.test.sql --local',
        'supabase test db supabase/tests/live_social_private_invites_v25.test.sql --local',
        'supabase test db supabase/tests/minor_exploitation_safety_v24_4_82.test.sql --local',
        'supabase test db supabase/tests/global_safety_compliance_v24_4_83.test.sql --local',
        'supabase test db supabase/tests/server_only_rls_contract_v25.test.sql --local',
        'supabase test db supabase/tests/security_advisor_contract_v24_5_24.test.sql --local',
        'supabase stop --no-backup',
    ):
        require(marker in workflow, f'workflow incomplet: {marker}')

    for forbidden in ('--linked', 'SUPABASE_ACCESS_TOKEN', 'SUPABASE_DB_PASSWORD', 'inputs.apply', 'db push'):
        require(forbidden not in workflow, f'workflow ne doit pas viser production: {forbidden}')

    print('OK En direct V25: modération live conserve V24.4.82, conformité globale inclut la 15e garde, invitations strict server-only, wrappers INVOKER, anti-raid et aucune collecte IP/GPS; production non touchée.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
