#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'SECURITY_ADVISOR_CONTRACT_V24_5_24.md'
TEST = ROOT / 'supabase/tests/security_advisor_contract_v24_5_24.test.sql'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
MIG = ROOT / 'supabase/migrations/20260823044507_sinjira_v24_5_24_security_definer_reconstruction_convergence.sql'


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in (DOC, TEST, LEDGER, MIG):
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for err in errors:
            print('- ' + err)
        return 1

    doc = read(DOC).lower()
    test = read(TEST).lower()
    migration = read(MIG).lower()
    rows = [line.strip() for line in read(LEDGER).splitlines() if line.strip() and not line.startswith('#')]

    expected_last = '20260823044507 sinjira_v24_5_24_security_definer_reconstruction_convergence'
    if len(rows) != 156:
        errors.append(f'Ledger: {len(rows)} migrations au lieu de 156.')
    if not rows or rows[-1] != expected_last:
        errors.append('Le ledger doit finir sur la convergence SECURITY DEFINER V24.5.24.')
    if rows.count(expected_last) != 1:
        errors.append('Le ledger doit contenir exactement une occurrence de la migration V24.5.24.')

    migration_markers = [
        'drop function if exists public.grant_owner_novel_library()',
        'drop function if exists public.grant_owner_product_entitlement()',
        'drop function if exists public.grant_owner_project_access()',
        'drop function if exists public.spend_sinjira_tokens(integer, text, text, text, uuid)',
        'revoke all privileges on function public.project_access_rank(uuid, uuid) from public, anon, authenticated',
        'grant execute on function public.project_access_rank(uuid, uuid) to service_role',
    ]
    for marker in migration_markers:
        if marker not in migration:
            errors.append(f'Migration V24.5.24 incomplète: {marker}')
    if 'cascade' in migration.replace('aucun cascade', '').replace('sans cascade', ''):
        errors.append('La convergence V24.5.24 ne doit pas utiliser DROP ... CASCADE.')

    doc_markers = [
        '156 migrations',
        '20260823044507',
        'convergence',
        'sans `cascade`',
        'rls enabled no policy',
        'aucun privilège direct',
        'security definer',
        'security invoker',
        'unused_index',
        'aucun index ne doit être supprimé',
        'leaked password protection disabled',
        'plan payant',
        'aucun service payant',
        'branch protection',
    ]
    for marker in doc_markers:
        if marker not in doc:
            errors.append(f'Document V24.5.24 incomplet: {marker}')

    test_markers = [
        'select plan(4)',
        "n.nspname in ('public','private')",
        "not exists(select 1 from pg_policy pol where pol.polrelid=c.oid)",
        "has_table_privilege('anon'",
        "has_table_privilege('authenticated'",
        "n.nspname='public'",
        'p.prosecdef',
        'string_agg',
        "'public.private_profiles'::regclass",
        'select * from finish()',
        'rollback;',
    ]
    for marker in test_markers:
        if marker not in test:
            errors.append(f'Contrat pgTAP V24.5.24 incomplet: {marker}')

    forbidden = ['stripe', 'paypal', 'twilio', 'api.resend.com', 'api.openai.com', 'shippo', 'easypost']
    for token in forbidden:
        if token in test or token in migration:
            errors.append(f'V24.5.24 ne doit intégrer aucun fournisseur externe: {token}')

    if errors:
        print(f'ECHEC V24.5.24 contrat advisor sécurité: {len(errors)} problème(s).')
        for err in errors:
            print('- ' + err)
        return 1

    print('OK V24.5.24: convergence reproductible, tables scellées protégées, SECURITY DEFINER public non exposé, aucun service payant activé, ledger 156 synchronisé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
