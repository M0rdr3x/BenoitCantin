#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260822190619_sinjira_v24_5_6_livre_1_shipping_pickup_preparation.sql'
PUBLIC=ROOT/'projets/sinjira/romans/precommande.html'
ACCOUNT=ROOT/'compte/mes-achats.html'
PUBLIC_JS=ROOT/'assets/js/sinjira-preorder-fulfillment-v24-5-6.js'
PUBLIC_CSS=ROOT/'assets/css/sinjira-preorder-fulfillment-v24-5-6.css'
ADMIN=ROOT/'admin/sinjira/precommandes.html'
ADMIN_JS=ROOT/'assets/js/sinjira-admin-preorder-fulfillment-v24-5-6.js'
ADMIN_CSS=ROOT/'assets/css/sinjira-admin-preorder-fulfillment-v24-5-6.css'
DOC=ROOT/'LIVRAISON_RAMASSAGE_LIVRE_I_V24_5_6.md'
POLICY=ROOT/'SERVICES_EXTERNES_PAYANTS.md'
ARCH=ROOT/'ARCHITECTURE_COMPTE_UNIVERSEL.md'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'


def read(path):
    return path.read_text('utf-8',errors='ignore') if path.exists() else ''


def main()->int:
    errors=[]
    files=[MIG,PUBLIC,ACCOUNT,PUBLIC_JS,PUBLIC_CSS,ADMIN,ADMIN_JS,ADMIN_CSS,DOC,POLICY,ARCH,LEDGER]
    for p in files:
        if not p.exists():errors.append(f'Fichier V24.5.6 absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors:print('- '+e)
        return 1

    sql=read(MIG).lower(); compact=re.sub(r'\s+','',sql)
    public=read(PUBLIC).lower(); account=read(ACCOUNT).lower(); public_js=read(PUBLIC_JS).lower()
    admin=read(ADMIN).lower(); admin_js=read(ADMIN_JS).lower(); doc=read(DOC).lower(); policy=read(POLICY).lower(); arch=read(ARCH).lower(); ledger=read(LEDGER)

    for table in ['preorder_fulfillment_settings','preorder_shipping_zones','preorder_pickup_points']:
        if f'create table if not exists public.{table}' not in sql:errors.append(f'Table V24.5.6 absente: {table}')
        if f'alter table public.{table} enable row level security' not in sql:errors.append(f'RLS absente: {table}')
        if f'revoke all on table public.{table} from public, anon, authenticated' not in sql:errors.append(f'ACL directe insuffisante: {table}')

    locks={
        'shipping_customer_pays':'true',
        'pickup_interest_enabled':'true',
        'external_carrier_api_enabled':'false',
        'external_shipping_purchase_enabled':'false',
        'pickup_shipping_charge_cents':'0'
    }
    for name,value in locks.items():
        if f'{name}' not in sql or value not in sql:errors.append(f'Verrou livraison absent: {name}={value}')
    for marker in [
        "fulfillment_preference in ('shipping','pickup','undecided')",
        'product_preorder_fulfillment_options',
        'product_preorder_shipping_estimate',
        'product_preorder_fulfillment_status',
        'product_preorder_set_fulfillment_preference',
        'admin_preorder_fulfillment_get',
        'admin_preorder_fulfillment_settings_save',
        'admin_preorder_shipping_zone_save',
        'admin_preorder_shipping_zone_publish',
        'admin_preorder_pickup_point_save',
        'admin_preorder_pickup_point_publish'
    ]:
        if marker not in sql:errors.append(f'Contrat SQL absent: {marker}')
    if sql.count('private.require_sinjira_admin_aal2()') < 6:errors.append('Toutes les RPC admin livraison ne sont pas protégées par MFA/AAL2.')
    if 'grant execute on function public.product_preorder_fulfillment_options(text) to anon, authenticated' not in sql:errors.append('Options publiques de réception non exposées via RPC contrôlée.')
    if 'grant execute on function public.product_preorder_shipping_estimate(text,text,integer) to anon, authenticated' not in sql:errors.append('Estimateur public non exposé via RPC contrôlée.')

    forbidden=['api.canadapost','canadapost.ca','ups.com','fedex.com','purolator.com','easypost','shippo','stripe','paypal','api.resend.com','twilio','insert into public.orders','insert into public.order_items']
    for marker in forbidden:
        if marker in sql:errors.append(f'Intégration externe/transactionnelle interdite dans SQL: {marker}')
        if marker in public_js:errors.append(f'Intégration externe interdite dans runtime public: {marker}')
        if marker in admin_js:errors.append(f'Intégration externe interdite dans runtime admin: {marker}')
    for runtime,name in [(public_js,'public'),(admin_js,'admin')]:
        if 'fetch(' in runtime or '.functions.invoke(' in runtime:errors.append(f'Runtime {name} appelle un transport externe au lieu des RPC Supabase.')

    for html,name in [(public,'Page publique'),(account,'Compte')]:
        if 'frais de livraison seront à la charge du client' not in html and 'frais de livraison seront à votre charge' not in html:errors.append(f'{name}: avertissement frais de livraison absent.')
        if 'ramassage sur place' not in html:errors.append(f'{name}: option ramassage absente.')
        if 'data-preorder-fulfillment' not in html:errors.append(f'{name}: bloc V24.5.6 absent.')
        if 'data-pf-estimate' not in html:errors.append(f'{name}: estimateur absent.')
        if 'sinjira-preorder-fulfillment-v24-5-6.js?v=24.5.6' not in html:errors.append(f'{name}: runtime V24.5.6 non chargé.')
        if 'adresse de livraison' not in html:errors.append(f'{name}: minimisation de l’adresse non expliquée.')

    for marker in ['data-pf-admin-settings','data-pf-admin-zone-form','data-pf-admin-pickup-form','api transporteur','frais de livraison','ramassage']:
        if marker not in admin:errors.append(f'Console admin: marqueur absent: {marker}')
    if 'publier ce point de ramassage' not in admin_js or 'adresse personnelle' not in admin_js:errors.append('La publication d’un point de ramassage ne comporte plus l’avertissement de confidentialité.')
    if 'publier cette estimation de livraison' not in admin_js:errors.append('Publication explicite des estimations absente.')

    for text,name in [(doc,'Document V24.5.6'),(policy,'Politique payante'),(arch,'Architecture')]:
        for marker in ['frais de livraison','ramassage','external_carrier_api_enabled']:
            if marker not in text:errors.append(f'{name}: règle V24.5.6 absente: {marker}')
    if '20260822190619 sinjira_v24_5_6_livre_1_shipping_pickup_preparation' not in ledger:errors.append('Ledger production sans migration V24.5.6.')

    if errors:
        print(f'ECHEC V24.5.6 livraison/ramassage: {len(errors)} problème(s).')
        for e in errors:print('- '+e)
        return 1
    print('OK V24.5.6: frais de livraison à la charge du client, estimateur local, ramassage sans frais, publication MFA/AAL2 et services transporteurs externes désactivés.')
    return 0

if __name__=='__main__':raise SystemExit(main())
