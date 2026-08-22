#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG1=ROOT/'supabase/migrations/20260822180500_sinjira_v24_5_5_preorder_commercial_preparation.sql'
MIG2=ROOT/'supabase/migrations/20260822180501_sinjira_v24_5_5_commercial_revision_hardening.sql'
ADMIN=ROOT/'admin/sinjira/precommandes.html'
ADMIN_JS=ROOT/'assets/js/sinjira-admin-preorder-commercial-v24-5-5.js'
PUBLIC_JS=ROOT/'assets/js/sinjira-preorder-commercial-v24-5-5.js'
ACCOUNT=ROOT/'compte/mes-achats.html'
PUBLIC=ROOT/'projets/sinjira/romans/precommande.html'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'


def read(path):
    return path.read_text('utf-8',errors='ignore') if path.exists() else ''


def main()->int:
    errors=[]
    m1=read(MIG1);m2=read(MIG2);sql=(m1+'\n'+m2).lower()
    admin=read(ADMIN);admin_js=read(ADMIN_JS);public_js=read(PUBLIC_JS)
    account=read(ACCOUNT);public=read(PUBLIC);ledger=read(LEDGER)

    for p in [MIG1,MIG2,ADMIN,ADMIN_JS,PUBLIC_JS,ACCOUNT,PUBLIC,LEDGER]:
        if not p.exists():errors.append(f'Fichier V24.5.5 absent: {p.relative_to(ROOT)}')

    if 'create table if not exists public.preorder_commercial_plans' not in sql:
        errors.append('Table preorder_commercial_plans absente.')
    if 'alter table public.preorder_commercial_plans enable row level security' not in sql:
        errors.append('RLS du plan commercial absente.')
    if 'revoke all on table public.preorder_commercial_plans from public, anon, authenticated' not in sql:
        errors.append('ACL directe du plan commercial insuffisamment scellée.')

    locks=['sales_enabled','checkout_enabled','payment_enabled','external_fulfillment_enabled','auto_conversion_allowed']
    compact=re.sub(r'\s+','',sql)
    for name in locks:
        if f'{name}booleannotnulldefaultfalsecheck({name}=false)' not in compact:
            errors.append(f'Verrou DB manquant ou affaibli: {name}=false.')
        if f'new.{name}:=false;' not in compact:
            errors.append(f'Trigger serveur ne réimpose plus {name}=false.')

    for rpc in ['admin_preorder_commercial_plan_get','admin_preorder_commercial_plan_save','admin_preorder_commercial_plan_mark_ready','admin_preorder_commercial_plan_publish']:
        if rpc not in sql:errors.append(f'RPC admin V24.5.5 absente: {rpc}')
    if sql.count('private.require_sinjira_admin_aal2()') < 4:
        errors.append('Toutes les RPC admin commerciales ne sont pas protégées par MFA/AAL2.')

    if 'product_preorder_commercial_info' not in sql or "c.status = 'published'" not in sql:
        errors.append('La lecture publique ne se limite pas explicitement à une révision publiée.')
    if 'grant execute on function public.product_preorder_commercial_info(text) to anon, authenticated' not in sql:
        errors.append('RPC informative publique non exposée via exécution contrôlée.')

    for marker in ['release_at is not null','terms_summary', 'paper_price_cents', 'digital_price_cents', 'paper_edition_label', 'digital_edition_label']:
        if marker not in sql:errors.append(f'Critère de complétude commerciale absent: {marker}')
    if "status = 'superseded'" not in sql or 'commercial_plan_immutable' not in sql:
        errors.append('Versionnage/immutabilité des informations publiées incomplet.')

    forbidden_sql=['insert into public.orders','insert into public.order_items','stripe','paypal','checkout.session','api.resend.com','twilio']
    for marker in forbidden_sql:
        if marker in sql:errors.append(f'Intégration interdite dans le module commercial préparatoire: {marker}')

    for text,name in [(admin_js,'JS admin'),(public_js,'JS public')]:
        low=text.lower()
        for marker in ['stripe','paypal','api.resend.com','twilio']:
            if marker in low:errors.append(f'{name} référence un fournisseur externe interdit: {marker}')
    for marker in ['aucune vente','aucun checkout','aucun paiement','aucun avis']:
        if marker not in admin_js.lower():errors.append(f'Confirmation admin ne rappelle plus le garde-fou: {marker}')
    if 'product_preorder_commercial_info' not in public_js:
        errors.append('Le runtime public ne lit plus la RPC commerciale assainie.')
    if 'locked(info)' not in public_js:
        errors.append('Le runtime public ne vérifie plus les cinq verrous de non-vente.')

    for html,name in [(account,'Compte'),(public,'Page publique')]:
        if 'sinjira-preorder-commercial-v24-5-5.js?v=24.5.5' not in html:
            errors.append(f'{name} ne charge pas le runtime commercial V24.5.5.')
        if 'data-preorder-commercial' not in html:
            errors.append(f'{name} ne contient pas le bloc d’informations commerciales.')
        if 'conversion automatique' not in html.lower():
            errors.append(f'{name} ne rappelle pas que la réservation ne devient pas automatiquement une commande.')

    if 'data-pc-admin-form' not in admin or 'data-pc-admin-publish' not in admin:
        errors.append('Console admin V24.5.5 incomplète.')
    if '20260822181301 sinjira_v24_5_5_preorder_commercial_preparation' not in ledger:
        errors.append('Ledger production sans migration V24.5.5 principale.')
    if '20260822181317 sinjira_v24_5_5_commercial_revision_hardening' not in ledger:
        errors.append('Ledger production sans hardening V24.5.5.')

    if errors:
        print(f'ECHEC V24.5.5 préparation commerciale: {len(errors)} problème(s).')
        for e in errors:print('- '+e)
        return 1
    print('OK V24.5.5: prix/date/éditions préparables et publiables comme information seulement; MFA/AAL2, RLS, versionnage et cinq verrous de non-vente sont conservés.')
    return 0

if __name__=='__main__':raise SystemExit(main())
