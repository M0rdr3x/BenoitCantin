#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823034619_sinjira_v24_5_22_rls_helper_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'RLS_HELPER_RPC_BOUNDARY_V24_5_22.md'
TARGETS=[
'is_fracture_party_member','moderation_content_visible','sinjira_can_social_interact',
'sinjira_content_allowed','sinjira_cycle_allowed','sinjira_mfa_access_allowed',
'sinjira_my_age_band','social_is_blocked','social_is_suspended']


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
        'create schema if not exists sinjira_rls_internal',
        'revoke all on schema sinjira_rls_internal from public, anon',
        'grant usage on schema sinjira_rls_internal to authenticated, service_role',
        'if v_count <> 9 then',
        'alter function public.%i(%s) set schema sinjira_rls_internal',
        'revoke all on function sinjira_rls_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_rls_internal.%i(%s) to authenticated, service_role',
        'language sql stable security invoker',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]
    for marker in required:
        if marker not in flat: errors.append(f'Migration V24.5.22 incomplète: {marker}')
    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'Helper RLS absent: {name}')
    if len(TARGETS)!=9 or len(set(TARGETS))!=9: errors.append('La liste V24.5.22 doit contenir exactement 9 helpers uniques.')
    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_rls_internal)\..*?\s+to\s+anon',low,re.S): errors.append('V24.5.22 ne doit jamais accorder EXECUTE à anon.')

    row='20260823034619 sinjira_v24_5_22_rls_helper_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)!=153: errors.append(f'Ledger: {len(rows)} migrations au lieu de 153.')
    if rows.count(row)!=1 or not rows or rows[-1]!=row: errors.append('V24.5.22 doit être la dernière migration unique du ledger courant.')

    for marker in ['neuf','security invoker','stable','sinjira_rls_internal','153 migrations','81/81','19 `sinjira_mfa_access_allowed`','12 `social_is_suspended`','aucun warning','rls enabled no policy','pro+','l’humain avant tout']:
        if marker not in doc: errors.append(f'Document V24.5.22 incomplet: {marker}')
    for token in ['stripe','paypal','twilio','api.resend.com','openai.com','shippo','easypost']:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.22: {token}')

    if errors:
        print(f'ECHEC V24.5.22 frontière helpers RLS: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.22: 9 helpers RLS isolés, wrappers STABLE SECURITY INVOKER, anon révoqué, 81 références RLS documentées et ledger 153 synchronisé.')
    return 0

if __name__=='__main__': raise SystemExit(main())
