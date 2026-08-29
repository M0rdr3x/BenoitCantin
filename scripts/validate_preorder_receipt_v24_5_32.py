#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase/migrations/20260829233536_sinjira_v24_5_32_preorder_receipt_and_uuid_privacy.sql'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
JS = ROOT / 'assets/js/sinjira-preorders-v24-5-3.js'
PUBLIC_PAGE = ROOT / 'projets/sinjira/romans/precommande.html'
ACCOUNT_PAGE = ROOT / 'compte/mes-achats.html'
DOC = ROOT / 'PREORDER_RECEIPT_UUID_PRIVACY_V24_5_32.md'
TEST = ROOT / 'supabase/tests/preorder_receipt_uuid_privacy_v24_5_32.test.sql'


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in [MIG, LEDGER, JS, PUBLIC_PAGE, ACCOUNT_PAGE, DOC, TEST]:
        if not path.exists(): errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors: print('- ' + error)
        return 1

    sql = read(MIG).lower()
    js = read(JS)
    pages = (read(PUBLIC_PAGE) + '\n' + read(ACCOUNT_PAGE)).lower()
    doc = read(DOC).lower()
    rows = [x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    for marker in [
        'add column if not exists reservation_reference text',
        "'pr-' || upper(encode(gen_random_bytes(8), 'hex'))",
        'product_preorders_reservation_reference_uidx',
        "check (reservation_reference ~ '^pr-[0-9a-f]{16}$')",
        'drop function if exists public.product_preorder_my_status(text)',
        'security invoker',
        'security definer',
        'revoke all on function public.product_preorder_my_status(text) from public, anon',
        'grant execute on function public.product_preorder_my_status(text) to authenticated, service_role',
        'pp.reservation_reference',
        'pp.disclosure_version',
        'pp.disclosure_acknowledged_at',
        'pp.fulfillment_preference',
        'pp.user_id = auth.uid()',
    ]:
        if marker not in sql: errors.append(f'Migration V24.5.32 incomplète: {marker}')

    public_result = sql.split('create function public.product_preorder_my_status',1)[-1]
    public_result = public_result.split('language sql',1)[0]
    for forbidden in ['preorder_id uuid','user_id uuid','product_id uuid','pickup_point_id uuid']:
        if forbidden in public_result: errors.append(f'Identifiant interne exposé dans le résultat public: {forbidden}')

    for marker in [
        'Référence de réservation',
        'reservation_reference',
        'Conditions de réservation',
        'disclosure_acknowledged_at',
        'Réception souhaitée',
        'Cette référence identifie seulement votre réservation SINJIRA™',
    ]:
        if marker not in js: errors.append(f'Runtime V24.5.32 incomplet: {marker}')
    if 'preorder_id' in js or 'product_id' in js or 'user_id' in js:
        errors.append('Le runtime V24.5.32 ne doit manipuler aucun UUID interne de précommande.')

    if not re.search(r'sinjira-preorders-v24-5-3\.js\?v=24\.5\.(?:3[2-9]|[4-9]\d|\d{3,})', pages):
        errors.append('Les pages doivent charger le runtime de précommande avec un cache-buster V24.5.32 ou ultérieur.')
    for marker in ['référence de réservation indépendante','frais de livraison seront à la charge du client','0 $ de frais de livraison']:
        if marker not in pages: errors.append(f'Transparence utilisateur V24.5.32 absente: {marker}')

    row = '20260829233536 sinjira_v24_5_32_preorder_receipt_and_uuid_privacy'
    if len(rows) != 165: errors.append(f'Ledger: {len(rows)} migrations au lieu de 165.')
    if rows.count(row) != 1: errors.append('Le ledger doit contenir exactement une occurrence de V24.5.32.')
    if not rows or rows[-1] != row: errors.append('V24.5.32 doit rester la dernière migration tant qu’aucune migration ultérieure n’est ajoutée.')

    for marker in ['aucun uuid interne','référence visible','anciennes réservations','165 migrations','aucun paiement','aucune adresse exacte']:
        if marker not in doc: errors.append(f'Document V24.5.32 incomplet: {marker}')

    combined = (sql + '\n' + js).lower()
    for forbidden in ['stripe.com','checkout.stripe.com','paypal.com','api.resend.com','twilio','shippo','easypost','canada post api','fedex api']:
        if forbidden in combined: errors.append(f'Intégration externe interdite dans V24.5.32: {forbidden}')

    if errors:
        print(f'ECHEC V24.5.32 preuve de réservation: {len(errors)} problème(s).')
        for error in errors: print('- ' + error)
        return 1
    print('OK V24.5.32 historique: référence indépendante, aucun UUID public, preuve de transparence conservée et cache-buster V24.5.32 ou ultérieur.')
    return 0


if __name__ == '__main__': raise SystemExit(main())
