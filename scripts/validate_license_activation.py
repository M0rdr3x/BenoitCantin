#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260817233134_sinjira_v24_4_49_license_activation_production.sql'
REDEEM=ROOT/'supabase/functions/redeem-license-code/index.ts'
ADMIN=ROOT/'supabase/functions/admin-license-codes/index.ts'
MANIFEST=ROOT/'scripts/validate_production_schema_manifest.py'
LEDGER=ROOT/'supabase/production-migration-ledger.txt'
errors=[]

def need(condition,msg):
    if not condition: errors.append(msg)

need(MIG.exists(),'migration V24.4.49 absente')
if MIG.exists():
    sql=MIG.read_text('utf-8')
    for marker in ('license_batches','activation_codes','license_redemptions','redeem_sinjira_activation','sinjira_license_health','service_role'):
        need(marker in sql,f'migration licence incomplète: {marker}')
    need('revoke all on public.activation_codes from public,anon,authenticated' in sql,'ACL activation_codes non fermée')
    need("on conflict (user_id,product_id) do nothing" in sql,'activation non idempotente sur user_entitlements')
for path,name in ((REDEEM,'redeem-license-code'),(ADMIN,'admin-license-codes')):
    need(path.exists(),f'{name} absent')
    if path.exists():
        text=path.read_text('utf-8')
        need("24.4.49" in text,f'{name}: version 24.4.49 absente')
        need("sinjira_license_health" in text,f'{name}: prévol schéma absent')
        need("LICENSE_SCHEMA_UNAVAILABLE" in text,f'{name}: erreur schéma explicite absente')
need("'license_batches','activation_codes','license_redemptions'" in MANIFEST.read_text('utf-8').replace('\n',''), 'tables licence non classées production')
need('20260817233134 sinjira_v24_4_49_license_activation_production' in LEDGER.read_text('utf-8'),'ledger production V24.4.49 absent')
if errors:
    print(f'ECHEC licence V24.4.49: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK licence V24.4.49: schéma ciblé, activation atomique, ACL service-only, diagnostic et Edge Functions alignés.')
