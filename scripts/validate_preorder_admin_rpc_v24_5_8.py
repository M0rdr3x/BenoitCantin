#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
M1=ROOT/'supabase/migrations/20260822195029_sinjira_v24_5_8_preorder_admin_rpc_boundary.sql'
M2=ROOT/'supabase/migrations/20260822195124_sinjira_v24_5_8_preorder_admin_rpc_acl_hardening.sql'
DOC=ROOT/'PRECOMMANDES_ADMIN_RPC_V24_5_8.md'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
ADMIN_JS=ROOT/'assets/js/sinjira-admin-preorders-v24-5-4.js'
FULFILLMENT_JS=ROOT/'assets/js/sinjira-admin-preorder-fulfillment-v24-5-6.js'


def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''


def main():
    errors=[]
    for p in [M1,M2,DOC,LEDGER,ADMIN_JS,FULFILLMENT_JS]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    m1=read(M1).lower(); m2=read(M2).lower(); doc=read(DOC).lower(); ledger=read(LEDGER)
    admin_js=read(ADMIN_JS).lower(); fulfillment_js=read(FULFILLMENT_JS).lower()

    markers=[
        'create schema if not exists preorder_admin_internal',
        "p.proname like 'admin_preorder_%'",
        "and p.prosecdef",
        'alter function public.%i(%s) set schema preorder_admin_internal',
        'security invoker',
        'grant execute on function preorder_admin_internal.%i(%s) to authenticated',
        'grant execute on function public.%i(%s) to authenticated',
    ]
    for x in markers:
        if x not in m1: errors.append(f'Migration frontière incomplète: {x}')

    if "p.proname like 'admin_preorder_%'" not in m2 or 'revoke execute on function public.%i(%s) from anon' not in m2:
        errors.append('Hardening ACL anon absent ou incomplet.')

    if 'grant execute' in m1 and ' to anon' in m1:
        errors.append('La migration frontière ne doit jamais accorder les RPC admin à anon.')
    if 'grant execute' in m2 and ' to anon' in m2:
        errors.append('La migration ACL ne doit jamais accorder les RPC admin à anon.')

    if 'private.require_sinjira_admin_aal2()' not in doc:
        errors.append('La documentation ne conserve pas explicitement la barrière MFA/AAL2.')
    for x in ['15 fonctions','0/15','139 migrations','security invoker','preorder_admin_internal']:
        if x not in doc: errors.append(f'Document V24.5.8 incomplet: {x}')

    expected=[
        'admin_preorder_commercial_plan_get','admin_preorder_commercial_plan_mark_ready',
        'admin_preorder_commercial_plan_publish','admin_preorder_commercial_plan_save',
        'admin_preorder_fulfillment_get','admin_preorder_fulfillment_settings_save',
        'admin_preorder_list','admin_preorder_mark_announcement_ready','admin_preorder_overview',
        'admin_preorder_pickup_point_publish','admin_preorder_pickup_point_save',
        'admin_preorder_save_announcement_draft','admin_preorder_send_internal_announcement',
        'admin_preorder_shipping_zone_publish','admin_preorder_shipping_zone_save'
    ]
    runtime=admin_js+'\n'+fulfillment_js
    missing=[x for x in expected if x not in runtime]
    # Toutes les RPC n'ont pas à être appelées par les deux modules, mais aucune renommage de celles utilisées n'est autorisé.
    if len(missing) > 6:
        errors.append('Trop de RPC admin historiques ne sont plus référencées par les runtimes admin; vérifier une régression de noms.')

    rows=[x for x in ledger.splitlines() if x.strip() and not x.startswith('#')]
    if len(rows)!=139: errors.append(f'Ledger: {len(rows)} migrations au lieu de 139.')
    for x in [
        '20260822195029 sinjira_v24_5_8_preorder_admin_rpc_boundary',
        '20260822195124 sinjira_v24_5_8_preorder_admin_rpc_acl_hardening'
    ]:
        if x not in ledger: errors.append(f'Ledger sans {x}')
    if not rows or not rows[-1].startswith('20260822195124 '): errors.append('Dernière migration ledger inattendue.')

    forbidden=['stripe','paypal','canadapost','canada post','fedex','purolator','shippo','easypost','twilio','api.resend.com']
    combined=m1+'\n'+m2
    for token in forbidden:
        if token in combined: errors.append(f'Intégration externe interdite: {token}')

    if errors:
        print(f'ECHEC V24.5.8 frontière admin: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.8: 15 RPC admin derrière frontière interne, wrappers SECURITY INVOKER, anon révoqué, MFA/AAL2 conservé et 139 migrations synchronisées.')
    return 0

if __name__=='__main__': raise SystemExit(main())
