#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/e2e-site.yml'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_NODE_SHA = '249970729cb0ef3589644e2896645e5dc5ba9c38'


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def action_targets(text: str) -> list[str]:
    targets = []
    for line in text.splitlines():
        match = re.match(r'^\s*(?:-\s*)?uses:\s+(\S+)', line)
        if match:
            targets.append(match.group(1))
    return targets


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'permissions:\n  contents: read' in text, 'permissions.contents doit rester read')
    require(errors, 'contents: write' not in text, 'permission contents:write interdite')
    require(errors, 'secrets.' not in text, 'aucun secret GitHub ne doit être référencé par les tests navigateur')

    require(errors, text.count(f'uses: actions/checkout@{CHECKOUT_SHA}') == 3, 'les trois checkouts doivent être épinglés au SHA vérifié')
    require(errors, text.count('persist-credentials: false') == 3, 'les trois checkouts doivent désactiver la persistance des credentials')
    require(errors, 'persist-credentials: true' not in text, 'persist-credentials=true interdit')
    require(errors, text.count(f'uses: actions/setup-python@{SETUP_PYTHON_SHA}') == 2, 'les deux setup-python doivent être épinglés au SHA vérifié')
    require(errors, text.count(f'uses: actions/setup-node@{SETUP_NODE_SHA}') == 1, 'setup-node doit être épinglé au SHA vérifié')

    targets = action_targets(text)
    require(errors, len(targets) == 6, f'nombre inattendu d’actions réutilisables: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'référence d’action non immuable: {target}')

    require(errors, '  workflow-contract:\n' in text, 'job workflow-contract absent')
    require(errors, 'python3 scripts/validate_e2e_workflow_security.py --self-test' in text, 'auto-tests du contrat E2E absents')
    require(errors, 'python3 scripts/validate_e2e_workflow_security.py' in text, 'validation du contrat E2E absente')
    require(errors, text.count('needs: workflow-contract') == 2, 'les deux jobs navigateur doivent dépendre du contrat de sécurité')

    for marker in ('browser-smoke:', 'lighthouse-mobile:'):
        require(errors, marker in text, f'job E2E attendu absent: {marker}')
    return errors


def run_self_tests(text: str) -> None:
    cases = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'setup-node mobile': text.replace(f'actions/setup-node@{SETUP_NODE_SHA}', 'actions/setup-node@v6', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'secret ajouté': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-24.04\n    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}', 1),
        'dépendance contrat retirée': text.replace('    needs: workflow-contract\n', '', 1),
    }
    for name, mutated in cases.items():
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test E2E: mutation non détectée: {name}')
    print(f'OK auto-tests E2E: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not WORKFLOW.is_file():
        raise SystemExit(f'ERREUR E2E: workflow absent: {WORKFLOW.relative_to(ROOT)}')
    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        run_self_tests(text)
        return 0
    errors = validate_text(text)
    if errors:
        for error in errors:
            print(f'ERREUR sécurité E2E: {error}')
        return 1
    print('OK sécurité E2E: actions immuables, credentials Git non persistés, aucun secret et contrat préalable obligatoire.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
