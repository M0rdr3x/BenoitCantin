#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823020820_sinjira_v24_5_15_social_user_rpc_boundary.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'SOCIAL_USER_RPC_BOUNDARY_V24_5_15.md'
COMMUNITY=ROOT/'supabase/tests/community_safety_v24_4_79.test.sql'
MINORS=ROOT/'supabase/tests/minor_exploitation_safety_v24_4_82.test.sql'
TARGETS=['social_my_blocks','social_my_reports','social_report_content','social_unblock_user']


def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''
def compact(s): return re.sub(r'\s+',' ',s.lower()).strip()


def main():
    errors=[]
    for p in [MIG,LEDGER,DOC,COMMUNITY,MINORS]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1
    sql=read(MIG); low=sql.lower(); flat=compact(sql); ledger=read(LEDGER); doc=read(DOC).lower()
    community=read(COMMUNITY).lower(); minors=read(MINORS).lower()
    for marker in [
        'create schema if not exists sinjira_social_user_internal',
        'revoke all on schema sinjira_social_user_internal from public',
        'grant usage on schema sinjira_social_user_internal to authenticated, service_role',
        'if v_count <> 4 then',
        'alter function public.%i(%s) set schema sinjira_social_user_internal',
        'revoke all on function sinjira_social_user_internal.%i(%s) from public, anon',
        'grant execute on function sinjira_social_user_internal.%i(%s) to authenticated, service_role',
        'security invoker',
        'grant execute on function public.%i(%s) to authenticated, service_role',
    ]:
        if marker not in flat: errors.append(f'Migration V24.5.15 incomplète: {marker}')
    for name in TARGETS:
        if f"'{name}'" not in low: errors.append(f'RPC sociale absente: {name}')
    if len(TARGETS)!=4 or len(set(TARGETS))!=4: errors.append('V24.5.15 doit contenir exactement 4 RPC uniques.')
    for helper in ['social_is_blocked','social_is_suspended']:
        if f"'{helper}'" not in low: errors.append(f'Garde explicite du helper RLS absente: {helper}')
    if re.search(r'grant\s+execute\s+on\s+function\s+(?:public|sinjira_social_user_internal)\..*?\s+to\s+anon',low,re.S): errors.append('Aucun EXECUTE anon permis.')

    row='20260823020820 sinjira_v24_5_15_social_user_rpc_boundary'
    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)<146: errors.append(f'Ledger historique incomplet: {len(rows)} migrations, au moins 146 attendues.')
    if rows.count(row)!=1: errors.append('Le ledger doit contenir exactement une occurrence de V24.5.15.')
    if row in rows and rows.index(row)!=145: errors.append('V24.5.15 doit conserver sa position historique 146.')

    if 'sinjira_social_user_internal.social_report_content' not in community: errors.append('Le contrat communauté doit lire le corps interne du signalement.')
    if 'sinjira_social_user_internal.social_my_blocks' not in community: errors.append('Le contrat communauté doit lire le corps interne des blocages.')
    if 'sinjira_social_user_internal.social_my_reports' not in community: errors.append('Le contrat communauté doit lire le corps interne des signalements personnels.')
    if minors.count('sinjira_social_user_internal.social_report_content')<2: errors.append('Le contrat sécurité mineurs doit vérifier le signalement interne.')

    for marker in ['4 rpc','4/4','security invoker','sinjira_social_user_internal','146 migrations','auth.uid','8 politiques rls','12 politiques rls','priority_safety','l’humain avant tout']:
        if marker not in doc: errors.append(f'Document V24.5.15 incomplet: {marker}')
    for token in ['stripe','paypal','twilio','api.resend.com']:
        if token in low: errors.append(f'Intégration externe interdite: {token}')
    if errors:
        print(f'ECHEC V24.5.15 frontière RPC sociales utilisateur: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.15 historique: 4 RPC sociales utilisateur isolées, helpers RLS préservés et contrats de sécurité conservés.')
    return 0


if __name__=='__main__': raise SystemExit(main())
