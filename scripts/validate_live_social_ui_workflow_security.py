#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

from live_social_node_ci_security import self_test as common_self_test
from live_social_node_ci_security import validate_baseline

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-live-social-ui-v25.yml'
SELF_TEST = 'python scripts/validate_live_social_ui_workflow_security.py --self-test'
SELF_CHECK = 'python scripts/validate_live_social_ui_workflow_security.py'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}\n'
COMMON_TRIGGER = "      - 'scripts/live_social_node_ci_security.py'\n"

TRIGGER_PATHS = (
    "'assets/js/sinjira-community-real.js'",
    "'assets/js/sinjira-live-runtime-v25.js'",
    "'assets/js/sinjira-live-ui-model-v25.js'",
    "'assets/js/sinjira-live-ui-v25.js'",
    "'assets/js/sinjira-live-ui-shell-v25.js'",
    "'assets/js/sinjira-live-share-codes-model-v25.js'",
    "'assets/js/sinjira-live-share-codes-client-v25.js'",
    "'assets/js/sinjira-live-share-codes-ui-v25.js'",
    "'assets/js/sinjira-live-invites-model-v25.js'",
    "'assets/js/sinjira-live-invites-client-v25.js'",
    "'assets/js/sinjira-live-invites-ui-v25.js'",
    "'assets/js/sinjira-live-community-bridge-v25.js'",
    "'assets/css/v25-live-ui.css'",
    "'assets/css/v25-live-share-codes.css'",
    "'assets/css/v25-live-invites.css'",
    "'scripts/test_live_social_ui_model_v25.mjs'",
    "'scripts/test_live_social_share_codes_client_v25.mjs'",
    "'scripts/test_live_social_invites_client_v25.mjs'",
    "'scripts/test_live_social_community_bridge_v25.mjs'",
    "'scripts/validate_live_social_ui_v25.py'",
    "'scripts/validate_live_social_share_codes_client_v25.py'",
    "'scripts/validate_live_social_share_codes_ui_v25.py'",
    "'scripts/validate_live_social_invites_client_v25.py'",
    "'scripts/validate_live_social_invites_ui_v25.py'",
    "'scripts/validate_live_social_community_bridge_v25.py'",
    "'scripts/validate_live_social_runtime_v25.py'",
    "'scripts/validate_live_social_typed_commands_v25.py'",
    "'scripts/validate_live_social_foundation_v25.py'",
    "'scripts/validate_live_social_safety_v25.py'",
    "'scripts/validate_social_home_v25.py'",
    "'scripts/live_social_node_ci_security.py'",
    "'scripts/validate_live_social_ui_workflow_security.py'",
    "'supabase/migrations/**'",
    "'supabase/tests/live_social_*.test.sql'",
    "'supabase/tests/global_safety_compliance_v24_4_83.test.sql'",
    "'**/*.html'",
    "'.github/workflows/sinjira-live-social-ui-v25.yml'",
)

NODE_SYNTAX = (
    'node --check /tmp/sinjira-live-ui-model-v25.mjs',
    'node --check /tmp/sinjira-live-ui-v25.mjs',
    'node --check /tmp/sinjira-live-ui-shell-v25.mjs',
    'node --check /tmp/sinjira-live-share-codes-model-v25.mjs',
    'node --check /tmp/sinjira-live-share-codes-client-v25.mjs',
    'node --check /tmp/sinjira-live-share-codes-ui-v25.mjs',
    'node --check /tmp/sinjira-live-invites-model-v25.mjs',
    'node --check /tmp/sinjira-live-invites-client-v25.mjs',
    'node --check /tmp/sinjira-live-invites-ui-v25.mjs',
    'node --check /tmp/sinjira-live-community-bridge-v25.mjs',
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


def fail(message: str) -> None:
    raise ValueError(message)


def validate_text(text: str) -> None:
    validate_baseline(text, timeout_minutes=10, trigger_paths=TRIGGER_PATHS)

    if SELF_TEST not in text:
        fail('auto-test contrat absent')
    if SELF_CHECK_LINE not in text:
        fail('validation réelle contrat absente')
    for marker in NODE_SYNTAX:
        if marker not in text:
            fail(f'preuve syntaxe Node absente: {marker}')
    for marker in NODE_TESTS:
        if marker not in text:
            fail(f'test Node absent: {marker}')
    for marker in PYTHON_CHECKS:
        if marker not in text:
            fail(f'validateur dark launch absent: {marker}')

    first_syntax = text.index(NODE_SYNTAX[0])
    first_test = text.index(NODE_TESTS[0])
    first_python = text.index(PYTHON_CHECKS[0])
    if not first_syntax < first_test < first_python:
        fail('ordre syntaxe -> tests Node -> validateurs Python non respecté')


def extra_mutations(text: str):
    yield 'déclencheur commun retiré', text.replace(COMMON_TRIGGER, '', 2)
    yield 'déclencheur runtime retiré', text.replace("      - 'assets/js/sinjira-live-runtime-v25.js'\n", '', 2)
    yield 'déclencheur modèle UI retiré', text.replace("      - 'assets/js/sinjira-live-ui-model-v25.js'\n", '', 2)
    yield 'déclencheur invitations client retiré', text.replace("      - 'assets/js/sinjira-live-invites-client-v25.js'\n", '', 2)
    yield 'déclencheur bridge retiré', text.replace("      - 'assets/js/sinjira-live-community-bridge-v25.js'\n", '', 2)
    yield 'déclencheur migrations retiré', text.replace("      - 'supabase/migrations/**'\n", '', 2)
    yield 'déclencheur HTML retiré', text.replace("      - '**/*.html'\n", '', 2)
    yield 'auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '        run: echo auto-test-retire\n', 1)
    yield 'contrat réel retiré', text.replace(SELF_CHECK_LINE, '        run: echo contrat-retire\n', 1)
    yield 'syntaxe UI retirée', text.replace(NODE_SYNTAX[1], 'echo ui-check-retire', 1)
    yield 'syntaxe invitations retirée', text.replace(NODE_SYNTAX[7], 'echo invites-check-retire', 1)
    yield 'syntaxe bridge retirée', text.replace(NODE_SYNTAX[-1], 'echo bridge-check-retire', 1)
    yield 'test modèle retiré', text.replace(NODE_TESTS[0], 'echo ui-test-retire', 1)
    yield 'test codes retiré', text.replace(NODE_TESTS[1], 'echo share-test-retire', 1)
    yield 'test invitations retiré', text.replace(NODE_TESTS[2], 'echo invite-test-retire', 1)
    yield 'test bridge retiré', text.replace(NODE_TESTS[3], 'echo bridge-test-retire', 1)
    for index, marker in enumerate(PYTHON_CHECKS):
        yield f'validateur Python {index + 1} retiré', text.replace(marker, f'echo python-check-{index + 1}-retire', 1)


def self_test(text: str) -> None:
    common_self_test(text, validate_text, extra_mutations(text), label='interface En direct')


def main() -> int:
    if not WORKFLOW.is_file():
        print('ECHEC CI interface En direct: workflow absent', file=sys.stderr)
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
