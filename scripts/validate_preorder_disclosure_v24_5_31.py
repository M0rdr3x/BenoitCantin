#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase/migrations/20260824215053_sinjira_v24_5_31_preorder_disclosure_acknowledgement.sql'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
JS = ROOT / 'assets/js/sinjira-preorders-v24-5-3.js'
PUBLIC_PAGE = ROOT / 'projets/sinjira/romans/precommande.html'
ACCOUNT_PAGE = ROOT / 'compte/mes-achats.html'
DOC = ROOT / 'PREORDER_DISCLOSURE_ACK_V24_5_31.md'


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def compact(value):
    return re.sub(r'\s+', ' ', value.lower()).strip()


def main():
    errors = []
    for path in [MIG, LEDGER, JS, PUBLIC_PAGE, ACCOUNT_PAGE, DOC]:
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors: print('- ' + error)
        return 1

    sql = read(MIG)
    low = sql.lower()
    flat = compact(sql)
    js = read(JS)
    pages = {'page publique': read(PUBLIC_PAGE), 'Mes achats': read(ACCOUNT_PAGE)}
    doc = read(DOC).lower()
    rows = [x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    sql_markers = [
        'add column if not exists disclosure_version text',
        'add column if not exists disclosure_acknowledged_at timestamptz',
        'product_preorders_disclosure_pair_chk',
        "message = 'preorder_disclosure_required'",
        'product_preorder_reserve_confirmed',
        "v_expected_version constant text := 'preorder-disclosure-v24.5.31'",
        'p_disclosure_acknowledged is distinct from true',
        "payment_status = 'not_collected'",
        'financial_commitment = false',
        'security invoker',
        'revoke all on function public.product_preorder_reserve_confirmed',
        'from public, anon',
        'to authenticated, service_role',
    ]
    for marker in sql_markers:
        if marker not in low:
            errors.append(f'Migration V24.5.31 incomplète: {marker}')

    if "create or replace function preorder_user_internal.product_preorder_reserve(" not in low:
        errors.append('L’ancien RPC interne de réservation doit rester verrouillé explicitement.')
    old_block = low.split('create or replace function preorder_user_internal.product_preorder_reserve(', 1)[-1].split('create or replace function public.product_preorder_reserve(', 1)[0]
    if 'preorder_disclosure_required' not in old_block:
        errors.append('L’ancien RPC interne doit échouer avec PREORDER_DISCLOSURE_REQUIRED.')
    if 'insert into public.product_preorders' in old_block:
        errors.append('L’ancien RPC interne ne doit plus pouvoir écrire une réservation.')

    js_markers = [
        "const DISCLOSURE_VERSION = 'preorder-disclosure-v24.5.31'",
        "root.querySelector('[data-preorder-disclosure]')",
        'if (!nodes.disclosure?.checked)',
        "rpc('product_preorder_reserve_confirmed'",
        'p_disclosure_version: DISCLOSURE_VERSION',
        'p_disclosure_acknowledged: true',
        "nodes.disclosure.checked = false",
    ]
    for marker in js_markers:
        if marker not in js:
            errors.append(f'Runtime V24.5.31 incomplet: {marker}')
    if "rpc('product_preorder_reserve'," in js:
        errors.append('Le navigateur ne doit plus appeler l’ancien RPC sans accusé.')

    for name, page in pages.items():
        low_page = page.lower()
        if 'data-preorder-disclosure' not in page:
            errors.append(f'{name}: case de compréhension explicite absente.')
        if re.search(r'<input[^>]*checked[^>]*data-preorder-disclosure|<input[^>]*data-preorder-disclosure[^>]*checked', page, re.I):
            errors.append(f'{name}: la case de compréhension ne doit jamais être précochée.')
        for marker in [
            'frais de livraison seront à ma charge',
            '0 $ de frais de livraison',
            'non contractuelles',
            'total final',
            'pas une commande',
        ]:
            if marker not in low_page:
                errors.append(f'{name}: avertissement incomplet: {marker}')
        if 'sinjira-preorders-v24-5-3.js?v=24.5.31' not in page:
            errors.append(f'{name}: cache-buster V24.5.31 absent.')

    row = '20260824215053 sinjira_v24_5_31_preorder_disclosure_acknowledgement'
    if len(rows) != 164:
        errors.append(f'Ledger: {len(rows)} migrations au lieu de 164.')
    if rows.count(row) != 1:
        errors.append('Le ledger doit contenir exactement une occurrence de V24.5.31.')
    if not rows or rows[-1] != row:
        errors.append('V24.5.31 doit être la dernière migration du ledger courant.')

    for marker in [
        'réserver aujourd’hui ne signifie jamais consentir à payer demain',
        'frais de livraison seront à la charge du client',
        '0 $ de frais de livraison',
        'non contractuelles',
        'preorder-disclosure-v24.5.31',
        'aucun consentement financier',
        '164 migrations',
        'aucun historique détaillé supplémentaire',
    ]:
        if marker not in doc:
            errors.append(f'Document V24.5.31 incomplet: {marker}')

    forbidden_runtime = ['stripe', 'paypal', 'api.resend.com', 'twilio', 'shippo', 'easypost']
    combined_runtime = (js + sql).lower()
    for token in forbidden_runtime:
        if token in combined_runtime:
            errors.append(f'Intégration externe interdite dans V24.5.31: {token}')

    if errors:
        print(f'ECHEC V24.5.31 accusé de compréhension: {len(errors)} problème(s).')
        for error in errors: print('- ' + error)
        return 1

    print('OK V24.5.31: accusé explicite non financier requis, ancien RPC verrouillé, livraison/ramassage/estimations transparents, ledger 164 synchronisé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
