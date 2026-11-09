"""SINJIRA V48 — protéger la recette isolée des lecteurs contre une dérive dangereuse."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql"
TESTS = ROOT / "tests/security/sql"
SETUP = TESTS / "setup_sinjira_reader_v48.sql"
CLIENT_A = TESTS / "test_sinjira_reader_v48_client_a.sql"
CLIENT_B = TESTS / "test_sinjira_reader_v48_client_b.sql"
RETURN_A = TESTS / "test_sinjira_reader_v48_client_a_return.sql"


class ReaderV48IsolatedSecurityContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = SETUP.read_text(encoding="utf-8")
        cls.client_a = CLIENT_A.read_text(encoding="utf-8")
        cls.client_b = CLIENT_B.read_text(encoding="utf-8")
        cls.return_a = RETURN_A.read_text(encoding="utf-8")
        cls.migration = MIGRATION.read_text(encoding="utf-8")

    def test_the_original_migration_is_used_without_rewriting_it(self):
        self.assertEqual(self.setup.count(
            r"\i supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql"
        ), 1)
        self.assertRegex(
            self.migration,
            r"(?i)add\s+column\s+if\s+not\s+exists\s+scroll_ratio\s+numeric\(5,4\)",
        )
        self.assertIn("sinjira_reader_library_scroll_ratio_range", self.migration)

    def test_setup_has_real_rls_and_both_checks(self):
        s = self.setup.lower()
        for phrase in (
            "enable row level security",
            'create policy "sinjira reader library own"',
            "using ((select auth.uid()) = user_id)",
            "with check ((select auth.uid()) = user_id)",
            "foreign key",  # as table FK columns, not separately in the fixture
        ):
            if phrase == "foreign key":
                self.assertIn("references auth.users", s)
                self.assertIn("references public.sinjira_novels", s)
            else:
                self.assertIn(phrase, s)
        self.assertIn("PRIMARY KEY(user_id,novel_id)", self.setup)
        self.assertIn("GRANT SELECT,INSERT,UPDATE,DELETE", self.setup)
        self.assertIn("scroll_ratio IS NULL", self.setup)

    def test_three_independent_client_sql_scripts(self):
        self.assertIn("SET ROLE authenticated;", self.client_a)
        self.assertIn("SET ROLE authenticated;", self.client_b)
        self.assertIn("SET ROLE authenticated;", self.return_a)
        self.assertIn("00000000-0000-0000-0000-000000000001", self.client_a)
        self.assertIn("00000000-0000-0000-0000-000000000002", self.client_b)
        self.assertIn("00000000-0000-0000-0000-000000000001", self.return_a)
        self.assertIn("V48-CLIENT-A-PASS", self.client_a)
        self.assertIn("V48-CLIENT-B-PASS", self.client_b)
        self.assertIn("V48-REPRISE-PASS", self.return_a)

    def test_attacks_are_explicit_and_fail_closed(self):
        self.assertIn("WHEN check_violation", self.client_a)
        self.assertIn("WHEN insufficient_privilege", self.client_b)
        self.assertIn("GET DIAGNOSTICS affected=ROW_COUNT", self.client_b)
        self.assertIn("SET ROLE anon;", self.client_b)
        self.assertIn("IF n<>0 THEN RAISE EXCEPTION", self.client_b)
        self.assertIn("scroll_ratio=0.5678", self.return_a)
        self.assertIn("scroll_ratio=1.0000", self.return_a)

    def test_no_real_identifiers_credentials_or_remote_connections(self):
        combined = "\n".join((self.setup,self.client_a,self.client_b,self.return_a))
        for token in (
            "gpvivleexywljowcqkru", "supabase.co",
            "service_role_key", "SUPABASE_DB_PASSWORD",
            "postgresql://", "AUTHORIZATION: Bearer",
            "db push", "apply_migration", "CREATE EXTENSION dblink",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token.lower(), combined.lower())
        self.assertFalse(re.search(r"(?i)https?://", combined))
        self.assertIn("Aucun", self.return_a.replace("aucun", "Aucun") if "aucun" in self.return_a else self.setup)

    def test_all_commands_are_local_only(self):
        for source in (self.setup,self.client_a,self.client_b,self.return_a):
            self.assertIn(r"\set ON_ERROR_STOP on", source)
            self.assertNotRegex(source, r"(?im)^\s*\\(?:connect|copy|gexec|shell|!)\b")
            self.assertNotRegex(source, r"(?i)\b(?:pg_read_file|lo_import|pg_ls_dir)\s*\(")
        self.assertNotIn("DROP TABLE", self.setup.upper())
        self.assertNotIn("DROP SCHEMA", self.setup.upper())

    def test_own_row_only_and_legacy_null_compatibility(self):
        self.assertIn("ON CONFLICT (user_id,novel_id) DO UPDATE",self.client_a)
        self.assertIn("ratio IS NOT NULL",self.client_a)
        self.assertIn("ratio IS NOT NULL",self.client_b)
        self.assertIn("ratio<>0.5678",self.return_a)

    def test_anon_access_is_denied_even_with_direct_grant(self):
        self.assertIn("TO anon, authenticated",self.setup)
        self.assertIn("SET ROLE anon;",self.client_b)
        self.assertIn("WHERE user_id='00000000-0000-0000-0000-000000000001'",self.client_b)


if __name__ == "__main__":
    unittest.main()
