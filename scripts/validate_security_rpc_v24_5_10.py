#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260822201257_sinjira_v24_5_10_security_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'SECURITY_RPC_BOUNDARY_V24_5_10.md'

TARGETS=[
'security_after_password_recovery','security_cancel_travel_plan','security_compromise_account',
'security_create_travel_plan','security_disable_push_for_device','security_get_settings',
'security_list_sessions','security_push_status','security_register_device',
'security_register_push_endpoint','security_report_lost_device','security_resolve_connection_challenge',
'security_resolve_connection_challenge_mfa','security_revoke_device','security_sensitive_access_status',
'security_set_device_trust','security_update_settings']


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
        'create schema if not exists sinjira_security_internal',
        'revoke all on schema sinjira_security_internal from public',
        'grant usage on schema sinjira_security_internal to authenticated, service_role',
        'if v_count <> 17 then',
        'alter function public.%i(%s) set schema sinjira_security_internal',
        'revoke all on function sinjira_security_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_security_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]
    for marker in required:
        if marker not in flat: errors.append(f'Migration V24.5.10 incomplète: {marker}')

    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'RPC sécurité absente de la liste V24.5.10: {name}')
    if len(TARGETS)!=17 or len(set(TARGETS))!=17:
        errors.append('La liste V24.5.10 doit contenir exactement 17 RPC uniques.')

    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_security_internal)\..*?\s+to\s+anon',low,re.S):
        errors.append('V24.5.10 ne doit jamais accorder EXECUTE à anon.')

    row='20260822201257 sinjira_v24_5_10_security_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if rows.count(row)!=1: errors.append('Le ledger doit contenir exactement une occurrence de V24.5.10.')
    if len(rows)<141: errors.append(f'Ledger historique incomplet: {len(rows)} migrations, au moins 141 attendues.')
    if row in rows:
        idx=rows.index(row)
        if idx<140: errors.append('V24.5.10 apparaît trop tôt dans le ledger historique.')

    for marker in ['17 rpc','17/17','2/17','security invoker','sinjira_security_internal','141 migrations','auth.uid','service_role']:
        if marker not in doc: errors.append(f'Document V24.5.10 incomplet: {marker}')

    forbidden=['stripe','paypal','canadapost','canada post','fedex','purolator','shippo','easypost','twilio','api.resend.com']
    for token in forbidden:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.10: {token}')

    if errors:
        print(f'ECHEC V24.5.10 frontière RPC sécurité: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.10 historique: 17 RPC sécurité isolées, wrappers SECURITY INVOKER, anon révoqué, identité utilisateur et droits authenticated/service_role conservés.')
    return 0

if __name__=='__main__': raise SystemExit(main())
