#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-native-push-producer-boundary-v25.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_NODE = 'actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38'
SELF_TEST = 'python3 scripts/validate_native_push_producer_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_native_push_producer_workflow_security.py'
HISTORICAL = (
    'python3 scripts/validate_native_push_producer_boundary_v25.py',
    'python3 scripts/validate_security_push_background_v25.py',
    'node scripts/test_security_push_policy_v25.mjs',
    'node scripts/test_security_push_receipts_v25.mjs',
    'node scripts/test_security_push_network_v25.mjs',
)
TRIGGER_PATHS = (
    "      - 'supabase/functions/**'",
    "      - 'supabase/migrations/**'",
    "      - 'supabase/config.toml'",
    "      - 'assets/js/sinjira-security-push-bridge-v24-4-98.js'",
    "      - 'mobile-native/App.tsx'",
    "      - 'scripts/test_security_push_policy_v25.mjs'",
    "      - 'scripts/test_security_push_receipts_v25.mjs'",
    "      - 'scripts/test_security_push_network_v25.mjs'",
    "      - 'scripts/validate_native_push_producer_boundary_v25.py'",
    "      - 'scripts/validate_security_push_background_v25.py'",
    "      - 'scripts/validate_native_push_producer_workflow_security.py'",
    "      - '.github/workflows/sinjira-native-push-producer-boundary-v25.yml'",
)


def fail(message: str) -> None:
    raise ValueError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def active_text(text: str) -> str:
    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))


def run_line(command: str) -> str:
    return f'        run: {command}\n'


def validate_text(text: str) -> None:
    active = active_text(text)
    require('pull_request:\n    branches: [ main ]' in text, 'Les PR doivent rester ciblées vers main.')
    require('push:\n    branches: [ main ]' in text, 'Le push main doit rester couvert tant que #135 n’est pas prouvé.')
    require('workflow_dispatch:' in text, 'Le déclenchement manuel historique doit rester disponible.')
    for path in TRIGGER_PATHS:
        require(text.count(path) == 2, f'Le chemin doit couvrir PR et push: {path.strip()}')

    require('permissions:\n  contents: read' in text, 'Le token GitHub doit rester en lecture seule.')
    require('runs-on: ubuntu-24.04' in text and 'ubuntu-latest' not in active, 'Le runner doit rester figé sur Ubuntu 24.04.')
    require('timeout-minutes: 5' in text, 'Le timeout de 5 minutes doit rester présent.')

    uses = [line.strip().split('uses:', 1)[1].strip().split()[0] for line in active.splitlines() if line.strip().startswith('uses: ')]
    require(uses == [CHECKOUT, SETUP_PYTHON, SETUP_NODE], f'Actions inattendues ou ordre modifié: {uses}')
    for action in uses:
        require(re.search(r'@[0-9a-f]{40}$', action) is not None, f'Action non immuable: {action}')
    require('persist-credentials: false' in text, 'Les credentials Git ne doivent pas être persistés.')
    require("python-version: '3.12.14'" in text, 'Python doit rester figé à 3.12.14.')
    require("node-version: '22.23.2'" in text, 'Node doit rester figé à 22.23.2.')
    require('cache:' not in active and 'cache-dependency-path:' not in active, 'Aucun cache package-manager n’est nécessaire pour ces tests sans installation.')

    commands = (SELF_TEST, SELF_CHECK, *HISTORICAL)
    lines = [run_line(command) for command in commands]
    for command, line in zip(commands, lines, strict=True):
        require(line in text, f'Commande de preuve exacte absente: {command}')
    positions = [text.find(line) for line in lines]
    require(min(positions) >= 0 and positions == sorted(positions), 'Ordre des preuves push natif modifié.')

    forbidden = (
        '${{ secrets.', 'contents: write', 'persist-credentials: true', 'environment: production',
        'SUPABASE_ACCESS_TOKEN', 'SUPABASE_DB_PASSWORD', 'SERVICE_ROLE_KEY',
        'supabase db push', 'supabase functions deploy', 'supabase secrets set',
        'supabase migration repair', 'supabase link', '--linked', '--no-verify-jwt',
        'curl ', 'wget ', 'gh api', 'git push', 'npm install', 'npm ci',
        'continue-on-error: true', 'set -x',
    )
    found = [marker for marker in forbidden if marker in active]
    require(not found, f'Écriture, secret, accès distant ou contournement interdit: {found}')


def mutation_cases(text: str) -> tuple[tuple[str, str], ...]:
    node_version = "          node-version: '22.23.2'\n"
    return (
        ('runner mobile', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)),
        ('checkout mutable', text.replace(CHECKOUT, 'actions/checkout@v6', 1)),
        ('setup-python mutable', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)),
        ('setup-node mutable', text.replace(SETUP_NODE, 'actions/setup-node@v6', 1)),
        ('Python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)),
        ('Node large', text.replace("node-version: '22.23.2'", "node-version: '22'", 1)),
        ('credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)),
        ('permissions write', text.replace('contents: read', 'contents: write', 1)),
        ('cache ajouté', text.replace(node_version, node_version + '          cache: npm\n', 1)),
        ('timeout retiré', text.replace('    timeout-minutes: 5\n', '', 1)),
        ('secret injecté', text.replace('    steps:\n', '    steps:\n      - run: echo "${{ secrets.SUPABASE_ACCESS_TOKEN }}"\n', 1)),
        ('production injectée', text.replace('    timeout-minutes: 5\n', '    timeout-minutes: 5\n    environment: production\n', 1)),
        ('curl ajouté', text.replace('      - name: Tester le réseau Expo borné\n', '      - run: curl https://exp.host/\n\n      - name: Tester le réseau Expo borné\n', 1)),
        ('push Git ajouté', text.replace('      - name: Tester le réseau Expo borné\n', '      - run: git push origin HEAD:main\n\n      - name: Tester le réseau Expo borné\n', 1)),
        ('installation npm ajoutée', text.replace('      - name: Tester le payload push réel\n', '      - run: npm install\n\n      - name: Tester le payload push réel\n', 1)),
        ('continue-on-error', text.replace('    timeout-minutes: 5\n', '    timeout-minutes: 5\n    continue-on-error: true\n', 1)),
        ('push main retiré', text.replace('  push:\n    branches: [ main ]\n', '  push:\n    branches: [ mobile ]\n', 1)),
        ('chemin functions retiré', text.replace("      - 'supabase/functions/**'\n", '', 1)),
        ('chemin contrat retiré', text.replace("      - 'scripts/validate_native_push_producer_workflow_security.py'\n", '', 1)),
        ('auto-test retiré', text.replace(run_line(SELF_TEST), '', 1)),
        ('contrat retiré', text.replace(run_line(SELF_CHECK), '', 1)),
        ('frontière retirée', text.replace(run_line(HISTORICAL[0]), '', 1)),
        ('background retiré', text.replace(run_line(HISTORICAL[1]), '', 1)),
        ('payload retiré', text.replace(run_line(HISTORICAL[2]), '', 1)),
        ('reçus retirés', text.replace(run_line(HISTORICAL[3]), '', 1)),
        ('réseau retiré', text.replace(run_line(HISTORICAL[4]), '', 1)),
    )


def self_test(text: str) -> None:
    validate_text(text)
    cases = mutation_cases(text)
    for name, mutated in cases:
        require(mutated != text, f'Mutation inopérante: {name}')
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
        'OK CI producteur push natif: runner/Python/Node/actions immuables, Git read-only, '
        'aucune installation, aucun secret et aucune opération Supabase distante.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
