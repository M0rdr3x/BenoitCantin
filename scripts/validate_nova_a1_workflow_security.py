#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'nova-a1.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
PYTHON_VERSION = '3.12.14'
SELF_TEST = 'python3 scripts/validate_nova_a1_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_nova_a1_workflow_security.py'
SEO_SELF_TEST = 'python3 scripts/validate_nova_seo_workflow_security.py --self-test'
SEO_CHECK = 'python3 scripts/validate_nova_seo_workflow_security.py'
PROJECT_CHECK = 'python3 scripts/check_nova_a1.py'


def fail(message: str) -> None:
    raise ValueError(message)


def active_text(text: str) -> str:
    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def validate_text(text: str) -> None:
    active = active_text(text)

    require('permissions:\n  contents: read' in text, 'permissions.contents doit rester en lecture seule.')
    require('runs-on: ubuntu-24.04' in text, 'Le runner doit rester figé sur Ubuntu 24.04.')
    require('ubuntu-latest' not in active, 'ubuntu-latest est interdit.')
    require('timeout-minutes: 10' in text, 'Le timeout de 10 minutes est obligatoire.')

    for path in (
        "      - 'projets/projet-nova/**'",
        "      - 'scripts/check_nova_a1.py'",
        "      - 'scripts/normalize_nova_seo.py'",
        "      - 'scripts/validate_nova_a1_workflow_security.py'",
        "      - 'scripts/validate_nova_seo_workflow_security.py'",
        "      - '.github/workflows/nova-a1.yml'",
        "      - '.github/workflows/nova-seo-normalize.yml'",
    ):
        require(text.count(path) >= 2, f'Le chemin doit couvrir PR et push: {path.strip()}')

    require('pull_request:\n    branches: [ main ]' in text, 'Le workflow doit couvrir les PR vers main.')
    require('push:\n    branches: [ main ]' in text, 'Le workflow doit couvrir les pushes vers main.')
    require('workflow_dispatch:' in text, 'Le déclenchement manuel doit rester disponible.')

    require(f'uses: {CHECKOUT}' in text, 'actions/checkout doit être épinglé au SHA vérifié.')
    require('persist-credentials: false' in text, 'Les credentials Git ne doivent pas être persistés.')
    require(f'uses: {SETUP_PYTHON}' in text, 'actions/setup-python doit être épinglé au SHA vérifié.')
    require(f"python-version: '{PYTHON_VERSION}'" in text, f'Python doit rester figé à {PYTHON_VERSION}.')

    uses = [line.strip() for line in active.splitlines() if line.strip().startswith('uses: ')]
    require(len(uses) == 2, f'Exactement deux actions réutilisables sont attendues; reçu={uses}')
    for line in uses:
        target = line.split('uses:', 1)[1].strip().split()[0]
        require(re.search(r'@[0-9a-f]{40}$', target) is not None, f'Action non immuable: {target}')

    forbidden = (
        '${{ secrets.',
        'permissions:\n  contents: write',
        'persist-credentials: true',
        'environment: production',
        'SUPABASE_ACCESS_TOKEN',
        'SUPABASE_DB_PASSWORD',
        'SERVICE_ROLE_KEY',
        'supabase db push',
        'supabase functions deploy',
        'supabase secrets set',
        'supabase migration repair',
        'supabase link',
        '--linked',
        '--no-verify-jwt',
        'curl ',
        'wget ',
        'gh api',
        'git push',
        'continue-on-error: true',
        'set -x',
    )
    found = [marker for marker in forbidden if marker in active]
    require(not found, f'Surface distante, écriture ou contournement interdit: {found}')

    commands = (SELF_TEST, SELF_CHECK, SEO_SELF_TEST, SEO_CHECK, PROJECT_CHECK)
    for command in commands:
        require(command in text, f'Commande attendue absente: {command}')

    positions = [
        text.find(SELF_TEST),
        text.find(SELF_CHECK + '\n'),
        text.find(SEO_SELF_TEST),
        text.find(SEO_CHECK + '\n'),
        text.find(PROJECT_CHECK),
    ]
    require(min(positions) >= 0, 'Ordre des validations impossible à établir.')
    require(
        positions == sorted(positions),
        'Ordre attendu: auto-test Nova, contrat Nova, auto-test SEO, contrat SEO, validation Projet Nova.',
    )


def mutation_cases(text: str) -> tuple[tuple[str, str], ...]:
    return (
        ('runner mobile', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)),
        ('checkout mutable', text.replace(CHECKOUT, 'actions/checkout@v6', 1)),
        ('setup-python mutable', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)),
        ('Python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)),
        ('credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)),
        ('permissions écriture', text.replace('contents: read', 'contents: write', 1)),
        ('timeout retiré', text.replace('    timeout-minutes: 10\n', '', 1)),
        ('secret injecté', text.replace('    steps:\n', '    steps:\n      - run: echo "${{ secrets.SUPABASE_ACCESS_TOKEN }}"\n', 1)),
        ('environnement production', text.replace('    timeout-minutes: 10\n', '    timeout-minutes: 10\n    environment: production\n', 1)),
        ('accès HTTP', text.replace(PROJECT_CHECK, PROJECT_CHECK + '\n      - run: curl https://example.com', 1)),
        ('push Git', text.replace(PROJECT_CHECK, PROJECT_CHECK + '\n      - run: git push origin HEAD:main', 1)),
        ('continue-on-error', text.replace(PROJECT_CHECK, PROJECT_CHECK + '\n        continue-on-error: true', 1)),
        ('set -x', text.replace(PROJECT_CHECK, PROJECT_CHECK + '\n      - run: set -x', 1)),
        ('chemin validateur Nova supprimé', text.replace("      - 'scripts/validate_nova_a1_workflow_security.py'\n", '', 1)),
        ('chemin projet supprimé', text.replace("      - 'projets/projet-nova/**'\n", '', 1)),
        ('auto-test Nova retiré', text.replace(f'        run: {SELF_TEST}\n', '', 1)),
        ('contrat Nova retiré', text.replace(f'        run: {SELF_CHECK}\n', '', 1)),
        ('validation projet retirée', text.replace(f'        run: {PROJECT_CHECK}\n', '', 1)),
        ('chemin normaliseur SEO supprimé', text.replace("      - 'scripts/normalize_nova_seo.py'\n", '', 1)),
        ('chemin validateur SEO supprimé', text.replace("      - 'scripts/validate_nova_seo_workflow_security.py'\n", '', 1)),
        ('chemin workflow SEO supprimé', text.replace("      - '.github/workflows/nova-seo-normalize.yml'\n", '', 1)),
        ('auto-test SEO retiré', text.replace(f'        run: {SEO_SELF_TEST}\n', '', 1)),
        ('contrat SEO retiré', text.replace(f'        run: {SEO_CHECK}\n', '', 1)),
    )


def self_test(text: str) -> None:
    validate_text(text)
    cases = mutation_cases(text)
    for name, mutated in cases:
        require(mutated != text, f'La mutation ne modifie pas le workflow: {name}')
        try:
            validate_text(mutated)
        except ValueError:
            continue
        fail(f'Mutation critique non détectée: {name}')
    print(f'OK: {len(cases)}/{len(cases)} mutations critiques détectées')


def main() -> int:
    require(WORKFLOW.is_file(), f'Workflow absent: {WORKFLOW.relative_to(ROOT)}')
    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if '--self-test' in sys.argv[1:]:
        self_test(text)
        return 0
    validate_text(text)
    print(
        'OK Projet Nova A1: runner/Python/actions immuables, credentials Git non persistés, '
        'permissions lecture seule, contrat SEO chaîné et aucune opération distante ou production.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
