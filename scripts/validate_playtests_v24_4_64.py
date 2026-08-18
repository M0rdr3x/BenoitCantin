#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'/'20260818042852_sinjira_v24_4_64_playtest_self_service_hardening.sql'


def read(path:Path)->str:
    if not path.exists():
        raise AssertionError(f'Fichier absent: {path.relative_to(ROOT)}')
    return path.read_text('utf-8',errors='ignore')


def require(text:str,markers:list[str],label:str)->None:
    missing=[m for m in markers if m.lower() not in text.lower()]
    if missing:
        raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text:str,markers:list[str],label:str)->None:
    found=[m for m in markers if m.lower() in text.lower()]
    if found:
        raise AssertionError(f'{label}: marqueurs interdits présents: {found}')


def main()->int:
    migration=read(MIG)
    page=read(ROOT/'compte'/'playtests.html')
    client=read(ROOT/'assets'/'js'/'sinjira-playtests-v24-4-64.js')
    admin=read(ROOT/'supabase'/'functions'/'admin-console'/'index.ts')
    ledger=read(ROOT/'supabase'/'production-migration-ledger.txt')

    require(migration,[
        'revoke all on table public.playtests from public, anon, authenticated',
        'grant select on table public.playtests to authenticated',
        'revoke all on table public.playtest_participants from public, anon, authenticated',
        'grant insert (playtest_id, user_id, status, application_message)',
        'grant update (status) on table public.playtest_participants to authenticated',
        'playtests_read_authorized',
        'playtest_participants_apply',
        'playtest_participants_withdraw_own',
        "status in ('open','active')",
        "p.status = 'open'",
        "when 'tester' then 30",
        "when 'player' then 20",
        "status in ('invited','applied','approved')",
        "status = 'withdrawn'"
    ],'migration Playtests')

    forbid(migration,[
        'grant insert on table public.playtests to authenticated',
        'grant update on table public.playtests to authenticated',
        'grant delete on table public.playtests to authenticated',
        'grant delete on table public.playtest_participants to authenticated'
    ],'migration Playtests')

    require(admin,[
        "serviceClient()",
        "action==='save_playtest'",
        "service.from('playtests').upsert",
        "action==='review_playtest_participant'",
        "service.from('playtest_participants').update"
    ],'administration serveur Playtests')

    require(page,[
        'data-library-page="playtests-v24-4-64"',
        'data-my-playtests-list',
        'data-open-playtests-list',
        'sinjira-playtests-v24-4-64.js?v=24.4.64',
        'jamais vous auto-approuver',
        'sans service payant'
    ],'page Mes playtests')

    require(client,[
        "from('playtests')",
        "from('playtest_participants')",
        "status:'applied'",
        ".update({status:'withdrawn'})",
        'data-withdraw-playtest',
        "item.status==='open'"
    ],'client Playtests')

    # Le client ne doit jamais envoyer un statut d'administration.
    for forbidden_status in ("status:'approved'","status:'refused'","status:'completed'","status:'invited'"):
        if forbidden_status in client.replace(' ', ''):
            raise AssertionError(f'Client Playtests: statut administrateur interdit détecté: {forbidden_status}')

    forbid(client,['functions.invoke(','service_role','stripe','checkout','api.openai.com'],'client Playtests')
    require(ledger,['20260818042852 sinjira_v24_4_64_playtest_self_service_hardening'],'ledger Playtests')

    print('OK Playtests V24.4.64: ACL minimales, niveau requis imposé, historique participant visible et retrait self-only sans auto-approbation.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
