#!/usr/bin/env python3
"""Tests du périmètre Actions : injection, élévation et dérive de dépendances."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_github_workflow_trust_boundary import (  # noqa: E402
    WORKFLOWS, check_repository, violations,
)

PIN = "d23441a48e516b6c34aea4fa41551a30e30af803"
BASE = (
    "name: Audit\n"
    "on:\n"
    "  pull_request:\n"
    "    branches: [main]\n"
    "permissions:\n"
    "  contents: read\n"
    "jobs:\n"
    "  audit:\n"
    "    runs-on: ubuntu-24.04\n"
    "    steps:\n"
    f"      - uses: actions/checkout@{PIN}\n"
    "        with:\n"
    "          persist-credentials: false\n"
    "      - run: echo 'pass'\n"
)


PAGES_SAFE = (
    "name: Confinement Pages\n"
    "on:\n"
    "  workflow_dispatch:\n"
    "    inputs:\n"
    "      expected_sha:\n"
    "        required: true\n"
    "permissions:\n"
    "  contents: read\n"
    "jobs:\n"
    "  build:\n"
    "    steps:\n"
    "      - run: python3 scripts/build_netlify_public.py --output _site --security-containment\n"
    "      - uses: actions/upload-pages-artifact@56afc609e74202658d3ffba0e8f6dda462b719fa\n"
    "        with:\n"
    "          path: _site\n"
    "  deploy:\n"
    "    needs: build\n"
    "    if: github.ref == 'refs/heads/main' && inputs.confirm_containment == 'CONTAIN' && inputs.acknowledge_header_gap == 'ACK_HEADER_GAP'\n"
    "    permissions:\n"
    "      pages: write\n"
    "      id-token: write\n"
    "    environment:\n"
    "      name: github-pages\n"
    "    steps:\n"
    "      - uses: actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346\n"
)


class WorkflowTrustBoundaryTests(unittest.TestCase):
    def test_full_repository_baseline(self):
        self.assertEqual(check_repository(), [])

    def test_safe_workflow_accepted(self):
        self.assertEqual(violations("audit.yml", BASE), [])

    def test_pull_request_target_is_forbidden(self):
        self.assertTrue(violations("audit.yml", BASE.replace(
            "  pull_request:\n", "  pull_request_target:\n"
        )))

    def test_workflow_run_privileged_event_is_forbidden(self):
        self.assertTrue(violations("audit.yml", BASE.replace(
            "  pull_request:\n", "  workflow_run:\n"
        )))

    def test_unpinned_external_action_is_forbidden(self):
        for mutation in (
            "actions/checkout@v6",
            "actions/checkout@main",
            "actions/checkout@d23441a48e",
            "org/action",
            "docker://alpine:latest",
        ):
            with self.subTest(action=mutation):
                self.assertTrue(violations("audit.yml", BASE.replace(
                    f"actions/checkout@{PIN}", mutation
                )))

    def test_local_action_is_allowed(self):
        self.assertEqual(violations("audit.yml", BASE.replace(
            f"actions/checkout@{PIN}", "./.github/actions/internal"
        )), [])

    def test_global_write_forbidden(self):
        self.assertTrue(violations("audit.yml", BASE.replace(
            "  contents: read", "  contents: write"
        )))
        self.assertTrue(violations("audit.yml", BASE.replace(
            "permissions:\n  contents: read", "permissions: write-all"
        )))

    def test_unreviewed_job_write_forbidden(self):
        modified = BASE.replace(
            "    runs-on:", "    permissions:\n      contents: write\n    runs-on:"
        )
        self.assertTrue(violations("audit.yml", modified))

    def test_nominal_write_job_is_strictly_named(self):
        modified = BASE.replace(
            "    runs-on:", "    permissions:\n      contents: write\n    runs-on:"
        ).replace("  audit:", "  commit:")
        self.assertEqual(violations("nova-seo-normalize.yml", modified), [])
        self.assertTrue(violations("other.yml", modified))

    def test_global_oidc_write_forbidden(self):
        self.assertTrue(violations("audit.yml", BASE.replace(
            "  contents: read", "  id-token: write\n  contents: read"
        )))

    def test_job_oidc_write_forbidden(self):
        self.assertTrue(violations("audit.yml", BASE.replace(
            "    runs-on:", "    permissions:\n      id-token: write\n    runs-on:"
        )))

    def test_missing_global_permissions_forbidden(self):
        self.assertTrue(violations("audit.yml", BASE.replace(
            "permissions:\n  contents: read\n", ""
        )))

    def test_inline_yaml_events_are_refused(self):
        self.assertTrue(violations("audit.yml", BASE.replace(
            "on:\n  pull_request:\n    branches: [main]",
            "on: [pull_request_target]"
        )))
        self.assertTrue(violations("audit.yml", BASE.replace(
            "on:\n  pull_request:\n    branches: [main]",
            "on: {workflow_run: {workflows: [deploy]}}"
        )))

    def test_inline_job_permission_cannot_escape_parser(self):
        self.assertTrue(violations("audit.yml", BASE.replace(
            "    runs-on:", "    permissions: {contents: write}\n    runs-on:"
        )))

    def test_duplicate_global_permissions_are_refused(self):
        self.assertTrue(violations("audit.yml", BASE.replace(
            "permissions:\n  contents: read",
            "permissions:\n  contents: read\npermissions:\n  contents: write"
        )))


    def test_pages_oidc_exception_is_exact_and_restricted(self):
        self.assertEqual(violations("deploy-github-pages-isolated.yml", PAGES_SAFE), [])
        self.assertTrue(violations("other.yml", PAGES_SAFE))
        self.assertTrue(violations("deploy-github-pages-isolated.yml",
                                   PAGES_SAFE.replace("  workflow_dispatch:", "  push:")))

    def test_pages_refuses_executing_code_under_deploy_token(self):
        self.assertTrue(violations("deploy-github-pages-isolated.yml",
            PAGES_SAFE.replace("    environment:",
                               "    steps:\n      - run: curl https://example.invalid\n    environment:")))
        self.assertTrue(violations("deploy-github-pages-isolated.yml",
            PAGES_SAFE.replace("    needs: build", "    needs: other")))

    def test_pages_refuses_extra_oidc_and_unpinned_deploy_action(self):
        self.assertTrue(violations("deploy-github-pages-isolated.yml",
            PAGES_SAFE.replace("      id-token: write", "      id-token: write\n      id-token: write")))
        self.assertTrue(violations("deploy-github-pages-isolated.yml",
            PAGES_SAFE.replace("actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346",
                               "actions/deploy-pages@v4")))

    def test_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)
            for i in range(90):
                (path / f"workflow-{i}.yml").write_text(BASE, "utf-8")
            self.assertEqual(check_repository(path), [])
            (path / "workflow-1.yml").unlink()
            (path / "workflow-1.yml").symlink_to(path / "workflow-2.yml")
            self.assertTrue(check_repository(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
