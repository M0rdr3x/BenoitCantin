#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823031850_sinjira_v24_5_20_owner_character_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'OWNER_CHARACTER_RPC_BOUNDARY_V24_5_20.md'


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
        'create schema if not exists sinjira_owner_internal',
        "p.proname='ensure_sinjira_owner_character'",
        'alter function public.%i(%s) set schema sinjira_owner_internal',
        'revoke all on function sinjira_owner_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_owner_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'select sinjira_owner_internal.ensure_sinjira_owner_character()',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]
    for marker in required:
        if marker not in flat: errors.append(f'Migration V24.5.20 incomplète: {marker}')
    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_owner_internal)\.ensure_sinjira_owner_character.*?\s+to\s+anon',low,re.S):
        errors.append('Aucun EXECUTE anon permis sur ensure_sinjira_owner_character.')

    row='20260823031850 sinjira_v24_5_20_owner_character_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)<151: errors.append(f'Ledger: {len(rows)} migrations, V24.5.20 exige au moins 151.')
    if rows.count(row)!=1: errors.append('Le ledger doit conserver exactement une occurrence de V24.5.20.')
    if row in rows and rows.index(row)!=150: errors.append('V24.5.20 doit conserver sa position historique 151 dans le ledger.')

    for marker in ['security invoker','sinjira_owner_internal','151 migrations','auth.uid()','identité','registre','l’humain avant tout','service externe payant']:
        if marker not in doc: errors.append(f'Document V24.5.20 incomplet: {marker}')
    for token in ['stripe','paypal','twilio','api.resend.com','openai.com']:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.20: {token}')

    if errors:
        print(f'ECHEC V24.5.20 frontière personnage propriétaire: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.20 historique: ensure_sinjira_owner_character reste isolée et sa position 151 est conservée.')
    return 0

if __name__=='__main__': raise SystemExit(main())
