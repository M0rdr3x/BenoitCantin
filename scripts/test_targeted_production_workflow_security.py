#!/usr/bin/env python3
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_targeted_production_workflow_security import (  # noqa: E402
    CHECKOUT_SHA,
    SETUP_CLI_SHA,
    TARGETS,
    validate_text,
)

WORKFLOW_DIR = ROOT / ".github" / "workflows"


class TargetedProductionWorkflowSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflows = {
            name: (WORKFLOW_DIR / name).read_text(encoding="utf-8")
            for name in TARGETS
        }

    def assertRejected(self, filename: str, text: str, fragment: str):
        errors = validate_text(filename, text)
        self.assertTrue(errors, "La mutation dangereuse aurait dû être refusée.")
        self.assertTrue(
            any(fragment in error for error in errors),
            f"Erreur attendue contenant {fragment!r}; reçu: {errors}",
        )

    def test_current_workflows_are_accepted(self):
        for filename, text in self.workflows.items():
            with self.subTest(filename=filename):
                self.assertEqual(validate_text(filename, text), [])

    def test_job_level_token_is_rejected(self):
        filename = "sinjira-v25-employment-production.yml"
        text = self.workflows[filename]
        bad = text.replace(
            "    steps:\n",
            "    env:\n      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n    steps:\n",
            1,
        )
        self.assertRejected(filename, bad, "interdit au niveau du job")

    def test_checkout_moving_tag_is_rejected(self):
        filename = "sinjira-v25-production-deploy.yml"
        text = self.workflows[filename]
        pinned = f"actions/checkout@{CHECKOUT_SHA}"
        self.assertIn(pinned, text)
        self.assertRejected(
            filename,
            text.replace(pinned, "actions/checkout@v6", 1),
            "actions/checkout doit être épinglé",
        )

    def test_setup_cli_moving_ref_is_rejected(self):
        filename = "sinjira-v25-personal-ai-production-readiness.yml"
        text = self.workflows[filename]
        pinned = f"supabase/setup-cli@{SETUP_CLI_SHA}"
        self.assertIn(pinned, text)
        self.assertRejected(
            filename,
            text.replace(pinned, "supabase/setup-cli@v2", 1),
            "supabase/setup-cli doit être épinglé",
        )

    def test_checkout_without_main_is_rejected(self):
        filename = "sinjira-v25-personal-ai-production-readiness.yml"
        text = self.workflows[filename]
        self.assertIn("          ref: main\n", text)
        self.assertRejected(
            filename,
            text.replace("          ref: main\n", "", 1),
            "checkout production doit forcer ref: main",
        )

    def test_non_main_dispatch_guard_removal_is_rejected(self):
        filename = "sinjira-v25-auth-password-hardening.yml"
        text = self.workflows[filename]
        guard = '          test "$GITHUB_REF" = "refs/heads/main" || {\n'
        self.assertIn(guard, text)
        self.assertRejected(
            filename,
            text.replace(guard, '          test -n "$GITHUB_REF" || {\n', 1),
            "lancement hors main non refusé",
        )

    def test_remote_step_without_scoped_token_is_rejected(self):
        filename = "sinjira-v25-employment-production.yml"
        text = self.workflows[filename]
        marker = "      - name: Vérifier l'historique Emploi en lecture seule\n"
        start = text.index(marker)
        tail = text[start:]
        env_line = "          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n"
        self.assertIn(env_line, tail)
        bad = text[:start] + tail.replace(env_line, "", 1)
        self.assertRejected(filename, bad, "étape utilisant le token sans env borné")

    def test_secret_exposed_to_checkout_is_rejected(self):
        filename = "sinjira-v25-production-deploy.yml"
        text = self.workflows[filename]
        marker = f"        uses: actions/checkout@{CHECKOUT_SHA}"
        bad = text.replace(
            marker,
            marker + "\n        env:\n          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}",
            1,
        )
        self.assertRejected(filename, bad, "secret production exposé à une action réutilisable")


if __name__ == "__main__":
    unittest.main(verbosity=2)
