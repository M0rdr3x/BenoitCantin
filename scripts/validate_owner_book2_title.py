#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIG = ROOT / 'supabase/migrations/20260818022036_sinjira_v24_4_58_owner_book2_title_consistency.sql'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
errors = []


def need(condition, message):
    if not condition:
        errors.append(message)


need(MIG.exists(), 'migration V24.4.58 absente')
if MIG.exists():
    sql = MIG.read_text('utf-8')
    low = sql.lower()
    for marker in (
        'SINJIRA — Livre II (titre à confirmer)',
        'SINJIRA — Livre II : Le Sang du Sauveur',
        'ensure_sinjira_owner_character',
        'execute replace',
        'kingtyrano@gmail.com',
        'public.characters',
        'novel_note',
        "'{placement}'",
        'sinjira_owner_book2_title_health',
        "'version', '24.4.58'",
    ):
        need(marker.lower() in low, 'élément de cohérence Livre II absent: ' + marker)
    need('revoke all on function public.sinjira_owner_book2_title_health() from public, anon, authenticated' in low,
         'healthcheck V24.4.58 exposé à un rôle navigateur')
    need('grant execute on function public.sinjira_owner_book2_title_health() to service_role' in low,
         'healthcheck V24.4.58 non réservé au service_role')

need(LEDGER.exists(), 'ledger production absent')
if LEDGER.exists():
    ledger = LEDGER.read_text('utf-8')
    need('20260818022036 sinjira_v24_4_58_owner_book2_title_consistency' in ledger,
         'migration V24.4.58 absente du ledger production')

if errors:
    print(f'ECHEC cohérence Livre II propriétaire V24.4.58: {len(errors)} problème(s).')
    for error in errors:
        print('- ' + error)
    raise SystemExit(1)

print('OK V24.4.58: AbyssTime et sa routine de réparation utilisent le titre officiel du Livre II; healthcheck service-only et ledger alignés.')
