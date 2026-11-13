"""V50: prototype local de CAS atomique, jamais une migration de production."""
from pathlib import Path
import unittest
import re

ROOT=Path(__file__).resolve().parents[2]
SQL=ROOT/"tests/security/sql"
SETUP=(SQL/"setup_sinjira_reader_v50_cas_local.sql").read_text(encoding="utf-8")
B=(SQL/"test_sinjira_reader_v50_device_b_fresh.sql").read_text(encoding="utf-8")
A=(SQL/"test_sinjira_reader_v50_device_a_stale_rejected.sql").read_text(encoding="utf-8")
RECONCILE=(SQL/"test_sinjira_reader_v50_rls_and_reconcile.sql").read_text(encoding="utf-8")
CODE=(ROOT/"assets/js/sinjira-liseuse-v26.js").read_text(encoding="utf-8")
FAKE_ID="00000000-0000-0000-0000-000000000001"
FAKE_NOVEL="10000000-0000-0000-0000-000000000001"

class CasProofNotProduction(unittest.TestCase):
    def test_no_production_migration_or_real_identity(self):
        all_sql="\n".join(line for sql in (SETUP,B,A,RECONCILE) for line in sql.splitlines() if not line.lstrip().startswith("--"))
        for forbidden in (
            "gpvivleexywljowcqkru","supabase.co","SERVICE_ROLE",
            "supabase db push","apply_migration","postgresql://",
            "CREATE EXTENSION dblink","SECURITY DEFINER",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.lower(),all_sql.lower())
        self.assertIn("BASE JETABLE",SETUP)
        for text in (B,A,RECONCILE):
            self.assertIn(r"\set ON_ERROR_STOP on",text)
            self.assertNotRegex(text,r"(?im)^\s*\\(?:connect|copy|gexec|shell|!)\b")

    def test_server_side_atomic_compare_and_swap(self):
        self.assertIn("SECURITY INVOKER",SETUP)
        self.assertIn("AND local_test_revision=expected_revision",SETUP)
        self.assertIn("local_test_revision=local_test_revision+1",SETUP)
        self.assertIn("user_id=(SELECT auth.uid())",SETUP)
        self.assertIn("GET DIAGNOSTICS changed=ROW_COUNT",SETUP)
        self.assertNotIn("updated_at=excluded.updated_at",SETUP)
        self.assertIn("REVOKE ALL ON FUNCTION",SETUP)
        self.assertIn("FROM PUBLIC,anon",SETUP)
        self.assertIn("TO authenticated",SETUP)

    def test_new_version_is_only_a_disposable_test_column(self):
        self.assertIn("ADD COLUMN local_test_revision bigint",SETUP)
        self.assertIn("CHECK (local_test_revision >= 0)",SETUP)
        self.assertEqual(SETUP.count("ALTER TABLE"),1)
        self.assertIn(FAKE_ID,SETUP)
        self.assertNotIn("CREATE TABLE",SETUP)

    def test_two_sessions_share_owner_and_novel(self):
        for sql in (B,A,RECONCILE):
            self.assertIn(FAKE_ID,sql)
            self.assertIn(FAKE_NOVEL,sql)
            self.assertIn("SET ROLE authenticated;",sql)
        self.assertIn("0,31,60,0.8123",B)
        self.assertIn("0,12,25,0.2100",A)

    def test_stale_request_rejected_without_overwriting_b(self):
        self.assertIn("wrote IS DISTINCT FROM false",A)
        self.assertIn("page<>31 OR ratio<>0.8123 OR rev<>1",A)
        self.assertIn("V50-STALE-REJECTED-PASS",A)

    def test_reconciliation_explicit_not_auto_replay(self):
        self.assertIn("1,33,62,0.8500",RECONCILE)
        self.assertIn("page<>33 OR ratio<>0.8500 OR rev<>2",RECONCILE)
        self.assertIn("V50-RLS-RECONCILE-PASS",RECONCILE)
        self.assertNotIn("service_role",RECONCILE.lower())

    def test_existing_browser_has_not_been_replaced_or_certified(self):
        self.assertIn(".upsert(payload,{onConflict:'user_id,novel_id'})",CODE)
        self.assertNotIn("sinjira_reader_v50_try_save",CODE)
        self.assertIn("V50-SETUP-PASS",SETUP)

if __name__=="__main__":
    unittest.main()
