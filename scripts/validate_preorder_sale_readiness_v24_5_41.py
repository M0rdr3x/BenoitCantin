#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'admin/sinjira/precommandes-readiness.html'
JS=ROOT/'assets/js/sinjira-admin-preorder-readiness-v24-5-41.js'
DOC=ROOT/'PREORDER_SALE_READINESS_V24_5_41.md'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'


def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''


def main():
    errors=[]
    for p in [PAGE,JS,DOC,LEDGER]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    page=read(PAGE).lower(); js=read(JS).lower(); doc=read(DOC).lower()
    rows=[x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    for marker in ['noindex,nofollow','v24.5.41 · lecture seule · mfa/aal2','data-readiness-grid','data-readiness-blockers','data-readiness-locks','aucun bouton « ouvrir les ventes »']:
        if marker not in page: errors.append(f'Page readiness incomplète: {marker}')
    for marker in ['admin_preorder_sale_readiness','requireadminaal2','getauthenticatorassurancelevel','ready_for_future_manual_opening','sales_enabled','checkout_enabled','payment_enabled','external_fulfillment_enabled','auto_conversion_allowed','external_carrier_api_enabled','external_shipping_purchase_enabled','shipping_customer_pays','pickup_shipping_charge_cents','taxes_calculated_by_sinjira']:
        if marker not in js: errors.append(f'Contrôleur readiness incomplet: {marker}')
    for forbidden in ['stripe','paypal','resend','twilio','shippo','easypost','fedex','canadapost','canada post','paymentintent','checkout.session','row.user_id','user.email']:
        if forbidden in js+page: errors.append(f'Activation/donnée interdite V24.5.41: {forbidden}')
    for marker in ['lecture seule','décision humaine séparée','livraison à la charge du client','ramassage avec 0 $','172 migrations','aucune migration supabase']:
        if marker not in doc: errors.append(f'Document V24.5.41 incomplet: {marker}')

    expected='20260830035043 sinjira_v24_5_38_preorder_logistics_queue'
    if len(rows)!=172: errors.append(f'Ledger: {len(rows)} migrations au lieu de 172; V24.5.41 ne doit pas ajouter de migration.')
    if not rows or rows[-1]!=expected: errors.append('V24.5.41 doit conserver V24.5.38 comme dernière migration production.')

    dangerous=['ouvrir les ventes</button>','activer le paiement</button>','convertir les réservations</button>','sales_enabled = true','checkout_enabled = true','payment_enabled = true']
    for marker in dangerous:
        if marker in page+js: errors.append(f'Action commerciale interdite dans la checklist: {marker}')

    if errors:
        print(f'ECHEC V24.5.41 checklist préparation vente: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.41: checklist admin MFA/AAL2 en lecture seule, aucun bouton d’ouverture/paiement, aucun service externe, ledger 172 inchangé.')
    return 0

if __name__=='__main__': raise SystemExit(main())
