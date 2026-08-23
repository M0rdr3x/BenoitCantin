#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260822202024_sinjira_v24_5_11_preorder_user_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'PREORDER_USER_RPC_BOUNDARY_V24_5_11.md'

TARGETS=[
    'product_preorder_cancel',
    'product_preorder_fulfillment_status',
    'product_preorder_my_status',
    'product_preorder_reserve',
    'product_preorder_set_fulfillment_preference',
]


def read(p):
    return p.read_text('utf-8',errors='ignore') if p.exists() else ''


def compact(s):
    return re.sub(r'\s+',' ',s.lower()).strip()


def main():
    errors=[]
    for p in [MIG,LEDGER,DOC]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    sql=read(MIG); low=sql.lower(); flat=compact(sql)
    ledger=read(LEDGER); doc=read(DOC).lower()

    required=[
        'create schema if not exists preorder_user_internal',
        'revoke all on schema preorder_user_internal from public',
        'grant usage on schema preorder_user_internal to authenticated, service_role',
        'if v_count <> 5 then',
        'alter function public.%i(%s) set schema preorder_user_internal',
        'revoke all on function preorder_user_internal.%i(%s) from public, anon',
        'grant execute on function preorder_user_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]
    for marker in required:
        if marker not in flat: errors.append(f'Migration V24.5.11 incomplète: {marker}')

    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'RPC précommande utilisateur absente: {name}')
    if len(TARGETS)!=5 or len(set(TARGETS))!=5:
        errors.append('La liste V24.5.11 doit contenir exactement 5 RPC uniques.')

    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|preorder_user_internal)\..*?\s+to\s+anon',low,re.S):
        errors.append('V24.5.11 ne doit jamais accorder EXECUTE à anon.')

    row='20260822202024 sinjira_v24_5_11_preorder_user_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)!=142: errors.append(f'Ledger: {len(rows)} migrations au lieu de 142.')
    if rows.count(row)!=1: errors.append('Le ledger doit contenir exactement une occurrence de V24.5.11.')
    if not rows or rows[-1]!=row: errors.append('V24.5.11 doit être la dernière migration du ledger courant.')

    for marker in [
        '5 rpc','5/5','security invoker','preorder_user_internal','142 migrations',
        'auth.uid','service_role','aucun paiement','aucune conversion automatique'
    ]:
        if marker not in doc: errors.append(f'Document V24.5.11 incomplet: {marker}')

    forbidden=['stripe','paypal','canadapost','canada post','fedex','purolator','shippo','easypost','twilio','api.resend.com']
    for token in forbidden:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.11: {token}')

    if errors:
        print(f'ECHEC V24.5.11 frontière RPC utilisateur précommandes: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1

    print('OK V24.5.11: 5 RPC utilisateur précommandes isolées, wrappers SECURITY INVOKER, anon révoqué, auth.uid() et droits authenticated/service_role conservés, ledger 142 synchronisé.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
