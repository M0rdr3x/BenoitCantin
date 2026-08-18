#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MIG=ROOT/'supabase/migrations/20260818001515_sinjira_v24_4_54_license_fk_indexes.sql'
errors=[]

def need(cond,msg):
    if not cond: errors.append(msg)

need(MIG.exists(),'migration V24.4.54 absente')
if MIG.exists():
    sql=MIG.read_text('utf-8')
    for marker in (
      'activation_codes_redeemed_by_idx',
      'license_batches_created_by_idx',
      'sinjira_license_index_health',
      "'version','24.4.54'"
    ):
        need(marker in sql,'élément index licence absent: '+marker)
    need('on public.activation_codes(redeemed_by)' in sql,'index FK redeemed_by incorrect')
    need('on public.license_batches(created_by)' in sql,'index FK created_by incorrect')
    need('revoke all on function public.sinjira_license_index_health() from public,anon,authenticated' in sql,'healthcheck index licence exposé')

if errors:
    print(f'ECHEC index licences V24.4.54: {len(errors)} problème(s).')
    for e in errors: print('- '+e)
    raise SystemExit(1)
print('OK index licences V24.4.54: les deux clés étrangères possèdent un index de support et le healthcheck est privé.')
