#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase'/'migrations'/'20260818044154_sinjira_v24_4_65_playtest_invitations.sql'


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
    client=read(ROOT/'assets'/'js'/'sinjira-playtests-v24-4-65.js')
    page=read(ROOT/'compte'/'playtests.html')
    ledger=read(ROOT/'supabase'/'production-migration-ledger.txt')

    require(migration,[
        'create or replace function public.invite_sinjira_playtest_participant',
        'create or replace function public.accept_sinjira_playtest_invitation',
        'security definer',
        'set search_path = pg_catalog, public',
        'internal_admin_users',
        "v_status not in ('open','active')",
        'account_safety_profiles',
        'v_age < 12',
        'v_age < 18',
        "g.status='verified'",
        'g.revoked_at is null',
        "v_existing_status not in ('refused','withdrawn')",
        "status='invited'",
        "pp.user_id=v_user",
        "and pp.status='invited'",
        "set status='approved'",
        'insert into public.project_access',
        "'tester'",
        "'playtest_invite'",
        'revoke all on function public.invite_sinjira_playtest_participant(uuid,uuid) from public, anon, authenticated',
        'revoke all on function public.accept_sinjira_playtest_invitation(uuid) from public, anon, authenticated',
        'grant execute on function public.invite_sinjira_playtest_participant(uuid,uuid) to authenticated, service_role',
        'grant execute on function public.accept_sinjira_playtest_invitation(uuid) to authenticated, service_role'
    ],'migration invitations')

    require(client,[
        "rpc('accept_sinjira_playtest_invitation'",
        "rpc('invite_sinjira_playtest_participant'",
        "rpc('is_sinjira_admin'",
        "functions.invoke('admin-users'",
        'data-accept-playtest',
        'data-admin-invite-form',
        "participant.status==='invited'",
        "data.code==='ALREADY_INVITED'"
    ],'client invitations')

    # L’interface ne doit jamais contourner l’acceptation RPC par une écriture approved.
    compact=client.replace(' ','').replace('\n','')
    if ".update({status:'approved'})" in compact or "status:'approved'" in compact:
        raise AssertionError('Client invitations: auto-approbation directe détectée.')

    forbid(client,['api.openai.com','stripe','paypal','twilio','sendgrid'],'client invitations')

    require(page,[
        'data-library-page="playtests-v24-4-65"',
        'data-admin-playtest-invites',
        'data-admin-invite-form',
        'data-admin-invite-playtest',
        'data-admin-invite-user',
        'data-playtest-invite-count',
        'sinjira-playtests-v24-4-65.js?v=24.4.65',
        'invitations internes, sans service payant'
    ],'page invitations')

    require(ledger,['20260818044154 sinjira_v24_4_65_playtest_invitations'],'ledger invitations')

    print('OK invitations Playtests V24.4.65: admin-only, acceptation self-only, garde jeunesse serveur et aucun service externe payant.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
