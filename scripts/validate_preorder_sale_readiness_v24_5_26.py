#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260823171121_sinjira_v24_5_26_preorder_sale_readiness_guard.sql'
TEST=ROOT/'supabase/tests/preorder_sale_readiness_v24_5_26.test.sql'
DOC=ROOT/'PREORDER_SALE_READINESS_V24_5_26.md'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
COST=ROOT/'assets/js/sinjira-preorder-cost-summary-v24-5-25.js'
ADMIN=ROOT/'assets/js/sinjira-admin-preorder-readiness-v24-5-26.js'
LOADER=ROOT/'assets/js/sinjira-admin-preorder-commercial-v24-5-5.js'


def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''
def compact(s): return re.sub(r'\s+',' ',s.lower()).strip()

def main():
    errors=[]
    for p in [MIG,TEST,DOC,LEDGER,COST,ADMIN,LOADER]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    sql=read(MIG); flat=compact(sql); cost=read(COST).lower(); admin=read(ADMIN).lower(); loader=read(LOADER); doc=read(DOC).lower(); test=read(TEST).lower()

    required_sql=[
        'create schema if not exists preorder_readiness_internal',
        'private.require_sinjira_admin_aal2()',
        'security definer',
        'create or replace function public.admin_preorder_sale_readiness',
        'security invoker',
        'revoke all on function public.admin_preorder_sale_readiness(text) from public, anon',
        'grant execute on function public.admin_preorder_sale_readiness(text) to authenticated, service_role',
        "'ready_for_future_manual_opening'",
        "'taxes_calculated_by_sinjira', false",
        'shipping_customer_pays is true',
        'external_carrier_api_enabled is false',
        'external_shipping_purchase_enabled is false',
        'pickup_shipping_charge_cents = 0',
        'not v_plan.sales_enabled',
        'not v_plan.checkout_enabled',
        'not v_plan.payment_enabled',
        'not v_plan.external_fulfillment_enabled',
        'not v_plan.auto_conversion_allowed',
    ]
    for marker in required_sql:
        if marker not in flat: errors.append(f'Migration V24.5.26 incomplète: {marker}')
    if re.search(r'grant\s+execute\s+on\s+function\s+public\.admin_preorder_sale_readiness.*?\s+to\s+anon',sql,re.I|re.S):
        errors.append('La checklist admin ne doit jamais être exécutable par anon.')

    for marker in ['sous-total estimatif avant taxes','taxes applicables','ne sont pas calculées ici','les frais de livraison seront à la charge du client','ramassage sur place — 0 $ de frais de livraison','réservation ≠ vente','total estimatif indisponible pour le moment']:
        if marker not in cost: errors.append(f'Transparence coût historique absente: {marker}')

    for marker in ["rpc('admin_preorder_sale_readiness'",'préparation incomplète','vente toujours désactivée','taxes calculées dans sinjira','ouverture automatique','impossible']:
        if marker not in admin: errors.append(f'Checklist admin V24.5.26 incomplète: {marker}')
    if "import './sinjira-admin-preorder-readiness-v24-5-26.js';" not in loader:
        errors.append('Le module commercial admin doit charger la checklist V24.5.26.')

    rows=[x.strip() for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]
    row='20260823171121 sinjira_v24_5_26_preorder_sale_readiness_guard'
    if rows.count(row)!=1: errors.append('Le ledger doit contenir exactement une V24.5.26.')
    if row in rows and rows.index(row) >= len(rows): errors.append('Position ledger V24.5.26 invalide.')

    for marker in ['157 migrations','admin_preorder_sale_readiness','require_sinjira_admin_aal2','sous-total estimatif avant taxes','ne sont pas calculées par sinjira','0 $ de frais de livraison','aucun checkout','aucun paiement','aucun service payant']:
        if marker not in doc: errors.append(f'Document historique V24.5.26 incomplet: {marker}')

    for marker in ['select plan(8)','security invoker','preorder_readiness_internal.sale_readiness','require_sinjira_admin_aal2','taxes_calculated_by_sinjira','select * from finish()','rollback;']:
        if marker not in test: errors.append(f'pgTAP V24.5.26 incomplet: {marker}')

    forbidden=['stripe','paypal','canada post','canadapost','fedex','purolator','shippo','easypost','twilio','api.resend.com','api.openai.com']
    for token in forbidden:
        if token in sql.lower() or token in admin:
            errors.append(f'Intégration externe interdite dans V24.5.26: {token}')

    if errors:
        print(f'ECHEC V24.5.26 historique: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.26 historique: garde admin MFA/AAL2, vente désactivée, livraison client, ramassage 0 $ et transparence avant taxes préservés.')
    return 0

if __name__=='__main__': raise SystemExit(main())
