#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-public-edge-auth-guard.yml'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
PYTHON_VERSION = '3.12.14'
ADMIN_REPORTS_TRIGGER = "      - 'scripts/validate_admin_reports_request_security.py'\n"
ADMIN_LICENSE_TRIGGER = "      - 'scripts/validate_admin_license_codes_security.py'\n"
ADMIN_CONSOLE_TRIGGER = "      - 'scripts/validate_admin_console_request_security.py'\n"
ADMIN_V18_TRIGGER = "      - 'scripts/validate_admin_sinjira_v18_request_security.py'\n"
ADMIN_ANALYTICS_TRIGGER = "      - 'scripts/validate_admin_analytics_request_security.py'\n"
ADMIN_USERS_TRIGGER = "      - 'scripts/validate_admin_users_privacy.py'\n"


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
    require(errors, 'timeout-minutes: 5' in text, 'timeout borné à 5 minutes requis')

    require(errors, text.count(f'uses: actions/checkout@{CHECKOUT_SHA}') == 1, 'checkout doit être épinglé au SHA vérifié')
    require(errors, text.count('persist-credentials: false') == 1, 'checkout doit désactiver les credentials persistés')
    require(errors, 'persist-credentials: true' not in text, 'persist-credentials=true interdit')
    require(errors, text.count(f'uses: actions/setup-python@{SETUP_PYTHON_SHA}') == 1, 'setup-python doit être épinglé au SHA vérifié')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, 'version Python exacte requise')

    targets = action_targets(text)
    require(errors, len(targets) == 2, f'nombre inattendu d’actions réutilisables: {len(targets)}')
    for target in targets:
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'référence d’action non immuable: {target}')

    required = [
        'python scripts/validate_public_edge_auth_workflow_security.py --self-test',
        'python scripts/validate_public_edge_auth_workflow_security.py\n',
        'python scripts/validate_public_edge_auth.py',
        'python scripts/validate_license_redemption_security.py --self-test',
        'python scripts/validate_license_redemption_security.py\n',
        'python scripts/validate_security_context_request_security.py --self-test',
        'python scripts/validate_security_context_request_security.py\n',
        'python scripts/validate_admin_reports_request_security.py --self-test',
        'python scripts/validate_admin_reports_request_security.py\n',
        'python scripts/validate_admin_license_codes_security.py --self-test',
        'python scripts/validate_admin_license_codes_security.py\n',
        'python scripts/validate_admin_console_request_security.py --self-test',
        'python scripts/validate_admin_console_request_security.py\n',
        'python scripts/validate_admin_sinjira_v18_request_security.py --self-test',
        'python scripts/validate_admin_sinjira_v18_request_security.py\n',
        'python scripts/validate_admin_analytics_request_security.py --self-test',
        'python scripts/validate_admin_analytics_request_security.py\n',
        'python scripts/validate_admin_users_privacy.py --self-test',
        'python scripts/validate_admin_users_privacy.py\n',
        "- 'scripts/validate_public_edge_auth_workflow_security.py'",
    ]
    for marker in required:
        require(errors, marker in text, f'contrôle CI obligatoire absent: {marker.strip()}')
    require(errors, text.count(ADMIN_REPORTS_TRIGGER) == 2, 'le validateur admin-reports doit déclencher le workflow sur pull_request et push')
    require(errors, text.count(ADMIN_LICENSE_TRIGGER) == 2, 'le validateur admin-license-codes doit déclencher le workflow sur pull_request et push')
    require(errors, text.count(ADMIN_CONSOLE_TRIGGER) == 2, 'le validateur admin-console doit déclencher le workflow sur pull_request et push')
    require(errors, text.count(ADMIN_V18_TRIGGER) == 2, 'le validateur admin-sinjira-v18 doit déclencher le workflow sur pull_request et push')
    require(errors, text.count(ADMIN_ANALYTICS_TRIGGER) == 2, 'le validateur admin-analytics doit déclencher le workflow sur pull_request et push')
    require(errors, text.count(ADMIN_USERS_TRIGGER) == 2, 'le validateur admin-users doit déclencher le workflow sur pull_request et push')
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
        'contrôle public retiré': text.replace('        run: python scripts/validate_public_edge_auth.py\n', '', 1),
        'auto-test admin-reports retiré': text.replace('        run: python scripts/validate_admin_reports_request_security.py --self-test\n', '', 1),
        'contrôle admin-reports retiré': text.replace('        run: python scripts/validate_admin_reports_request_security.py\n', '', 1),
        'déclencheur admin-reports retiré': text.replace(ADMIN_REPORTS_TRIGGER, '', 1),
        'auto-test admin-license-codes retiré': text.replace('        run: python scripts/validate_admin_license_codes_security.py --self-test\n', '', 1),
        'contrôle admin-license-codes retiré': text.replace('        run: python scripts/validate_admin_license_codes_security.py\n', '', 1),
        'déclencheur admin-license-codes retiré': text.replace(ADMIN_LICENSE_TRIGGER, '', 1),
        'auto-test admin-console retiré': text.replace('        run: python scripts/validate_admin_console_request_security.py --self-test\n', '', 1),
        'contrôle admin-console retiré': text.replace('        run: python scripts/validate_admin_console_request_security.py\n', '', 1),
        'déclencheur admin-console retiré': text.replace(ADMIN_CONSOLE_TRIGGER, '', 1),
        'auto-test admin-sinjira-v18 retiré': text.replace('        run: python scripts/validate_admin_sinjira_v18_request_security.py --self-test\n', '', 1),
        'contrôle admin-sinjira-v18 retiré': text.replace('        run: python scripts/validate_admin_sinjira_v18_request_security.py\n', '', 1),
        'déclencheur admin-sinjira-v18 retiré': text.replace(ADMIN_V18_TRIGGER, '', 1),
        'auto-test admin-analytics retiré': text.replace('        run: python scripts/validate_admin_analytics_request_security.py --self-test\n', '', 1),
        'contrôle admin-analytics retiré': text.replace('        run: python scripts/validate_admin_analytics_request_security.py\n', '', 1),
        'déclencheur admin-analytics retiré': text.replace(ADMIN_ANALYTICS_TRIGGER, '', 1),
        'auto-test admin-users retiré': text.replace('        run: python scripts/validate_admin_users_privacy.py --self-test\n', '', 1),
        'contrôle admin-users retiré': text.replace('        run: python scripts/validate_admin_users_privacy.py\n', '', 1),
        'déclencheur admin-users retiré': text.replace(ADMIN_USERS_TRIGGER, '', 1),
    }
    for name, mutated in cases.items():
        if mutated == text:
            raise SystemExit(f'ERREUR auto-test garde Edge public: mutation sans effet: {name}')
        if not validate_text(mutated):
            raise SystemExit(f'ERREUR auto-test garde Edge public: mutation non détectée: {name}')
    print(f'OK auto-tests garde Edge public: {len(cases)} affaiblissements critiques détectés.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not WORKFLOW.is_file():
        raise SystemExit(f'ERREUR garde Edge public: workflow absent: {WORKFLOW.relative_to(ROOT)}')
    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        run_self_tests(text)
        return 0
    errors = validate_text(text)
    if errors:
        for error in errors:
            print(f'ERREUR sécurité garde Edge public: {error}')
        return 1
    print('OK sécurité garde Edge public: actions immuables, runtime figé, credentials non persistés et contrôles Edge sensibles conservés.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
