#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'targeted-production-workflow-security.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SELF_TEST = 'python3 scripts/validate_targeted_production_ci_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_targeted_production_ci_workflow_security.py'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}\n'

TARGET_PATHS = (
    "'.github/workflows/sinjira-v25-production-deploy.yml'",
    "'.github/workflows/sinjira-v25-employment-production.yml'",
    "'.github/workflows/sinjira-v25-personal-ai-production-readiness.yml'",
    "'.github/workflows/sinjira-v25-auth-password-hardening.yml'",
    "'.github/workflows/targeted-production-workflow-security.yml'",
    "'scripts/validate_targeted_production_workflow_security.py'",
    "'scripts/test_targeted_production_workflow_security.py'",
    "'scripts/validate_targeted_production_ci_workflow_security.py'",
)

HISTORICAL = (
    'python3 scripts/validate_targeted_production_workflow_security.py',
    'python3 scripts/test_targeted_production_workflow_security.py',
)

FORBIDDEN = (
    '${{ secrets.',
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
    'continue-on-error: true',
    'set -x',
)


def fail(message: str) -> None:
    raise ValueError(message)


def section(text: str, start: str, end: str) -> str:
    begin = text.find(start)
    if begin < 0:
        fail(f'section absente: {start.strip()}')
    finish = text.find(end, begin + len(start))
    if finish < 0:
        fail(f'fin de section absente: {end.strip()}')
    return text[begin:finish]


def validate_text(text: str) -> None:
    if 'permissions:\n  contents: read' not in text:
        fail('permissions read absentes')
    if 'runs-on: ubuntu-24.04' not in text or 'ubuntu-latest' in text:
        fail('runner non figé')
    if 'timeout-minutes: 5' not in text:
        fail('timeout 5 absent')

    for action in (CHECKOUT, SETUP_PYTHON):
        if action not in text:
            fail(f'action épinglée absente: {action}')
    if text.count('uses:') != 2:
        fail('nombre d actions externe inattendu')
    for mutable in ('actions/checkout@v', 'actions/setup-python@v'):
        if mutable in text:
            fail(f'action mobile interdite: {mutable}')
    if 'persist-credentials: false' not in text:
        fail('credentials Git persistés')
    if "python-version: '3.12.14'" not in text:
        fail('Python non figé')

    push = section(text, '  push:', '  pull_request:')
    pr = section(text, '  pull_request:', '\npermissions:')
    if 'branches: [ main ]' not in push or 'branches: [ main ]' not in pr:
        fail('couverture main PR/push absente')
    for marker in TARGET_PATHS:
        if marker not in push or marker not in pr:
            fail(f'cible critique non couverte PR+push: {marker}')

    if SELF_TEST not in text:
        fail('auto-test du contrat CI absent')
    if SELF_CHECK_LINE not in text:
        fail('contrat CI réel absent')
    for marker in HISTORICAL:
        if marker not in text:
            fail(f'preuve historique absente: {marker}')

    self_index = text.index(SELF_CHECK_LINE)
    historical_indexes = [text.index(marker) for marker in HISTORICAL]
    if not self_index < min(historical_indexes) < max(historical_indexes):
        fail('ordre contrat CI -> validateur historique -> tests historiques non respecté')

    for marker in FORBIDDEN:
        if marker in text:
            fail(f'capacité distante/secret interdit dans le méta-garde: {marker}')


def remove_push(text: str) -> str:
    begin = text.index('  push:')
    end = text.index('  pull_request:', begin)
    return text[:begin] + text[end:]


def mutations(text: str):
    yield 'checkout mobile', text.replace(CHECKOUT, 'actions/checkout@v6', 1)
    yield 'setup-python mobile', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)
    yield 'runner latest', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)
    yield 'credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)
    yield 'python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)
    yield 'permissions écriture', text.replace('contents: read', 'contents: write', 1)
    yield 'push main retiré', remove_push(text)
    yield 'cible coffre retirée', text.replace("      - '.github/workflows/sinjira-v25-production-deploy.yml'\n", '', 2)
    yield 'cible emploi retirée', text.replace("      - '.github/workflows/sinjira-v25-employment-production.yml'\n", '', 2)
    yield 'cible IA retirée', text.replace("      - '.github/workflows/sinjira-v25-personal-ai-production-readiness.yml'\n", '', 2)
    yield 'cible auth retirée', text.replace("      - '.github/workflows/sinjira-v25-auth-password-hardening.yml'\n", '', 2)
    yield 'validateur historique path retiré', text.replace("      - 'scripts/validate_targeted_production_workflow_security.py'\n", '', 2)
    yield 'tests historiques path retiré', text.replace("      - 'scripts/test_targeted_production_workflow_security.py'\n", '', 2)
    yield 'contrat path retiré', text.replace("      - 'scripts/validate_targeted_production_ci_workflow_security.py'\n", '', 2)
    yield 'auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '        run: echo auto-test-retire\n', 1)
    yield 'contrat réel retiré', text.replace(SELF_CHECK_LINE, '        run: echo contrat-retire\n', 1)
    yield 'validateur historique retiré', text.replace(HISTORICAL[0], 'echo validateur-retire', 1)
    yield 'tests historiques retirés', text.replace(HISTORICAL[1], 'echo tests-retire', 1)
    yield 'secret ajouté', text + '\nenv:\n  SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n'
    yield 'production env ajouté', text.replace('jobs:\n', 'jobs:\n  # environment: production\n', 1)
    yield 'db push ajouté', text + '\n# supabase db push --linked\n'
    yield 'curl ajouté', text + '\n# curl https://api.supabase.com/v1\n'
    yield 'continue on error', text.replace('timeout-minutes: 5', 'timeout-minutes: 5\n    continue-on-error: true', 1)
    yield 'shell trace', text.replace('set -euo pipefail', 'set -x', 1)


def self_test(text: str) -> None:
    validate_text(text)
    total = 0
    detected = 0
    for name, mutated in mutations(text):
        total += 1
        try:
            validate_text(mutated)
        except ValueError:
            detected += 1
        else:
            raise SystemExit(f'ECHEC auto-test méta-garde production: mutation non détectée: {name}')
    print(f'OK: {detected}/{total} mutations critiques détectées')


def main() -> int:
    if not WORKFLOW.is_file():
        print('ECHEC CI méta-garde production: workflow absent', file=sys.stderr)
        return 1
    text = WORKFLOW.read_text('utf-8')
    try:
        if '--self-test' in sys.argv[1:]:
            self_test(text)
        else:
            validate_text(text)
            print('OK: méta-garde workflows production ciblés épinglé, local et sans capacité distante')
    except ValueError as exc:
        print(f'ECHEC CI méta-garde production: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
