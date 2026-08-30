#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT = ROOT / 'compte' / 'mes-achats.html'
PUBLIC = ROOT / 'projets' / 'sinjira' / 'romans' / 'precommande.html'
DOC = ROOT / 'PREORDER_PUBLIC_CACHE_CONVERGENCE_V24_5_44.md'
LEDGER = ROOT / 'supabase' / 'production-migration-ledger.txt'

ASSETS = [
    'sinjira-preorders-v24-5-3.css',
    'sinjira-preorder-commercial-v24-5-5.css',
    'sinjira-preorder-fulfillment-v24-5-6.css',
    'sinjira-preorders-v24-5-3.js',
    'sinjira-preorder-commercial-v24-5-5.js',
    'sinjira-preorder-fulfillment-v24-5-6.js',
]


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def check_page(path, errors):
    text = read(path)
    low = text.lower()
    if not text:
        errors.append(f'Page absente ou vide: {path.relative_to(ROOT)}')
        return

    for asset in ASSETS:
        expected = asset + '?v=24.5.44'
        if expected not in text:
            errors.append(f'{path.relative_to(ROOT)} ne charge pas {expected}')
        matches = re.findall(re.escape(asset) + r'\?v=([^"\'<>\s]+)', text)
        if matches != ['24.5.44']:
            errors.append(f'{path.relative_to(ROOT)} cache-buster inattendu pour {asset}: {matches}')

    semantic_markers = [
        'aucun paiement',
        'une réservation n’est pas une commande',
        'frais de livraison seront à',
        '0 $',
        'indicatives et non contractuelles',
    ]
    for marker in semantic_markers:
        if marker not in low:
            errors.append(f'{path.relative_to(ROOT)} a perdu un garde utilisateur: {marker}')

    if 'compte/mes-achats.html' in path.as_posix():
        for marker in ['aucune donnée bancaire', 'adresse de facturation', 'adresse de livraison']:
            if marker not in low:
                errors.append(f'Mes achats a perdu le garde de minimisation: {marker}')


def main():
    errors = []
    for path in [ACCOUNT, PUBLIC, DOC, LEDGER]:
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')

    if errors:
        for err in errors:
            print('- ' + err)
        return 1

    check_page(ACCOUNT, errors)
    check_page(PUBLIC, errors)

    doc = read(DOC).lower()
    for marker in [
        '172 migrations',
        'aucune migration',
        'réservation n’est pas une commande',
        'frais de livraison',
        '0 $ de frais de livraison',
        'indicatives et non contractuelles',
        'aucun checkout',
        'aucun fournisseur externe',
    ]:
        if marker not in doc:
            errors.append(f'Document V24.5.44 incomplet: {marker}')

    rows = [line for line in read(LEDGER).splitlines() if line.strip() and not line.startswith('#')]
    if len(rows) != 172:
        errors.append(f'Ledger modifié: {len(rows)} migrations au lieu de 172.')

    changed = (read(ACCOUNT) + read(PUBLIC) + read(DOC)).lower()
    forbidden = [
        'api.stripe.com', 'paypal.com/sdk', 'api.resend.com', 'twilio.com',
        'api.shippo.com', 'api.easypost.com', 'api.fedex.com', 'api.ups.com',
        'canada post api key', 'external_tax_api_enabled = true',
        'payment_enabled = true', 'checkout_enabled = true', 'sales_enabled = true',
    ]
    for token in forbidden:
        if token in changed:
            errors.append(f'Activation externe/commerciale interdite dans V24.5.44: {token}')

    if errors:
        print(f'ECHEC V24.5.44 cache public précommandes: {len(errors)} problème(s).')
        for err in errors:
            print('- ' + err)
        return 1

    print('OK V24.5.44: deux surfaces utilisateur convergées sur cache 24.5.44; règles livraison, ramassage, non-paiement et minimisation conservées; ledger 172 inchangé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
