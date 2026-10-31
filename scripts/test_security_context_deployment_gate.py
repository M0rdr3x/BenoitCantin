#!/usr/bin/env python3
"""Tests négatifs du contrat de déploiement Edge (sans secret ni réseau)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_security_context_deployment_gate import (  # noqa: E402
    EXPECTED_RPC,
    GATE_NAME,
    QUERY,
    SOURCE,
    WORKFLOW,
    validate_contract,
    validate_result,
    validate_source,
    validate_workflow,
)


class EdgeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text("utf-8")
        cls.workflow = WORKFLOW.read_text("utf-8")

    def test_candidate_contract_is_valid(self):
        self.assertEqual(validate_contract(), [])

    def test_response_one_literal_boolean_true_only(self):
        self.assertEqual(validate_result([{"security_context_rpc_ready": True}]), [])

    def test_denies_absent_false_or_malformed(self):
        invalid = (
            [],
            {},
            None,
            [{"security_context_rpc_ready": False}],
            [{"security_context_rpc_ready": 1}],
            [{"security_context_rpc_ready": "true"}],
            [{"security_context_rpc_ready": None}],
            [{"security_context_rpc_ready": True}, {"security_context_rpc_ready": False}],
            [{"security_context_rpc_ready": True, "extra": "unexpected"}],
            [{"error": "forbidden"}],
            {"data": [{"security_context_rpc_ready": True}]},
        )
        for response in invalid:
            with self.subTest(response=repr(response)[:100]):
                self.assertTrue(validate_result(response))

    def test_query_is_metadata_only(self):
        self.assertTrue(QUERY.strip().upper().startswith("SELECT EXISTS"))
        for expected in (
            "pg_catalog.pg_proc", "pg_catalog.pg_namespace",
            "service_security_evaluate_context_session", "security_rebind_service_session",
            "request_session_id", "has_function_privilege('anon'",
            "has_function_privilege('authenticated'", "has_function_privilege('service_role'",
            "fn.prosecdef", "pg_catalog.jsonb",
        ):
            self.assertIn(expected, QUERY)
        self.assertNotIn(";", QUERY, "Un seul SELECT readonly, pas de multi-statement")
        for fragment in ("auth.users", "SELECT *", "INSERT ", "UPDATE ", "DELETE ", "DROP ", "COPY "):
            self.assertNotIn(fragment, QUERY)

    def test_production_source_is_explicit_session_bound(self):
        self.assertEqual(validate_source(self.source), [])

    def test_rejects_legacy_remote_rpc(self):
        bad = self.source.replace(EXPECTED_RPC, "security_evaluate_context")
        self.assertTrue(validate_source(bad))

    def test_rejects_missing_signed_session(self):
        for marker in ("sessionIdFromVerifiedRequest(req)", "p_session_id: sessionId",
                       "await requiredUser(req)", "if (error) throw error;"):
            with self.subTest(marker=marker):
                self.assertTrue(validate_source(self.source.replace(marker, "null", 1)))

    def test_rejects_extra_rpc(self):
        bad = self.source + "\nservice.rpc('security_evaluate_context', {});\n"
        self.assertTrue(validate_source(bad))

    def test_workflow_guard_is_in_approved_sequence(self):
        self.assertEqual(validate_workflow(self.workflow), [])

    def test_workflow_refuses_gate_removal(self):
        start = self.workflow.index("      - name: " + GATE_NAME)
        end = self.workflow.index("\n      - name: ", start + 10)
        self.assertTrue(validate_workflow(self.workflow[:start] + self.workflow[end:]))

    def test_workflow_refuses_gate_after_deploy(self):
        token = "      - name: " + GATE_NAME
        start = self.workflow.index(token)
        end = self.workflow.index("\n      - name: ", start + 10)
        step = self.workflow[start:end]
        bad = (self.workflow[:start] + self.workflow[end:]
               + "\n" + step)
        self.assertTrue(validate_workflow(bad))

    def test_workflow_refuses_write_enabled_query(self):
        self.assertTrue(validate_workflow(
            self.workflow.replace("/database/query/read-only", "/database/query", 1)
        ))

    def test_workflow_refuses_silent_fail(self):
        self.assertTrue(validate_workflow(
            self.workflow.replace("--check-response \"$response\"",
                                  "--check-response \"$response\" || true", 1)
        ))

    def test_workflow_refuses_skip_auth_guard(self):
        marker = ("if: " + chr(36) +
                  "{{ github.event_name == 'workflow_dispatch' && inputs.apply == true && steps.auth.outputs.ready == 'true' }}")
        gate_start = self.workflow.index("      - name: " + GATE_NAME)
        gate_end = self.workflow.index("\n      - name: ", gate_start + 10)
        block = self.workflow[gate_start:gate_end]
        self.assertIn(marker, block)
        self.assertTrue(validate_workflow(self.workflow.replace(block, block.replace(marker, "if: always()"), 1)))

    def test_workflow_refuses_secretless_api(self):
        # Cibler spécifiquement le gate, pas un secret d'un autre job.
        gate_start = self.workflow.index("      - name: " + GATE_NAME)
        gate_end = self.workflow.index("\n      - name: ", gate_start + 10)
        block = self.workflow[gate_start:gate_end]
        changed = block.replace("SUPABASE_ACCESS_TOKEN:", "UNRELATED_TOKEN:", 1)
        self.assertTrue(validate_workflow(self.workflow.replace(block, changed, 1)))

    def test_workflow_refuses_removed_trigger(self):
        marker = "      - 'scripts/test_security_context_deployment_gate.py'\n"
        self.assertEqual(self.workflow.count(marker), 2)
        self.assertTrue(validate_workflow(self.workflow.replace(marker, "", 1)))

    def test_cli_does_not_print_remote_response(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "response.json"
            bad.write_text(json.dumps([{"security_context_rpc_ready": False}]))
            runner = ROOT / "scripts/validate_security_context_deployment_gate.py"
            proc = subprocess.run([sys.executable, str(runner), "--check-response", str(bad)],
                                  capture_output=True, text=True, timeout=5)
            self.assertNotEqual(proc.returncode, 0)
            self.assertNotIn("False", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
