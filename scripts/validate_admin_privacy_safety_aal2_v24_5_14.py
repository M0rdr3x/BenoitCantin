from pathlib import Path

MIGRATION = Path('supabase/migrations/20260824013042_sinjira_v24_5_14_admin_privacy_safety_aal2_hardening.sql')
LEDGER = Path('supabase/production-migration-ledger.txt')

TARGETS = [
    'privacy_admin_incidents',
    'privacy_admin_record_incident',
    'privacy_admin_requests',
    'privacy_admin_update_request',
    'safety_admin_escalation_cases',
]

sql = MIGRATION.read_text(encoding='utf-8')
ledger = LEDGER.read_text(encoding='utf-8')

assert MIGRATION.exists()
assert '20260824013042 sinjira_v24_5_14_admin_privacy_safety_aal2_hardening' in ledger
for name in TARGETS:
    marker = f'function sinjira_admin_internal.{name}'
    assert marker in sql, f'missing {name}'

assert sql.count('private.require_sinjira_admin_aal2()') == len(TARGETS)
assert 'is_sinjira_admin(auth.uid())' not in sql
assert 'grant execute' not in sql.lower()
assert 'revoke all' not in sql.lower()
print('V24.5.14 admin privacy/safety AAL2 contract: OK')
