#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
BRIDGE=ROOT/'supabase/migrations/20260823205908_sinjira_v24_5_14_privacy_moderation_user_rpc_boundary.sql'
CONV=ROOT/'supabase/migrations/20260823210123_sinjira_v24_5_28_user_rights_boundary_convergence.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'USER_RIGHTS_BOUNDARY_CONVERGENCE_V24_5_28.md'
TEST=ROOT/'supabase/tests/user_rights_boundary_convergence_v24_5_28.test.sql'
TARGETS=['moderation_my_decisions','moderation_submit_appeal','privacy_create_request','privacy_export_my_extended_data','privacy_my_requests']

def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''
def flat(s): return re.sub(r'\s+',' ',s.lower()).strip()

def main():
    errors=[]
    for p in [BRIDGE,CONV,LEDGER,DOC,TEST]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    bridge=read(BRIDGE).lower(); conv=read(CONV).lower(); fconv=flat(conv); doc=read(DOC).lower(); test=read(TEST).lower()

    for name in TARGETS:
        if name not in bridge: errors.append(f'Pont historique incomplet: {name}')
        if name not in conv: errors.append(f'Convergence V24.5.28 incomplète: {name}')

    required=[
      "sinjira_user_rights_internal",
      "security invoker",
      "revoke all on function public.%i(%s) from public, anon",
      "grant execute on function public.%i(%s) to authenticated, service_role",
      "drop schema if exists sinjira_privacy_moderation_internal",
      "revoke all on schema sinjira_user_rights_internal from public, anon",
      "grant usage on schema sinjira_user_rights_internal to authenticated, service_role",
    ]
    for marker in required:
        if marker not in fconv: errors.append(f'Marqueur de convergence absent: {marker}')

    if 'cascade' in conv:
        errors.append('La convergence V24.5.28 ne doit pas utiliser CASCADE.')

    rows=[x.strip() for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]
    bridge_row='20260823205908 sinjira_v24_5_14_privacy_moderation_user_rpc_boundary'
    conv_row='20260823210123 sinjira_v24_5_28_user_rights_boundary_convergence'
    if len(rows)!=162: errors.append(f'Ledger: {len(rows)} migrations au lieu de 162.')
    if rows.count(bridge_row)!=1: errors.append('Migration de pont absente ou dupliquée dans le ledger.')
    if rows.count(conv_row)!=1: errors.append('Migration V24.5.28 absente ou dupliquée dans le ledger.')
    if not rows or rows[-1]!=conv_row: errors.append('V24.5.28 doit être la dernière migration courante du ledger.')

    for marker in ['5/5','security invoker','security definer','auth.uid()','default 20','schéma intermédiaire','162 migrations','aucun paiement']:
        if marker not in doc: errors.append(f'Document V24.5.28 incomplet: {marker}')

    for marker in ['select plan(15)','sinjira_user_rights_internal','sinjira_privacy_moderation_internal','security invoker','auth.uid()','default 20','select * from finish()','rollback;']:
        if marker not in test: errors.append(f'pgTAP V24.5.28 incomplet: {marker}')

    forbidden=['stripe','paypal','avalara','taxjar','vertex','twilio','api.resend.com','api.openai.com','canadapost','canada post','fedex','purolator','shippo','easypost']
    for token in forbidden:
        if token in bridge or token in conv: errors.append(f'Fournisseur externe interdit dans la convergence V24.5.28: {token}')

    if errors:
        print(f'ECHEC V24.5.28 convergence droits utilisateur: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.28: frontière canonique restaurée, schéma redondant supprimé, ACL et auth.uid() conservés, ledger 162 synchronisé.')
    return 0

if __name__=='__main__': raise SystemExit(main())
