#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

from live_social_node_ci_security import self_test as common_self_test
from live_social_node_ci_security import validate_baseline

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-live-social-runtime-v25.yml'
SELF_TEST = 'python scripts/validate_live_social_runtime_workflow_security.py --self-test'
SELF_CHECK = 'python scripts/validate_live_social_runtime_workflow_security.py'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}\n'
COMMON_TRIGGER = "      - 'scripts/live_social_node_ci_security.py'\n"

TRIGGER_PATHS = (
    "'assets/js/sinjira-live-command-parser-v25.js'",
    "'assets/js/sinjira-live-runtime-v25.js'",
    "'scripts/test_live_social_command_parser_v25.mjs'",
    "'scripts/validate_live_social_runtime_v25.py'",
    "'scripts/validate_live_social_typed_commands_v25.py'",
    "'scripts/validate_live_social_foundation_v25.py'",
    "'scripts/validate_live_social_safety_v25.py'",
    "'scripts/validate_social_home_v25.py'",
    "'scripts/live_social_node_ci_security.py'",
    "'scripts/validate_live_social_runtime_workflow_security.py'",
    "'supabase/migrations/**'",
    "'supabase/tests/live_social_*.test.sql'",
    "'supabase/tests/global_safety_compliance_v24_4_83.test.sql'",
    "'**/*.html'",
    "'.github/workflows/sinjira-live-social-runtime-v25.yml'",
)

VALIDATORS = (
    'python scripts/validate_live_social_runtime_v25.py',
    'python scripts/validate_live_social_typed_commands_v25.py',
    'python scripts/validate_live_social_foundation_v25.py',
    'python scripts/validate_live_social_safety_v25.py',
    'python scripts/validate_social_home_v25.py',
)

NODE_PROOFS = (
    'node --check /tmp/sinjira-live-command-parser-v25.mjs',
    'node --check /tmp/sinjira-live-runtime-v25.mjs',
    'node scripts/test_live_social_command_parser_v25.mjs',
)


def fail(message: str) -> None:
    raise ValueError(message)


def validate_text(text: str) -> None:
    validate_baseline(text, timeout_minutes=10, trigger_paths=TRIGGER_PATHS)

    if SELF_TEST not in text:
        fail('auto-test contrat absent')
    if SELF_CHECK_LINE not in text:
        fail('validation réelle contrat absente')
    for marker in NODE_PROOFS:
        if marker not in text:
            fail(f'preuve Node absente: {marker}')
    for marker in VALIDATORS:
        if marker not in text:
            fail(f'validateur dark launch absent: {marker}')

    syntax_index = text.index(NODE_PROOFS[0])
    parser_test_index = text.index(NODE_PROOFS[2])
    runtime_index = text.index(VALIDATORS[0])
    if not syntax_index < parser_test_index < runtime_index:
        fail('ordre syntaxe -> parseur -> dark launch non respecté')


def extra_mutations(text: str):
    yield 'déclencheur commun retiré', text.replace(COMMON_TRIGGER, '', 2)
    yield 'déclencheur HTML retiré', text.replace("      - '**/*.html'\n", '', 2)
    yield 'déclencheur migrations retiré', text.replace("      - 'supabase/migrations/**'\n", '', 2)
    yield 'auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '        run: echo auto-test-retire\n', 1)
    yield 'contrat réel retiré', text.replace(SELF_CHECK_LINE, '        run: echo contrat-retire\n', 1)
    yield 'syntaxe parseur retirée', text.replace(NODE_PROOFS[0], 'echo parser-check-retire', 1)
    yield 'syntaxe runtime retirée', text.replace(NODE_PROOFS[1], 'echo runtime-check-retire', 1)
    yield 'test parseur retiré', text.replace(NODE_PROOFS[2], 'echo parser-test-retire', 1)
    yield 'validateur runtime retiré', text.replace(VALIDATORS[0], 'echo runtime-validator-retire', 1)
    yield 'validateur commandes retiré', text.replace(VALIDATORS[1], 'echo typed-validator-retire', 1)
    yield 'validateur fondation retiré', text.replace(VALIDATORS[2], 'echo foundation-validator-retire', 1)
    yield 'validateur safety retiré', text.replace(VALIDATORS[3], 'echo safety-validator-retire', 1)
    yield 'validateur accueil social retiré', text.replace(VALIDATORS[4], 'echo social-home-validator-retire', 1)


def self_test(text: str) -> None:
    common_self_test(text, validate_text, extra_mutations(text), label='runtime En direct')


def main() -> int:
    if not WORKFLOW.is_file():
        print('ECHEC CI runtime En direct: workflow absent', file=sys.stderr)
        return 1
    text = WORKFLOW.read_text('utf-8')
    try:
        if '--self-test' in sys.argv[1:]:
            self_test(text)
        else:
            validate_text(text)
            print('OK: contrat CI runtime En direct V25 respecté')
    except ValueError as exc:
        print(f'ECHEC CI runtime En direct V25: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
