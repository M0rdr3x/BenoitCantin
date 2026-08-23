#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823033756_sinjira_v24_5_21_fracture_player_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'FRACTURE_PLAYER_RPC_BOUNDARY_V24_5_21.md'
TARGETS=[
'create_fracture_party','fracture_engine_get_state','fracture_engine_pick','fracture_engine_start',
'fracture_engine_submit_accusation','fracture_engine_submit_keep','fracture_engine_submit_report','join_fracture_party']


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
        'create schema if not exists sinjira_fracture_internal',
        'revoke all on schema sinjira_fracture_internal from public, anon',
        'grant usage on schema sinjira_fracture_internal to authenticated, service_role',
        'if v_count <> 8 then',
        'alter function public.%i(%s) set schema sinjira_fracture_internal',
        'revoke all on function sinjira_fracture_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_fracture_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]
    for marker in required:
        if marker not in flat: errors.append(f'Migration V24.5.21 incomplète: {marker}')
    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'RPC Fracture absente: {name}')
    if len(TARGETS)!=8 or len(set(TARGETS))!=8: errors.append('La liste V24.5.21 doit contenir exactement 8 RPC uniques.')
    if 'is_fracture_party_member' in low: errors.append('V24.5.21 ne doit pas déplacer le helper RLS is_fracture_party_member.')
    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_fracture_internal)\..*?\s+to\s+anon',low,re.S): errors.append('V24.5.21 ne doit jamais accorder EXECUTE à anon.')

    row='20260823033756 sinjira_v24_5_21_fracture_player_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)!=152: errors.append(f'Ledger: {len(rows)} migrations au lieu de 152.')
    if rows.count(row)!=1 or not rows or rows[-1]!=row: errors.append('V24.5.21 doit être la dernière migration unique du ledger courant.')

    if '8 rpc' not in doc and 'huit rpc' not in doc:
        errors.append('Document V24.5.21 incomplet: huit RPC')
    for marker in ['security invoker','sinjira_fracture_internal','152 migrations','auth.uid()','_fracture_engine_get_state_raw','is_fracture_party_member','quatre politiques rls','état brut','aucun paiement','l’humain avant tout']:
        if marker not in doc: errors.append(f'Document V24.5.21 incomplet: {marker}')
    for token in ['stripe','paypal','twilio','api.resend.com','openai.com','shippo','easypost']:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.21: {token}')

    if errors:
        print(f'ECHEC V24.5.21 frontière RPC Fracture: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.21: 8 RPC joueur Fracture isolées, helper RLS conservé, anon révoqué et ledger 152 synchronisé.')
    return 0

if __name__=='__main__': raise SystemExit(main())
