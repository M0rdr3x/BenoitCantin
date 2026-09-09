#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-mobile-native-security-hub-v25.yml'
LOCKFILE = ROOT / 'mobile-native' / 'package-lock.json'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_NODE = 'actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38'
SELF_TEST = 'python3 scripts/validate_mobile_native_security_hub_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_mobile_native_security_hub_workflow_security.py'
HISTORICAL = (
    'python3 scripts/validate_mobile_native_security_hub_v25.py',
    'python3 scripts/validate_device_challenge_client_boundary.py',
    'python3 scripts/validate_mobile_navigation_boundary_v25.py',
    'python3 scripts/validate_mobile_safe_share_v25.py',
    'python3 scripts/validate_no_committed_secrets.py',
    'npm install --ignore-scripts --no-audit --no-fund',
    'npm run validate:vault',
    'npm run typecheck',
)
TRIGGER_PATHS = (
    "      - 'mobile-native/App.tsx'",
    "      - 'mobile-native/NativeSecurityHub.tsx'",
    "      - 'mobile-native/safePublicShare.ts'",
    "      - 'mobile-native/package.json'",
    "      - 'mobile-native/package-lock.json'",
    "      - 'mobile-native/scripts/validate-vault-mobile.mjs'",
    "      - 'compte/securite.html'",
    "      - 'scripts/validate_mobile_native_security_hub_v25.py'",
    "      - 'scripts/validate_mobile_navigation_boundary_v25.py'",
    "      - 'scripts/validate_mobile_safe_share_v25.py'",
    "      - 'scripts/validate_device_challenge_client_boundary.py'",
    "      - 'scripts/validate_no_committed_secrets.py'",
    "      - 'scripts/validate_mobile_native_security_hub_workflow_security.py'",
    "      - '.github/workflows/sinjira-mobile-native-security-hub-v25.yml'",
)


def fail(message: str) -> None:
    raise ValueError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def active_text(text: str) -> str:
    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))


def exact_run_commands(text: str) -> list[str]:
    commands: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('run: '):
            commands.append(stripped.removeprefix('run: '))
    return commands


def validate_text(text: str) -> None:
    active = active_text(text)

    require('pull_request:\n    branches: [ main ]' in text, 'Les PR doivent rester ciblées vers main.')
    require('push:\n    branches: [ main ]' in text, 'Le push main doit rester couvert tant que #135 n’est pas prouvé.')
    require('workflow_dispatch:' in text, 'Le déclenchement manuel historique doit rester disponible.')
    for path in TRIGGER_PATHS:
        require(text.count(path) == 2, f'Le chemin doit couvrir PR et push: {path.strip()}')

    require('permissions:\n  contents: read' in text, 'Le token GitHub doit rester en lecture seule.')
    require('runs-on: ubuntu-24.04' in text, 'Le runner doit rester figé sur Ubuntu 24.04.')
    require('ubuntu-latest' not in active, 'ubuntu-latest est interdit.')
    require('timeout-minutes: 10' in text, 'Le timeout de 10 minutes doit rester présent.')

    uses = [
        line.strip().split('uses:', 1)[1].strip().split()[0]
        for line in active.splitlines()
        if line.strip().startswith('uses: ')
    ]
    require(uses == [CHECKOUT, SETUP_PYTHON, SETUP_NODE], f'Actions inattendues ou ordre modifié: {uses}')
    for action in uses:
        require(re.search(r'@[0-9a-f]{40}$', action) is not None, f'Action non immuable: {action}')

    require('persist-credentials: false' in text, 'Les credentials Git ne doivent pas être persistés.')
    require("python-version: '3.12.14'" in text, 'Python doit rester figé à 3.12.14.')
    require("node-version: '22.23.2'" in text, 'Node doit rester figé à 22.23.2.')
    require('cache:' not in active, 'Aucun cache package-manager ne doit être activé sans lockfile revu.')
    require('cache-dependency-path:' not in active, 'Aucun faux chemin de cache ne doit être configuré.')

    expected_runs = [SELF_TEST, SELF_CHECK, *HISTORICAL]
    require(exact_run_commands(text) == expected_runs, 'Les commandes exécutables ou leur ordre ont changé hors contrat.')

    require('working-directory: mobile-native' in text, 'Les commandes npm doivent rester bornées à mobile-native.')
    require(text.count('working-directory: mobile-native') == 3, 'Seules installation, validation vault et typecheck doivent utiliser mobile-native.')

    forbidden = (
        '${{ secrets.',
        'contents: write',
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
    require(not found, f'Écriture, secret, accès distant ou contournement interdit: {found}')


def validate_repo_state() -> None:
    require(
        not LOCKFILE.exists(),
        'mobile-native/package-lock.json est apparu: migrer explicitement ce workflow vers npm ci et un cache fondé sur le lockfile dans une PR revue.',
    )


def mutation_cases(text: str) -> tuple[tuple[str, str], ...]:
    node_line = "          node-version: '22.23.2'\n"
    return (
        ('runner mobile', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)),
        ('checkout mutable', text.replace(CHECKOUT, 'actions/checkout@v4', 1)),
        ('setup-python mutable', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)),
        ('setup-node mutable', text.replace(SETUP_NODE, 'actions/setup-node@v4', 1)),
        ('Python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)),
        ('Node large', text.replace("node-version: '22.23.2'", "node-version: '22'", 1)),
        ('credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)),
        ('permissions write', text.replace('contents: read', 'contents: write', 1)),
        ('cache npm ajouté', text.replace(node_line, node_line + '          cache: npm\n', 1)),
        ('timeout retiré', text.replace('    timeout-minutes: 10\n', '', 1)),
        ('secret injecté', text.replace('    steps:\n', '    env:\n      LEAK: "${{ secrets.SUPABASE_ACCESS_TOKEN }}"\n    steps:\n', 1)),
        ('production injectée', text.replace('    timeout-minutes: 10\n', '    timeout-minutes: 10\n    environment: production\n', 1)),
        ('push main retiré', text.replace('  push:\n    branches: [ main ]\n', '  push:\n    branches: [ mobile ]\n', 1)),
        ('workflow dispatch retiré', text.replace('  workflow_dispatch:\n', '', 1)),
        ('chemin App retiré', text.replace("      - 'mobile-native/App.tsx'\n", '', 1)),
        ('chemin garde retiré', text.replace("      - 'scripts/validate_mobile_native_security_hub_workflow_security.py'\n", '', 1)),
        ('auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '', 1)),
        ('contrat retiré', text.replace(f'        run: {SELF_CHECK}\n', '', 1)),
        ('hub retiré', text.replace(f'        run: {HISTORICAL[0]}\n', '', 1)),
        ('challenge retiré', text.replace(f'        run: {HISTORICAL[1]}\n', '', 1)),
        ('navigation retirée', text.replace(f'        run: {HISTORICAL[2]}\n', '', 1)),
        ('partage retiré', text.replace(f'        run: {HISTORICAL[3]}\n', '', 1)),
        ('garde secrets retiré', text.replace(f'        run: {HISTORICAL[4]}\n', '', 1)),
        ('scripts npm réactivés', text.replace(HISTORICAL[5], 'npm install --no-audit --no-fund', 1)),
        ('vault retiré', text.replace(f'        run: {HISTORICAL[6]}\n', '', 1)),
        ('typecheck retiré', text.replace(f'        run: {HISTORICAL[7]}\n', '', 1)),
        ('continue-on-error', text.replace('    timeout-minutes: 10\n', '    timeout-minutes: 10\n    continue-on-error: true\n', 1)),
        ('push Git ajouté', text.replace('      - name: Vérifier TypeScript\n', '      - run: git push origin HEAD:main\n\n      - name: Vérifier TypeScript\n', 1)),
        ('Supabase distant ajouté', text.replace('      - name: Vérifier TypeScript\n', '      - run: supabase db push --linked\n\n      - name: Vérifier TypeScript\n', 1)),
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
    validate_repo_state()
    print(
        'OK CI Hub Sécurité natif: runner/Python/Node/actions immuables, Git read-only, '
        'scripts npm désactivés, aucun faux cache et aucune opération Supabase distante.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
