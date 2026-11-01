#!/usr/bin/env python3
"""Execute the actual Bash summary blocks with synthetic values.

GitHub Actions deploy evidence must not use unescaped shell backticks.
No hosting deployment, credentials or network access is involved.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = {
    "github-pages": (
        ROOT / ".github/workflows/deploy-github-pages-isolated.yml",
        "Résumer la frontière de publication",
    ),
    "netlify": (
        ROOT / ".github/workflows/deploy-netlify-staging.yml",
        "Résumer la preuve pré-DNS",
    ),
}

TEST_VARS = {
    "GITHUB_SHA": "0123456789abcdef0123456789abcdef01234567",
    "GITHUB_REF": "refs/heads/main",
    "PAGES_PUBLIC_FILE_COUNT": "1234",
    "NETLIFY_SITE_NAME": "site-test",
    "PREVIEW_PERMALINK": "https://preview--site-test.netlify.app",
    "PRODUCTION_PERMALINK": "https://candidate--site-test.netlify.app",
}
EXPECTED = {
    "github-pages": (
        TEST_VARS["GITHUB_SHA"],
        TEST_VARS["PAGES_PUBLIC_FILE_COUNT"],
        "Source téléversée : _site",
        "Racine du dépôt : **non publiée**",
    ),
    "netlify": (
        TEST_VARS["GITHUB_REF"],
        TEST_VARS["GITHUB_SHA"],
        TEST_VARS["NETLIFY_SITE_NAME"],
        TEST_VARS["PREVIEW_PERMALINK"],
        TEST_VARS["PRODUCTION_PERMALINK"],
        "Promotion production Netlify : **non**",
    ),
}


def summary_shell(source: str, title: str) -> str:
    name = f"- name: {title}"
    start = source.find(name)
    if start < 0:
        raise AssertionError(f"Étape de preuve absente : {title}")
    run_start = source.find("\n        run: |\n", start)
    if run_start < 0:
        raise AssertionError(f"Bloc run Bash absent : {title}")
    lines = source[run_start + len("\n        run: |\n"):].splitlines()
    bash_lines: list[str] = []
    for line in lines:
        if line.startswith("          "):
            bash_lines.append(line[10:])
        else:
            break
    if not bash_lines:
        raise AssertionError("Résumé Bash vide")
    return "\n".join(bash_lines) + "\n"


def execute_summary(script: str) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory(prefix="web-release-shell-") as folder:
        summary = Path(folder) / "step-summary.md"
        env = {**os.environ, **TEST_VARS, "GITHUB_STEP_SUMMARY": str(summary)}
        result = subprocess.run(
            ["bash", "-e", "-u", "-o", "pipefail"],
            input=script, text=True, capture_output=True, env=env, timeout=5,
            check=False,
        )
        return (
            result.returncode,
            result.stderr,
            summary.read_text("utf-8") if summary.is_file() else "",
        )


class ShellDeploymentSummaryTests(unittest.TestCase):
    def test_all_release_proofs_preserve_values_without_running_variables(self):
        for key, (path, title) in WORKFLOWS.items():
            with self.subTest(workflow=key):
                script = summary_shell(path.read_text("utf-8"), title)
                code, stderr, content = execute_summary(script)
                self.assertEqual(code, 0, stderr)
                self.assertEqual(stderr, "", "Le résumé a essayé d'exécuter une commande")
                for value in EXPECTED[key]:
                    self.assertIn(value, content)

    def test_unsafe_markdown_backticks_are_detected(self):
        path, title = WORKFLOWS["github-pages"]
        script = summary_shell(path.read_text("utf-8"), title)
        anchor = '"- SHA approuvé : $GITHUB_SHA"'
        self.assertIn(anchor, script)
        injected = script.replace(anchor, '"- SHA approuvé : `$GITHUB_SHA`"', 1)
        code, stderr, content = execute_summary(injected)
        self.assertTrue(
            code != 0 or stderr or TEST_VARS["GITHUB_SHA"] not in content,
            "Une substitution Bash accidentelle doit être détectée",
        )

    def test_no_shell_substitution_inside_double_quoted_release_proofs(self):
        for key, (path, title) in WORKFLOWS.items():
            with self.subTest(workflow=key):
                script = summary_shell(path.read_text("utf-8"), title)
                for line in script.splitlines():
                    if re.search(r"\b(?:echo|printf)\b", line):
                        self.assertFalse(
                            re.search(r'"[^"\n]*`[^"\n]*"', line),
                            f"Substitution Bash interdite : {line}",
                        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
