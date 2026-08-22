#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260822200413_sinjira_v24_5_9_global_admin_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'ADMIN_RPC_BOUNDARY_V24_5_9.md'

TARGETS=[
'admin_life_story_case_detail','admin_life_story_cleanup_due','admin_life_story_close_without_delivery',
'admin_life_story_complete_case','admin_life_story_complete_cleanup_task','admin_life_story_confirm_case',
'admin_life_story_get_export','admin_life_story_get_purgeable_export','admin_life_story_pending_requests',
'admin_life_story_prepare_export','admin_life_story_resolve_contest','admin_life_story_revoke_export',
'admin_life_story_verify_death','admin_parallel_list_cycles','admin_parallel_list_responses',
'admin_parallel_list_stories','admin_parallel_publish_story','admin_parallel_retract_story',
'admin_parallel_save_cycle','admin_parallel_set_cycle_status','privacy_admin_incidents',
'privacy_admin_record_incident','privacy_admin_requests','privacy_admin_update_request',
'safety_admin_escalation_cases']


def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''

def compact(s): return re.sub(r'\s+',' ',s.lower()).strip()


def main():
    errors=[]
    for p in [MIG,LEDGER,DOC]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    sql=read(MIG); low=sql.lower(); flat=compact(sql); ledger=read(LEDGER); doc=read(DOC).lower()

    required=[
        'create schema if not exists sinjira_admin_internal',
        'revoke all on schema sinjira_admin_internal from public',
        'grant usage on schema sinjira_admin_internal to authenticated, service_role',
        'if v_count <> 25 then',
        'alter function public.%i(%s) set schema sinjira_admin_internal',
        'revoke all on function sinjira_admin_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_admin_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]
    for marker in required:
        if marker not in flat: errors.append(f'Migration V24.5.9 incomplète: {marker}')

    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'RPC cible absente de la liste V24.5.9: {name}')

    if len(TARGETS)!=25 or len(set(TARGETS))!=25:
        errors.append('La liste de contrat V24.5.9 doit contenir exactement 25 RPC uniques.')

    forbidden_grants=[
        r'grant\s+execute\s+on\s+function\s+public\..*?\s+to\s+anon',
        r'grant\s+execute\s+on\s+function\s+sinjira_admin_internal\..*?\s+to\s+anon',
    ]
    for pat in forbidden_grants:
        if re.search(pat,low,re.S): errors.append('V24.5.9 ne doit jamais accorder EXECUTE à anon.')

    row='20260822200413 sinjira_v24_5_9_global_admin_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if row not in rows: errors.append('Ledger sans migration V24.5.9.')
    if len(rows)!=140: errors.append(f'Ledger: {len(rows)} migrations au lieu de 140.')
    if not rows or rows[-1]!=row: errors.append('V24.5.9 doit être la dernière migration du ledger courant.')

    for marker in ['25 fonctions','20/25','5/25','security invoker','sinjira_admin_internal','140 migrations','service_role']:
        if marker not in doc: errors.append(f'Document V24.5.9 incomplet: {marker}')

    forbidden=['stripe','paypal','canadapost','canada post','fedex','purolator','shippo','easypost','twilio','api.resend.com']
    for token in forbidden:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.9: {token}')

    if errors:
        print(f'ECHEC V24.5.9 frontière RPC admin globale: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.9: 25 RPC admin isolées, wrappers SECURITY INVOKER, anon révoqué, authenticated/service_role conservés et ledger 140 synchronisé.')
    return 0

if __name__=='__main__': raise SystemExit(main())
