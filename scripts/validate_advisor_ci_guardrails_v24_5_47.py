#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'ADVISOR_AND_CI_GUARDRAILS_V24_5_47.md'
E2E = ROOT / '.github/workflows/e2e-site.yml'
LEDGER = ROOT / 'supabase/production-migration-ledger.txt'
MIGRATIONS = ROOT / 'supabase/migrations'


def read(path: Path) -> str:
    return path.read_text('utf-8', errors='ignore') if path.exists() else ''


def main() -> int:
    errors = []
    for path in (DOC, E2E, LEDGER):
        if not path.exists():
            errors.append(f'Fichier absent: {path.relative_to(ROOT)}')

    if errors:
        for error in errors:
            print('- ' + error)
        return 1

    doc = read(DOC).lower()
    e2e = read(E2E)
    rows = [line.strip() for line in read(LEDGER).splitlines() if line.strip() and not line.startswith('#')]

    if len(rows) != 174:
        errors.append(f'Ledger: {len(rows)} migrations au lieu de 174.')
    expected_last = '20260831004411 sinjira_v24_5_46_preorder_uuid_output_hardening'
    if not rows or rows[-1] != expected_last:
        errors.append('V24.5.47 ne doit pas ajouter une migration no-op; V24.5.46 doit rester la dernière migration production.')

    v47_migrations = sorted(MIGRATIONS.glob('*v24_5_47*.sql'))
    if v47_migrations:
        errors.append('V24.5.47 est un contrat CI/documentaire et ne doit pas créer de migration Supabase.')

    required_doc = [
        'rls enabled no policy',
        'ne jamais créer une politique permissive',
        'unused_index',
        'ne pas supprimer automatiquement un index couvrant une clé étrangère',
        'leaked password protection disabled',
        '12 caractères',
        'une seule relance bornée',
        'aucune assertion fonctionnelle n\'est supprimée',
        'n\'active aucun paiement',
        'uuid internes restent opaques',
    ]
    for marker in required_doc:
        if marker not in doc:
            errors.append(f'Document V24.5.47 incomplet: {marker}')

    workflow_markers = [
        'if [ "$BROWSER" != "firefox" ]; then',
        'Premier passage Firefox en échec; une seule relance bornée',
        'sleep 2',
        'python tests/e2e/test_public_site.py',
    ]
    for marker in workflow_markers:
        if marker not in e2e:
            errors.append(f'Workflow navigateur sans garde V24.5.47: {marker}')

    if e2e.count('Premier passage Firefox en échec; une seule relance bornée') != 1:
        errors.append('La relance Firefox doit être déclarée exactement une fois.')
    if e2e.count('if [ "$BROWSER" != "firefox" ]; then') != 1:
        errors.append('Le retry doit rester strictement limité à Firefox.')

    if errors:
        print(f'ECHEC V24.5.47: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1

    print('OK V24.5.47: advisor interprété sans ouverture RLS artificielle, index conservés sans lint-chasing, aucun service payant activé et retry Firefox unique borné; ledger inchangé à 174.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
