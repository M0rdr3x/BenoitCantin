#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

import validate_production_migration_workflow_security as guard

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / '.github/workflows/sinjira-production-migration-history-guard-v25.yml'
VALIDATION = ROOT / '.github/workflows/validate-production-ledger.yml'


class ProductionMigrationWorkflowSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.history = HISTORY.read_text(encoding='utf-8', errors='strict')
        cls.validation = VALIDATION.read_text(encoding='utf-8', errors='strict')

    def assertHistoryRejected(self, mutated: str) -> None:
        with self.assertRaises(AssertionError):
            guard.validate_action_integrity(
                mutated,
                'garde historique',
                require_full_history=True,
            )

    def assertValidationRejected(self, mutated: str) -> None:
        with self.assertRaises(AssertionError):
            guard.validate_validation_workflow_contract(mutated)

    def test_baselines_are_accepted(self) -> None:
        guard.validate_action_integrity(
            self.history,
            'garde historique',
            require_full_history=True,
        )
        guard.validate_validation_workflow_contract(self.validation)

    def test_history_mobile_checkout_is_rejected(self) -> None:
        self.assertHistoryRejected(
            self.history.replace(
                f'actions/checkout@{guard.CHECKOUT_SHA}',
                'actions/checkout@v6',
                1,
            )
        )

    def test_history_mobile_setup_python_is_rejected(self) -> None:
        self.assertHistoryRejected(
            self.history.replace(
                f'actions/setup-python@{guard.SETUP_PYTHON_SHA}',
                'actions/setup-python@v6',
                1,
            )
        )

    def test_history_floating_runner_is_rejected(self) -> None:
        self.assertHistoryRejected(
            self.history.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)
        )

    def test_history_floating_python_is_rejected(self) -> None:
        self.assertHistoryRejected(
            self.history.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)
        )

    def test_validation_floating_runner_is_rejected(self) -> None:
        self.assertValidationRejected(
            self.validation.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)
        )

    def test_validation_floating_python_is_rejected(self) -> None:
        self.assertValidationRejected(
            self.validation.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)
        )

    def test_validation_persisted_credentials_are_rejected(self) -> None:
        self.assertValidationRejected(
            self.validation.replace(
                'persist-credentials: false',
                'persist-credentials: true',
                1,
            )
        )

    def test_secret_reference_is_rejected(self) -> None:
        self.assertValidationRejected(
            self.validation.replace(
                'runs-on: ubuntu-24.04',
                'runs-on: ubuntu-24.04\n    env:\n      TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}',
                1,
            )
        )

    def test_history_requires_full_git_history(self) -> None:
        self.assertHistoryRejected(
            self.history.replace('fetch-depth: 0', 'fetch-depth: 1', 1)
        )

    def test_validator_path_must_trigger_validation(self) -> None:
        self.assertValidationRejected(
            self.validation.replace(
                "      - 'scripts/validate_production_migration_workflow_security.py'\n",
                '',
            )
        )

    def test_history_validator_path_must_trigger_validation(self) -> None:
        self.assertValidationRejected(
            self.validation.replace(
                "      - 'scripts/validate_production_migration_history_workflow_security.py'\n",
                '',
            )
        )

    def test_mutation_tests_must_be_executed(self) -> None:
        self.assertValidationRejected(
            self.validation.replace(
                'python scripts/test_production_migration_workflow_security.py',
                'echo tests-disabled',
                1,
            )
        )

    def test_history_mutation_self_test_must_be_executed(self) -> None:
        self.assertValidationRejected(
            self.validation.replace(
                'python scripts/validate_production_migration_history_workflow_security.py --self-test',
                'echo history-self-test-disabled',
                1,
            )
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
