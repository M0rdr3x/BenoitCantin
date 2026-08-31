#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JS=ROOT/'assets/js/sinjira-admin-preorder-workflow-v24-5-36.js'
DOC=ROOT/'PREORDER_LOGISTICS_PRINT_HARDENING_V24_5_40.md'
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
    start=js.find('function printlogisticssheet')
    end=js.find('function bind()',start)
    print_slice=js[start:end] if start>=0 and end>start else ''

    for marker in [
        'content-security-policy', "default-src 'none'", "connect-src 'none'",
        "object-src 'none'", "frame-src 'none'", "base-uri 'none'", "form-action 'none'",
        'name="referrer" content="no-referrer"', 'id="sinjira-local-print"',
        "addeventlistener('click', () => printwindow.print())", 'printwindow.opener = null',
        'document.write(sheet)', 'escapehtml('
    ]:
        if marker not in print_slice: errors.append(f'Durcissement impression incomplet: {marker}')

    for forbidden in ['onclick=', '<script', 'fetch(', 'xmlhttprequest', 'sendbeacon', 'websocket', 'eventsource']:
        if forbidden in print_slice: errors.append(f'Comportement interdit dans la feuille locale: {forbidden}')
    for forbidden in ['row.user_id','row.email','row.phone','row.shipping_address','row.billing_address','row.payment_status','row.financial_commitment']:
        if forbidden in print_slice: errors.append(f'Donnée privée interdite dans la feuille locale: {forbidden}')

    for marker in ['livraison : frais à la charge du client','ramassage : 0 $ de frais de livraison','aucun gestionnaire `onclick`','window.opener','default-src \'none\'','172 migrations','aucune migration supabase']:
        if marker not in doc: errors.append(f'Document V24.5.40 incomplet: {marker}')

    expected='20260830035043 sinjira_v24_5_38_preorder_logistics_queue'
    if len(rows)<172: errors.append(f'Ledger régressé: {len(rows)} migrations, moins que les 172 connues en V24.5.40.')
    if len(rows)>=172 and rows[171]!=expected: errors.append('L’historique V24.5.40 n’est plus aligné sur la 172e migration canonique.')
    if rows.count(expected)!=1: errors.append('La migration terminale connue en V24.5.40 doit exister exactement une fois.')

    for token in ['stripe','paypal','resend','twilio','shippo','easypost','fedex','ups.com','canadapost','canada post']:
        if token in print_slice: errors.append(f'Fournisseur externe interdit dans V24.5.40: {token}')

    if errors:
        print(f'ECHEC V24.5.40 durcissement impression locale: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.40 historique: CSP locale restrictive, aucun réseau/opener, minimisation conservée; migrations ultérieures autorisées.')
    return 0

if __name__=='__main__': raise SystemExit(main())
