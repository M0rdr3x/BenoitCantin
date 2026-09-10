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
PYTHON_VERSION = '3.12.14'
NODE_VERSION = '22.23.2'
LIGHTHOUSE_VERSION = '13.4.1'
PLAYWRIGHT_IMAGE = (
    'mcr.microsoft.com/playwright/python:v1.61.0-noble'
    '@sha256:a9731514f24121d1dcd25d58d0a38146646d290a5998fd80d3e533e7b5e21c69'
)
SELF_TEST_COMMAND = 'python3 scripts/validate_e2e_workflow_security.py --self-test'
VALIDATE_COMMAND = 'python3 scripts/validate_e2e_workflow_security.py'
SELF_TEST_RUN_LINE = f'run: {SELF_TEST_COMMAND}'
VALIDATE_RUN_LINE = f'run: {VALIDATE_COMMAND}'
LITERATURE_TEST_COMMAND = 'python tests/e2e/test_literature_site.py'


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def count_exact_stripped(text: str, target: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip() == target)


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
    require(errors, 'continue-on-error:' not in text, 'continue-on-error est interdit dans le workflow navigateur')
    require(errors, 'set -x' not in text, 'set -x est interdit afin de ne pas élargir les traces CI')

    require(errors, text.count(f'uses: actions/checkout@{CHECKOUT_SHA}') == 3, 'les trois checkouts doivent être épinglés au SHA vérifié')
    require(errors, text.count('persist-credentials: false') == 3, 'les trois checkouts doivent désactiver la persistance des credentials')
    require(errors, 'persist-credentials: true' not in text, 'persist-credentials=true interdit')
    require(errors, text.count(f'uses: actions/setup-python@{SETUP_PYTHON_SHA}') == 2, 'les deux setup-python doivent être épinglés au SHA vérifié')
    require(errors, text.count(f'uses: actions/setup-node@{SETUP_NODE_SHA}') == 1, 'setup-node doit être épinglé au SHA vérifié')

    targets = action_targets(text)
    require(errors, len(targets) == 6, f'nombre inattendu d’actions réutilisables: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'référence d’action non immuable: {target}')

    require(errors, text.count('runs-on: ubuntu-24.04') == 3, 'les trois jobs E2E doivent rester sur Ubuntu 24.04 explicite')
    require(errors, 'runs-on: ubuntu-latest' not in text, 'ubuntu-latest est interdit pour les tests E2E reproductibles')
    require(errors, f'image: {PLAYWRIGHT_IMAGE}' in text, 'l’image Playwright doit être épinglée au digest Microsoft vérifié')
    require(errors, 'image: mcr.microsoft.com/playwright/python:v1.61.0-noble\n' not in text, 'le tag Playwright sans digest est interdit')
    require(errors, text.count(f"python-version: '{PYTHON_VERSION}'") == 2, f'Python doit rester figé à {PYTHON_VERSION}')
    require(errors, f"node-version: '{NODE_VERSION}'" in text, f'Node doit rester figé à {NODE_VERSION}')
    require(errors, f'npx --yes lighthouse@{LIGHTHOUSE_VERSION} ' in text, f'Lighthouse doit rester figé à {LIGHTHOUSE_VERSION}')
    require(errors, 'npx --yes lighthouse http' not in text, 'Lighthouse sans version explicite est interdit')

    cache_input = re.search(r'^\s*(?:cache|package-manager-cache|cache-dependency-path):\s*', text, re.MULTILINE)
    require(
        errors,
        cache_input is None,
        'aucune entrée de cache de gestionnaire de paquets n’est permise sans lockfile npm approuvé',
    )

    require(errors, '  workflow-contract:\n' in text, 'job workflow-contract absent')
    require(errors, count_exact_stripped(text, SELF_TEST_RUN_LINE) == 1, 'auto-test exact du contrat E2E absent ou dupliqué')
    require(errors, count_exact_stripped(text, VALIDATE_RUN_LINE) == 1, 'validation exacte du contrat E2E absente ou dupliquée')
    require(errors, count_exact_stripped(text, 'needs: workflow-contract') == 2, 'les deux jobs navigateur doivent dépendre exactement du contrat de sécurité')
    require(errors, text.count('python tests/e2e/test_public_site.py') == 2, 'le smoke test public doit couvrir le dépôt local et le site déployé')
    require(errors, count_exact_stripped(text, LITERATURE_TEST_COMMAND) == 2, 'le contrat Littérature doit couvrir le dépôt local et le site déployé')

    for marker in ('browser-smoke:', 'lighthouse-mobile:'):
        require(errors, marker in text, f'job E2E attendu absent: {marker}')
    return errors


def run_self_tests(text: str) -> None:
    baseline_errors = validate_text(text)
    if baseline_errors:
        raise SystemExit(
            'ERREUR auto-test E2E: le baseline doit être valide avant les mutations: '
            + ' | '.join(baseline_errors)
        )

    cases = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'setup-node mobile': text.replace(f'actions/setup-node@{SETUP_NODE_SHA}', 'actions/setup-node@v6', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'secret ajouté': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-24.04\n    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}', 1),
        'dépendance contrat retirée': text.replace('    needs: workflow-contract\n', '', 1),
        'runner mobile': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1),
        'image Playwright sans digest': text.replace(PLAYWRIGHT_IMAGE, 'mcr.microsoft.com/playwright/python:v1.61.0-noble', 1),
        'Python non figé': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'Node non figé': text.replace(f"node-version: '{NODE_VERSION}'", "node-version: '22'", 1),
        'Lighthouse non figé': text.replace(f'lighthouse@{LIGHTHOUSE_VERSION}', 'lighthouse', 1),
        'cache npm ajouté': text.replace(f"node-version: '{NODE_VERSION}'", f"node-version: '{NODE_VERSION}'\n          cache: npm", 1),
        'cache false ajouté': text.replace(f"node-version: '{NODE_VERSION}'", f"node-version: '{NODE_VERSION}'\n          package-manager-cache: false", 1),
        'test Littérature retiré': text.replace(f'            {LITERATURE_TEST_COMMAND}\n', '', 1),
        'validation contrat retirée': text.replace(f'run: {VALIDATE_COMMAND}\n', 'run: echo validation-retirée\n', 1),
        'continue-on-error ajouté': text.replace('timeout-minutes: 5', 'timeout-minutes: 5\n    continue-on-error: true', 1),
        'set -x ajouté': text.replace('          run_suite() {', '          set -x\n          run_suite() {', 1),
    }
    for name, mutated in cases.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test E2E: mutation non appliquée: {name}')
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test E2E: mutation non détectée: {name}')
    print(f'OK auto-tests E2E: baseline valide + {len(cases)} affaiblissements critiques détectés.')


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
    print(
        'OK sécurité E2E: actions immuables, credentials Git non persistés, aucun secret, '
        'Ubuntu/Python/Node/Lighthouse figés, aucun cache npm sans lockfile et contrat Littérature actif.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
