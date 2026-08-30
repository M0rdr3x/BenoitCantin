#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260830035043_sinjira_v24_5_38_preorder_logistics_queue.sql'
JS=ROOT/'assets/js/sinjira-admin-preorder-workflow-v24-5-36.js'
DOC=ROOT/'PREORDER_LOGISTICS_V24_5_38.md'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
TEST=ROOT/'supabase/tests/preorder_logistics_v24_5_38.test.sql'

def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''

def main():
    errors=[]
    for p in [MIG,JS,DOC,LEDGER,TEST]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        print('\n'.join('- '+e for e in errors)); return 1
    sql=read(MIG).lower(); js=read(JS).lower(); doc=read(DOC).lower(); test=read(TEST).lower()
    rows=[x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]
    for marker in ['admin_preorder_logistics_queue','private.require_sinjira_admin_aal2()','security invoker','security definer','preorder_admin_internal','pickup_point_label','pickup_city','disclosure_version','workflow_state']:
        if marker not in sql: errors.append(f'Migration V24.5.38 incomplète: {marker}')
    for forbidden in ['pp.user_id','pr.email','public_address','shipping_address','billing_address','payment_status','financial_commitment']:
        if forbidden in sql: errors.append(f'RPC logistique expose un champ interdit: {forbidden}')
    if re.search(r'grant\s+execute\s+on\s+function\s+public\.admin_preorder_logistics_queue.*?to\s+anon',sql,re.S):
        errors.append('anon ne doit jamais pouvoir exécuter la file logistique.')
    for marker in ['v24.5.38 · préparation logistique interne','admin_preorder_logistics_queue','export csv local','aucun nom de compte, courriel, adresse, uuid ou donnée de paiement','url.createobjecturl','new blob']:
        if marker not in js: errors.append(f'Interface logistique incomplète: {marker}')
    for forbidden in ['row.user_id','row.email','row.public_address','row.payment_status','row.financial_commitment','fetch(','xmlhttprequest','navigator.sendbeacon']:
        if forbidden in js: errors.append(f'Export local contient une surface interdite: {forbidden}')
    expected='20260830035043 sinjira_v24_5_38_preorder_logistics_queue'
    if len(rows)!=172: errors.append(f'Ledger: {len(rows)} migrations au lieu de 172.')
    if not rows or rows[-1]!=expected: errors.append('V24.5.38 doit être la dernière migration du ledger courant.')
    for marker in ['172 migrations','mfa/aal2','aucun fichier n’est envoyé','ni uuid','aucune api transporteur','0 $ de frais de livraison']:
        if marker not in doc: errors.append(f'Document V24.5.38 incomplet: {marker}')
    for marker in ['rpc logistique existe','wrapper public est security invoker','anon ne peut pas exécuter la rpc logistique','implémentation interne exige admin + mfa/aal2','aucun champ sensible dans le type de retour']:
        if marker not in test: errors.append(f'pgTAP V24.5.38 incomplet: {marker}')
    for forbidden in ['stripe','paypal','resend','twilio','shippo','easypost','fedex','ups.com','canadapost','canada post']:
        if forbidden in sql+js: errors.append(f'Intégration externe interdite V24.5.38: {forbidden}')
    if errors:
        print(f'ECHEC V24.5.38 logistique: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.38: file logistique minimale, MFA/AAL2, export CSV local, aucun UUID/adresse/paiement/service externe, ledger 172 synchronisé.')
    return 0

if __name__=='__main__': raise SystemExit(main())
