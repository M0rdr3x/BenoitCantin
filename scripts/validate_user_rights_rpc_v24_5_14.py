#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823015621_sinjira_v24_5_14_user_rights_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'USER_RIGHTS_RPC_BOUNDARY_V24_5_14.md'

TARGETS=[
    'moderation_my_decisions',
    'moderation_submit_appeal',
    'privacy_create_request',
    'privacy_export_my_extended_data',
    'privacy_my_requests',
]


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
        'create schema if not exists sinjira_user_rights_internal',
        'revoke all on schema sinjira_user_rights_internal from public',
        'grant usage on schema sinjira_user_rights_internal to authenticated, service_role',
        'if v_count <> 5 then',
        'alter function public.%i(%s) set schema sinjira_user_rights_internal',
        'revoke all on function sinjira_user_rights_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_user_rights_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]
    for marker in required:
        if marker not in flat: errors.append(f'Migration V24.5.14 incomplète: {marker}')

    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'RPC droits utilisateur absente: {name}')
    if len(TARGETS)!=5 or len(set(TARGETS))!=5:
        errors.append('La liste V24.5.14 doit contenir exactement 5 RPC uniques.')

    if 'moderation_content_visible' in low:
        errors.append('Le helper RLS moderation_content_visible ne doit pas être déplacé par V24.5.14.')
    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_user_rights_internal)\..*?\s+to\s+anon',low,re.S):
        errors.append('V24.5.14 ne doit jamais accorder EXECUTE à anon.')

    row='20260823015621 sinjira_v24_5_14_user_rights_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)!=145: errors.append(f'Ledger: {len(rows)} migrations au lieu de 145.')
    if rows.count(row)!=1: errors.append('Le ledger doit contenir exactement une occurrence de V24.5.14.')
    if not rows or rows[-1]!=row: errors.append('V24.5.14 doit être la dernière migration du ledger courant.')

    for marker in [
        '5 rpc','5/5','security invoker','sinjira_user_rights_internal','145 migrations',
        'auth.uid','service_role','révision humaine','l’humain avant tout','aucune nouvelle donnée personnelle'
    ]:
        if marker not in doc: errors.append(f'Document V24.5.14 incomplet: {marker}')

    forbidden=['stripe','paypal','canadapost','canada post','fedex','purolator','shippo','easypost','twilio','api.resend.com']
    for token in forbidden:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.14: {token}')

    if errors:
        print(f'ECHEC V24.5.14 frontière RPC droits utilisateur: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1

    print('OK V24.5.14: 5 RPC Confidentialité/Appels isolées, wrappers SECURITY INVOKER, anon révoqué, auth.uid() et droits authenticated/service_role conservés, ledger 145 synchronisé.')
    return 0


if __name__=='__main__': raise SystemExit(main())
