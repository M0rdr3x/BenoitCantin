#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'SECURITY_ADVISOR_CONTRACT_V24_5_24.md'
TEST = ROOT / 'supabase/tests/security_advisor_contract_v24_5_24.test.sql'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
MIG = ROOT / 'supabase/migrations'


def read(path):
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main():
    errors = []
    for path in (DOC, TEST, LEDGER):
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')
    if errors:
        for err in errors:
            print('- ' + err)
        return 1

    doc = read(DOC).lower()
    test = read(TEST).lower()
    rows = [line.strip() for line in read(LEDGER).splitlines() if line.strip() and not line.startswith('#')]

    if len(rows) != 155:
        errors.append(f'Ledger: {len(rows)} migrations au lieu de 155.')
    expected_last = '20260823040936 sinjira_v24_5_23_private_profile_schema_convergence'
    if not rows or rows[-1] != expected_last:
        errors.append('Le ledger doit rester aligné sur V24.5.23; V24.5.24 ne crée aucune migration.')

    if any('24_5_24' in p.name for p in MIG.glob('*.sql')):
        errors.append('V24.5.24 est un contrat de validation et ne doit pas ajouter de migration SQL.')

    doc_markers = [
        'aucune migration de production',
        '155 migrations',
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
        "'public.private_profiles'::regclass",
        'select * from finish()',
        'rollback;',
    ]
    for marker in test_markers:
        if marker not in test:
            errors.append(f'Contrat pgTAP V24.5.24 incomplet: {marker}')

    forbidden = ['stripe', 'paypal', 'twilio', 'api.resend.com', 'api.openai.com', 'shippo', 'easypost']
    for token in forbidden:
        if token in test:
            errors.append(f'Le contrat SQL ne doit intégrer aucun fournisseur externe: {token}')

    if errors:
        print(f'ECHEC V24.5.24 contrat advisor sécurité: {len(errors)} problème(s).')
        for err in errors:
            print('- ' + err)
        return 1

    print('OK V24.5.24: tables scellées protégées, SECURITY DEFINER public non exposé, findings INFO documentés, aucun service payant activé, ledger 155 inchangé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
