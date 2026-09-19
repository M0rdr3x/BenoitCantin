#!/usr/bin/env python3
"""Security contract for the private-profile CI workflow."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

WORKFLOW = Path('.github/workflows/sinjira-private-profile-v24-5-23.yml')
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_SUPABASE_SHA = '3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
PYTHON_VERSION = '3.12.14'
SUPABASE_VERSION = '2.111.0'
CONTRACT_TRIGGER = "      - 'scripts/validate_private_profile_workflow_security.py'"
CHECKS = (
    'python scripts/validate_private_profile_editing_v24_5_23.py',
    'python scripts/validate_production_schema_manifest.py',
    'python scripts/validate_production_migration_ledger.py',
    'python scripts/validate_rls_helper_rpc_v24_5_22.py',
    'python scripts/validate_security_contract.py',
    'python scripts/validate_free_only_mode.py',
    'supabase start',
    'supabase db reset',
    'supabase test db supabase/tests/private_profile_editing_v24_5_23.test.sql',
    'supabase test db supabase/tests/private_profile_child_age_v25.test.sql',
)


def fail(message: str) -> None:
    raise SystemExit(f'ERREUR: {message}')


def validate_text(text: str) -> None:
    for needle in (
        'permissions:\n  contents: read',
        'push:\n    branches: [main]',
        'runs-on: ubuntu-24.04',
        'timeout-minutes: 25',
        f'uses: actions/checkout@{CHECKOUT_SHA}',
        'persist-credentials: false',
        f'uses: actions/setup-python@{SETUP_PYTHON_SHA}',
        f"python-version: '{PYTHON_VERSION}'",
        f'uses: supabase/setup-cli@{SETUP_SUPABASE_SHA}',
        f"version: {SUPABASE_VERSION}",
        'supabase stop --no-backup',
        'python scripts/validate_private_profile_workflow_security.py --self-test',
        'python scripts/validate_private_profile_workflow_security.py',
        *CHECKS,
    ):
        if needle not in text:
            fail(f'élément obligatoire absent: {needle}')

    profile_test = 'supabase test db supabase/tests/private_profile_editing_v24_5_23.test.sql'
    child_test = 'supabase test db supabase/tests/private_profile_child_age_v25.test.sql'
    ledger = 'python scripts/validate_production_migration_ledger.py'
    if not (text.find(profile_test) < text.find(child_test) < text.find(ledger)):
        fail('le ledger production doit rester après les preuves pgTAP locales')
    if '      - name: Ledger production\n        if: always()\n        run: python scripts/validate_production_migration_ledger.py' not in text:
        fail('le ledger production doit toujours être exécuté après les preuves locales')

    if text.count(CONTRACT_TRIGGER) != 2:
        fail('le contrat CI doit déclencher le workflow sur PR et push')
    for path in ('scripts/validate_security_contract.py', 'scripts/validate_free_only_mode.py'):
        if text.count(f"      - '{path}'") != 2:
            fail(f'le script exécuté doit déclencher PR et push: {path}')

    for needle in (
        'ubuntu-latest', 'actions/checkout@v', 'actions/setup-python@v',
        "python-version: '3.12'", 'persist-credentials: true',
        'SUPABASE_ACCESS_TOKEN', 'SUPABASE_DB_PASSWORD', 'supabase db push',
        '--linked', 'supabase functions deploy',
    ):
        if needle in text:
            fail(f'élément mutable, distant ou dangereux détecté: {needle}')
    if re.search(r'\$\{\{\s*secrets\.', text):
        fail('le workflow ne doit référencer aucun secret GitHub')
    if re.search(r'^\s*[A-Za-z0-9_-]+:\s*write\s*$', text, flags=re.MULTILINE):
        fail('permission GitHub en écriture détectée')

    uses_targets = re.findall(r'^\s*-?\s*uses:\s+(\S+)\s*$', text, flags=re.MULTILINE)
    if len(uses_targets) != 3:
        fail(f'nombre inattendu d’actions réutilisables: {len(uses_targets)}')
    for target in uses_targets:
        if '@' not in target or not re.fullmatch(r'[0-9a-f]{40}', target.rsplit('@', 1)[1]):
            fail(f'référence action non immuable: {target}')


def self_test(text: str) -> None:
    mutations = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'setup-supabase mobile': text.replace(f'supabase/setup-cli@{SETUP_SUPABASE_SHA}', 'supabase/setup-cli@v1', 1),
        'version Supabase mobile': text.replace(f'version: {SUPABASE_VERSION}', 'version: latest', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'runner mobile': text.replace('ubuntu-24.04', 'ubuntu-latest', 1),
        'timeout réduit': text.replace('timeout-minutes: 25', 'timeout-minutes: 10', 1),
        'Python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'secret GitHub': text.replace('permissions:\n  contents: read', 'permissions:\n  contents: read\nenv:\n  BAD: ${{ secrets.BAD }}', 1),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'opération distante': text.replace('      - name: Contrat Profil privé V24.5.23\n', '      - name: Mauvaise opération distante\n        run: supabase db push --linked\n\n      - name: Contrat Profil privé V24.5.23\n', 1),
        'push main retiré': text.replace('  push:\n    branches: [main]\n', '', 1),
        'déclencheur contrat retiré': text.replace(CONTRACT_TRIGGER + '\n', '', 1),
        'auto-test retiré': text.replace('      - name: Auto-tester le contrat CI profil privé\n        run: python scripts/validate_private_profile_workflow_security.py --self-test\n\n', '', 1),
        'ledger replacé avant les tests': text.replace(
            '      - name: Ledger production\n        if: always()\n        run: python scripts/validate_production_migration_ledger.py\n\n',
            '      - name: Ledger production\n        if: always()\n        run: python scripts/validate_production_migration_ledger.py\n\n      - name: Marqueur ordre invalide\n        run: true\n\n',
            1
        ).replace(
            '      - name: Prouver le coffre privé historique\n',
            '      - name: Ledger production déplacé\n        if: always()\n        run: python scripts/validate_production_migration_ledger.py\n\n      - name: Prouver le coffre privé historique\n',
            1
        ),
    }
    for index, check in enumerate(CHECKS, start=1):
        mutations[f'contrôle {index} retiré'] = text.replace(f'        run: {check}\n', '', 1)

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
        print('OK: contrat CI profil privé respecté')


if __name__ == '__main__':
    main()
