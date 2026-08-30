#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / 'assets/js/sinjira-preorders-v24-5-3.js'
DOC = ROOT / 'PREORDER_REFERENCE_COPY_V24_5_34.md'
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

    for marker in [
        'async function copyReservationReference(reference, button, statusNode)',
        "/^PR-[0-9A-F]{16}$/",
        'navigator.clipboard?.writeText',
        'navigator.clipboard.writeText(value)',
        "document.createElement('textarea')",
        "document.execCommand('copy')",
        'data-preorder-copy',
        'Copier la référence',
        'data-preorder-copy-status',
        'role="status" aria-live="polite"',
        'Référence de réservation copiée.',
        'copyReservationReference(preorder.reservation_reference, copyButton, copyStatus)',
    ]:
        if marker not in js: errors.append(f'Runtime V24.5.34 incomplet: {marker}')

    copy_block = low.split('async function copyreservationreference', 1)[-1].split('function printpreorderconfirmation', 1)[0]
    for forbidden in ['fetch(', '.rpc(', 'xmlhttprequest', 'websocket', 'eventsource', 'sendbeacon', 'localstorage', 'sessionstorage', 'indexeddb']:
        if forbidden in copy_block: errors.append(f'La copie de référence ne doit ni transmettre ni stocker: {forbidden}')

    for forbidden in ['preorder_id', 'user_id', 'product_id', 'pickup_point_id']:
        if forbidden in copy_block: errors.append(f'Identifiant interne interdit dans la copie: {forbidden}')

    for name, page in [('page publique', pages[0]), ('Mes achats', pages[1])]:
        if 'sinjira-preorders-v24-5-3.js?v=24.5.34' not in page:
            errors.append(f'{name}: cache-buster V24.5.34 absent.')

    expected_last = '20260830001742 sinjira_v24_5_32_user_rights_redundant_boundary_cleanup'
    if len(rows) != 167:
        errors.append(f'Ledger: {len(rows)} migrations au lieu de 167; V24.5.34 ne doit pas ajouter de migration.')
    if not rows or rows[-1] != expected_last:
        errors.append('V24.5.34 ne doit pas modifier la dernière migration production actuelle.')

    for marker in [
        'copie locale de la référence', 'navigator.clipboard.writetext', 'repli local',
        'aucun uuid', 'aucun événement de copie', 'aucune migration supabase',
        '167 migrations', 'frais de livraison', '0 $ de frais de livraison'
    ]:
        if marker not in doc: errors.append(f'Document V24.5.34 incomplet: {marker}')

    combined = low + '\n' + doc
    for forbidden in ['stripe.com', 'checkout.stripe.com', 'paypal.com', 'api.resend.com', 'twilio', 'shippo', 'easypost']:
        if forbidden in combined: errors.append(f'Intégration externe interdite dans V24.5.34: {forbidden}')

    if errors:
        print(f'ECHEC V24.5.34 copie de référence: {len(errors)} problème(s).')
        for error in errors: print('- ' + error)
        return 1
    print('OK V24.5.34: copie locale de PR-…, accessible, sans UUID, stockage, réseau, service payant ni nouvelle migration; ledger 167 inchangé.')
    return 0


if __name__ == '__main__': raise SystemExit(main())
