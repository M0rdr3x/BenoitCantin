#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823021612_sinjira_v24_5_16_parallel_user_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'PARALLEL_USER_RPC_BOUNDARY_V24_5_16.md'
TARGETS=['parallel_my_context','parallel_my_identity','parallel_save_cycle_response','parallel_set_my_identity']


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
    for marker in [
        'create schema if not exists sinjira_parallel_user_internal',
        'revoke all on schema sinjira_parallel_user_internal from public',
        'grant usage on schema sinjira_parallel_user_internal to authenticated, service_role',
        'if v_count <> 4 then',
        'alter function public.%i(%s) set schema sinjira_parallel_user_internal',
        'revoke all on function sinjira_parallel_user_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_parallel_user_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]:
        if marker not in flat: errors.append(f'Migration V24.5.16 incomplète: {marker}')
    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'RPC Monde parallèle absente: {name}')
    if len(TARGETS)!=4 or len(set(TARGETS))!=4: errors.append('V24.5.16 doit contenir exactement 4 RPC uniques.')
    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_parallel_user_internal)\..*?\s+to\s+anon',low,re.S): errors.append('Aucun EXECUTE anon permis.')

    for forbidden in ['reader_characters','registry_account_links','account_identities','compte_courriel','compte_pseudo']:
        if forbidden in low: errors.append(f'Référence d’identité interdite dans la migration: {forbidden}')

    row='20260823021612 sinjira_v24_5_16_parallel_user_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)<147: errors.append(f'Ledger: {len(rows)} migrations, moins que les 147 requises à V24.5.16.')
    if rows.count(row)!=1: errors.append('Le ledger doit conserver exactement une occurrence de V24.5.16.')
    if row in rows and any(x.startswith('202608') and x < row for x in rows[rows.index(row)+1:]): errors.append('Ordre historique du ledger invalide après V24.5.16.')

    for marker in ['4 rpc','4/4','security invoker','sinjira_parallel_user_internal','147 migrations','auth.uid','public.parallel_my_identity()','identité parallèle reste une identité distincte','validation humaine','l’humain avant tout']:
        if marker not in doc: errors.append(f'Document V24.5.16 incomplet: {marker}')
    for token in ['stripe','paypal','twilio','api.resend.com']:
        if token in low: errors.append(f'Intégration externe interdite: {token}')
    if errors:
        print(f'ECHEC V24.5.16 frontière RPC Monde parallèle utilisateur: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.16 historique: 4 RPC Monde parallèle isolées, wrappers SECURITY INVOKER, identité séparée et migration conservée dans le ledger.')
    return 0


if __name__=='__main__': raise SystemExit(main())
