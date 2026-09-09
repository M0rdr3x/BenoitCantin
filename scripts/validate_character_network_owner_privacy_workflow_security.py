#!/usr/bin/env python3
"""Security contract for the character-network owner privacy workflow."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

WORKFLOW = Path('.github/workflows/sinjira-character-network-owner-privacy-v25.yml')
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
PYTHON_VERSION = '3.12.14'
CONTRACT_TRIGGER = "      - 'scripts/validate_character_network_owner_privacy_workflow_security.py'"
RUNTIME_TRIGGER = "      - 'assets/js/sinjira-community-character.js'"
SELF_TEST_STEP = (
    '      - name: Auto-tester le contrat CI confidentialité Réseau personnage\n'
    '        run: python scripts/validate_character_network_owner_privacy_workflow_security.py --self-test\n'
)
CONTRACT_STEP = (
    '      - name: Vérifier le contrat CI confidentialité Réseau personnage\n'
    '        run: python scripts/validate_character_network_owner_privacy_workflow_security.py\n'
)


def fail(message: str) -> None:
    raise SystemExit(f'ERREUR: {message}')


def validate_text(text: str) -> None:
    required = [
        'permissions:\n  contents: read',
        'pull_request:',
        'push:\n    branches: [main]',
        'workflow_dispatch:',
        'runs-on: ubuntu-24.04',
        'timeout-minutes: 8',
        f'uses: actions/checkout@{CHECKOUT_SHA}',
        'persist-credentials: false',
        f'uses: actions/setup-python@{SETUP_PYTHON_SHA}',
        f"python-version: '{PYTHON_VERSION}'",
        SELF_TEST_STEP,
        CONTRACT_STEP,
        'python3 scripts/validate_character_network_owner_privacy_v25.py',
        'python3 scripts/validate_owner_role_invoker.py',
        'python3 scripts/validate_owner_character_rpc_v24_5_20.py',
        'python3 scripts/validate_character_identity_rls.py',
        'python3 scripts/validate_social_user_rpc_v24_5_15.py',
        'python3 scripts/validate_no_committed_secrets.py',
    ]
    for needle in required:
        if needle not in text:
            fail(f'élément obligatoire absent: {needle}')

    if text.count(CONTRACT_TRIGGER) != 2:
        fail('le contrat CI doit déclencher le workflow sur PR et push')
    if text.count(RUNTIME_TRIGGER) != 2:
        fail('le runtime Réseau personnage doit déclencher PR et push')

    forbidden = [
        'ubuntu-latest',
        'actions/checkout@v',
        'actions/setup-python@v',
        "python-version: '3.12'",
        'persist-credentials: true',
        'SUPABASE_ACCESS_TOKEN',
        'SUPABASE_DB_PASSWORD',
        'environment: production',
        'supabase db',
        'supabase migration',
        'supabase link',
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
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'secret GitHub': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\nenv:\n  BAD: ${{ secrets.BAD }}',
            1,
        ),
        'environnement production': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\nenvironment: production',
            1,
        ),
        'capacité Supabase distante': text.replace(
            '      - name: Valider la confidentialité du rôle propriétaire\n',
            '      - name: Mauvaise capacité distante\n        run: supabase link\n\n      - name: Valider la confidentialité du rôle propriétaire\n',
            1,
        ),
        'push main retiré': text.replace('  push:\n    branches: [main]\n', '', 1),
        'déclencheur contrat retiré': text.replace(CONTRACT_TRIGGER + '\n', '', 1),
        'déclencheur runtime retiré': text.replace(RUNTIME_TRIGGER + '\n', '', 1),
        'auto-test retiré': text.replace(SELF_TEST_STEP + '\n', '', 1),
        'contrat CI retiré': text.replace(CONTRACT_STEP + '\n', '', 1),
        'garde confidentialité retiré': text.replace(
            '        run: python3 scripts/validate_character_network_owner_privacy_v25.py\n',
            '',
            1,
        ),
        'garde propriétaire retiré': text.replace(
            '        run: python3 scripts/validate_owner_role_invoker.py\n',
            '',
            1,
        ),
        'garde RLS retiré': text.replace(
            '        run: python3 scripts/validate_character_identity_rls.py\n',
            '',
            1,
        ),
        'garde secrets retiré': text.replace(
            '        run: python3 scripts/validate_no_committed_secrets.py\n',
            '',
            1,
        ),
        'timeout modifié': text.replace('timeout-minutes: 8', 'timeout-minutes: 30', 1),
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
        print('OK: contrat CI confidentialité Réseau personnage V25 respecté')


if __name__ == '__main__':
    main()
