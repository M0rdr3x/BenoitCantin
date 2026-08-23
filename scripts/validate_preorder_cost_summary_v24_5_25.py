#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
JS=ROOT/'assets/js/sinjira-preorder-cost-summary-v24-5-25.js'
CSS=ROOT/'assets/css/sinjira-preorder-cost-summary-v24-5-25.css'
LOADER=ROOT/'assets/js/sinjira-preorder-fulfillment-v24-5-6.js'
DOC=ROOT/'PREORDER_COST_SUMMARY_V24_5_25.md'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
MIG=ROOT/'supabase/migrations'


def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''

def main():
    errors=[]
    for p in [JS,CSS,LOADER,DOC,LEDGER]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    js=read(JS); low=js.lower(); loader=read(LOADER); doc=read(DOC).lower()
    required_js=[
        'les frais de livraison seront à la charge du client',
        'ramassage sur place — 0 $ de frais de livraison',
        'total estimatif indisponible pour le moment',
        'réservation ≠ vente',
        'aucune adresse exacte',
        'estimation non contractuelle',
        "rpc('product_preorder_commercial_info'",
        "rpc('product_preorder_fulfillment_options'",
        "rpc('product_preorder_shipping_estimate'",
        'function centsvalue(value)',
        "value === null || value === undefined || value === ''",
        'info.sales_enabled !== false',
        'info.checkout_enabled !== false',
        'info.payment_enabled !== false',
        'info.auto_conversion_allowed !== false',
        'shipping_customer_pays === true',
        'estimate_nonbinding === true',
    ]
    for marker in required_js:
        if marker not in low: errors.append(f'Contrat JS absent: {marker}')

    if "import './sinjira-preorder-cost-summary-v24-5-25.js';" not in loader:
        errors.append('Le module V24.5.25 doit être chargé par le module de livraison existant.')

    forbidden=['stripe','paypal','canada post','canadapost','ups.com','fedex','purolator','shippo','easypost','twilio','api.resend.com']
    for token in forbidden:
        if token in low: errors.append(f'Intégration externe interdite: {token}')

    if re.search(r'<input[^>]+(?:address|postal|zip|street)',js,re.I):
        errors.append('Le résumé ne doit pas demander une adresse exacte.')
    if re.search(r'\b(?:paper|digital|shipping)[a-z_]*\s*=\s*\d{3,}',low):
        errors.append('Le résumé ne doit pas embarquer de prix/tarif commercial fixe.')

    rows=[x.strip() for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)!=156: errors.append(f'Ledger: {len(rows)} migrations au lieu de 156; V24.5.25 doit rester frontend-only.')
    expected='20260823044507 sinjira_v24_5_24_security_definer_reconstruction_convergence'
    if not rows or rows[-1]!=expected: errors.append('V24.5.25 ne doit pas ajouter de migration Supabase.')
    if list(MIG.glob('*v24_5_25*.sql')): errors.append('Une migration V24.5.25 existe alors que ce jalon doit rester frontend-only.')

    for marker in ['frontend-only','156 migrations','frais de livraison seront à la charge du client','0 $ de frais de livraison','aucune adresse exacte','réservation reste distincte d’une vente']:
        if marker not in doc: errors.append(f'Document V24.5.25 incomplet: {marker}')

    if errors:
        print(f'ECHEC V24.5.25 résumé coût: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.25: coût affiché seulement depuis données publiées, livraison client, ramassage 0 $, null non converti en 0, aucun service payant, ledger 156 inchangé.')
    return 0

if __name__=='__main__': raise SystemExit(main())
