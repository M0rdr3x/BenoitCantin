"""SINJIRA V49 — contrat du banc PostgreSQL local de migration V32 répétable.

L'attestation de production, des droits de lecture réels et du login
multiappareils sont EXCLUES de ce contrat de tests.
"""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
V49=(ROOT/"tests/security/sql/test_sinjira_reader_v49_repeat_v32.sql").read_text(encoding="utf-8")
V32=(ROOT/"supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/sinjira-reader-v48-multisession.yml").read_text(encoding="utf-8")

class MigrationV49LocalOnly(unittest.TestCase):
    def test_real_migration_replayed_twice_after_v48(self):
        self.assertEqual(V49.count(r"\i supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql"),2)
        self.assertIn("add column if not exists scroll_ratio numeric(5,4)",V32.lower())
        self.assertIn("sinjira_reader_library_scroll_ratio_range",V32)
        self.assertLess(WF.index("test_sinjira_reader_v48_client_a_return.sql"),
                        WF.index("test_sinjira_reader_v49_repeat_v32.sql"))
    def test_refuse_other_database_before_changes(self):
        self.assertIn("current_database()<>'sinjira_reader_v48_test_only'",V49)
        self.assertLess(V49.index("current_database()"),V49.index("INSERT INTO public.sinjira_reader_library"))
        self.assertIn("RLS absente avant répétition",V49)
    def test_exact_three_dummy_bookmarks_and_timestamps(self):
        for tok in ("CREATE TEMP TABLE v49_before AS","created_at,updated_at,last_opened_at",
                    "last_page=13 AND progress_percent=28 AND scroll_ratio=1.0000",
                    "last_page=8 AND progress_percent=35 AND scroll_ratio=0.2500",
                    "IF n<>3 THEN","EXCEPT","scroll_ratio IS NULL"):
            with self.subTest(tok=tok):self.assertIn(tok,V49)
    def test_rls_and_other_user_isolation_after_replay(self):
        for tok in ("SET ROLE authenticated;","SET ROLE anon;",
                    "policyname='sinjira reader library own'",
                    "GET DIAGNOSTICS affected=ROW_COUNT",
                    "IF affected<>0 THEN","RLS conservées",
                    "WHERE user_id='00000000-0000-0000-0000-000000000002'"):
            with self.subTest(tok=tok):self.assertIn(tok,V49)
    def test_no_remote_endpoint_identity_password_or_secrets(self):
        for bad in ("supabase.co","gpvivleexywljowcqkru",
                    "postgresql://","service_role_key","pgpassword",
                    "http://","https://","supabase db push","apply_migration"):
            with self.subTest(bad=bad):self.assertNotIn(bad,V49.lower())
    def test_only_fictional_users_and_not_real_book_text(self):
        self.assertIn("JAMAIS",V49)
        self.assertIn("00000000-0000-0000-0000-000000000001",V49)
        self.assertIn("00000000-0000-0000-0000-000000000002",V49)
        self.assertIn("10000000-0000-0000-0000-000000000002",V49)
        self.assertNotIn("INSERT INTO public.sinjira_novels",V49)
    def test_contract_does_not_claim_go_or_modify_live_gate(self):
        self.assertIn("V49-REPEAT-V32-PASS",V49)
        self.assertNotIn("reader_v32_prod=PASS",V49)
        self.assertNotIn("reader_two_devices=PASS",V49)
        self.assertNotIn("GO_LIVE",V49)
        self.assertIn("permissions:\n  contents: read",WF)
        self.assertIn("persist-credentials: false",WF)

if __name__=="__main__":
    unittest.main()
