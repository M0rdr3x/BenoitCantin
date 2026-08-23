#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823013006_sinjira_v24_5_13_life_story_user_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'LIFE_STORY_USER_RPC_BOUNDARY_V24_5_13.md'

TARGETS=[
'life_story_contest_death_verification','life_story_create_report_code','life_story_list_report_codes',
'life_story_my_posthumous_case','life_story_report_death_by_code','life_story_revoke_report_code']


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
        'create schema if not exists sinjira_life_story_internal',
        'revoke all on schema sinjira_life_story_internal from public',
        'grant usage on schema sinjira_life_story_internal to authenticated, service_role',
        'if v_count <> 6 then',
        'alter function public.%i(%s) set schema sinjira_life_story_internal',
        'revoke all on function sinjira_life_story_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_life_story_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]
    for marker in required:
        if marker not in flat: errors.append(f'Migration V24.5.13 incomplète: {marker}')

    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'RPC Histoire de vie absente: {name}')
    if len(TARGETS)!=6 or len(set(TARGETS))!=6:
        errors.append('La liste V24.5.13 doit contenir exactement 6 RPC uniques.')

    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_life_story_internal)\..*?\s+to\s+anon',low,re.S):
        errors.append('V24.5.13 ne doit jamais accorder EXECUTE à anon.')

    row='20260823013006 sinjira_v24_5_13_life_story_user_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if rows.count(row)!=1: errors.append('Le ledger doit contenir exactement une occurrence de V24.5.13.')
    if len(rows)<144: errors.append(f'Ledger historique incomplet: {len(rows)} migrations, au moins 144 attendues.')
    if row in rows and rows.index(row)<143: errors.append('V24.5.13 apparaît trop tôt dans le ledger historique.')

    for marker in ['6 rpc','6/6','5/6','security invoker','sinjira_life_story_internal','144 migrations','auth.uid','service_role','distincte du registre','clonage ia posthume reste interdit','pdf final']:
        if marker not in doc: errors.append(f'Document V24.5.13 incomplet: {marker}')

    forbidden=['stripe','paypal','canadapost','canada post','fedex','purolator','shippo','easypost','twilio','api.resend.com']
    for token in forbidden:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.13: {token}')

    if errors:
        print(f'ECHEC V24.5.13 frontière RPC utilisateur Histoire de vie: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.13 historique: 6 RPC Histoire de vie isolées, wrappers SECURITY INVOKER, anon révoqué, auth.uid(), MFA historique et droits authenticated/service_role conservés.')
    return 0

if __name__=='__main__': raise SystemExit(main())
