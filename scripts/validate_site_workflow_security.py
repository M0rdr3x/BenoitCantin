#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/validate-site.yml'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_NODE_SHA = '249970729cb0ef3589644e2896645e5dc5ba9c38'
PYTHON_VERSION = '3.12.14'
NODE_VERSION = '22.23.2'
V18_SELF = 'python scripts/validate_admin_v18_privacy_security.py --self-test'
V18_VALIDATE = 'python scripts/validate_admin_v18_privacy_security.py'
ADMIN_CONSOLE_SELF = 'python scripts/validate_admin_console_security.py --self-test'
ADMIN_CONSOLE_VALIDATE = 'python scripts/validate_admin_console_security.py'
ADMIN_PRIVATE_READS_SELF = 'python scripts/validate_admin_private_reads_security.py --self-test'
ADMIN_PRIVATE_READS_VALIDATE = 'python scripts/validate_admin_private_reads_security.py'


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


def exact_run_count(text: str, command: str) -> int:
    target = f'run: {command}'
    return sum(1 for line in text.splitlines() if line.strip() == target)


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'permissions:\n  contents: read' in text, 'permissions.contents doit rester read')
    require(errors, 'contents: write' not in text, 'permission contents:write interdite')
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'la validation centrale ne doit référencer aucun secret GitHub')
    require(errors, text.count('runs-on: ubuntu-24.04') == 2, 'les deux jobs doivent utiliser Ubuntu 24.04 explicite')
    require(errors, 'ubuntu-latest' not in text, 'ubuntu-latest interdit pour cette barrière critique')

    require(errors, text.count(f'uses: actions/checkout@{CHECKOUT_SHA}') == 2, 'les deux checkouts doivent être épinglés au SHA vérifié')
    require(errors, text.count('persist-credentials: false') == 2, 'les deux checkouts doivent désactiver la persistance des credentials')
    require(errors, 'persist-credentials: true' not in text, 'persist-credentials=true interdit')
    require(errors, text.count(f'uses: actions/setup-python@{SETUP_PYTHON_SHA}') == 1, 'setup-python doit être épinglé au SHA vérifié')
    require(errors, text.count(f'uses: actions/setup-node@{SETUP_NODE_SHA}') == 1, 'setup-node doit être épinglé au SHA vérifié')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python exacte requise')
    require(errors, f"node-version: '{NODE_VERSION}'" in text, 'version Node exacte requise')

    targets = action_targets(text)
    require(errors, len(targets) == 4, f'nombre inattendu d’actions réutilisables: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'référence d’action non immuable: {target}')

    require(errors, '  workflow-contract:\n' in text, 'job workflow-contract absent')
    require(errors, 'python3 scripts/validate_site_workflow_security.py --self-test' in text, 'auto-tests du contrat absents')
    require(errors, 'python3 scripts/validate_site_workflow_security.py\n' in text, 'validation du contrat absente')
    require(errors, text.count('needs: workflow-contract') == 1, 'le job validate doit dépendre du contrat')
    require(errors, 'python scripts/validate_site.py' in text, 'validation principale du site absente')
    require(errors, exact_run_count(text, V18_SELF) == 1, 'auto-test admin V18 absent ou dupliqué')
    require(errors, exact_run_count(text, V18_VALIDATE) == 1, 'validation admin V18 absente ou dupliquée')
    require(errors, exact_run_count(text, ADMIN_CONSOLE_SELF) == 1, 'auto-test admin-console absent ou dupliqué')
    require(errors, exact_run_count(text, ADMIN_CONSOLE_VALIDATE) == 1, 'validation admin-console absente ou dupliquée')
    require(errors, exact_run_count(text, ADMIN_PRIVATE_READS_SELF) == 1, 'auto-test lectures admin privées absent ou dupliqué')
    require(errors, exact_run_count(text, ADMIN_PRIVATE_READS_VALIDATE) == 1, 'validation lectures admin privées absente ou dupliquée')
    return errors


def run_self_tests(text: str) -> None:
    cases = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'setup-node mobile': text.replace(f'actions/setup-node@{SETUP_NODE_SHA}', 'actions/setup-node@v6', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'secret ajouté': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-24.04\n    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}', 1),
        'runner mobile': text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1),
        'python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'node large': text.replace(f"node-version: '{NODE_VERSION}'", "node-version: '22'", 1),
        'dépendance contrat retirée': text.replace('    needs: workflow-contract\n', '', 1),
        'auto-test V18 retiré': text.replace(f'        run: {V18_SELF}\n', '', 1),
        'validation V18 retirée': text.replace(f'        run: {V18_VALIDATE}\n', '', 1),
        'auto-test admin-console retiré': text.replace(f'        run: {ADMIN_CONSOLE_SELF}\n', '', 1),
        'validation admin-console retirée': text.replace(f'        run: {ADMIN_CONSOLE_VALIDATE}\n', '', 1),
        'auto-test lectures admin privées retiré': text.replace(f'        run: {ADMIN_PRIVATE_READS_SELF}\n', '', 1),
        'validation lectures admin privées retirée': text.replace(f'        run: {ADMIN_PRIVATE_READS_VALIDATE}\n', '', 1),
    }
    for name, mutated in cases.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test validation site: mutation sans effet: {name}')
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test validation site: mutation non détectée: {name}')
    print(f'OK auto-tests validation site: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not WORKFLOW.is_file():
        raise SystemExit(f'ERREUR validation site: workflow absent: {WORKFLOW.relative_to(ROOT)}')
    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        run_self_tests(text)
        return 0
    errors = validate_text(text)
    if errors:
        for error in errors:
            print(f'ERREUR sécurité validation site: {error}')
        return 1
    print('OK sécurité validation site: actions immuables, runtimes figés, credentials non persistés et gardes admin V18/admin-console/lectures privées obligatoires.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
