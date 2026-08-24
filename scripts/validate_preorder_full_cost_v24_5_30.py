#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULFILLMENT = ROOT / 'assets/js/sinjira-preorder-fulfillment-v24-5-6.js'
COST = ROOT / 'assets/js/sinjira-preorder-cost-summary-v24-5-25.js'
TAX = ROOT / 'assets/js/sinjira-preorder-tax-estimate-v24-5-27.js'
PUBLIC_PAGE = ROOT / 'projets/sinjira/romans/precommande.html'
ACCOUNT_PAGE = ROOT / 'compte/mes-achats.html'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
DOC = ROOT / 'PREORDER_FULL_COST_CONTRACT_V24_5_30.md'


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in [FULFILLMENT, COST, TAX, PUBLIC_PAGE, ACCOUNT_PAGE, LEDGER, DOC]:
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors: print('- ' + error)
        return 1

    fulfillment = read(FULFILLMENT)
    cost = read(COST)
    tax = read(TAX)
    public_page = read(PUBLIC_PAGE)
    account_page = read(ACCOUNT_PAGE)
    doc = read(DOC).lower()
    rows = [x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    for marker in [
        "import './sinjira-preorder-cost-summary-v24-5-25.js'",
        "import './sinjira-preorder-tax-estimate-v24-5-27.js'",
    ]:
        if marker not in fulfillment:
            errors.append(f'Chaîne frontend incomplète: {marker}')

    for name, page in [('page publique', public_page), ('Mes achats', account_page)]:
        if 'sinjira-preorder-fulfillment-v24-5-6.js' not in page:
            errors.append(f'{name}: module fulfillment absent.')
        if 'Les frais de livraison seront à la charge du client.' not in page:
            errors.append(f'{name}: avertissement frais de livraison absent.')
        if '0 $' not in page or 'ramassage' not in page.lower():
            errors.append(f'{name}: ramassage à 0 $ non explicite.')

    cost_markers = [
        'Sous-total estimatif avant taxes',
        'Réservation ≠ vente.',
        'Aucun paiement n’est prélevé maintenant.',
        'Aucune adresse exacte n’est demandée',
        "row.shipping_customer_pays === true",
        "row.estimate_nonbinding === true",
        "info.sales_enabled !== false",
        "info.checkout_enabled !== false",
        "info.payment_enabled !== false",
        "info.auto_conversion_allowed !== false",
        "value === null || value === undefined || value === ''",
    ]
    for marker in cost_markers:
        if marker not in cost:
            errors.append(f'Résumé de coût incomplet: {marker}')

    tax_markers = [
        'Choisissez explicitement un profil publié correspondant à votre situation.',
        'SINJIRA ne sélectionne jamais une zone fiscale à votre place.',
        'Taxes estimées',
        'Total indicatif après taxes',
        'billing_authoritative !== false',
        'estimate_nonbinding !== true',
        'final_tax_confirmation_required !== true',
        'external_tax_api_enabled !== false',
        'Les taxes réellement applicables et le montant final devront être confirmés avant toute transaction.',
    ]
    for marker in tax_markers:
        if marker not in tax:
            errors.append(f'Estimation fiscale incomplète: {marker}')

    forbidden_runtime = ['stripe', 'paypal', 'api.resend.com', 'twilio', 'shippo', 'easypost']
    combined = (fulfillment + cost + tax).lower()
    for token in forbidden_runtime:
        if token in combined:
            errors.append(f'Intégration externe interdite dans le runtime de précommande: {token}')

    if len(rows) != 163:
        errors.append(f'Ledger: {len(rows)} migrations au lieu de 163; V24.5.30 ne doit ajouter aucune migration.')
    if not rows or rows[-1] != '20260824013042 sinjira_v24_5_14_admin_privacy_safety_aal2_hardening':
        errors.append('V24.5.30 doit conserver la dernière migration production 20260824013042.')

    for marker in [
        'livraison sont à la charge du client',
        'ramassage sur place ajoute 0 $',
        'zone fiscale',
        'non contractuelle',
        '163 migrations',
        'aucune migration supabase',
        'checkout',
        'conversion automatique',
    ]:
        if marker not in doc:
            errors.append(f'Document V24.5.30 incomplet: {marker}')

    if errors:
        print(f'ECHEC V24.5.30 transparence précommande: {len(errors)} problème(s).')
        for error in errors: print('- ' + error)
        return 1

    print('OK V24.5.30: coût, livraison/ramassage et taxes sont chaînés; aucune vente, paiement, API transporteur/fiscale ou migration ajoutée.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
