#!/usr/bin/env python3
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_supabase_production_preflight_security import validate_text  # noqa: E402

WORKFLOW = ROOT / ".github" / "workflows" / "supabase-production-preflight.yml"
MANUAL_ONLY_GUARD = "        if: ${{ github.event_name == 'workflow_dispatch' }}\n"


class SupabaseProductionPreflightSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = WORKFLOW.read_text(encoding="utf-8")

    def assertRejected(self, text: str, fragment: str):
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
