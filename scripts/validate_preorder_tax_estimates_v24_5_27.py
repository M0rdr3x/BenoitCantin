#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MIG1=ROOT/'supabase/migrations/20260823195851_sinjira_v24_5_27_preorder_tax_estimate_preparation.sql'
MIG2=ROOT/'supabase/migrations/20260823200303_sinjira_v24_5_27_tax_rate_precision_hardening.sql'
MIG3=ROOT/'supabase/migrations/20260823201127_sinjira_v24_5_27_tax_input_and_readiness_hardening.sql'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
DOC=ROOT/'PREORDER_TAX_ESTIMATES_V24_5_27.md'
ADMIN=ROOT/'assets/js/sinjira-admin-preorder-tax-v24-5-27.js'
PUBLIC=ROOT/'assets/js/sinjira-preorder-tax-estimate-v24-5-27.js'
ADMIN_LOADER=ROOT/'assets/js/sinjira-admin-preorder-readiness-v24-5-26.js'
PUBLIC_LOADER=ROOT/'assets/js/sinjira-preorder-fulfillment-v24-5-6.js'
SCHEMA=ROOT/'scripts/validate_production_schema_manifest.py'
POLICY=ROOT/'SERVICES_EXTERNES_PAYANTS.md'
TEST=ROOT/'supabase/tests/preorder_tax_estimates_v24_5_27.test.sql'


def read(p): return p.read_text('utf-8',errors='ignore') if p.exists() else ''
def flat(s): return re.sub(r'\s+',' ',s.lower()).strip()

def main():
    errors=[]
    for p in [MIG1,MIG2,MIG3,LEDGER,DOC,ADMIN,PUBLIC,ADMIN_LOADER,PUBLIC_LOADER,SCHEMA,POLICY,TEST]:
        if not p.exists(): errors.append(f'Fichier absent: {p.relative_to(ROOT)}')
    if errors:
        for e in errors: print('- '+e)
        return 1

    m1=read(MIG1); m2=read(MIG2); m3=read(MIG3); sql=flat(m1+'\n'+m2+'\n'+m3); doc=read(DOC).lower(); admin=read(ADMIN).lower(); public=read(PUBLIC).lower()

    required_sql=[
      'create table if not exists public.preorder_tax_estimate_profiles',
      'alter table public.preorder_tax_estimate_profiles enable row level security',
      'revoke all on table public.preorder_tax_estimate_profiles from public, anon, authenticated',
      'create policy preorder_tax_profiles_service_role',
      'create schema if not exists preorder_tax_internal',
      'private.require_sinjira_admin_aal2()',
      'create or replace function public.product_preorder_tax_options',
      'create or replace function public.product_preorder_tax_estimate',
      'security invoker',
      "'estimate_nonbinding',true",
      "'billing_authoritative',false",
      "'external_tax_api_enabled',false",
      "'final_tax_confirmation_required',true",
      'published_at is not null',
      'source_reference',
      'effective_on',
      'sales_enabled is distinct from false',
      'checkout_enabled is distinct from false',
      'payment_enabled is distinct from false',
      'external_fulfillment_enabled is distinct from false',
      'auto_conversion_allowed is distinct from false',
    ]
    for marker in required_sql:
        if marker not in sql: errors.append(f'Contrat SQL V24.5.27 absent: {marker}')

    for marker in [
      'paper_rate_basis_points type numeric(10,3)',
      'digital_rate_basis_points type numeric(10,3)',
      'shipping_rate_basis_points type numeric(10,3)',
      '14,975 %',
      'p_paper_rate_basis_points numeric',
      'p_digital_rate_basis_points numeric',
      'p_shipping_rate_basis_points numeric',
    ]:
        if marker not in m2.lower(): errors.append(f'Précision fiscale V24.5.27 absente: {marker}')

    hardening=flat(m3)
    for marker in [
      "p_format is null or p_format not in ('paper','digital','both')",
      "p_fulfillment_method is null or p_fulfillment_method not in ('shipping','pickup','undecided')",
      'preorder_tax_profiles_label_length_check',
      'preorder_tax_profiles_source_length_check',
      'v_tax_profile_count>0',
      "'tax_estimate_ready',v_tax_profile_count>0",
      "'published_tax_profiles',v_tax_profile_count",
      'publier au moins un profil fiscal indicatif vérifié',
    ]:
        if marker not in hardening: errors.append(f'Hardening V24.5.27 absent: {marker}')

    # Contrôle ACL strict, limité à une instruction SQL. Ne doit jamais traverser
    # plusieurs GRANT et produire un faux positif à cause de re.S.
    if re.search(r'(?im)^\s*grant\s+execute\s+on\s+function\s+public\.admin_preorder_tax_[^\n;]*\s+to\s+anon\s*;',m1):
        errors.append('Les RPC fiscales admin ne doivent jamais être exécutables par anon.')
    for name in ['product_preorder_tax_options','product_preorder_tax_estimate']:
        if name not in m1 or f'grant execute on function public.{name}' not in m1.lower(): errors.append(f'RPC publique fiscale absente: {name}')

    table_ddl=m1.lower().split('create schema if not exists preorder_tax_internal',1)[0]
    for col in ['paper_rate_basis_points','digital_rate_basis_points','shipping_rate_basis_points']:
        line=next((x for x in table_ddl.splitlines() if col in x), '')
        if 'default' in line: errors.append(f'Aucun taux ne doit être prérempli: {col}')

    rows=[x.strip() for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]
    expected=[
      '20260823195851 sinjira_v24_5_27_preorder_tax_estimate_preparation',
      '20260823200303 sinjira_v24_5_27_tax_rate_precision_hardening',
      '20260823201127 sinjira_v24_5_27_tax_input_and_readiness_hardening'
    ]
    if len(rows)<160: errors.append(f'Ledger: {len(rows)} migrations; V24.5.27 exige au moins 160 migrations historiques.')
    positions=[]
    for row in expected:
        if rows.count(row)!=1: errors.append(f'Ledger V24.5.27 absent/dupliqué: {row}')
        elif row in rows: positions.append(rows.index(row))
    if len(positions)==3 and positions!=sorted(positions): errors.append('Les trois migrations V24.5.27 ne sont pas dans leur ordre canonique.')

    for marker in ['160 migrations','aucun profil fiscal','mfa/aal2','14,975 %','external_tax_api_enabled = false','billing_authoritative = false','final_tax_confirmation_required = true','aucun paiement','livraison à la charge du client','0 $ de frais de livraison','ready_for_future_manual_opening']:
        if marker not in doc: errors.append(f'Document V24.5.27 incomplet: {marker}')

    for marker in ["rpc('admin_preorder_tax_get'","rpc('admin_preorder_tax_profile_save'","rpc('admin_preorder_tax_profile_publish'",'aucun taux automatique','api fiscale externe : désactivée','taxes finales']:
        if marker not in admin: errors.append(f'Interface admin fiscale incomplète: {marker}')
    for marker in ["rpc('product_preorder_tax_options'","rpc('product_preorder_tax_estimate'",'estimation non contractuelle','billing_authoritative','external_tax_api_enabled','final_tax_confirmation_required','aucune estimation fiscale publiée']:
        if marker not in public: errors.append(f'Interface publique fiscale incomplète: {marker}')

    if "import './sinjira-admin-preorder-tax-v24-5-27.js';" not in read(ADMIN_LOADER): errors.append('Le module admin V24.5.27 n’est pas chargé.')
    if "import './sinjira-preorder-tax-estimate-v24-5-27.js';" not in read(PUBLIC_LOADER): errors.append('Le module public V24.5.27 n’est pas chargé.')
    if "'preorder_tax_estimate_profiles'" not in read(SCHEMA): errors.append('La table fiscale manque au manifeste production.')

    forbidden=['stripe','paypal','avalara','taxjar','vertex','twilio','api.resend.com','api.openai.com','canada post','canadapost','fedex','purolator','shippo','easypost']
    for token in forbidden:
        if token in (m1+'\n'+m2+'\n'+m3+'\n'+read(ADMIN)+'\n'+read(PUBLIC)).lower(): errors.append(f'Fournisseur externe interdit en V24.5.27: {token}')

    test=read(TEST).lower()
    for marker in ['select plan(','preorder_tax_estimate_profiles','numeric_scale','security invoker','require_sinjira_admin_aal2','external_tax_api_enabled','billing_authoritative','tax_estimate_ready','select * from finish()','rollback;']:
        if marker not in test: errors.append(f'pgTAP V24.5.27 incomplet: {marker}')

    if 'préparer une intégration ne constitue jamais une autorisation de l’activer' not in read(POLICY).lower(): errors.append('Politique services payants canonique absente.')

    if errors:
        print(f'ECHEC V24.5.27 estimation fiscale: {len(errors)} problème(s).')
        for e in errors: print('- '+e)
        return 1
    print('OK V24.5.27: estimation fiscale indicative, précision décimale, validation serveur, publication humaine MFA, aucun taux par défaut, aucune API externe et aucune facturation; contrat historique préservé.')
    return 0

if __name__=='__main__': raise SystemExit(main())
