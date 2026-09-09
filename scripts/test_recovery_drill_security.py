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

    def test_mobile_supabase_action_reference_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                f'supabase/setup-cli@{guard.SETUP_CLI_SHA}',
                'supabase/setup-cli@v2',
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

    def test_secret_reference_is_rejected(self) -> None:
        self.assertRejected(
            self.baseline.replace(
                'runs-on: ubuntu-latest',
                'runs-on: ubuntu-latest\n    env:\n      TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}',
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
