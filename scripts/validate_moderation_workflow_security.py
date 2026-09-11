#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/validate-moderation-v24-4-90.yml'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_NODE_SHA = '249970729cb0ef3589644e2896645e5dc5ba9c38'
PYTHON_VERSION = '3.12.14'
NODE_VERSION = '22.23.2'
REQUEST_TRIGGER = "      - 'scripts/validate_admin_social_request_security.py'\n"
WORKFLOW_TRIGGER = "      - 'scripts/validate_moderation_workflow_security.py'\n"


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    def need(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    need('permissions:\n  contents: read' in text, 'permissions.contents doit rester read')
    need('contents: write' not in text, 'permission contents:write interdite')
    need(re.search(r'\$\{\{\s*secrets\.', text) is None, 'aucun secret GitHub ne doit être référencé')
    need('runs-on: ubuntu-24.04' in text, 'runner Ubuntu 24.04 exact requis')
    need('ubuntu-latest' not in text, 'ubuntu-latest interdit')
    need('timeout-minutes: 10' in text, 'timeout de 10 minutes requis')
    need(text.count(f'actions/checkout@{CHECKOUT_SHA}') == 1, 'checkout SHA exact requis')
    need(text.count(f'actions/setup-python@{SETUP_PYTHON_SHA}') == 1, 'setup-python SHA exact requis')
    need(text.count(f'actions/setup-node@{SETUP_NODE_SHA}') == 1, 'setup-node SHA exact requis')
    need(text.count('persist-credentials: false') == 1, 'credentials checkout non persistés requis')
    need('persist-credentials: true' not in text, 'persist-credentials=true interdit')
    need(f"python-version: '{PYTHON_VERSION}'" in text, 'Python exact requis')
    need(f"node-version: '{NODE_VERSION}'" in text, 'Node exact requis')

    actions = re.findall(r'^\s*-?\s*uses:\s+(\S+)\s*$', text, flags=re.MULTILINE)
    need(len(actions) == 3, f'nombre inattendu d’actions réutilisables: {len(actions)}')
    for action in actions:
        need(re.search(r'@[0-9a-f]{40}$', action) is not None, f'action non immuable: {action}')

    required_commands = [
        'python scripts/validate_moderation_workflow_security.py --self-test',
        'python scripts/validate_moderation_workflow_security.py\n',
        'python scripts/validate_admin_social_request_security.py --self-test',
        'python scripts/validate_admin_social_request_security.py\n',
        'python scripts/validate_moderation_appeals_v24_4_90.py',
        'python scripts/validate_production_migration_ledger.py',
        'python scripts/validate_production_schema_manifest.py',
        'node --check assets/js/sinjira-admin-social-v20.js',
        'node --check assets/js/sinjira-moderation-appeals-v24-4-90.js',
    ]
    for command in required_commands:
        need(command in text, f'commande de validation absente: {command.strip()}')
    need(text.count(REQUEST_TRIGGER) == 2, 'le garde HTTP modération doit déclencher PR et push')
    need(text.count(WORKFLOW_TRIGGER) == 2, 'le méta-garde workflow doit déclencher PR et push')
    return errors


def self_test(text: str) -> None:
    mutations = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'node mobile': text.replace(f'actions/setup-node@{SETUP_NODE_SHA}', 'actions/setup-node@v6', 1),
        'runner mobile': text.replace('ubuntu-24.04', 'ubuntu-latest', 1),
        'python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'node large': text.replace(f"node-version: '{NODE_VERSION}'", "node-version: '22'", 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'secret ajouté': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-24.04\n    env:\n      BAD: ${{ secrets.BAD }}', 1),
        'auto-test HTTP retiré': text.replace('        run: python scripts/validate_admin_social_request_security.py --self-test\n', '', 1),
        'contrôle HTTP retiré': text.replace('        run: python scripts/validate_admin_social_request_security.py\n', '', 1),
        'déclencheur HTTP retiré': text.replace(REQUEST_TRIGGER, '', 1),
        'contrat appels retiré': text.replace('        run: python scripts/validate_moderation_appeals_v24_4_90.py\n', '', 1),
    }
    for label, mutated in mutations.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test workflow modération: mutation sans effet: {label}')
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test workflow modération: mutation non détectée: {label}')
    print(f'OK auto-test workflow modération: {len(mutations)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Valide le durcissement du workflow modération.')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not WORKFLOW.is_file():
        print(f'ÉCHEC workflow modération: fichier absent: {WORKFLOW.relative_to(ROOT)}')
        return 1
    text = WORKFLOW.read_text('utf-8', errors='strict')
    if args.self_test:
        self_test(text)
        return 0
    errors = validate_text(text)
    if errors:
        print(f'ÉCHEC workflow modération: {len(errors)} problème(s).')
        for error in errors:
            print('- ' + error)
        return 1
    print('OK workflow modération: runner et actions immuables, runtimes exacts et gardes HTTP/appels conservés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
