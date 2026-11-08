"""Contrat statique V45 — aucune action autre que dix permissions RPC ciblées."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "scripts/proposals/sinjira_fracture_v45_mutation_rpc_quarantine_candidate.sql"
TEST_SQL = ROOT / "tests/security/sql/test_fracture_rpc_quarantine_v45.sql"
TARGETS = {
    f"{schema}.{name}({args})"
    for schema in ("public", "sinjira_fracture_internal")
    for name, args in (
        ("fracture_engine_start", "text"),
        ("fracture_engine_pick", "text, bigint"),
        ("fracture_engine_submit_keep", "text, bigint[]"),
        ("fracture_engine_submit_report", "text, text, integer, bigint"),
        ("fracture_engine_submit_accusation", "text, integer[]"),
    )
}


class FractureV45QuarantineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = CANDIDATE.read_text(encoding="utf-8")
        cls.sql = re.sub(r"--[^\n]*", "", cls.content).strip()
        cls.fixture = TEST_SQL.read_text(encoding="utf-8")

    def test_only_ten_targeted_revokes_and_explicit_service_grants(self):
        names = []
        grants = []
        for line in self.sql.splitlines():
            line = line.strip()
            if line.startswith("REVOKE EXECUTE"):
                match = re.fullmatch(
                    r"REVOKE EXECUTE ON FUNCTION (.+) FROM PUBLIC, anon, authenticated;", line
                )
                self.assertIsNotNone(match, line)
                names.append(match.group(1))
            if line.startswith("GRANT EXECUTE"):
                match = re.fullmatch(
                    r"GRANT EXECUTE ON FUNCTION (.+) TO service_role;", line
                )
                self.assertIsNotNone(match, line)
                grants.append(match.group(1))
        self.assertEqual(len(names), 10)
        self.assertEqual(len(grants), 10)
        self.assertEqual(set(names), TARGETS)
        self.assertEqual(set(grants), TARGETS)

    def test_no_ddl_dml_broad_permissions_or_secrets(self):
        self.assertEqual(self.sql.splitlines()[0], "BEGIN;")
        self.assertEqual(self.sql.splitlines()[-1], "COMMIT;")
        self.assertEqual(self.sql.count(";"), 22)
        self.assertNotRegex(self.sql, r"(?i)\b(?:ALTER|CREATE|DROP|UPDATE|INSERT|DELETE|TRUNCATE|DO|COPY|CALL|PERFORM|EXECUTE\s+PROCEDURE)\b")
        self.assertNotRegex(self.sql, r"(?i)\bALL\s+FUNCTIONS\b|\bALL\s+ROUTINES\b|\bCASCADE\b")
        self.assertNotIn("supabase db push", self.sql)
        self.assertNotIn("gpvivleexywljowcqkru", self.sql)

    def test_readonly_functions_are_not_in_revocation_list(self):
        for name in ("fracture_engine_get_state", "fracture_engine_get_state_safe",
                     "fracture_engine_health", "fracture_engine_privacy_health",
                     "fracture_engine_sanitize_state"):
            self.assertNotIn(name + "(", self.sql)

    def test_test_fixture_has_no_production_data_and_checks_both_roles(self):
        self.assertIn("V45-PASS", self.fixture)
        self.assertIn("SET ROLE authenticated", self.fixture)
        self.assertIn("SET ROLE service_role", self.fixture)
        self.assertIn("insufficient_privilege", self.fixture)
        self.assertIn("has_function_privilege('anon'", self.fixture)
        self.assertNotIn("gpvivleexywljowcqkru", self.fixture)
        self.assertIn("sinjira_fracture_v45_mutation_rpc_quarantine_candidate.sql", self.fixture)

    def test_no_automatic_migration(self):
        self.assertIn("NON AUTORISÉ POUR LA PRODUCTION", self.content)
        self.assertEqual(CANDIDATE.parent.name, "proposals")
        self.assertNotIn("supabase/migrations/", str(CANDIDATE))


if __name__ == "__main__":
    unittest.main()
