#!/usr/bin/env python3
"""Security contract for the contribution revocation CI workflow."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

WORKFLOW = Path('.github/workflows/sinjira-contribution-revocation-v24-5-52.yml')
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
PYTHON_VERSION = '3.12.14'


def fail(message: str) -> None:
    raise SystemExit(f'ERREUR: {message}')


def validate_text(text: str) -> None:
    required = [
        'permissions:\n  contents: read',
        'runs-on: ubuntu-24.04',
        'timeout-minutes: 5',
        f'uses: actions/checkout@{CHECKOUT_SHA}',
        'persist-credentials: false',
        f'uses: actions/setup-python@{SETUP_PYTHON_SHA}',
        f"python-version: '{PYTHON_VERSION}'",
        'python scripts/validate_contribution_revocation_workflow_security.py --self-test',
        'python scripts/validate_contribution_revocation_workflow_security.py',
        'python scripts/validate_contribution_revocation_v24_5_52.py',
        'python scripts/validate_delete_account_v24_5_51.py',
        'python scripts/validate_edge_function_inventory.py',
        'python scripts/validate_production_migration_ledger.py',
    ]
    for needle in required:
        if needle not in text:
            fail(f'élément obligatoire absent: {needle}')

    forbidden = [
        'ubuntu-latest',
        'actions/checkout@v',
        'actions/setup-python@v',
        "python-version: '3.12'",
        'persist-credentials: true',
        'SUPABASE_ACCESS_TOKEN',
        'SUPABASE_DB_PASSWORD',
        'supabase db push',
        '--linked',
        'supabase functions deploy',
    ]
    for needle in forbidden:
        if needle in text:
            fail(f'élément mutable, distant ou dangereux détecté: {needle}')

    if re.search(r'\$\{\{\s*secrets\.', text):
        fail('le workflow ne doit référencer aucun secret GitHub')

    if re.search(r'^\s*[A-Za-z0-9_-]+:\s*write\s*$', text, flags=re.MULTILINE):
        fail('permission GitHub en écriture détectée')

    uses_targets = re.findall(r'^\s*-?\s*uses:\s+(\S+)\s*$', text, flags=re.MULTILINE)
    if len(uses_targets) != 2:
        fail(f'nombre inattendu d’actions réutilisables: {len(uses_targets)}')
    for target in uses_targets:
        if '@' not in target or not re.fullmatch(r'[0-9a-f]{40}', target.rsplit('@', 1)[1]):
            fail(f'référence action non immuable: {target}')


def self_test(text: str) -> None:
    mutations = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'runner mobile': text.replace('ubuntu-24.04', 'ubuntu-latest', 1),
        'Python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'secret GitHub': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\nenv:\n  BAD: ${{ secrets.BAD }}',
            1,
        ),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'opération Supabase distante': text.replace(
            '      - name: Vérifier V24.5.52\n',
            '      - name: Mauvaise opération distante\n        run: supabase db push --linked\n\n      - name: Vérifier V24.5.52\n',
            1,
        ),
        'auto-test retiré': text.replace(
            '      - name: Auto-tester le contrat CI révocation contributions\n'
            '        run: python scripts/validate_contribution_revocation_workflow_security.py --self-test\n\n',
            '',
            1,
        ),
        'révocation retirée': text.replace('          python scripts/validate_contribution_revocation_v24_5_52.py\n', '', 1),
        'suppression de compte retirée': text.replace('          python scripts/validate_delete_account_v24_5_51.py\n', '', 1),
        'inventaire Edge retiré': text.replace('          python scripts/validate_edge_function_inventory.py\n', '', 1),
        'ledger retiré': text.replace('          python scripts/validate_production_migration_ledger.py\n', '', 1),
    }

    for label, mutated in mutations.items():
        if mutated == text:
            fail(f'auto-test invalide, mutation sans effet: {label}')
        try:
            validate_text(mutated)
        except SystemExit:
            continue
        fail(f'auto-test non détecté: {label}')

    print(f'OK: {len(mutations)} mutations critiques détectées')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()

    text = WORKFLOW.read_text(encoding='utf-8')
    if args.self_test:
        self_test(text)
    else:
        validate_text(text)
        print('OK: contrat CI révocation contributions respecté')


if __name__ == '__main__':
    main()
