"""Tests adversariaux du prévol V47 sur SQL local et migration V32."""
import unittest
from scripts.validate_sinjira_reader_v47_preflight import (
    PREFLIGHT, V32, EXPECTED_CHECKS, validate_sources, validate_files,
)


class SinjiraReaderV47Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = PREFLIGHT.read_text(encoding="utf-8")
        cls.v32 = V32.read_text(encoding="utf-8")

    def assert_bad_sql(self, transform, expected):
        errors = validate_sources(transform(self.sql), self.v32)
        self.assertIn(expected, errors)

    def test_canonical_sources_are_valid(self):
        self.assertEqual(validate_files(), [])

    def test_exactly_eleven_checks(self):
        self.assertEqual(len(EXPECTED_CHECKS), 11)
        self.assertIn("reader_release_decision", EXPECTED_CHECKS)

    def test_refuse_ddl_insertion(self):
        self.assert_bad_sql(lambda s: s+"\nALTER TABLE public.sinjira_reader_library DROP COLUMN user_id;",
                            "MUTATION_SQL_PRESENT")

    def test_refuse_sensitive_user_rows(self):
        self.assert_bad_sql(lambda s: s.replace("FROM checks\nUNION ALL", "FROM public.sinjira_reader_library\nUNION ALL"),
                            "NON_METADATA_SOURCE")

    def test_refuse_renouncing_owner_policy(self):
        self.assert_bad_sql(lambda s: s.replace("reader_single_owner_policy", "reader_unchecked_policy", 1),
                            "RELEASE_CHECK_INVENTORY_CHANGED")

    def test_refuse_lost_release_gate(self):
        self.assert_bad_sql(lambda s: s.replace(
            "CASE WHEN EXISTS(SELECT 1 FROM checks WHERE status='BLOCK')",
            "CASE WHEN false",
        ), "NO_FAIL_CLOSED_GATE")

    def test_refuse_go_without_approval(self):
        self.assert_bad_sql(lambda s: s.replace("THEN 'NO_GO' ELSE 'REVIEW_REQUIRED'",
                                                   "THEN 'GO' ELSE 'GO'"),
                            "UNSUPPORTED_GO_STATUS")

    def test_refuse_undisclosed_anon_grants(self):
        self.assert_bad_sql(lambda s: s.replace("reader_anon_direct_grants", "reader_grants_ok", 1),
                            "RELEASE_CHECK_INVENTORY_CHANGED")

    def test_refuse_changed_column_type(self):
        migration = self.v32.replace("scroll_ratio numeric(5,4)", "scroll_ratio numeric(2,1)")
        self.assertIn("V32_MIGRATION_DRIFT",validate_sources(self.sql, migration))

    def test_refuse_removed_null_compatibility(self):
        migration = self.v32.replace("scroll_ratio is null or ", "")
        self.assertIn("V32_BOUNDS_DRIFT",validate_sources(self.sql, migration))

    def test_refuse_expanded_ratio_bounds(self):
        migration = self.v32.replace("scroll_ratio <= 1", "scroll_ratio <= 2")
        self.assertIn("V32_BOUNDS_DRIFT",validate_sources(self.sql, migration))

    def test_refuse_second_statement(self):
        self.assert_bad_sql(lambda s: s+"\nSELECT current_user;", "MULTI_STATEMENT")

    def test_refuse_absent_catalogue_source(self):
        self.assert_bad_sql(lambda s: s.replace("FROM pg_class", "FROM auth.users"),
                            "NON_METADATA_SOURCE")

    def test_refuse_production_dsn(self):
        self.assert_bad_sql(lambda s: s+"\n-- postgresql://database.example.com:5432",
                            "PRODUCTION_CONNECTION_ARTIFACT")

    def test_refuse_deleting_range_gate(self):
        self.assert_bad_sql(lambda s: s.replace("SELECT 'reader_scroll_ratio_range'", "SELECT 'reader_no_range'"),
                            "RELEASE_CHECK_INVENTORY_CHANGED")

    def test_comments_can_explain_rules_without_mutating_database(self):
        self.assertEqual(validate_sources(self.sql+"\n-- CREATE or ALTER is forbidden here",self.v32), [])


if __name__ == "__main__":
    unittest.main()
