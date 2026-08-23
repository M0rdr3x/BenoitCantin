#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823011647_sinjira_v24_5_12_dating_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'DATING_RPC_BOUNDARY_V24_5_12.md'

TARGETS=[
'dating_block_connection','dating_close_connection','dating_compatibility_candidates',
'dating_compatibility_detail','dating_confirm_single_and_serious','dating_connections_overview',
'dating_conversation','dating_import_registry_traits','dating_pause_profile',
'dating_report_connection','dating_request_conversation','dating_respond_connection',
'dating_safe_meet_cancel','dating_safe_meet_opt_in','dating_safe_meet_status',
'dating_self_status','dating_send_message','dating_set_photo_consent']


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
        'create schema if not exists sinjira_dating_internal',
        'revoke all on schema sinjira_dating_internal from public',
        'grant usage on schema sinjira_dating_internal to authenticated, service_role',
        'if v_count <> 18 then',
        'alter function public.%i(%s) set schema sinjira_dating_internal',
        'revoke all on function sinjira_dating_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_dating_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]
    for marker in required:
        if marker not in flat: errors.append(f'Migration V24.5.12 incomplète: {marker}')

    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'RPC Rencontres absente: {name}')
    if len(TARGETS)!=18 or len(set(TARGETS))!=18:
        errors.append('La liste V24.5.12 doit contenir exactement 18 RPC uniques.')

    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_dating_internal)\..*?\s+to\s+anon',low,re.S):
        errors.append('V24.5.12 ne doit jamais accorder EXECUTE à anon.')

    row='20260823011647 sinjira_v24_5_12_dating_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if rows.count(row)!=1: errors.append('Le ledger doit contenir exactement une occurrence de V24.5.12.')
    if len(rows)<143: errors.append(f'Ledger historique incomplet: {len(rows)} migrations, au moins 143 attendues.')
    if row in rows and rows.index(row)<142: errors.append('V24.5.12 apparaît trop tôt dans le ledger historique.')

    for marker in ['18 rpc','18/18','security invoker','sinjira_dating_internal','143 migrations','auth.uid','service_role','aucune identité','aucun consentement photo']:
        if marker not in doc: errors.append(f'Document V24.5.12 incomplet: {marker}')

    forbidden=['stripe','paypal','canadapost','canada post','fedex','purolator','shippo','easypost','twilio','api.resend.com']
    for token in forbidden:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.12: {token}')

    if errors:
        print(f'ECHEC V24.5.12 frontière RPC Rencontres: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.12 historique: 18 RPC Rencontres isolées, wrappers SECURITY INVOKER, anon révoqué, auth.uid() et droits authenticated/service_role conservés.')
    return 0

if __name__=='__main__': raise SystemExit(main())
