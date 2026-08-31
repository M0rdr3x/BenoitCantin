#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'admin/sinjira/precommandes.html'
DOC = ROOT / 'PREORDER_ADMIN_CACHE_CONVERGENCE_V24_5_43.md'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'

MODULES = [
    'sinjira-admin-preorders-v24-5-4.js?v=24.5.43',
    'sinjira-admin-preorder-workflow-v24-5-36.js?v=24.5.43',
    'sinjira-admin-preorder-commercial-v24-5-5.js?v=24.5.43',
    'sinjira-admin-preorder-fulfillment-v24-5-6.js?v=24.5.43',
]


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in [PAGE, DOC, LEDGER]:
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- ' + e)
        return 1

    page = read(PAGE)
    doc = read(DOC).lower()
    ledger_rows = [x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    for marker in MODULES:
        if marker not in page:
            errors.append(f'Cache-buster admin manquant: {marker}')

    if 'V24.5.43 · administration privée · MFA requis' not in page:
        errors.append('Le marqueur de version V24.5.43 manque dans la console admin.')

    stale = [
        'sinjira-admin-preorders-v24-5-4.js?v=24.5.36',
        'sinjira-admin-preorder-workflow-v24-5-36.js?v=24.5.36',
        'sinjira-admin-preorder-commercial-v24-5-5.js?v=24.5.5',
        'sinjira-admin-preorder-fulfillment-v24-5-6.js?v=24.5.6',
    ]
    for marker in stale:
        if marker in page:
            errors.append(f'Ancien cache-buster encore présent: {marker}')

    required_contract = [
        'aucun paiement',
        'aucun checkout',
        'frais de livraison à la charge du client',
        '0 $ de frais de livraison',
        '172 migrations',
        'aucune migration supabase',
    ]
    for marker in required_contract:
        if marker not in doc:
            errors.append(f'Document V24.5.43 incomplet: {marker}')

    historical_row = '20260830035043 sinjira_v24_5_38_preorder_logistics_queue'
    if len(ledger_rows) < 172:
        errors.append(f'Ledger régressé: {len(ledger_rows)} migrations, moins que les 172 connues en V24.5.43.')
    if len(ledger_rows) >= 172 and ledger_rows[171] != historical_row:
        errors.append('L’historique V24.5.43 n’est plus aligné sur la 172e migration canonique.')
    if ledger_rows.count(historical_row) != 1:
        errors.append('La migration terminale connue en V24.5.43 doit exister exactement une fois.')

    forbidden = ['stripe', 'paypal', 'twilio', 'api.resend.com', 'shippo', 'easypost']
    changed = (page + doc).lower()
    for token in forbidden:
        if token in changed:
            errors.append(f'Intégration externe/payante interdite dans V24.5.43: {token}')

    if errors:
        print(f'ECHEC V24.5.43 cache admin: {len(errors)} problème(s).')
        for e in errors: print('- ' + e)
        return 1

    print('OK V24.5.43 historique: cache admin 24.5.43 et garde-fous commerciaux conservés; migrations ultérieures autorisées.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
