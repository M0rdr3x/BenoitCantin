#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260831004411_sinjira_v24_5_46_preorder_uuid_output_hardening.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'PREORDER_UUID_OUTPUT_HARDENING_V24_5_46.md'
JS=ROOT/'assets/js/sinjira-preorders-v24-5-3.js'


def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''


def main():
    errors=[]
    for p in [MIG,LEDGER,DOC,JS]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    sql=read(MIG).lower(); doc=read(DOC).lower(); js=read(JS).lower()
    rows=[x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    required_sql=[
        'drop function if exists public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)',
        'create function preorder_user_internal.product_preorder_reserve_confirmed',
        'returns text',
        'returning reservation_reference into v_reference',
        'create function public.product_preorder_reserve_confirmed',
        'select preorder_user_internal.product_preorder_reserve_confirmed($1,$2,$3,$4,$5,$6)',
        'drop function if exists public.admin_preorder_list(text,text,text,integer,integer)',
        'create function preorder_admin_internal.admin_preorder_list',
        'reservation_reference text',
        'pp.reservation_reference',
        'create function public.admin_preorder_list',
        'security invoker',
        'revoke all on function public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean) from public, anon',
        'revoke all on function public.admin_preorder_list(text,text,text,integer,integer) from public, anon',
    ]
    for marker in required_sql:
        if marker not in sql: errors.append(f'Migration V24.5.46 incomplète: {marker}')

    # La nouvelle définition ne doit jamais remettre l'UUID de précommande en sortie.
    confirmed=sql[sql.find('create function preorder_user_internal.product_preorder_reserve_confirmed'):sql.find('-- la console admin')]
    if 'returns uuid' in confirmed or 'return v_preorder_id' in confirmed:
        errors.append('La réservation confirmée expose encore un UUID interne.')
    admin=sql[sql.find('create function preorder_admin_internal.admin_preorder_list'):]
    if 'preorder_id uuid' in admin or 'pp.id,' in admin:
        errors.append('La liste admin expose encore preorder_id/pp.id.')

    if "rpc('product_preorder_reserve_confirmed'" not in js:
        errors.append('Le parcours utilisateur n’utilise plus la RPC confirmée attendue.')
    # L’interface doit continuer à relire l’état sûr et ne pas afficher le retour brut.
    if 'await refreshall();' not in js or 'reservation_reference' not in js:
        errors.append('Le parcours utilisateur ne relit pas la référence sûre après réservation.')

    # Contrat historique : V24.5.46 doit rester enregistré exactement une fois.
    # Le dernier état global du ledger est validé par validate_production_migration_ledger.py.
    row='20260831004411 sinjira_v24_5_46_preorder_uuid_output_hardening'
    if rows.count(row)!=1: errors.append('V24.5.46 doit apparaître exactement une fois dans le ledger.')

    for marker in ['uuid interne','reservation_reference','pr-','174 migrations','aucune vente active','aucun paiement actif','0 $ de frais de livraison','aucun service payant activé']:
        if marker not in doc: errors.append(f'Document V24.5.46 incomplet: {marker}')

    for token in ['api.stripe.com','paypal.com/sdk','api.resend.com','twilio.com','api.shippo.com','api.easypost.com','payment_enabled = true','checkout_enabled = true','sales_enabled = true']:
        if token in sql+'\n'+doc: errors.append(f'Activation externe/commerciale interdite V24.5.46: {token}')

    if errors:
        print(f'ECHEC V24.5.46 confidentialité UUID: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.46: réservation confirmée et liste admin utilisent la référence PR-…; aucun UUID interne en sortie, ACL et garde-fous commerciaux conservés; migration historique enregistrée une fois.')
    return 0

if __name__=='__main__': raise SystemExit(main())
