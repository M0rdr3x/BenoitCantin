#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase/migrations/20260831002808_sinjira_v24_5_45_transaction_tables_acl_hardening.sql'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
DOC = ROOT / 'TRANSACTION_TABLES_ACL_HARDENING_V24_5_45.md'


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in [MIG, LEDGER, DOC]:
        if not path.exists(): errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for err in errors: print('- ' + err)
        return 1

    sql=read(MIG).lower(); ledger=read(LEDGER); doc=read(DOC).lower()
    required_sql=[
        'revoke all on table public.orders from anon','revoke all on table public.order_items from anon',
        'revoke insert, update, delete, truncate, references, trigger on table public.orders from authenticated',
        'revoke insert, update, delete, truncate, references, trigger on table public.order_items from authenticated',
        'grant select on table public.orders to authenticated','grant select on table public.order_items to authenticated']
    for marker in required_sql:
        if marker not in sql: errors.append(f'Migration V24.5.45 incomplète: {marker}')
    for marker in [
        'grant insert on table public.orders to authenticated','grant update on table public.orders to authenticated',
        'grant delete on table public.orders to authenticated','grant insert on table public.order_items to authenticated',
        'grant update on table public.order_items to authenticated','grant delete on table public.order_items to authenticated',
        'grant select on table public.orders to anon','grant select on table public.order_items to anon']:
        if marker in sql: errors.append(f'Privilège transactionnel interdit réintroduit: {marker}')

    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    row='20260831002808 sinjira_v24_5_45_transaction_tables_acl_hardening'
    if len(rows)<173: errors.append(f'Ledger régressé: {len(rows)} migrations, moins que les 173 connues en V24.5.45.')
    if len(rows)>=173 and rows[172]!=row: errors.append('L’historique V24.5.45 n’est plus aligné sur la 173e migration canonique.')
    if rows.count(row)!=1: errors.append('La migration V24.5.45 doit exister exactement une fois.')

    for marker in ['0 ligne','rls','anon','authenticated','select','173 migrations','aucune vente','checkout_enabled = false','payment_enabled = false','frais de livraison','0 $ de frais de livraison','aucun service payant activé']:
        if marker not in doc: errors.append(f'Document V24.5.45 incomplet: {marker}')

    combined=sql+'\n'+doc
    for token in ['api.stripe.com','paypal.com/sdk','api.resend.com','twilio.com','api.shippo.com','api.easypost.com','payment_enabled = true','checkout_enabled = true','sales_enabled = true']:
        if token in combined: errors.append(f'Activation externe/commerciale interdite dans V24.5.45: {token}')

    if errors:
        print(f'ECHEC V24.5.45 ACL transactionnelles: {len(errors)} problème(s).')
        for err in errors: print('- '+err)
        return 1
    print('OK V24.5.45 historique: ACL transactionnelles scellées et 173e migration canonique conservées; migrations ultérieures autorisées.')
    return 0

if __name__=='__main__': raise SystemExit(main())
