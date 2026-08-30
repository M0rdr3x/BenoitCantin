#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase/migrations/20260830012533_sinjira_v24_5_36_preorder_admin_workflow.sql'
JS = ROOT / 'assets/js/sinjira-admin-preorder-workflow-v24-5-36.js'
PAGE = ROOT / 'admin/sinjira/precommandes.html'
DOC = ROOT / 'PREORDER_ADMIN_WORKFLOW_V24_5_36.md'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
TEST = ROOT / 'supabase/tests/preorder_admin_workflow_v24_5_36.test.sql'


def read(path): return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in [MIG, JS, PAGE, DOC, LEDGER, TEST]:
        if not path.exists(): errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors: print('- ' + error)
        return 1

    sql = read(MIG); low = sql.lower(); js = read(JS); js_low = js.lower(); page = read(PAGE).lower(); doc = read(DOC).lower(); test = read(TEST).lower()
    rows = [x for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    for marker in [
        'create table if not exists private.preorder_admin_workflow',
        "workflow_state in ('pending','ready_for_future_contact','completed')",
        'alter table private.preorder_admin_workflow enable row level security',
        'revoke all on table private.preorder_admin_workflow from public, anon, authenticated',
        'admin_preorder_workflow_by_reference', 'admin_preorder_set_workflow_state', 'admin_preorder_workflow_queue',
        'private.require_sinjira_admin_aal2()', "^PR-[0-9A-F]{16}$", 'security definer', 'security invoker',
        'revoke all on function public.admin_preorder_workflow_by_reference(text) from public, anon',
        'revoke all on function public.admin_preorder_set_workflow_state(text,text) from public, anon',
        'revoke all on function public.admin_preorder_workflow_queue(text,integer) from public, anon',
    ]:
        if marker.lower() not in low: errors.append(f'Migration V24.5.36 incomplète: {marker}')

    if re.search(r'\b(note|notes|details|email|address|phone)\b\s+(text|varchar)', low):
        errors.append('Le suivi V24.5.36 ne doit pas introduire de champ libre/PII.')

    for marker in ['suivi interne non financier','admin_preorder_workflow_queue','admin_preorder_set_workflow_state','aucune note libre','aucun avis, aucune commande et aucun paiement']:
        if marker not in js_low: errors.append(f'Interface V24.5.36 incomplète: {marker}')
    for forbidden in ['row.email','row.user_id','row.preorder_id','row.product_id','row.public_address','row.payment_status','row.financial_commitment']:
        if forbidden in js_low: errors.append(f'Interface V24.5.36 expose un champ interdit: {forbidden}')

    if 'noindex,nofollow' not in page: errors.append('La console admin doit rester noindex,nofollow.')
    if 'administration privée · mfa requis' not in page: errors.append('Le garde administration privée + MFA doit rester visible dans la console.')
    if not re.search(r'sinjira-admin-preorder-workflow-v24-5-36\.js\?v=24\.5\.\d+', page):
        errors.append('Le module physique V24.5.36 doit rester chargé avec un cache-buster V24.5.x.')

    expected = '20260830012533 sinjira_v24_5_36_preorder_admin_workflow'
    if len(rows) < 169: errors.append(f'Ledger historique tronqué: {len(rows)} migrations, au moins 169 attendues.')
    if rows.count(expected) != 1: errors.append('V24.5.36 doit apparaître exactement une fois dans le ledger.')
    elif rows.index(expected) != 168: errors.append('V24.5.36 doit rester la 169e migration canonique.')

    for marker in ['169 migrations','aucune note libre','mfa/aal2','ne crée aucune commande','n’active aucune vente','livraison d’un livre physique reste à la charge du client','0 $ de frais de livraison']:
        if marker not in doc: errors.append(f'Document V24.5.36 incomplet: {marker}')

    for marker in ['table privée de suivi existe','rls suivi activée','anon ne lit pas le suivi','wrappers publics sont security invoker','anon ne peut pas exécuter les rpc de suivi','implémentations internes exigent admin + mfa/aal2','aucune colonne de note libre ou pii']:
        if marker not in test: errors.append(f'pgTAP V24.5.36 incomplet: {marker}')

    for forbidden in ['stripe.com','checkout.stripe.com','paypal.com','api.resend.com','twilio','shippo','easypost','fedex.com','ups.com']:
        if forbidden in low + js_low: errors.append(f'Intégration externe interdite V24.5.36: {forbidden}')

    if errors:
        print(f'ECHEC V24.5.36 suivi admin: {len(errors)} problème(s).')
        for error in errors: print('- ' + error)
        return 1
    print('OK V24.5.36 historique: suivi admin non financier conservé à la 169e migration; module toujours chargé, MFA visible et cache-buster ultérieur accepté.')
    return 0

if __name__ == '__main__': raise SystemExit(main())
