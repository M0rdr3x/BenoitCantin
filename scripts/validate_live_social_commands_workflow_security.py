#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

from live_social_supabase_ci_security import self_test as common_self_test
from live_social_supabase_ci_security import validate_baseline

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-live-social-commands-v25.yml'
SELF_TEST = 'python scripts/validate_live_social_commands_workflow_security.py --self-test'
SELF_CHECK = 'python scripts/validate_live_social_commands_workflow_security.py'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}\n'
COMMON_TRIGGER = "      - 'scripts/live_social_supabase_ci_security.py'\n"

TRIGGER_PATHS = (
    "'supabase/production-migration-ledger.txt'",
    "'supabase/migrations/**'",
    "'supabase/tests/live_social_typed_commands_v25.test.sql'",
    "'supabase/tests/live_social_foundation_v25.test.sql'",
    "'supabase/tests/live_social_moderation_v25.test.sql'",
    "'supabase/tests/live_social_private_invites_v25.test.sql'",
    "'supabase/tests/security_advisor_contract_v24_5_24.test.sql'",
    "'scripts/validate_live_social_typed_commands_v25.py'",
    "'scripts/validate_live_social_foundation_v25.py'",
    "'scripts/validate_live_social_safety_v25.py'",
    "'scripts/validate_supabase.py'",
    "'scripts/validate_production_migration_ledger.py'",
    "'scripts/validate_production_schema_manifest.py'",
    "'scripts/live_social_supabase_ci_security.py'",
    "'scripts/validate_live_social_commands_workflow_security.py'",
    "'.github/workflows/sinjira-live-social-commands-v25.yml'",
)

STATIC_CHECKS = (
    'python scripts/validate_live_social_typed_commands_v25.py',
    'python scripts/validate_live_social_foundation_v25.py',
    'python scripts/validate_live_social_safety_v25.py',
    'python scripts/validate_supabase.py',
    'python scripts/validate_production_migration_ledger.py',
    'python scripts/validate_production_schema_manifest.py',
)

PGTAP_CHECKS = (
    'supabase test db supabase/tests/live_social_typed_commands_v25.test.sql --local',
    'supabase test db supabase/tests/live_social_foundation_v25.test.sql --local',
    'supabase test db supabase/tests/live_social_moderation_v25.test.sql --local',
    'supabase test db supabase/tests/live_social_private_invites_v25.test.sql --local',
    'supabase test db supabase/tests/security_advisor_contract_v24_5_24.test.sql --local',
)


def fail(message: str) -> None:
    raise ValueError(message)


def require_once(text: str, marker: str, label: str) -> None:
    if text.count(marker) != 1:
        fail(f'{label} doit apparaître exactement une fois')


def validate_text(text: str) -> None:
    validate_baseline(text, timeout_minutes=20, trigger_paths=TRIGGER_PATHS)

    require_once(text, SELF_TEST, 'auto-test contrat')
    require_once(text, SELF_CHECK_LINE, 'validation réelle contrat')
    for marker in STATIC_CHECKS:
        require_once(text, marker, f'validateur statique {marker}')
    for marker in PGTAP_CHECKS:
        require_once(text, marker, f'preuve pgTAP {marker}')

    static_index = text.index(STATIC_CHECKS[0])
    start_index = text.index('run: supabase start')
    test_indexes = [text.index(marker) for marker in PGTAP_CHECKS]
    stop_index = text.index('run: supabase stop --no-backup || true')
    if not static_index < start_index < test_indexes[0]:
        fail('contrats statiques ou démarrage Supabase mal ordonnés')
    if test_indexes != sorted(test_indexes) or not test_indexes[-1] < stop_index:
        fail('ordre commandes -> fondation -> modération -> invitations -> advisor -> stop non respecté')


def extra_mutations(text: str):
    yield 'déclencheur commun retiré', text.replace(COMMON_TRIGGER, '', 2)
    yield 'déclencheur ledger retiré', text.replace("      - 'supabase/production-migration-ledger.txt'\n", '', 2)
    yield 'déclencheur migrations retiré', text.replace("      - 'supabase/migrations/**'\n", '', 2)
    yield 'déclencheur commandes pgTAP retiré', text.replace("      - 'supabase/tests/live_social_typed_commands_v25.test.sql'\n", '', 2)
    yield 'déclencheur invitations pgTAP retiré', text.replace("      - 'supabase/tests/live_social_private_invites_v25.test.sql'\n", '', 2)
    yield 'déclencheur advisor retiré', text.replace("      - 'supabase/tests/security_advisor_contract_v24_5_24.test.sql'\n", '', 2)
    yield 'déclencheur contrat retiré', text.replace("      - 'scripts/validate_live_social_commands_workflow_security.py'\n", '', 2)
    yield 'auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '        run: echo auto-test-retire\n', 1)
    yield 'contrat réel retiré', text.replace(SELF_CHECK_LINE, '        run: echo contrat-retire\n', 1)
    for index, marker in enumerate(STATIC_CHECKS):
        yield f'validateur statique {index + 1} retiré', text.replace(marker, f'echo static-{index + 1}-retire', 1)
    for index, marker in enumerate(PGTAP_CHECKS):
        yield f'preuve pgTAP {index + 1} retirée', text.replace(marker, f'echo pgtap-{index + 1}-retire', 1)


def self_test(text: str) -> None:
    common_self_test(text, validate_text, extra_mutations(text), label='commandes En direct')


def main() -> int:
    if not WORKFLOW.is_file():
        print('ECHEC CI commandes En direct: workflow absent', file=sys.stderr)
        return 1
    text = WORKFLOW.read_text('utf-8')
    try:
        if '--self-test' in sys.argv[1:]:
            self_test(text)
        else:
            validate_text(text)
            print('OK: contrat CI commandes En direct V25 respecté')
    except ValueError as exc:
        print(f'ECHEC CI commandes En direct V25: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
