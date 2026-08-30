#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M1 = ROOT / 'supabase/migrations/20260830001642_sinjira_v24_5_14_privacy_moderation_user_rpc_boundary.sql'
M2 = ROOT / 'supabase/migrations/20260830001742_sinjira_v24_5_32_user_rights_redundant_boundary_cleanup.sql'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
DOC = ROOT / 'USER_RIGHTS_CONVERGENCE_V24_5_33.md'

TARGETS = [
    'privacy_create_request',
    'privacy_export_my_extended_data',
    'privacy_my_requests',
    'moderation_my_decisions',
    'moderation_submit_appeal',
]


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in (M1, M2, LEDGER, DOC):
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for err in errors: print('- ' + err)
        return 1

    first = read(M1).lower()
    cleanup = read(M2).lower()
    ledger = read(LEDGER)
    doc = read(DOC).lower()

    for name in TARGETS:
        if name not in first: errors.append(f'RPC absente de la migration initiale: {name}')
        if name not in cleanup: errors.append(f'RPC absente de la convergence: {name}')

    required_cleanup = [
        'sinjira_user_rights_internal',
        'security invoker',
        'revoke all on function public.%i(%s) from public, anon',
        'grant execute on function public.%i(%s) to authenticated, service_role',
        'drop schema sinjira_privacy_moderation_internal',
    ]
    for marker in required_cleanup:
        if marker not in cleanup:
            errors.append(f'Convergence incomplète: {marker}')

    if 'grant execute' in cleanup and ' to anon' in cleanup:
        errors.append('La convergence ne doit jamais accorder EXECUTE à anon.')

    rows = [line for line in ledger.splitlines() if line.strip() and not line.startswith('#')]
    expected_rows = [
        '20260830001642 sinjira_v24_5_14_privacy_moderation_user_rpc_boundary',
        '20260830001742 sinjira_v24_5_32_user_rights_redundant_boundary_cleanup',
    ]
    if len(rows) != 167: errors.append(f'Ledger: {len(rows)} migrations au lieu de 167.')
    for row in expected_rows:
        if rows.count(row) != 1: errors.append(f'Ledger: ligne absente ou dupliquée: {row}')
    if not rows or rows[-1] != expected_rows[-1]:
        errors.append('La convergence doit être la dernière migration du ledger courant.')

    for marker in ['167 migrations', 'sinjira_user_rights_internal', 'security invoker', 'anon', 'aucun paiement']:
        if marker not in doc:
            errors.append(f'Document V24.5.33 incomplet: {marker}')

    if errors:
        print(f'ECHEC V24.5.33: {len(errors)} problème(s).')
        for err in errors: print('- ' + err)
        return 1

    print('OK V24.5.33: frontière redondante tracée puis supprimée, wrappers directs vers sinjira_user_rights_internal, anon révoqué, ledger 167 synchronisé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
