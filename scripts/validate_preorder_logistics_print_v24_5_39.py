#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JS=ROOT/'assets/js/sinjira-admin-preorder-workflow-v24-5-36.js'
DOC=ROOT/'PREORDER_LOGISTICS_PRINT_V24_5_39.md'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'

def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''

def main():
    errors=[]
    for p in [JS,DOC,LEDGER]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1
    js=read(JS).lower(); doc=read(DOC).lower()
    rows=[x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    for marker in ['v24.5.39 · préparation logistique locale','data-pa-logistics-print','imprimer feuille locale','function printlogisticssheet','window.open(','window.print()','document.write(sheet)','logisticssummary(rows)','document interne préparatoire','livraison — frais client','ramassage — 0 $ livraison']:
        if marker not in js: errors.append(f'Impression locale incomplète: {marker}')

    for marker in ['reservation_reference','product_name','quantity','preferred_format','fulfillment_preference','pickup_point_label','pickup_city','workflow_state','disclosure_version','disclosure_acknowledged_at']:
        if marker not in js: errors.append(f'Champ logistique minimal absent du rendu: {marker}')

    for forbidden in ['row.user_id','row.email','row.phone','row.public_address','row.shipping_address','row.billing_address','row.payment_status','row.financial_commitment','navigator.sendbeacon','xmlhttprequest']:
        if forbidden in js: errors.append(f'Surface privée/réseau interdite dans la feuille locale: {forbidden}')

    print_slice=js[js.find('function printlogisticssheet'):js.find('function bind()')]
    if 'fetch(' in print_slice: errors.append('La feuille imprimable ne doit effectuer aucun fetch réseau.')
    if 'escapehtml(' not in print_slice: errors.append('Les données de la feuille imprimable doivent être échappées.')

    for marker in ['aucun fichier n’est téléversé','ni uuid','window.print','aucune api transporteur','0 $ de frais de livraison','172 migrations','aucune migration supabase']:
        if marker not in doc: errors.append(f'Document V24.5.39 incomplet: {marker}')

    expected='20260830035043 sinjira_v24_5_38_preorder_logistics_queue'
    if len(rows)!=172: errors.append(f'Ledger: {len(rows)} migrations au lieu de 172; V24.5.39 ne doit pas ajouter de migration.')
    if not rows or rows[-1]!=expected: errors.append('Le ledger V24.5.39 doit rester clôturé par V24.5.38.')

    forbidden_providers=['stripe','paypal','resend','twilio','shippo','easypost','fedex','ups.com','canadapost','canada post']
    for token in forbidden_providers:
        if token in print_slice: errors.append(f'Fournisseur externe interdit dans la feuille imprimable: {token}')

    if errors:
        print(f'ECHEC V24.5.39 impression logistique: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.39: feuille logistique imprimable localement, données minimales échappées, aucun upload/réseau/paiement, ledger inchangé à 172.')
    return 0

if __name__=='__main__': raise SystemExit(main())
