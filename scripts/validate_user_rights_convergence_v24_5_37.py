#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M1 = ROOT / 'supabase/migrations/20260830015838_sinjira_v24_5_14_privacy_moderation_user_rpc_boundary.sql'
M2 = ROOT / 'supabase/migrations/20260830015937_sinjira_v24_5_15_user_rights_wrapper_cleanup.sql'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
DOC = ROOT / 'USER_RIGHTS_CONVERGENCE_V24_5_37.md'

TARGETS = [
    'moderation_my_decisions',
    'moderation_submit_appeal',
    'privacy_create_request',
    'privacy_export_my_extended_data',
    'privacy_my_requests',
]


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in [M1, M2, LEDGER, DOC]:
        if not path.exists(): errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for error in errors: print('- ' + error)
        return 1

    first = read(M1).lower()
    cleanup = read(M2).lower()
    doc = read(DOC).lower()
    rows = [x.strip() for x in read(LEDGER).splitlines() if x.strip() and not x.startswith('#')]

    row1 = '20260830015838 sinjira_v24_5_14_privacy_moderation_user_rpc_boundary'
    row2 = '20260830015937 sinjira_v24_5_15_user_rights_wrapper_cleanup'
    if len(rows) < 171: errors.append(f'Ledger historique tronqué: {len(rows)} migrations, au moins 171 attendues.')
    if rows.count(row1) != 1 or rows.count(row2) != 1: errors.append('Les deux migrations de convergence doivent apparaître exactement une fois.')
    if row1 in rows and row2 in rows and (rows.index(row1) != 169 or rows.index(row2) != 170): errors.append('Les migrations V24.5.37 doivent rester les 170e et 171e migrations canoniques dans cet ordre.')

    if 'sinjira_privacy_moderation_internal' not in first:
        errors.append('La migration de traçabilité doit reproduire la couche intermédiaire réellement appliquée.')
    for target in TARGETS:
        if target not in first: errors.append(f'RPC absente de la migration de traçabilité: {target}')
        if target not in cleanup: errors.append(f'RPC absente de la migration corrective: {target}')

    required_cleanup = [
        'sinjira_user_rights_internal.moderation_my_decisions',
        'sinjira_user_rights_internal.moderation_submit_appeal',
        'sinjira_user_rights_internal.privacy_create_request',
        'sinjira_user_rights_internal.privacy_export_my_extended_data',
        'sinjira_user_rights_internal.privacy_my_requests',
        'security invoker',
        'revoke all on function public.moderation_my_decisions(integer) from public, anon',
        'revoke all on function public.moderation_submit_appeal(uuid,text) from public, anon',
        'revoke all on function public.privacy_create_request(text,text) from public, anon',
        'revoke all on function public.privacy_export_my_extended_data() from public, anon',
        'revoke all on function public.privacy_my_requests(integer) from public, anon',
        'drop schema if exists sinjira_privacy_moderation_internal',
        'p_limit integer default 50',
        'p_details text default null',
        'p_limit integer default 20',
    ]
    for marker in required_cleanup:
        if marker not in cleanup: errors.append(f'Migration corrective incomplète: {marker}')

    for forbidden in ['stripe.com','checkout.stripe.com','paypal.com','api.resend.com','twilio','shippo','easypost']:
        if forbidden in first + cleanup: errors.append(f'Intégration externe interdite: {forbidden}')

    for marker in ['171 migrations','sinjira_user_rights_internal','security invoker','default 50','default null','default 20','aucun droit `execute`','aucune donnée supplémentaire']:
        if marker not in doc: errors.append(f'Document V24.5.37 incomplet: {marker}')

    if errors:
        print(f'ECHEC V24.5.37 convergence droits utilisateur: {len(errors)} problème(s).')
        for error in errors: print('- ' + error)
        return 1
    print('OK V24.5.37 historique: migrations 170/171 conservées, couche redondante supprimée, wrappers canoniques et valeurs par défaut restaurés, anon révoqué.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
