#!/usr/bin/env python3
"""Regression tests for historical PR secret scanning; no real secrets."""
from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts import validate_pr_commit_secrets as audit


class HistoricalSecretsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "ci@example.invalid")
        self.git("config", "user.name", "Synthetic CI")
        (self.repo / "README.md").write_text("Public test fixture\n", encoding="utf-8")
        self.commit("Initial synthetic baseline")
        self.base = self.rev()

    def git(self, *args):
        p = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=True,
        )
        return p.stdout.decode("utf-8").strip()

    def rev(self):
        return self.git("rev-parse", "HEAD")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def test_secret_env_removed_from_final_tree_is_still_rejected(self):
        marker = self.repo / ".env.production"
        # No token, password or legitimate secret is ever written by the test.
        marker.write_text("SYNTHETIC_PLACEHOLDER=not_a_secret\n", encoding="utf-8")
        self.commit("Add prohibited env file")
        marker.unlink()
        self.commit("Remove env file before PR")
        commits, files, findings = audit.inspect_range(
            self.repo, self.base, self.rev())
        self.assertEqual(commits, 2)
        self.assertEqual(files, 1)
        self.assertEqual(len(findings), 1)
        self.assertIn(".env.production", findings[0])
        self.assertNotIn("SYNTHETIC_PLACEHOLDER", findings[0])

    def test_regular_changes_across_commits_are_allowed(self):
        (self.repo / "README.md").write_text("Updated public fixture\n", encoding="utf-8")
        self.commit("Change README")
        (self.repo / "docs.md").write_text("Public documentation\n", encoding="utf-8")
        self.commit("Add docs")
        commits, files, findings = audit.inspect_range(
            self.repo, self.base, self.rev())
        self.assertEqual((commits, files), (2, 2))
        self.assertEqual(findings, [])

    def test_removed_symlink_from_commit_history_is_rejected(self):
        link = self.repo / "legacy-link.txt"
        link.symlink_to("README.md")
        self.commit("Add symlink")
        link.unlink()
        self.commit("Remove symlink")
        _, _, findings = audit.inspect_range(
            self.repo, self.base, self.rev())
        self.assertEqual(len(findings), 1)
        self.assertIn("lien symbolique", findings[0])

    def test_history_limit_fails_closed_instead_of_silently_truncating(self):
        (self.repo / "README.md").write_text("Phase one\n", encoding="utf-8")
        self.commit("Change one")
        (self.repo / "README.md").write_text("Phase two\n", encoding="utf-8")
        self.commit("Change two")
        with self.assertRaisesRegex(ValueError, "trop long"):
            audit.inspect_range(self.repo, self.base, self.rev(), max_commits=1)

    def test_invalid_sha_is_rejected_before_git_commands(self):
        (self.repo / "README.md").write_text("one\n", encoding="utf-8")
        self.commit("Change")
        for invalid in (
            "main", "../main", self.rev() + ";rm -rf .", "abc123",
            "z" * 40,
        ):
            with self.subTest(invalid=invalid[:20]):
                with self.assertRaisesRegex(ValueError, "SHA"):
                    audit.inspect_range(self.repo, invalid, self.rev())

    def test_no_commit_changes_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Aucun commit"):
            audit.inspect_range(self.repo, self.base, self.base)


if __name__ == "__main__":
    unittest.main(verbosity=2)
