#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-child-signup-browser-v25.yml'
BROWSER_TEST = ROOT / 'tests/e2e/test_child_signup.py'
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
PYTHON_VERSION = '3.12.14'
PLAYWRIGHT_VERSION = '1.61.0'
PLAYWRIGHT_IMAGE = (
    'mcr.microsoft.com/playwright/python:v1.61.0-noble'
    '@sha256:a9731514f24121d1dcd25d58d0a38146646d290a5998fd80d3e533e7b5e21c69'
)
SELF_TEST_COMMAND = 'python3 scripts/validate_child_signup_browser_workflow_security.py --self-test'
VALIDATE_COMMAND = 'python3 scripts/validate_child_signup_browser_workflow_security.py'
BROWSER_COMMAND = 'python tests/e2e/test_child_signup.py'


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


def validate_text(text: str, browser_test: str) -> list[str]:
    errors: list[str] = []
    require(errors, 'permissions:\n  contents: read' in text, 'permissions.contents doit rester read')
    require(errors, 'contents: write' not in text, 'contents:write interdit')
    require(errors, 'secrets.' not in text, 'aucun secret GitHub ne doit être référencé')
    require(errors, 'pull_request_target' not in text, 'pull_request_target interdit')
    require(errors, 'continue-on-error:' not in text, 'continue-on-error interdit')
    require(errors, 'set -x' not in text, 'set -x interdit')
    require(errors, 'https://www.benoitcantin.com' not in text, 'la preuve enfant doit rester strictement locale')

    require(errors, text.count(f'uses: actions/checkout@{CHECKOUT_SHA}') == 2, 'les deux checkouts doivent être épinglés')
    require(errors, text.count('persist-credentials: false') == 2, 'les deux checkouts doivent désactiver les credentials persistés')
    require(errors, 'persist-credentials: true' not in text, 'persist-credentials=true interdit')
    require(errors, text.count(f'uses: actions/setup-python@{SETUP_PYTHON_SHA}') == 1, 'setup-python navigateur doit être épinglé')
    for target in action_targets(text):
        require(errors, re.search(r'@[0-9a-f]{40}$', target) is not None, f'action non immuable: {target}')

    require(errors, text.count('runs-on: ubuntu-24.04') == 2, 'les deux jobs doivent rester sur Ubuntu 24.04')
    require(errors, 'runs-on: ubuntu-latest' not in text, 'ubuntu-latest interdit')
    require(errors, f'image: {PLAYWRIGHT_IMAGE}' in text, 'image Playwright non épinglée au digest approuvé')
    require(errors, f"python-version: '{PYTHON_VERSION}'" in text, f'Python doit rester {PYTHON_VERSION}')
    require(errors, f'playwright=={PLAYWRIGHT_VERSION}' in text, f'Playwright doit rester {PLAYWRIGHT_VERSION}')

    require(errors, '  workflow-contract:\n' in text, 'job workflow-contract absent')
    require(errors, '  browser-proof:\n' in text, 'job browser-proof absent')
    require(errors, text.count('needs: workflow-contract') == 1, 'browser-proof doit dépendre exactement une fois du contrat')
    require(errors, count_exact_stripped(text, f'run: {SELF_TEST_COMMAND}') == 1, 'auto-test sécurité absent ou dupliqué')
    require(errors, count_exact_stripped(text, f'run: {VALIDATE_COMMAND}') == 1, 'validation sécurité absente ou dupliquée')
    require(errors, count_exact_stripped(text, f'run: {BROWSER_COMMAND}') == 1, 'preuve navigateur enfant absente ou dupliquée')
    require(errors, 'BASE_URL: http://127.0.0.1:4173/' in text, 'BASE_URL de la preuve doit rester locale')
    require(errors, "--bind 127.0.0.1" in text, 'serveur de test doit rester lié à loopback')
    require(errors, text.count('if: always()') == 1, 'seul le nettoyage serveur peut utiliser if: always()')

    forbidden = (
        'supabase db push', 'supabase link', 'supabase functions deploy', 'supabase secrets set',
        'supabase migration up', 'wrangler deploy', 'vercel deploy', 'netlify deploy',
    )
    low = text.lower()
    for command in forbidden:
        require(errors, command not in low, f'commande de production interdite: {command}')

    test_low = browser_test.lower()
    require(errors, 'page.route(' in browser_test and '@supabase/supabase-js@2/+esm' in browser_test,
            'le test navigateur doit intercepter le client Supabase public')
    require(errors,
            "getsession: async () => {" in test_low
            and "await new promise(resolve => settimeout(resolve, 500));" in test_low
            and "session:active ?" in test_low,
            'le test ne simule plus une session parent active avec frontière asynchrone')
    require(errors, 'signout: async () => { active = false;' in test_low,
            'le test ne simule plus la séparation locale de session')
    require(errors, "d.setfullyear(d.getfullyear() - 11)" in test_low,
            'le test ne couvre plus exactement 11 ans')
    require(errors, 'code.required === true' in browser_test,
            'le test ne vérifie plus le code parental obligatoire')
    require(errors, 'contributor && contributor.hidden' in browser_test,
            'le test ne vérifie plus la minimisation du Programme Contributeur')
    require(errors, 'https://gpvivleexywljowcqkru.supabase.co' not in browser_test,
            'le test ne doit jamais coder l’URL Supabase production')
    return errors


def run_self_tests(text: str, browser_test: str) -> None:
    baseline = validate_text(text, browser_test)
    if baseline:
        raise SystemExit('ERREUR auto-test navigateur enfant: baseline invalide: ' + ' | '.join(baseline))
    cases = {
        'checkout mobile': (text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1), browser_test),
        'credentials persistés': (text.replace('persist-credentials: false', 'persist-credentials: true', 1), browser_test),
        'secret ajouté': (text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-24.04\n    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}', 1), browser_test),
        'pull_request_target': (text.replace('  pull_request:\n', '  pull_request_target:\n', 1), browser_test),
        'image sans digest': (text.replace(PLAYWRIGHT_IMAGE, 'mcr.microsoft.com/playwright/python:v1.61.0-noble', 1), browser_test),
        'Python flottant': (text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1), browser_test),
        'Playwright flottant': (text.replace(f'playwright=={PLAYWRIGHT_VERSION}', 'playwright', 1), browser_test),
        'dépendance contrat retirée': (text.replace('    needs: workflow-contract\n', '', 1), browser_test),
        'URL production': (text.replace('BASE_URL: http://127.0.0.1:4173/', 'BASE_URL: https://www.benoitcantin.com/'), browser_test),
        'déploiement ajouté': (text.replace('run: python tests/e2e/test_child_signup.py', 'run: supabase db push', 1), browser_test),
        'interception Supabase retirée': (text, browser_test.replace('page.route(', 'page.not_route(', 1)),
        'session active retirée': (text, browser_test.replace('session:active ?', 'session:false ?', 1)),
    }
    for name, (mutated_workflow, mutated_test) in cases.items():
        if mutated_workflow == text and mutated_test == browser_test:
            raise SystemExit(f'ERREUR auto-test navigateur enfant: mutation non appliquée: {name}')
        if not validate_text(mutated_workflow, mutated_test):
            raise SystemExit(f'ERREUR auto-test navigateur enfant: mutation non détectée: {name}')
    print(f'OK auto-tests navigateur enfant: baseline valide + {len(cases)} affaiblissements détectés.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not WORKFLOW.is_file():
        raise SystemExit(f'ERREUR navigateur enfant: workflow absent: {WORKFLOW.relative_to(ROOT)}')
    if not BROWSER_TEST.is_file():
        raise SystemExit(f'ERREUR navigateur enfant: test absent: {BROWSER_TEST.relative_to(ROOT)}')
    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    browser_test = BROWSER_TEST.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        run_self_tests(text, browser_test)
        return 0
    errors = validate_text(text, browser_test)
    if errors:
        for error in errors:
            print(f'ERREUR sécurité navigateur enfant: {error}')
        return 1
    print('OK sécurité navigateur enfant: lecture seule, actions/runtimes immuables, test local isolé, aucun secret ni capacité de production.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
