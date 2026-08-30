#!/usr/bin/env python3
from pathlib import Path
import re

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
        if not re.search(r'sinjira-preorders-v24-5-3\.js\?v=24\.5\.(?:3[4-9]|[4-9]\d|\d{3,})', page):
            errors.append(f'{name}: cache-buster V24.5.34 ou ultérieur absent.')

    historical_anchor = '20260830001742 sinjira_v24_5_32_user_rights_redundant_boundary_cleanup'
    if len(rows) < 167:
        errors.append(f'Ledger: {len(rows)} migrations; V24.5.34 exige au moins les 167 présentes lors de sa livraison.')
    if rows.count(historical_anchor) != 1:
        errors.append('Le ledger doit conserver exactement une occurrence de l’ancre production présente lors de V24.5.34.')

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
    print('OK V24.5.34 historique: copie locale PR-… conservée, sans UUID, stockage, réseau ni service payant; ledger peut évoluer au-delà de 167.')
    return 0


if __name__ == '__main__': raise SystemExit(main())
