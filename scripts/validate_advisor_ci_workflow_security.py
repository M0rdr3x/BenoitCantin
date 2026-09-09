#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-advisor-ci-guardrails-v24-5-47.yml'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
PYTHON_VERSION = '3.12.14'


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def action_targets(text: str) -> list[str]:
    targets: list[str] = []
    for line in text.splitlines():
        match = re.match(r'^\s*(?:-\s*)?uses:\s+(\S+)', line)
        if match:
            targets.append(match.group(1))
    return targets


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'permissions:\n  contents: read' in text, 'permissions.contents doit rester read')
    require(errors, 'contents: write' not in text, 'permission contents:write interdite')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'aucun secret GitHub ne doit être référencé')
    require(errors, 'runs-on: ubuntu-24.04' in text, 'runner Ubuntu 24.04 explicite requis')
    require(errors, 'ubuntu-latest' not in text, 'ubuntu-latest interdit')
    require(errors, 'timeout-minutes: 5' in text, 'timeout de 5 minutes requis')

    require(errors, text.count(f'uses: actions/checkout@{CHECKOUT_SHA}') == 1, 'checkout doit être épinglé au SHA vérifié')
    require(errors, text.count('persist-credentials: false') == 1, 'checkout doit désactiver les credentials persistés')
    require(errors, 'persist-credentials: true' not in text, 'persist-credentials=true interdit')
    require(errors, text.count(f'uses: actions/setup-python@{SETUP_PYTHON_SHA}') == 1, 'setup-python doit être épinglé au SHA vérifié')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python exacte requise')

    targets = action_targets(text)
    require(errors, len(targets) == 2, f'nombre inattendu d’actions réutilisables: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'référence d’action non immuable: {target}')

    required_runs = (
        'python scripts/validate_advisor_ci_workflow_security.py --self-test',
        'python scripts/validate_advisor_ci_workflow_security.py\n',
        'python scripts/validate_advisor_ci_guardrails_v24_5_47.py',
        'python scripts/validate_auth_password_hardening_workflow.py',
    )
    for command in required_runs:
        require(errors, command in text, f'commande de contrôle absente: {command.strip()}')
    return errors


def run_self_tests(text: str) -> None:
    cases = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'secret ajouté': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-24.04\n    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}', 1),
        'runner mobile': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1),
        'python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'advisor retiré': text.replace('        run: python scripts/validate_advisor_ci_guardrails_v24_5_47.py\n', '', 1),
        'auth retiré': text.replace('        run: python scripts/validate_auth_password_hardening_workflow.py\n', '', 1),
    }
    for name, mutated in cases.items():
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test advisor CI: mutation non détectée: {name}')
    print(f'OK auto-tests advisor CI: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not WORKFLOW.is_file():
        raise SystemExit(f'ERREUR advisor CI: workflow absent: {WORKFLOW.relative_to(ROOT)}')
    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        run_self_tests(text)
        return 0
    errors = validate_text(text)
    if errors:
        for error in errors:
            print(f'ERREUR sécurité advisor CI: {error}')
        return 1
    print('OK sécurité advisor CI: actions immuables, runtime figé, credentials non persistés et contrôles advisor/Auth conservés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
