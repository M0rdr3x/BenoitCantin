#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-live-social-ui-v25.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_NODE = 'actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38'
SELF_TEST = 'python scripts/validate_live_social_ui_workflow_security.py --self-test'
SELF_CHECK = 'python scripts/validate_live_social_ui_workflow_security.py'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}\n'

CRITICAL_PATHS = (
    "'assets/js/sinjira-live-ui-v25.js'",
    "'assets/js/sinjira-live-ui-shell-v25.js'",
    "'assets/js/sinjira-live-share-codes-ui-v25.js'",
    "'assets/js/sinjira-live-invites-ui-v25.js'",
    "'assets/js/sinjira-live-community-bridge-v25.js'",
    "'assets/css/v25-live-ui.css'",
    "'assets/css/v25-live-share-codes.css'",
    "'assets/css/v25-live-invites.css'",
    "'scripts/validate_live_social_ui_v25.py'",
    "'scripts/validate_live_social_share_codes_ui_v25.py'",
    "'scripts/validate_live_social_invites_ui_v25.py'",
    "'scripts/validate_live_social_runtime_v25.py'",
    "'scripts/validate_live_social_typed_commands_v25.py'",
    "'scripts/validate_live_social_foundation_v25.py'",
    "'scripts/validate_live_social_safety_v25.py'",
    "'scripts/validate_social_home_v25.py'",
    "'scripts/validate_live_social_ui_workflow_security.py'",
    "'supabase/migrations/**'",
    "'supabase/tests/live_social_*.test.sql'",
    "'supabase/tests/global_safety_compliance_v24_4_83.test.sql'",
    "'**/*.html'",
    "'.github/workflows/sinjira-live-social-ui-v25.yml'",
)

NODE_TESTS = (
    'node scripts/test_live_social_ui_model_v25.mjs',
    'node scripts/test_live_social_share_codes_client_v25.mjs',
    'node scripts/test_live_social_invites_client_v25.mjs',
    'node scripts/test_live_social_community_bridge_v25.mjs /tmp/sinjira-live-community-bridge-v25.mjs',
)

PYTHON_CHECKS = (
    'python scripts/validate_live_social_ui_v25.py',
    'python scripts/validate_live_social_share_codes_client_v25.py',
    'python scripts/validate_live_social_share_codes_ui_v25.py',
    'python scripts/validate_live_social_invites_client_v25.py',
    'python scripts/validate_live_social_invites_ui_v25.py',
    'python scripts/validate_live_social_community_bridge_v25.py',
    'python scripts/validate_live_social_runtime_v25.py',
    'python scripts/validate_live_social_typed_commands_v25.py',
    'python scripts/validate_live_social_foundation_v25.py',
    'python scripts/validate_live_social_safety_v25.py',
    'python scripts/validate_social_home_v25.py',
)

FORBIDDEN = (
    '${{ secrets.', 'SUPABASE_ACCESS_TOKEN', 'SUPABASE_DB_PASSWORD', 'environment: production',
    'supabase db push', 'db push', '--linked', 'supabase link', 'functions deploy',
    'migration repair', 'inputs.apply', '--no-verify-jwt',
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
    if 'timeout-minutes: 10' not in text:
        fail('timeout 10 absent')
    for action in (CHECKOUT, SETUP_PYTHON, SETUP_NODE):
        if action not in text:
            fail(f'action épinglée absente: {action}')
    for mutable in ('actions/checkout@v', 'actions/setup-python@v', 'actions/setup-node@v'):
        if mutable in text:
            fail(f'action mobile interdite: {mutable}')
    if 'persist-credentials: false' not in text:
        fail('credentials Git persistés')
    if "python-version: '3.12.14'" not in text:
        fail('Python non figé')
    if "node-version: '22.23.2'" not in text:
        fail('Node non figé')
    if 'package-manager-cache: false' not in text:
        fail('cache Node non désactivé')

    pr = section(text, '  pull_request:', '  push:')
    push = section(text, '  push:', '  workflow_dispatch:')
    if 'branches: [main]' not in pr or 'branches: [main]' not in push:
        fail('couverture main PR/push absente')
    for marker in CRITICAL_PATHS:
        if marker not in pr or marker not in push:
            fail(f'chemin critique non couvert PR+push: {marker}')

    if SELF_TEST not in text:
        fail('auto-test contrat absent')
    if SELF_CHECK_LINE not in text:
        fail('contrat réel absent')
    for marker in NODE_TESTS:
        if marker not in text:
            fail(f'test Node absent: {marker}')
    for marker in PYTHON_CHECKS:
        if marker not in text:
            fail(f'validateur Python absent: {marker}')
    if text.index(NODE_TESTS[0]) > text.index(PYTHON_CHECKS[0]):
        fail('tests Node doivent précéder validateurs Python')
    for marker in FORBIDDEN:
        if marker in text:
            fail(f'capacité distante/secret interdit: {marker}')


def remove_push(text: str) -> str:
    begin = text.index('  push:')
    end = text.index('  workflow_dispatch:', begin)
    return text[:begin] + text[end:]


def mutations(text: str):
    yield 'checkout mobile', text.replace(CHECKOUT, 'actions/checkout@v6', 1)
    yield 'setup-python mobile', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)
    yield 'setup-node mobile', text.replace(SETUP_NODE, 'actions/setup-node@v6', 1)
    yield 'credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)
    yield 'runner latest', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)
    yield 'python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)
    yield 'node large', text.replace("node-version: '22.23.2'", "node-version: '22'", 1)
    yield 'permissions écriture', text.replace('contents: read', 'contents: write', 1)
    yield 'cache Node', text.replace('package-manager-cache: false', 'package-manager-cache: true', 1)
    yield 'secret GitHub', text + '\nenv:\n  SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n'
    yield 'db push', text + '\n# supabase db push --linked\n'
    yield 'production', text.replace('jobs:\n', 'jobs:\n  # environment: production\n', 1)
    yield 'push retiré', remove_push(text)
    yield 'html retiré', text.replace("      - '**/*.html'\n", '', 2)
    yield 'migrations retirées', text.replace("      - 'supabase/migrations/**'\n", '', 2)
    yield 'contrat path retiré', text.replace("      - 'scripts/validate_live_social_ui_workflow_security.py'\n", '', 2)
    yield 'auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '        run: echo auto-test-retire\n', 1)
    yield 'contrat réel retiré', text.replace(SELF_CHECK_LINE, '        run: echo contrat-retire\n', 1)
    yield 'test UI retiré', text.replace(NODE_TESTS[0], 'echo ui-test-retire', 1)
    yield 'test bridge retiré', text.replace(NODE_TESTS[-1], 'echo bridge-test-retire', 1)
    yield 'validateur UI retiré', text.replace(PYTHON_CHECKS[0], 'echo ui-validator-retire', 1)
    yield 'validateur codes retiré', text.replace(PYTHON_CHECKS[2], 'echo share-ui-retire', 1)
    yield 'validateur runtime retiré', text.replace(PYTHON_CHECKS[6], 'echo runtime-retire', 1)
    yield 'JWT désactivé', text + '\n# --no-verify-jwt\n'


def self_test(text: str) -> None:
    validate_text(text)
    detected = 0
    total = 0
    for name, mutated in mutations(text):
        total += 1
        try:
            validate_text(mutated)
        except ValueError:
            detected += 1
        else:
            raise SystemExit(f'ECHEC auto-test CI UI En direct: mutation non détectée: {name}')
    print(f'OK: {detected}/{total} mutations critiques détectées')


def main() -> int:
    if not WORKFLOW.is_file():
        print('ECHEC CI UI En direct: workflow absent', file=sys.stderr)
        return 1
    text = WORKFLOW.read_text('utf-8')
    try:
        if '--self-test' in sys.argv[1:]:
            self_test(text)
        else:
            validate_text(text)
            print('OK: contrat CI interface En direct V25 respecté')
    except ValueError as exc:
        print(f'ECHEC CI interface En direct V25: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
