#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADMIN_FULFILLMENT = ROOT / 'assets/js/sinjira-admin-preorder-fulfillment-v24-5-6.js'
ADMIN_TAX = ROOT / 'assets/js/sinjira-admin-preorder-tax-v24-5-27.js'
PUBLIC_FULFILLMENT = ROOT / 'assets/js/sinjira-preorder-fulfillment-v24-5-6.js'
COST = ROOT / 'assets/js/sinjira-preorder-cost-summary-v24-5-25.js'
TAX = ROOT / 'assets/js/sinjira-preorder-tax-estimate-v24-5-27.js'
READINESS = ROOT / 'admin/sinjira/precommandes-readiness.html'
DOC = ROOT / 'PREORDER_COMMERCIAL_CONVERGENCE_V24_5_42.md'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in [ADMIN_FULFILLMENT, ADMIN_TAX, PUBLIC_FULFILLMENT, COST, TAX, READINESS, DOC, LEDGER]:
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- ' + e)
        return 1

    admin = read(ADMIN_FULFILLMENT)
    admin_tax = read(ADMIN_TAX)
    public = read(PUBLIC_FULFILLMENT)
    cost = read(COST)
    tax = read(TAX)
    readiness = read(READINESS)
    doc = read(DOC).lower()
    ledger_rows = [x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    required_admin = [
        "import './sinjira-admin-preorder-tax-v24-5-27.js';",
        '/admin/sinjira/precommandes-readiness.html',
        'ensureReadinessLink()',
    ]
    for marker in required_admin:
        if marker not in admin:
            errors.append(f'Console admin non convergée: {marker}')

    required_public = [
        "import './sinjira-preorder-cost-summary-v24-5-25.js';",
        "import './sinjira-preorder-tax-estimate-v24-5-27.js';",
    ]
    for marker in required_public:
        if marker not in public:
            errors.append(f'Parcours public incomplet: {marker}')

    for marker in ['requireAdminAal2', 'admin_preorder_tax_profile_save', 'admin_preorder_tax_profile_publish', 'API fiscale externe : désactivée']:
        if marker not in admin_tax:
            errors.append(f'Éditeur fiscal incomplet: {marker}')

    for marker in ['shipping_customer_pays === true', 'estimate_nonbinding === true', 'Réservation ≠ vente']:
        if marker not in cost:
            errors.append(f'Résumé de coût ne conserve pas le garde: {marker}')

    for marker in ['external_tax_api_enabled !== false', 'billing_authoritative !== false', 'final_tax_confirmation_required !== true']:
        if marker not in tax:
            errors.append(f'Estimation fiscale ne conserve pas le garde: {marker}')

    forbidden_readiness = ['ouvrir les ventes</button>', 'activer le paiement</button>', 'convertir les réservations</button>']
    low_ready = readiness.lower()
    for marker in forbidden_readiness:
        if marker in low_ready:
            errors.append(f'La checklist contient une action commerciale interdite: {marker}')

    if len(ledger_rows) != 172:
        errors.append(f'Ledger modifié: {len(ledger_rows)} migrations au lieu de 172.')

    for marker in ['172 migrations', 'aucune migration', 'réservation ≠ commande', 'frais de livraison à la charge du client', '0 $ de frais de livraison', 'external_tax_api_enabled = false', 'aucun checkout']:
        if marker not in doc:
            errors.append(f'Document V24.5.42 incomplet: {marker}')

    forbidden_external = ['stripe', 'paypal', 'twilio', 'api.resend.com', 'shippo', 'easypost', 'canada post api', 'fedex api', 'ups api']
    changed_surface = (admin + doc).lower()
    for token in forbidden_external:
        if token in changed_surface:
            errors.append(f'Intégration payante/externe interdite dans V24.5.42: {token}')

    if errors:
        print(f'ECHEC V24.5.42: {len(errors)} problème(s).')
        for e in errors: print('- ' + e)
        return 1

    print('OK V24.5.42: fiscalité admin et checklist accessibles, résumé public prix/livraison/taxes conservé, ledger 172 inchangé, aucun paiement/checkout/fournisseur externe ajouté.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
