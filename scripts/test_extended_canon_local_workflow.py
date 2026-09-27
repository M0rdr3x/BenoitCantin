#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

import validate_extended_canon_local_workflow as guard

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-v25-extended-canon-local.yml'


class ExtendedCanonLocalWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = WORKFLOW.read_text(encoding='utf-8', errors='strict')

    def assertRejected(self, mutated: str) -> None:
        self.assertNotEqual(mutated, self.baseline, 'La mutation de test doit modifier le workflow.')
        with self.assertRaises(AssertionError):
            guard.validate_text(mutated)

    def test_baseline_is_accepted(self) -> None:
        guard.validate_text(self.baseline)

    def test_mobile_checkout_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace(
            f'actions/checkout@{guard.CHECKOUT_SHA}', 'actions/checkout@v6', 1
        ))

    def test_mobile_setup_python_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace(
            f'actions/setup-python@{guard.SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1
        ))

    def test_mobile_supabase_cli_action_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace(
            f'supabase/setup-cli@{guard.SETUP_CLI_SHA}', 'supabase/setup-cli@v2', 1
        ))

    def test_latest_runner_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1))

    def test_broad_python_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace(
            f"python-version: '{guard.PYTHON_VERSION}'", "python-version: '3.12'", 1
        ))

    def test_latest_cli_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace(
            f'version: {guard.CLI_VERSION}', 'version: latest', 1
        ))

    def test_secret_reference_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace(
            'runs-on: ubuntu-24.04',
            'runs-on: ubuntu-24.04\\n    env:\\n      TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}',
            1,
        ))

    def test_linked_operation_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace('supabase db reset', 'supabase db reset --linked', 1))

    def test_project_ref_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace(
            'supabase start', 'supabase start --project-ref gpvivleexywljowcqkru', 1
        ))

    def test_db_push_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace(
            'supabase db reset', 'supabase db reset\\n          supabase db push', 1
        ))

    def test_production_environment_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace(
            '    timeout-minutes: 30',
            '    timeout-minutes: 30\\n    environment: production',
            1,
        ))

    def test_draft_gate_is_rejected(self) -> None:
        self.assertRejected(self.baseline.replace(
            '    runs-on: ubuntu-24.04',
            "    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false\\n    runs-on: ubuntu-24.04",
            1,
        ))

    def test_locator_migration_trigger_cannot_be_removed(self) -> None:
        marker = "      - 'supabase/migrations/20260926212000_sinjira_v25_canon_source_locator_guard.sql'\\n"
        self.assertRejected(self.baseline.replace(marker, '', 1))

    def test_acl_migration_trigger_cannot_be_removed(self) -> None:
        marker = "      - 'supabase/migrations/20260926214500_sinjira_v25_extended_canon_rpc_acl_hardening.sql'\\n"
        self.assertRejected(self.baseline.replace(marker, '', 1))

    def test_provenance_test_cannot_be_removed(self) -> None:
        command = (
            'supabase test db '
            'supabase/tests/extended_canon_continuity_v25.test.sql '
            'supabase/tests/canon_provenance_v25.test.sql '
            'supabase/tests/server_only_rls_contract_v25.test.sql '
            'supabase/tests/security_advisor_contract_v24_5_24.test.sql'
        )
        self.assertRejected(self.baseline.replace(
            command,
            command.replace('supabase/tests/canon_provenance_v25.test.sql ', ''),
            1,
        ))

    def test_security_advisor_test_cannot_be_removed(self) -> None:
        command = (
            'supabase test db '
            'supabase/tests/extended_canon_continuity_v25.test.sql '
            'supabase/tests/canon_provenance_v25.test.sql '
            'supabase/tests/server_only_rls_contract_v25.test.sql '
            'supabase/tests/security_advisor_contract_v24_5_24.test.sql'
        )
        self.assertRejected(self.baseline.replace(
            command,
            command.replace(' supabase/tests/security_advisor_contract_v24_5_24.test.sql', ''),
            1,
        ))

    def test_cleanup_always_cannot_be_removed(self) -> None:
        self.assertRejected(self.baseline.replace('        if: always()\\n', '', 1))


if __name__ == '__main__':
    unittest.main(verbosity=2)
