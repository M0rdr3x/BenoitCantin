#!/usr/bin/env python3
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_supabase_production_preflight_security import (  # noqa: E402
    APPLY_JOB_GUARD,
    APPLY_STEP_GUARD,
    CONFIRMATION,
    PINNED_ACTIONS,
    REMOTE_JOB_GUARD,
    SELF_CHECK,
    SELF_TEST,
    validate_text,
)

WORKFLOW = ROOT / ".github" / "workflows" / "supabase-production-preflight.yml"


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

    def test_current_workflow_is_accepted(self):
        self.assertEqual(validate_text(self.valid), [])

    def test_runner_latest_is_rejected(self):
        bad = self.valid.replace("    runs-on: ubuntu-24.04", "    runs-on: ubuntu-latest", 1)
        self.assertRejected(bad, "ubuntu-latest")

    def test_broad_python_is_rejected(self):
        bad = self.valid.replace("          python-version: '3.12.14'", "          python-version: '3.12'", 1)
        self.assertRejected(bad, "3.12.14")

    def test_persisted_checkout_credentials_are_rejected(self):
        bad = self.valid.replace("          persist-credentials: false", "          persist-credentials: true", 1)
        self.assertRejected(bad, "trois checkouts")

    def test_contents_write_is_rejected(self):
        bad = self.valid.replace("  contents: read", "  contents: write", 1)
        self.assertRejected(bad, "lecture seule")

    def test_continue_on_error_is_rejected(self):
        bad = self.valid.replace("    timeout-minutes: 10", "    timeout-minutes: 10\n    continue-on-error: true", 1)
        self.assertRejected(bad, "continue-on-error")

    def test_shell_trace_is_rejected(self):
        bad = self.valid.replace("          set -euo pipefail", "          set -x", 1)
        self.assertRejected(bad, "set -x")

    def test_self_test_removal_is_rejected(self):
        bad = self.valid.replace(SELF_TEST, "echo auto-test-retire", 1)
        self.assertRejected(bad, "chaîne locale")

    def test_self_check_removal_is_rejected(self):
        bad = self.valid.replace(SELF_CHECK, "echo contrat-retire", 1)
        self.assertRejected(bad, "chaîne locale")

    def test_self_checks_order_is_rejected_when_swapped(self):
        temporary = "python scripts/__temp_preflight_security__.py"
        bad = self.valid.replace(SELF_TEST, temporary, 1)
        bad = bad.replace(SELF_CHECK, SELF_TEST, 1)
        bad = bad.replace(temporary, SELF_CHECK, 1)
        self.assertRejected(bad, "ordre doit rester")

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
            self.assertRejected(bad, "Action réutilisable non approuvée")

    def test_critical_trigger_path_removal_is_rejected(self):
        marker = "      - 'scripts/test_supabase_production_preflight_security.py'\n"
        bad = self.valid.replace(marker, "", 1)
        self.assertRejected(bad, "Chemin critique absent")

    def test_runbook_changes_must_trigger_security_workflow(self):
        marker = "      - 'docs/SUPABASE_PRODUCTION_RUNBOOK.md'\n"
        bad = self.valid.replace(marker, "", 1)
        self.assertRejected(bad, "Chemin critique absent")

    def test_local_preflight_cannot_receive_secret(self):
        bad = self.valid.replace(
            "    timeout-minutes: 10\n    steps:",
            "    timeout-minutes: 10\n    env:\n      TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n    steps:",
            1,
        )
        self.assertRejected(bad, "prévol local ne doit référencer aucun secret")

    def test_local_preflight_cannot_run_supabase_cli(self):
        bad = self.valid.replace(
            "          python scripts/validate_supabase.py",
            "          supabase --version\n          python scripts/validate_supabase.py",
            1,
        )
        self.assertRejected(bad, "prévol local ne doit exécuter aucune commande Supabase CLI")

    def test_remote_job_must_be_manual_only(self):
        bad = self.valid.replace(REMOTE_JOB_GUARD, "    if: ${{ always() }}", 1)
        self.assertRejected(bad, "prévol distant doit être réservé")

    def test_remote_preflight_cannot_write_database(self):
        dry = '(cd .prod-workspace && supabase db push --linked --dry-run --password "$SUPABASE_DB_PASSWORD")'
        write = '(cd .prod-workspace && supabase db push --linked --password "$SUPABASE_DB_PASSWORD")'
        bad = self.valid.replace(dry, write, 1)
        self.assertRejected(bad, "prévol distant ne doit jamais exécuter db push")

    def test_remote_preflight_cannot_deploy_functions(self):
        marker = "          (cd .prod-workspace && supabase db push --linked --dry-run --password \"$SUPABASE_DB_PASSWORD\") | tee /tmp/sinjira-dry-run.txt"
        bad = self.valid.replace(
            marker,
            marker + "\n          (cd .prod-workspace && supabase functions deploy --project-ref \"$PROJECT_ID\" --use-api)",
            1,
        )
        self.assertRejected(bad, "prévol distant ne doit jamais déployer")

    def test_remote_intent_requires_main_ref(self):
        bad = self.valid.replace('[ "${{ github.ref }}" != "refs/heads/main" ]', '[ -z "${{ github.ref }}" ]', 1)
        self.assertRejected(bad, "verrou d'intention")

    def test_remote_intent_requires_typed_confirmation(self):
        marker = f'[ "${{{{ inputs.confirmation }}}}" != "{CONFIRMATION}" ]'
        bad = self.valid.replace(marker, '[ -z "${{ inputs.confirmation }}" ]', 1)
        self.assertRejected(bad, "verrou d'intention")

    def test_apply_job_requires_full_gate(self):
        bad = self.valid.replace(
            APPLY_JOB_GUARD,
            "    if: ${{ github.event_name == 'workflow_dispatch' && inputs.apply == true }}",
            1,
        )
        self.assertRejected(bad, "job d'application doit exiger")

    def test_apply_job_requires_production_environment(self):
        bad = self.valid.replace("    environment: production\n", "    environment: staging\n", 1)
        self.assertRejected(bad, "environment GitHub production")

    def test_apply_job_requires_both_preflights(self):
        bad = self.valid.replace(
            "    needs: [local-preflight, remote-preflight]\n",
            "    needs: local-preflight\n",
            1,
        )
        self.assertRejected(bad, "prévols local et distant")

    def test_post_environment_revalidation_requires_dry_run(self):
        marker = '(cd .prod-workspace && supabase db push --linked --dry-run --password "$SUPABASE_DB_PASSWORD") | tee /tmp/sinjira-dry-run-approval.txt'
        bad = self.valid.replace(marker, "echo dry-run-retire", 1)
        self.assertRejected(bad, "Revalidation post-environment incomplète")

    def test_apply_step_keeps_redundant_fail_closed_gate(self):
        marker = "      - name: Appliquer les migrations de production depuis le workspace protégé\n"
        start = self.valid.index(marker)
        tail = self.valid[start:]
        bad_tail = tail.replace(APPLY_STEP_GUARD, "if: ${{ steps.auth.outputs.ready == 'true' }}", 1)
        bad = self.valid[:start] + bad_tail
        self.assertRejected(bad, "Étape apply sans garde")

    def test_remote_step_requires_scoped_database_password(self):
        marker = "      - name: Lier le projet de production dans le workspace protégé\n"
        start = self.valid.index(marker)
        tail = self.valid[start:]
        secret = "          SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}\n"
        self.assertIn(secret, tail)
        bad = self.valid[:start] + tail.replace(secret, "", 1)
        self.assertRejected(bad, "SUPABASE_DB_PASSWORD non borné")

    def test_db_write_must_not_escape_apply_job(self):
        marker = "          python scripts/validate_production_migration_ledger.py"
        write = '          (cd .prod-workspace && supabase db push --linked --password "$SUPABASE_DB_PASSWORD")'
        bad = self.valid.replace(marker, marker + "\n" + write, 1)
        self.assertRejected(bad, "Primitive mutante hors job apply-production")

    def test_confirmation_default_must_remain_non_mutating(self):
        bad = self.valid.replace('default: "PREFLIGHT_ONLY"', f'default: "{CONFIRMATION}"', 1)
        self.assertRejected(bad, "confirmation textuelle")

    def test_pr_summary_must_prove_no_secret_exposure(self):
        bad = self.valid.replace("aucun secret production exposé au run PR", "préflight PR", 1)
        self.assertRejected(bad, "aucun secret production exposé au run PR")


if __name__ == "__main__":
    unittest.main(verbosity=2)
