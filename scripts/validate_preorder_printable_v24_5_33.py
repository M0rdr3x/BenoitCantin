#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / 'assets/js/sinjira-preorders-v24-5-3.js'
DOC = ROOT / 'PREORDER_PRINTABLE_CONFIRMATION_V24_5_33.md'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
PUBLIC_PAGE = ROOT / 'projets/sinjira/romans/precommande.html'
ACCOUNT_PAGE = ROOT / 'compte/mes-achats.html'


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in [JS, DOC, LEDGER, PUBLIC_PAGE, ACCOUNT_PAGE]:
        if not path.exists(): errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors: print('- ' + error)
        return 1

    js = read(JS)
    low = js.lower()
    doc = read(DOC).lower()
    pages = [read(PUBLIC_PAGE), read(ACCOUNT_PAGE)]
    rows = [x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    required_js = [
        'function printPreorderConfirmation(preorder)',
        "window.open('', '_blank'",
        'printWindow.opener = null',
        'printWindow.document.write',
        'printWindow.print()',
        'data-preorder-print',
        'Imprimer / enregistrer en PDF',
        'Document généré localement dans votre navigateur',
        'SINJIRA™ n’enregistre pas la création, l’impression ou l’enregistrement PDF',
        'ni un UUID, ni un identifiant technique du compte, ni un numéro de commande',
        'ni une facture, ni un reçu de paiement, ni une promesse de prix',
        'frais de livraison seront à la charge du client',
        '0 $ de frais de livraison',
    ]
    for marker in required_js:
        if marker not in js: errors.append(f'Runtime V24.5.33 incomplet: {marker}')

    for page_name, page in [('page publique', pages[0]), ('Mes achats', pages[1])]:
        if 'sinjira-preorders-v24-5-3.js?v=24.5.33' not in page:
            errors.append(f'{page_name}: cache-buster V24.5.33 absent.')

    for forbidden in [
        'onclick=', '<script', 'preorder_id', 'user_id', 'product_id', 'pickup_point_id',
        'localstorage', 'sessionstorage', 'indexeddb', 'navigator.sendbeacon',
        'jspdf', 'pdf-lib', 'html2pdf', 'stripe.com', 'checkout.stripe.com', 'paypal.com',
        'api.resend.com', 'twilio', 'shippo', 'easypost', 'fedex api', 'canada post api'
    ]:
        if forbidden in low: errors.append(f'Élément interdit dans la confirmation locale V24.5.33: {forbidden}')

    print_block = js.split('function printPreorderConfirmation(preorder)', 1)[-1].split('function renderState', 1)[0].lower()
    for forbidden in ['fetch(', '.rpc(', 'xmlhttprequest', 'websocket', 'new eventsource', 'navigator.sendbeacon']:
        if forbidden in print_block: errors.append(f'La fonction d’impression ne doit faire aucun appel réseau: {forbidden}')

    if len(rows) != 165: errors.append(f'Ledger: {len(rows)} migrations au lieu de 165; V24.5.33 ne doit pas ajouter de migration.')
    if not rows or rows[-1] != '20260829233536 sinjira_v24_5_32_preorder_receipt_and_uuid_privacy':
        errors.append('V24.5.33 ne doit pas modifier la dernière migration production V24.5.32.')

    for marker in [
        'confirmation imprimable locale', 'aucun uuid', 'aucun service pdf externe',
        'ni une facture', 'ni un reçu de paiement', 'ni une commande',
        'frais de livraison restent à la charge du client', '0 $ de frais de livraison',
        'aucune migration supabase supplémentaire', '165 migrations'
    ]:
        if marker not in doc: errors.append(f'Document V24.5.33 incomplet: {marker}')

    if errors:
        print(f'ECHEC V24.5.33 confirmation imprimable: {len(errors)} problème(s).')
        for error in errors: print('- ' + error)
        return 1
    print('OK V24.5.33: copie imprimable locale, cache-buster courant, sans UUID, stockage, appel réseau, service payant ni nouvelle migration.')
    return 0


if __name__ == '__main__': raise SystemExit(main())
