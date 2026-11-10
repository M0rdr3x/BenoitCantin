"""Contrat V50 : révéler un écrasement possible, proposer un CAS de laboratoire.

N'atteste jamais Supabase production, les JWT réels ou deux appareils physiques.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SQL=(ROOT/"tests/security/sql/test_sinjira_reader_v50_stale_overwrite.sql").read_text(encoding="utf-8")
JS=(ROOT/"assets/js/sinjira-liseuse-v26.js").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/sinjira-reader-v50-cas-lab.yml").read_text(encoding="utf-8")

class V50NoProduction(unittest.TestCase):
    def test_current_client_has_unconditional_upsert_race(self):
        self.assertIn(".upsert(payload,{onConflict:'user_id,novel_id'})",JS)
        self.assertIn("shouldReplayReadingProgress",JS)
        self.assertNotIn("v50_lab_revision",JS)
        self.assertIn("V50-RISK-REPRODUCED",SQL)
    def test_guard_checks_exact_disposable_database_before_any_changes(self):
        self.assertIn("current_database()<>'sinjira_reader_v50_lab'",SQL)
        self.assertLess(SQL.index("current_database()"),SQL.index("CREATE TEMP TABLE"))
        self.assertLess(SQL.index("current_database()"),SQL.index("ALTER TABLE"))
    def test_simulates_newer_then_stale_write_by_same_fictional_identity(self):
        self.assertIn("last_page=42,progress_percent=75,scroll_ratio=0.8250",SQL)
        self.assertIn("last_page=13,progress_percent=28,scroll_ratio=1.0000",SQL)
        self.assertIn("ON CONFLICT (user_id,novel_id) DO UPDATE SET",SQL)
        self.assertIn("stamp>=now()+interval '1 minute'",SQL)
    def test_cas_prototype_rejects_stale_without_mistaking_for_production_fix(self):
        self.assertIn("ADD COLUMN v50_lab_revision bigint NOT NULL DEFAULT 0",SQL)
        self.assertIn("AND v50_lab_revision=0",SQL)
        self.assertIn("IF changed<>0 THEN",SQL)
        self.assertIn("IF page<>42 OR rev<>1 THEN",SQL)
        self.assertIn("AND v50_lab_revision=1",SQL)
        self.assertIn("IF page<>43 OR rev<>2 THEN",SQL)
    def test_other_account_is_not_overwritten_in_lab(self):
        self.assertIn("SET ROLE authenticated;",SQL)
        self.assertIn("SELECT auth.uid()",SQL)
        self.assertIn("00000000-0000-0000-0000-000000000002",SQL)
        self.assertIn("IF count_bad<>0 THEN",SQL)
    def test_does_not_import_private_content_or_real_credentials(self):
        for bad in ("supabase.co","postgresql://","service_role_key",
                    "supabase_db_password","supabase db push","apply_migration",
                    "https://","http://","gpvivleexywljowcqkru"):
            with self.subTest(bad=bad):
                self.assertNotIn(bad,SQL.lower())
        self.assertIn("jamais Supabase",SQL)
    def test_ci_executes_existing_v48_first_then_v50_only_local(self):
        self.assertIn("postgres:17.6",WF)
        self.assertIn("POSTGRES_DB: sinjira_reader_v50_lab",WF)
        self.assertIn("'127.0.0.1:5432:5432'",WF)
        self.assertIn("permissions:\n  contents: read",WF)
        self.assertIn("persist-credentials: false",WF)
        self.assertLess(WF.index("test_sinjira_reader_v48_client_a_return.sql"),
                        WF.index("test_sinjira_reader_v50_stale_overwrite.sql"))
    def test_no_false_go_when_cas_lab_passes(self):
        self.assertIn("V50-NO_GO-PRODUCTION",SQL)
        self.assertNotIn("reader_v32_prod=PASS",SQL)
        self.assertNotIn("reader_two_devices=PASS",SQL)
        self.assertIn("test_sinjira_reader_v50_cas_lab.py",WF)

if __name__=="__main__":
    unittest.main()
