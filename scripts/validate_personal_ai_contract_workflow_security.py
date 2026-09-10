#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-personal-ai-v25.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_SUPABASE = 'supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
SELF_TEST = 'python3 scripts/validate_personal_ai_contract_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_personal_ai_contract_workflow_security.py'
HISTORICAL = (
    'python3 scripts/validate_personal_ai_v25.py',
    'python3 scripts/validate_personal_ai_production_readiness.py',
    'python3 scripts/validate_personal_ai_postdeployment_workflow.py',
    'python3 scripts/validate_edge_function_inventory.py',
    'python3 scripts/validate_production_schema_manifest.py',
    'supabase db start',
    'supabase test db supabase/tests/personal_ai_v25.test.sql --local',
    'supabase stop --no-backup || true',
)
TRIGGER_PATHS = (
    "      - 'compte/mon-ia.html'",
    "      - 'compte/index.html'",
    "      - 'assets/js/sinjira-personal-ai-v25.js'",
    "      - 'mobile-native/**'",
    "      - 'supabase/functions/personal-ai/**'",
    "      - 'supabase/functions/_shared/auth.ts'",
    "      - 'supabase/config.toml'",
    "      - 'supabase/migrations/**personal_ai**.sql'",
    "      - 'supabase/tests/personal_ai_v25.test.sql'",
    "      - 'scripts/validate_personal_ai_v25.py'",
    "      - 'scripts/validate_personal_ai_production_readiness.py'",
    "      - 'scripts/validate_personal_ai_postdeployment_workflow.py'",
    "      - 'scripts/validate_edge_function_inventory.py'",
    "      - 'scripts/validate_production_schema_manifest.py'",
    "      - 'scripts/validate_personal_ai_contract_workflow_security.py'",
    "      - 'docs/sinjira-v25-personal-ai-production-readiness.md'",
    "      - 'docs/sinjira-v25-personal-ai-production-deployment-2026-09-05.md'",
    "      - '.github/workflows/sinjira-personal-ai-v25.yml'",
    "      - '.github/workflows/sinjira-v25-personal-ai-production-readiness.yml'",
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
    require('pull_request:\n    branches: [main]' in text, 'Les PR Mon IA doivent rester ciblées vers main.')
    require('push:\n    branches: [main]' in text, 'Le push main doit rester couvert tant que #135 n’est pas prouvé.')
    require('workflow_dispatch:' in text, 'Le déclenchement manuel historique doit rester disponible.')
    for path in TRIGGER_PATHS:
        require(text.count(path) == 2, f'Le chemin doit couvrir PR et push: {path.strip()}')

    require('permissions:\n  contents: read' in text, 'Le token GitHub doit rester en lecture seule.')
    require('runs-on: ubuntu-24.04' in text, 'Le runner doit rester figé sur Ubuntu 24.04.')
    require('ubuntu-latest' not in active, 'ubuntu-latest est interdit.')
    require('timeout-minutes: 20' in text, 'Le timeout de 20 minutes doit rester présent.')

    uses = [line.strip().split('uses:', 1)[1].strip().split()[0] for line in active.splitlines() if line.strip().startswith('uses: ')]
    require(uses == [CHECKOUT, SETUP_PYTHON, SETUP_SUPABASE], f'Actions inattendues ou ordre modifié: {uses}')
    for action in uses:
        require(re.search(r'@[0-9a-f]{40}$', action) is not None, f'Action non immuable: {action}')

    require('persist-credentials: false' in text, 'Les credentials Git ne doivent pas être persistés.')
    require("python-version: '3.12.14'" in text, 'Python doit rester figé à 3.12.14.')
    require('          version: 2.111.0' in text, 'Supabase CLI doit rester figé à 2.111.0.')
    require(exact_run_commands(text) == [SELF_TEST, SELF_CHECK, *HISTORICAL], 'Les commandes exécutables ou leur ordre ont changé hors contrat.')
    require(text.count('        if: always()') == 1, 'Le nettoyage Supabase local doit rester protégé par if: always().')

    forbidden = (
        '${{ secrets.', 'contents: write', 'persist-credentials: true', 'environment: production',
        'SUPABASE_ACCESS_TOKEN', 'SUPABASE_DB_PASSWORD', 'SERVICE_ROLE_KEY', 'supabase link',
        'supabase db push', 'supabase functions deploy', 'supabase secrets set', 'supabase migration repair',
        '--linked', '--no-verify-jwt', 'curl ', 'wget ', 'gh api', 'git push', 'continue-on-error: true', 'set -x',
    )
    found = [marker for marker in forbidden if marker in active]
    require(not found, f'Écriture, secret, accès Supabase distant ou contournement interdit: {found}')


def mutation_cases(text: str) -> tuple[tuple[str, str], ...]:
    return (
        ('runner mutable', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)),
        ('checkout mutable', text.replace(CHECKOUT, 'actions/checkout@v6', 1)),
        ('setup-python mutable', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)),
        ('setup-supabase mutable', text.replace(SETUP_SUPABASE, 'supabase/setup-cli@v2', 1)),
        ('Python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)),
        ('Supabase CLI large', text.replace('          version: 2.111.0', '          version: 2', 1)),
        ('credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)),
        ('permissions write', text.replace('contents: read', 'contents: write', 1)),
        ('timeout retiré', text.replace('    timeout-minutes: 20\n', '', 1)),
        ('secret injecté', text.replace('    steps:\n', '    env:\n      LEAK: "${{ secrets.SUPABASE_ACCESS_TOKEN }}"\n    steps:\n', 1)),
        ('production injectée', text.replace('    timeout-minutes: 20\n', '    timeout-minutes: 20\n    environment: production\n', 1)),
        ('push main retiré', text.replace('  push:\n    branches: [main]\n', '  push:\n    branches: [ai-ci]\n', 1)),
        ('workflow dispatch retiré', text.replace('  workflow_dispatch:\n', '', 1)),
        ('chemin Mon IA retiré', text.replace("      - 'compte/mon-ia.html'\n", '', 1)),
        ('chemin fonction retiré', text.replace("      - 'supabase/functions/personal-ai/**'\n", '', 1)),
        ('chemin migration retiré', text.replace("      - 'supabase/migrations/**personal_ai**.sql'\n", '', 1)),
        ('chemin pgTAP retiré', text.replace("      - 'supabase/tests/personal_ai_v25.test.sql'\n", '', 1)),
        ('chemin garde retiré', text.replace("      - 'scripts/validate_personal_ai_contract_workflow_security.py'\n", '', 1)),
        ('chemin workflow retiré', text.replace("      - '.github/workflows/sinjira-personal-ai-v25.yml'\n", '', 1)),
        ('chemin readiness retiré', text.replace("      - '.github/workflows/sinjira-v25-personal-ai-production-readiness.yml'\n", '', 1)),
        ('auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '', 1)),
        ('contrat retiré', text.replace(f'        run: {SELF_CHECK}\n', '', 1)),
        *tuple((f'preuve retirée {index + 1}', text.replace(f'        run: {command}\n', '', 1)) for index, command in enumerate(HISTORICAL)),
        ('cleanup always retiré', text.replace('        if: always()\n', '', 1)),
        ('test distant', text.replace('--local', '--linked', 1)),
        ('db push ajouté', text.replace('      - name: Arrêter Supabase local\n', '      - run: supabase db push --linked\n\n      - name: Arrêter Supabase local\n', 1)),
        ('link ajouté', text.replace('      - name: Arrêter Supabase local\n', '      - run: supabase link --project-ref fake\n\n      - name: Arrêter Supabase local\n', 1)),
        ('deploy fonction ajouté', text.replace('      - name: Arrêter Supabase local\n', '      - run: supabase functions deploy personal-ai\n\n      - name: Arrêter Supabase local\n', 1)),
        ('secret distant ajouté', text.replace('      - name: Arrêter Supabase local\n', '      - run: supabase secrets set X=Y\n\n      - name: Arrêter Supabase local\n', 1)),
        ('push Git ajouté', text.replace('      - name: Arrêter Supabase local\n', '      - run: git push origin HEAD:main\n\n      - name: Arrêter Supabase local\n', 1)),
        ('curl ajouté', text.replace('      - name: Arrêter Supabase local\n', '      - run: curl https://example.invalid\n\n      - name: Arrêter Supabase local\n', 1)),
        ('continue-on-error ajouté', text.replace('    timeout-minutes: 20\n', '    timeout-minutes: 20\n    continue-on-error: true\n', 1)),
        ('set -x ajouté', text.replace('      - name: Arrêter Supabase local\n', '      - run: set -x\n\n      - name: Arrêter Supabase local\n', 1)),
        ('migration repair ajouté', text.replace('      - name: Arrêter Supabase local\n', '      - run: supabase migration repair 20260101000000 --status applied\n\n      - name: Arrêter Supabase local\n', 1)),
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
    print('OK CI Mon IA: runner/Python/Supabase CLI/actions immuables, Git read-only, Supabase strictement local et aucune écriture distante.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
