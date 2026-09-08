#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase' / 'migrations' / '20260908140000_sinjira_v25_live_social_typed_commands.sql'
TEST = ROOT / 'supabase' / 'tests' / 'live_social_typed_commands_v25.test.sql'
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-live-social-commands-v25.yml'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f'ERREUR commandes En direct V25: {message}')


def main() -> int:
    migration = MIG.read_text('utf-8')
    test = TEST.read_text('utf-8')
    workflow = WORKFLOW.read_text('utf-8')
    ml = migration.lower()
    tl = test.lower()

    for name in (
        'social_live_join_public_room',
        'social_live_list_rooms',
        'social_live_me',
    ):
        require(f'function public.{name}' in ml, f'RPC absente: {name}')

    require(ml.count('security invoker') >= 3, 'les trois RPC doivent être SECURITY INVOKER')
    require('security definer' not in ml, 'aucune commande publique privilégiée ne doit être créée')
    require("visibility='public'" in ml, '/join doit être limité aux salons publics')
    require('insert into public.social_live_room_members(room_id)' in ml, '/join doit fournir uniquement room_id à l adhésion')
    require('social_live_room_invites' not in ml, '/join ne doit pas contourner les invitations privées')
    require("'profile_label'" in ml and "'owned_rooms'" in ml and "'joined_rooms'" in ml, '/me doit rester un résumé minimal')
    require("'user_id'" not in ml and "'owner_user_id'" not in ml, 'aucun UUID utilisateur ne doit être sérialisé comme clé JSON')
    require('create table' not in ml, 'cet incrément ne doit créer aucune table')
    require('realtime.send' not in ml and 'realtime.messages' not in ml, 'cet incrément ne doit pas modifier Realtime')

    for forbidden in (
        'execute format', 'execute immediate', 'dblink', 'inet_client_addr(', 'request.headers',
        'latitude', 'longitude', 'gps', 'date_of_birth'
    ):
        require(forbidden not in ml, f'construction/collecte interdite: {forbidden}')

    require('select plan(33);' in tl, 'plan pgTAP attendu = 33')
    require('aucune commande en direct publique privilégiée' in tl, 'contrat SECURITY INVOKER absent')
    require('/join ne contourne jamais le système d invitations privées' in tl, 'contrat private invite-only absent')
    require('/me ne retourne aucun uuid utilisateur' in tl, 'contrat minimisation /me absent')
    require('aucune présence persistante' in tl, 'contrat Presence éphémère absent')

    for marker in (
        'python scripts/validate_live_social_typed_commands_v25.py',
        'python scripts/validate_live_social_foundation_v25.py',
        'python scripts/validate_live_social_safety_v25.py',
        'python scripts/validate_production_migration_ledger.py',
        'python scripts/validate_production_schema_manifest.py',
        'supabase start',
        'supabase test db supabase/tests/live_social_typed_commands_v25.test.sql --local',
        'supabase test db supabase/tests/live_social_foundation_v25.test.sql --local',
        'supabase test db supabase/tests/security_advisor_contract_v24_5_24.test.sql --local',
        'supabase stop --no-backup',
    ):
        require(marker in workflow, f'workflow incomplet: {marker}')

    for forbidden in ('--linked', 'SUPABASE_ACCESS_TOKEN', 'SUPABASE_DB_PASSWORD', 'inputs.apply', 'db push'):
        require(forbidden not in workflow, f'workflow ne doit jamais viser production: {forbidden}')

    print('OK commandes En direct V25: /join, /rooms et /me sont des RPC typées SECURITY INVOKER, privées par RLS, sans interpréteur SQL, sans UUID utilisateur sérialisé et sans collecte IP/GPS.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
