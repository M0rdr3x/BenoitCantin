#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823031150_sinjira_v24_5_19_family_redeem_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'FAMILY_REDEEM_RPC_BOUNDARY_V24_5_19.md'


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
        "p.proname='redeem_family_link_invite'",
        'alter function public.%i(%s) set schema sinjira_family_playtest_internal',
        'revoke all on function sinjira_family_playtest_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_family_playtest_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'select sinjira_family_playtest_internal.redeem_family_link_invite($1,$2,$3,$4)',
        'sinjira_family_playtest_internal.redeem_family_link_invite(text,text,date,boolean)',
        "'version','24.5.19'",
        'revoke all on function public.sinjira_family_link_health() from public,anon,authenticated',
        'grant execute on function public.sinjira_family_link_health() to service_role',
    ]:
        if marker not in flat: errors.append(f'Migration V24.5.19 incomplète: {marker}')
    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_family_playtest_internal)\.redeem_family_link_invite.*?\s+to\s+anon',low,re.S): errors.append('Aucun EXECUTE anon permis sur redeem_family_link_invite.')
    row='20260823031150 sinjira_v24_5_19_family_redeem_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)<150: errors.append(f'Ledger: {len(rows)} migrations, V24.5.19 exige au moins 150.')
    if rows.count(row)!=1: errors.append('Le ledger doit conserver exactement une occurrence de V24.5.19.')
    if row in rows and rows.index(row) != 149: errors.append('V24.5.19 doit conserver sa position historique 150 dans le ledger.')
    for marker in ['security invoker','sinjira_family_playtest_internal','150 migrations','auth.uid','adult_child → child','family → other','confirmed','mirror_to_fiction=false','service_role','l’humain avant tout']:
        if marker not in doc: errors.append(f'Document V24.5.19 incomplet: {marker}')
    for token in ['stripe','paypal','twilio','api.resend.com','openai.com']:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.19: {token}')
    if errors:
        print(f'ECHEC V24.5.19 frontière lien familial: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.19 historique: redeem_family_link_invite reste isolée, health-check adapté et position 150 conservée.')
    return 0

if __name__=='__main__': raise SystemExit(main())
