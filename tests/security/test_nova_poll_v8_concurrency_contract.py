"""NOVA V8 : contrat des essais concurrents strictement locaux et fictifs."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=(ROOT/"scripts/test_nova_poll_v8_concurrent_local.sh").read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github/workflows/validate-nova-civic-poll.yml").read_text(encoding="utf-8")
SCHEMA=(ROOT/"supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql").read_text(encoding="utf-8")

class V8ConcurrencyNoLivePoll(unittest.TestCase):
    def test_server_database_fixed_and_asserted_before_reset(self):
        self.assertIn('DB="nova_poll_v7_disposable"',SCRIPT)
        self.assertIn('HOST="127.0.0.1"',SCRIPT)
        self.assertIn('actual="$(db -c',SCRIPT)
        self.assertIn('if [[ "$actual" != "nova_poll_v7_disposable:127.0.0.1" ]]',SCRIPT)
        self.assertLess(SCRIPT.index('actual="$(db -c'),SCRIPT.index('reset_fixture\n'))
    def test_no_network_remote_secrets_or_real_voters(self):
        for word in ("supabase.co","https://","curl ","wget ","PGPASSWORD",
                     "SERVICE_ROLE_KEY","NOVA_POLL_HMAC_KEY","NOVA_POLL_ENABLED",
                     "NOVA_POLL_APPROVED_VERSION","db push","apply_migration"):
            with self.subTest(word=word):
                self.assertNotIn(word.lower(),SCRIPT.lower())
        self.assertIn("JETABLE",SCRIPT)
        self.assertIn("vote réel",SCRIPT)
    def test_same_token_two_sessions_one_receipt(self):
        self.assertIn("submit_fake duplicate_1",SCRIPT)
        self.assertIn("submit_fake duplicate_2",SCRIPT)
        self.assertIn('wait "$pid1"',SCRIPT)
        self.assertIn('wait "$pid2"',SCRIPT)
        self.assertIn('"accepted" && "$two" == "duplicate"',SCRIPT)
        self.assertIn('"duplicate" ]]; }; then',SCRIPT)
        self.assertIn("public.nova_poll_receipts)<>1",SCRIPT)
        self.assertIn("public.nova_poll_counts)<>8",SCRIPT)
    def test_distinct_tokens_sixteen_sessions_and_rollback_privacy(self):
        self.assertIn("for i in $(seq 1 16); do",SCRIPT)
        self.assertIn("pids=\"\"",SCRIPT)
        self.assertIn('wait "$p"',SCRIPT)
        self.assertIn("public.nova_poll_receipts",SCRIPT)
        self.assertIn("n<>16",SCRIPT)
        self.assertIn("published<10 OR published>16",SCRIPT)
    def test_snapshot_consistency_checks_eight_questions(self):
        self.assertIn("published_rows<>8",SCRIPT)
        self.assertIn("total=published",SCRIPT)
        self.assertIn("total=16",SCRIPT)
        self.assertIn("check_output \"unique_$i\" \"accepted\"",SCRIPT)
        self.assertIn("ON CONFLICT(poll_version,question_id,option_value)",SCHEMA)
    def test_single_temporary_database_not_real_poll_schema_change(self):
        self.assertIn("TRUNCATE public.nova_poll_counts",SCRIPT)
        self.assertIn("UPDATE public.nova_poll_publication_state",SCRIPT)
        self.assertIn('DB="nova_poll_v7_disposable"',SCRIPT)
        for prohibited in ("CREATE TABLE","ALTER TABLE","DROP TABLE",
                           "CREATE OR REPLACE FUNCTION","SECURITY DEFINER"):
            self.assertNotIn(prohibited,SCRIPT)
    def test_ci_runs_after_schema_and_sequential_privacy_tests(self):
        self.assertIn("scripts/test_nova_poll_v8_concurrent_local.sh",WORKFLOW)
        self.assertIn("test_nova_poll_v8_concurrency_contract.py",WORKFLOW)
        self.assertLess(WORKFLOW.index("nova_poll_v7_private_batches.sql"),
                        WORKFLOW.index("bash scripts/test_nova_poll_v8_concurrent_local.sh"))
        self.assertIn("postgres:17.6",WORKFLOW)
        self.assertIn("persist-credentials: false",WORKFLOW)
    def test_test_does_not_promote_release_gate(self):
        self.assertIn("NOVA-V8-LAB-ONLY-NO_GO",SCRIPT)
        self.assertNotIn("POLL_CAPTCHA_ANTIREPLAY=PASSED",SCRIPT)
        self.assertNotIn("POLL_PRIVATE_PREFLIGHT=PASSED",SCRIPT)
        self.assertNotIn("published:true",SCRIPT)

if __name__=="__main__":
    unittest.main()
