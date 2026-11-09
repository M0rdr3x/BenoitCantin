"""NOVA sondage V7 — vérification statique des tests PostgreSQL éphémères.

Aucun réseau, jeton de vote réel, compte, collecte d'opinions ou secret.
N'équivaut PAS à la réception d'un audit de confidentialité en préproduction.
"""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DIR=ROOT/"tests/security/sql"
SCHEMA=(ROOT/"supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql").read_text(encoding="utf-8")
SETUP=(DIR/"nova_poll_v7_lab_setup.sql").read_text(encoding="utf-8")
SECURITY=(DIR/"nova_poll_v7_security_replay.sql").read_text(encoding="utf-8")
BATCHES=(DIR/"nova_poll_v7_private_batches.sql").read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github/workflows/nova-poll-v7-sql-private-lab.yml").read_text(encoding="utf-8")


class DisposablePrivacyContract(unittest.TestCase):
    def test_uses_original_schema_in_disposable_database_only(self):
        self.assertIn(r"\i supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql",SETUP)
        self.assertIn("BASE TEMPORAIRE",SETUP)
        self.assertIn("postgres:17.6",WORKFLOW)
        self.assertIn("127.0.0.1",WORKFLOW)
        self.assertIn("nova_poll_v7_disposable",WORKFLOW)

    def test_no_external_secrets_or_live_vote_endpoint(self):
        combined="\n".join([SETUP,SECURITY,BATCHES,WORKFLOW])
        for forbidden in (
            "gpvivleexywljowcqkru","supabase.co/functions/",
            "https://www.benoitcantin.com/projets/projet-nova/sondage",
            "SUPABASE_SERVICE_ROLE_KEY","NOVA_POLL_TURNSTILE_SECRET",
            "NOVA_POLL_HMAC_KEY","postgresql://","supabase db push",
            "apply_migration","curl ","wget ","service_role_key",
        ):
            with self.subTest(token=forbidden):
                self.assertNotIn(forbidden.lower(),combined.lower())

    def test_no_sql_changes_to_project_migration(self):
        self.assertIn("BEGIN;",SCHEMA)
        self.assertIn("COMMIT;",SCHEMA)
        self.assertIn("REVOKE ALL ON FUNCTION public.nova_poll_submit",SCHEMA)
        self.assertIn("TO service_role;",SCHEMA)
        for f in (SECURITY,BATCHES):
            self.assertNotIn("CREATE OR REPLACE FUNCTION",f)
            self.assertNotIn("ALTER TABLE",f)
            self.assertNotIn("DROP TABLE",f)

    def test_sql_guards_reject_duplicate_and_incomplete_ballot(self):
        self.assertIn("state<>'duplicate'",SECURITY)
        self.assertIn("WHEN SQLSTATE '22023'",SECURITY)
        self.assertIn("q99",SECURITY)
        self.assertIn("q02\":8",SECURITY)
        self.assertIn("nova_poll_receipts",SECURITY)

    def test_sql_privileges_and_rls_probed_for_real_in_lab(self):
        for token in (
            "has_function_privilege('anon'","has_function_privilege('authenticated'",
            "has_table_privilege('anon'","has_table_privilege('authenticated'",
            "c.relrowsecurity","SET ROLE anon;","SET ROLE service_role;",
        ):
            self.assertIn(token,SECURITY)

    def test_publish_rules_from_original_sql_not_fake_summary(self):
        for marker in (
            "v_total_ballots >= 10",
            "v_total_ballots - v_published_ballots >= 10",
            "now() - v_published_at >= interval '6 hours'",
            "current_count.total - COALESCE(previous_count.total,0) < 5",
            "SELECT published_ballots,published_at",
            "FOR UPDATE",
        ):
            self.assertIn(marker,SCHEMA)

    def test_batch_9_to_1_is_blocked_and_9_to_5_is_allowed(self):
        self.assertIn("i=20 THEN -1 ELSE -2",BATCHES)
        self.assertIn("IF v<>10 THEN",BATCHES)
        self.assertIn("IF v<>24 THEN",BATCHES)
        self.assertIn("option_value=-2 AND total=19",BATCHES)
        self.assertIn("option_value=-1 AND total=5",BATCHES)

    def test_six_hour_gate_is_tested_in_real_sql(self):
        self.assertIn("published_at=now()-interval '7 hours'",BATCHES)
        self.assertIn("V7: lot publié sans délai de six heures",BATCHES)
        self.assertIn("V7: lot après six heures non publié",BATCHES)

    def test_fixtures_are_synthetic_not_political_users(self):
        self.assertIn("ENTIÈREMENT",SECURITY.replace("intégralement","ENTIÈREMENT"))
        self.assertIn("fictif",SECURITY.lower())
        self.assertIn("TRUNCATE public.nova_poll_counts",BATCHES)
        self.assertIn("jetable",BATCHES.lower())
        self.assertIn("repeat(lpad(to_hex(i),2,'0'),32)",SECURITY)

    def test_workflow_is_readonly_and_ordered(self):
        self.assertIn("permissions:\n  contents: read",WORKFLOW)
        self.assertIn("persist-credentials: false",WORKFLOW)
        self.assertIn("actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",WORKFLOW)
        self.assertIn("nova_poll_v7_lab_setup.sql",WORKFLOW)
        first=WORKFLOW.index("nova_poll_v7_lab_setup.sql")
        security=WORKFLOW.index("nova_poll_v7_security_replay.sql")
        batches=WORKFLOW.index("nova_poll_v7_private_batches.sql")
        self.assertLess(first,security)
        self.assertLess(security,batches)

    def test_no_approval_or_score_change_in_test_payload(self):
        self.assertNotIn("opening_poll_approved",SECURITY+BATCHES)
        self.assertNotIn("published:true",SECURITY+BATCHES)
        self.assertNotIn("NOVA_POLL_ENABLED",SECURITY+BATCHES)
        self.assertNotIn("POLL_PRIVATE_PREFLIGHT\":\"PASSED",SECURITY+BATCHES)


if __name__=="__main__":
    unittest.main()
