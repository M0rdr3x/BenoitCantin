#!/usr/bin/env python3
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_supabase_production_preflight_security import (  # noqa: E402
    PINNED_ACTIONS,
    SELF_CHECK,
    SELF_TEST,
    validate_text,
)

WORKFLOW = ROOT / ".github" / "workflows" / "supabase-production-preflight.yml"
MANUAL_ONLY_GUARD = "        if: ${{ github.event_name == 'workflow_dispatch' }}\n"


class SupabaseProductionPreflightSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = WORKFLOW.read_text(encoding="utf-8")

    def assertRejected(self, text: str, fragment: str):
        self.assertNotEqual(text, self.valid, "La mutation doit réellement modifier le workflow.")
        errors = validate_text(text)
        self.assertTrue(errors, "La mutation dangereuse aurait dû être refusée.")
        self.assertTrue(
            any(fragment in error for error in errors),
            f"Erreur attendue contenant {fragment!r}; reçu: {errors}",
        )

    def without_step_guard(self, name: str) -> str:
        marker = f"      - name: {name}\n"
        start = self.valid.index(marker)
        tail = self.valid[start:]
        self.assertIn(MANUAL_ONLY_GUARD, tail)
        return self.valid[:start] + tail.replace(MANUAL_ONLY_GUARD, "", 1)

    def test_current_workflow_is_accepted(self):
        self.assertEqual(validate_text(self.valid), [])

    def test_runner_latest_is_rejected(self):
        bad = self.valid.replace("    runs-on: ubuntu-24.04", "    runs-on: ubuntu-latest", 1)
        self.assertRejected(bad, "ubuntu-24.04")

    def test_broad_python_is_rejected(self):
        bad = self.valid.replace("          python-version: '3.12.14'", "          python-version: '3.12'", 1)
        self.assertRejected(bad, "3.12.14")

    def test_persisted_checkout_credentials_are_rejected(self):
        bad = self.valid.replace("          persist-credentials: false", "          persist-credentials: true", 1)
        self.assertRejected(bad, "persist-credentials: false")

    def test_contents_write_is_rejected(self):
        bad = self.valid.replace("  contents: read", "  contents: write", 1)
        self.assertRejected(bad, "lecture seule")

    def test_self_test_removal_is_rejected(self):
        bad = self.valid.replace(SELF_TEST, "echo auto-test-retire", 1)
        self.assertRejected(bad, "auto-test du contrat sécurité")

    def test_self_check_removal_is_rejected(self):
        bad = self.valid.replace(SELF_CHECK, "echo contrat-retire", 1)
        self.assertRejected(bad, "validation du contrat sécurité")

    def test_self_checks_order_is_rejected_when_swapped(self):
        temporary = "python scripts/__temp_preflight_security__.py"
        bad = self.valid.replace(SELF_TEST, temporary, 1)
        bad = bad.replace(SELF_CHECK, SELF_TEST, 1)
        bad = bad.replace(temporary, SELF_CHECK, 1)
        self.assertRejected(bad, "ordre doit rester Python")

    def test_continue_on_error_is_rejected(self):
        bad = self.valid.replace("    timeout-minutes: 25", "    timeout-minutes: 25\n    continue-on-error: true", 1)
        self.assertRejected(bad, "continue-on-error")

    def test_shell_trace_is_rejected(self):
        bad = self.valid.replace("          set -euo pipefail", "          set -x", 1)
        self.assertRejected(bad, "set -x")

    def test_critical_trigger_path_removal_is_rejected(self):
        marker = "      - 'scripts/test_supabase_production_preflight_security.py'\n"
        bad = self.valid.replace(marker, "", 1)
        self.assertRejected(bad, "Chemin critique absent")

    def test_job_level_secret_is_rejected(self):
        bad = self.valid.replace(
            "    env:\n      PROJECT_ID:",
            "    env:\n      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n      PROJECT_ID:",
            1,
        )
        self.assertRejected(bad, "Secret interdit au niveau jobs.sync.env")

    def test_cli_before_workspace_is_rejected(self):
        bad = self.valid.replace(
            "- name: Installer Supabase CLI",
            "- name: TEMP INSTALL",
            1,
        ).replace(
            "- name: Construire le workspace production protégé",
            "- name: Installer Supabase CLI",
            1,
        ).replace(
            "- name: TEMP INSTALL",
            "- name: Construire le workspace production protégé",
            1,
        )
        self.assertRejected(bad, "workspace fail-closed")

    def test_cli_install_on_pr_or_push_is_rejected(self):
        bad = self.without_step_guard("Installer Supabase CLI")
        self.assertRejected(bad, "installation Supabase CLI doit être réservée")

    def test_cli_verification_on_pr_or_push_is_rejected(self):
        bad = self.without_step_guard("Vérifier Supabase CLI")
        self.assertRejected(bad, "vérification Supabase CLI doit être réservée")

    def test_all_reusable_actions_are_pinned(self):
        aliases = {
            "actions/checkout": "v6",
            "actions/setup-python": "v6",
            "supabase/setup-cli": "v2",
            "actions/upload-artifact": "v4",
        }
        for action, sha in PINNED_ACTIONS.items():
            pinned = f"{action}@{sha}"
            self.assertIn(pinned, self.valid)
            bad = self.valid.replace(pinned, f"{action}@{aliases[action]}", 1)
            self.assertRejected(bad, f"L'action {action} doit être épinglée")

    def test_auth_secrets_on_pr_or_push_are_rejected(self):
        bad = self.without_step_guard("Détecter les secrets de connexion Supabase")
        self.assertRejected(bad, "uniquement en workflow_dispatch manuel")

    def test_remote_preflight_on_pr_or_push_is_rejected(self):
        bad = self.valid.replace(
            "if: ${{ github.event_name == 'workflow_dispatch' && steps.auth.outputs.ready == 'true' }}",
            "if: ${{ steps.auth.outputs.ready == 'true' }}",
            1,
        )
        self.assertRejected(bad, "accessible hors lancement manuel")

    def test_apply_guard_removal_is_rejected(self):
        marker = "      - name: Appliquer les migrations de production depuis le workspace protégé\n"
        start = self.valid.index(marker)
        tail = self.valid[start:]
        bad_tail = tail.replace(
            "if: ${{ github.event_name == 'workflow_dispatch' && inputs.apply == true && steps.auth.outputs.ready == 'true' }}",
            "if: ${{ github.event_name == 'workflow_dispatch' && steps.auth.outputs.ready == 'true' }}",
            1,
        )
        bad = self.valid[:start] + bad_tail
        self.assertRejected(bad, "triple garde workflow_dispatch + apply=true + auth")

    def test_workspace_builder_removal_is_rejected(self):
        bad = self.valid.replace(
            "python scripts/build_supabase_production_workspace.py --output .prod-workspace/supabase",
            "echo builder-retire",
            1,
        )
        self.assertRejected(bad, "builder fail-closed")

    def test_remote_step_without_scoped_secret_is_rejected(self):
        block = "          SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}\n"
        marker = "      - name: Lier le projet de production dans le workspace protégé\n"
        start = self.valid.index(marker)
        tail = self.valid[start:]
        self.assertIn(block, tail)
        bad_tail = tail.replace(block, "", 1)
        bad = self.valid[:start] + bad_tail
        self.assertRejected(bad, "SUPABASE_DB_PASSWORD non borné")

    def test_pr_summary_must_prove_no_secret_exposure(self):
        bad = self.valid.replace(
            "aucun secret production exposé au run PR",
            "préflight PR",
            1,
        )
        self.assertRejected(bad, "aucun secret production exposé au run PR")


if __name__ == "__main__":
    unittest.main(verbosity=2)
