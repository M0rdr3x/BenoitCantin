#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-secret-guard.yml'
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
    require(errors, re.search(r'\$\{\{\s*secrets\.', text) is None, 'le garde secrets ne doit référencer aucun secret GitHub')
    require(errors, 'on:\n  pull_request:\n' in text, 'garde secrets obligatoire sur toutes les PR')
    require(errors, '    branches:\n      - main\n' in text, 'garde secrets obligatoire sur main')
    require(errors, re.search(r'(?m)^\s+paths(?:-ignore)?:', text) is None,
            'aucune exclusion de chemin permise')
    require(errors, 'pull_request_target:' not in text, 'aucun contexte PR privilégié permis')
    require(errors, 'continue-on-error:' not in text, 'le garde secrets doit bloquer')
    require(errors, '    timeout-minutes: 10\n' in text, 'durée maximale du garde secrets absente')
    require(errors, 'runs-on: ubuntu-24.04' in text, 'runner Ubuntu 24.04 explicite requis')
    require(errors, 'ubuntu-latest' not in text, 'ubuntu-latest interdit pour ce garde critique')

    require(errors, text.count(f'uses: actions/checkout@{CHECKOUT_SHA}') == 1, 'checkout doit être épinglé au SHA vérifié')
    require(errors, text.count(f'uses: actions/setup-python@{SETUP_PYTHON_SHA}') == 1, 'setup-python doit être épinglé au SHA vérifié')
    require(errors, text.count('persist-credentials: false') == 1, 'checkout doit désactiver la persistance des credentials')
    require(errors, 'persist-credentials: true' not in text, 'persist-credentials=true interdit')
    require(errors, 'fetch-depth: 1' in text, 'le scan doit conserver un checkout borné à un commit')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python exacte requise')

    targets = action_targets(text)
    require(errors, len(targets) == 2, f'nombre inattendu d’actions réutilisables: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'référence d’action non immuable: {target}')

    require(errors, 'python scripts/validate_secret_guard_workflow_security.py --self-test' in text, 'auto-tests du contrat absents')
    require(errors, 'python scripts/validate_secret_guard_workflow_security.py\n' in text, 'validation du contrat absente')
    require(errors, text.count('        run: python scripts/validate_repo_workflow_security.py --self-test\n') == 1,
            'autotest des workflows GitHub absent/dupliqué')
    require(errors, text.count('        run: python scripts/validate_repo_workflow_security.py\n') == 1,
            'audit des workflows GitHub absent/dupliqué')
    require(errors, text.count('          python scripts/validate_edge_jwt_boundaries.py --self-test\n') == 1,
            'autotests des trois exceptions JWT absents')
    require(errors, text.count('          python scripts/validate_edge_jwt_boundaries.py\n') == 1,
            'contrat JWT Edge absent')
    require(errors, text.count('        run: node --test tests/test_edge_error_log_redaction.cjs\n') == 1,
            'audit de confidentialité des journaux Edge absent')
    require(errors, text.count('        run: python scripts/validate_no_committed_secrets.py --self-test\n') == 1,
            'autotest exhaustif du garde secrets absent/dupliqué')
    require(errors, text.count('          python scripts/validate_admin_mfa_v24_4_67.py\n') == 1,
            'validation MFA administrateur obligatoire absente')
    require(errors, text.count('          node --test tests/test_admin_mfa_policy.cjs\n') == 1,
            'tests AAL2 serveur absents')
    require(errors, text.count('        run: node --test tests/test_edge_remote_pdf_stream.cjs\n') == 1,
            'tests PDF distants bornés obligatoires absents')
    require(errors, text.count('        run: node --test tests/test_admin_request_body_bounds.cjs\n') == 1,
            'tests du lecteur borné des six API administrateur absents')
    require(errors, text.count('        run: python scripts/validate_no_committed_secrets.py\n') == 1,
            'scan bloquant des secrets absent/dupliqué')
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
        'auto-test retiré': text.replace('        run: python scripts/validate_secret_guard_workflow_security.py --self-test\n', '', 1),
        'auto-test secrets retiré': text.replace('        run: python scripts/validate_no_committed_secrets.py --self-test\n', '', 1),
        'scan secrets retiré': text.replace('        run: python scripts/validate_no_committed_secrets.py\n', '', 1),
        'audit workflows retiré': text.replace('        run: python scripts/validate_repo_workflow_security.py\n', '', 1),
        'autotest workflows retiré': text.replace('        run: python scripts/validate_repo_workflow_security.py --self-test\n', '', 1),
        'scan avec filtre de chemins': text.replace('  pull_request:\n', '  pull_request:\n    paths: ["docs/**"]\n', 1),
        'scan non bloquant': text.replace('    timeout-minutes: 10\n', '    timeout-minutes: 10\n    continue-on-error: true\n', 1),
        'limite de temps supprimée': text.replace('    timeout-minutes: 10\n', '', 1),
    }
    for name, mutated in cases.items():
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test garde secrets: mutation non détectée: {name}')
    print(f'OK auto-tests garde secrets: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not WORKFLOW.is_file():
        raise SystemExit(f'ERREUR garde secrets: workflow absent: {WORKFLOW.relative_to(ROOT)}')
    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        run_self_tests(text)
        return 0
    errors = validate_text(text)
    if errors:
        for error in errors:
            print(f'ERREUR sécurité garde secrets: {error}')
        return 1
    print('OK sécurité garde secrets: actions immuables, runtime figé, permissions lecture seule et aucun secret consommé.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
