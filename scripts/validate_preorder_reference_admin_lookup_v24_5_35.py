#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase/migrations/20260830004410_sinjira_v24_5_35_preorder_reference_admin_lookup.sql'
JS = ROOT / 'assets/js/sinjira-admin-preorders-v24-5-4.js'
PAGE = ROOT / 'admin/sinjira/precommandes.html'
DOC = ROOT / 'PREORDER_REFERENCE_ADMIN_LOOKUP_V24_5_35.md'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
TEST = ROOT / 'supabase/tests/preorder_reference_admin_lookup_v24_5_35.test.sql'


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in [MIG, JS, PAGE, DOC, LEDGER, TEST]:
        if not path.exists(): errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors: print('- ' + error)
        return 1

    sql = read(MIG)
    low = sql.lower()
    js = read(JS)
    js_low = js.lower()
    page = read(PAGE).lower()
    doc = read(DOC).lower()
    test = read(TEST).lower()
    rows = [x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    for marker in [
        'preorder_admin_internal.admin_preorder_find_by_reference',
        'private.require_sinjira_admin_aal2()',
        "^PR-[0-9A-F]{16}$",
        'security definer',
        'security invoker',
        'revoke all on function public.admin_preorder_find_by_reference(text) from public, anon',
        'grant execute on function public.admin_preorder_find_by_reference(text) to authenticated, service_role',
    ]:
        if marker.lower() not in low: errors.append(f'Migration V24.5.35 incomplète: {marker}')

    return_match = re.search(r'admin_preorder_find_by_reference\(p_reservation_reference text\)\s*\nreturns table\((.*?)\)\s*\nlanguage', sql, re.S | re.I)
    if not return_match:
        errors.append('Signature de retour V24.5.35 introuvable.')
    else:
        return_block = return_match.group(1).lower()
        for forbidden in [' uuid', 'email', 'address', 'payment', 'preorder_id', 'product_id', 'pickup_point_id']:
            if forbidden in return_block: errors.append(f'Champ sensible interdit dans le résultat du lookup: {forbidden.strip()}')

    for marker in [
        'function installReferenceLookup()',
        'async function lookupReference(event)',
        'admin_preorder_find_by_reference',
        'PR-[0-9A-F]{16}',
        'Retrouver une réservation',
        'ni courriel, ni UUID, ni adresse',
        'Résultat volontairement minimal',
    ]:
        if marker.lower() not in js_low: errors.append(f'Console admin V24.5.35 incomplète: {marker}')

    lookup_block = js_low.split('async function lookupreference(event)', 1)[-1].split('function renderoverview()', 1)[0]
    for forbidden in ['row.user_id', 'row.preorder_id', 'row.product_id', 'row.pickup_point_id', 'row.email', 'row.public_address', 'row.payment_status', 'row.financial_commitment']:
        if forbidden in lookup_block: errors.append(f'La console expose un champ interdit: {forbidden}')

    if 'noindex,nofollow' not in page: errors.append('La console précommandes doit rester noindex,nofollow.')
    if 'sinjira-admin-preorders-v24-5-4.js?v=24.5.' not in page: errors.append('Le script admin précommandes doit garder un cache-buster versionné.')
    if 'administration privée · mfa requis' not in page: errors.append('La console n’annonce plus sa frontière admin/MFA.')

    expected_row = '20260830004410 sinjira_v24_5_35_preorder_reference_admin_lookup'
    if len(rows) < 168: errors.append(f'Ledger historique trop court: {len(rows)} migrations.')
    if rows.count(expected_row) != 1: errors.append('Le ledger doit contenir V24.5.35 exactement une fois.')
    if expected_row in rows and rows.index(expected_row) < 167: errors.append('V24.5.35 apparaît trop tôt dans le ledger historique.')

    for marker in ['168 migrations', 'mfa/aal2', 'aucune recherche par nom', 'aucun uuid', 'frais de livraison', '0 $ de frais de livraison']:
        if marker not in doc: errors.append(f'Document V24.5.35 incomplet: {marker}')

    for marker in ['anon ne peut pas rechercher', 'admin + mfa/aal2', 'résultat public ne contient ni uuid ni courriel', 'résultat public ne contient ni adresse ni donnée de paiement']:
        if marker not in test: errors.append(f'Test pgTAP V24.5.35 incomplet: {marker}')

    for forbidden in ['stripe.com', 'checkout.stripe.com', 'paypal.com', 'api.resend.com', 'twilio', 'shippo', 'easypost']:
        if forbidden in low + js_low: errors.append(f'Service externe interdit dans V24.5.35: {forbidden}')

    if errors:
        print(f'ECHEC V24.5.35 recherche admin par référence: {len(errors)} problème(s).')
        for error in errors: print('- ' + error)
        return 1
    print('OK V24.5.35 historique: lookup PR-… admin MFA/AAL2 et contrat de minimisation préservés après les versions ultérieures.')
    return 0


if __name__ == '__main__': raise SystemExit(main())
