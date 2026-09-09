#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

import validate_recovery_drill_security as guard

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/recovery-drill.yml'


class RecoveryDrillSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = WORKFLOW.read_text(encoding='utf-8', errors='strict')

    def assertRejected(self, mutated: str) -> None:
        self.assertNotEqual(mutated, self.baseline, 'La mutation de test doit réellement modifier le workflow.')
        with self.assertRaises(AssertionError):
            guard.validate_text(mutated)

    def test_baseline_is_accepted(self) -> None:
        guard.validate_text(self.baseline)

    def test_mobile_checkout_reference_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                f'actions/checkout@{guard.CHECKOUT_SHA}',
                'actions/checkout@v6',
                1,
            )
        )

    def test_mobile_setup_python_reference_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                f'actions/setup-python@{guard.SETUP_PYTHON_SHA}',
                'actions/setup-python@v6',
                1,
            )
        )

    def test_mobile_supabase_action_reference_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                f'supabase/setup-cli@{guard.SETUP_CLI_SHA}',
                'supabase/setup-cli@v2',
                1,
            )
        )

    def test_mobile_runner_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)
        )

    def test_broad_python_version_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                f"python-version: '{guard.PYTHON_VERSION}'",
                "python-version: '3.12'",
                1,
            )
        )

    def test_latest_cli_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                f'version: {guard.CLI_VERSION}',
                'version: latest',
                1,
            )
        )

    def test_persisted_git_credentials_are_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                'persist-credentials: false',
                'persist-credentials: true',
                1,
            )
        )

    def test_remote_linked_operation_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                'supabase db reset',
                'supabase db reset --linked',
                1,
            )
        )

    def test_remote_project_ref_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                'supabase test db',
                'supabase test db --project-ref gpvivleexywljowcqkru',
                1,
            )
        )

    def test_secret_reference_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                'runs-on: ubuntu-24.04',
                'runs-on: ubuntu-24.04\n    env:\n      TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}',
                1,
            )
        )

    def test_production_environment_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                '    timeout-minutes: 30',
                '    timeout-minutes: 30\n    environment: production',
                1,
            )
        )

    def test_guard_path_trigger_cannot_be_removed(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                "      - 'scripts/validate_recovery_drill_security.py'\n",
                '',
            )
        )

    def test_test_path_trigger_cannot_be_removed(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                "      - 'scripts/test_recovery_drill_security.py'\n",
                '',
            )
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
