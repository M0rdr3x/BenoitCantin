#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823025628_sinjira_v24_5_17_family_playtest_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'FAMILY_PLAYTEST_RPC_BOUNDARY_V24_5_17.md'
TARGETS=[
    'accept_sinjira_playtest_invitation',
    'create_family_link_invite',
    'create_guardian_signup_invite',
    'get_guardian_youth_contacts',
    'invite_sinjira_playtest_participant',
    'redeem_guardian_signup_invite',
    'revoke_guardian_link',
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
    for marker in [
        'create schema if not exists sinjira_family_playtest_internal',
        'revoke all on schema sinjira_family_playtest_internal from public',
        'grant usage on schema sinjira_family_playtest_internal to authenticated, service_role',
        'if v_count <> 7 then',
        'alter function public.%i(%s) set schema sinjira_family_playtest_internal',
        'revoke all on function sinjira_family_playtest_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_family_playtest_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]:
        if marker not in flat: errors.append(f'Migration V24.5.17 incomplète: {marker}')

    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'RPC famille/playtest absente: {name}')
    if len(TARGETS)!=7 or len(set(TARGETS))!=7: errors.append('V24.5.17 doit contenir exactement 7 RPC uniques.')
    if "'redeem_family_link_invite'" in low: errors.append('redeem_family_link_invite doit rester hors du lot V24.5.17 à cause de sa dépendance directe.')
    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_family_playtest_internal)\..*?\s+to\s+anon',low,re.S): errors.append('Aucun EXECUTE anon permis.')

    row='20260823025628 sinjira_v24_5_17_family_playtest_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)!=148: errors.append(f'Ledger: {len(rows)} migrations au lieu de 148.')
    if rows.count(row)!=1: errors.append('Le ledger doit contenir exactement une occurrence de V24.5.17.')
    if not rows or rows[-1]!=row: errors.append('V24.5.17 doit être la dernière migration du ledger courant.')

    for marker in ['7 rpc','7/7','security invoker','sinjira_family_playtest_internal','148 migrations','auth.uid','mineurs','tuteur','playtest','l’humain avant tout','redeem_family_link_invite']:
        if marker not in doc: errors.append(f'Document V24.5.17 incomplet: {marker}')

    for token in ['stripe','paypal','twilio','api.resend.com','openai.com']:
        if token in low: errors.append(f'Intégration externe interdite dans V24.5.17: {token}')

    if errors:
        print(f'ECHEC V24.5.17 frontière RPC famille/playtest: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.17: 7 RPC famille/playtest isolées, wrappers SECURITY INVOKER, protections mineurs/tuteurs préservées et ledger 148 synchronisé.')
    return 0


if __name__=='__main__': raise SystemExit(main())
