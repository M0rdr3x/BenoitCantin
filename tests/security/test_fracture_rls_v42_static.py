"""V42: empêcher tout élargissement de la proposition de politiques RLS."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "scripts/proposals/sinjira_fracture_v42_rls_update_candidate.sql"
FIXTURE = ROOT / "tests/security/sql/test_fracture_rls_v42.sql"


class FractureV42StaticContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = CANDIDATE.read_text(encoding="utf-8")
        cls.fixture = FIXTURE.read_text(encoding="utf-8")
        cls.sql = re.sub(r"--[^\n]*", "", cls.candidate)

    def test_only_two_existing_update_policies_are_modified(self):
        names = re.findall(
            r'alter\s+policy\s+"([^"]+)"\s+on\s+public\.([a-z_]+)',
            self.sql, flags=re.I,
        )
        self.assertEqual(names, [
            ("fracture endgame owner update", "fracture_endgame_reports"),
            ("fracture docs own update", "fracture_player_documents"),
        ])
        self.assertEqual(len(re.findall(r"\balter\s+policy\b", self.sql, re.I)), 2)
        self.assertNotRegex(
            self.sql,
            r"(?i)\b(create|drop|truncate|insert|delete|grant|revoke|"
            r"create\s+function|disable\s+row\s+level\s+security)\b",
        )

    def test_both_policies_keep_authenticated_owner(self):
        parts = re.split(r"(?i)\balter\s+policy\b", self.sql)[1:]
        self.assertEqual(len(parts), 2)
        for p in parts:
            self.assertRegex(p, r"(?i)\bto\s+authenticated\b")
            self.assertRegex(p, r"(?i)\busing\s*\(")
            self.assertRegex(p, r"(?i)\bwith\s+check\s*\(")
            self.assertIn("(select auth.uid())", p.lower())

    def test_target_party_checked_for_report_and_document(self):
        self.assertRegex(
            self.sql, r"(?is)fracture_endgame_reports.*?with\s+check"
            r"\s*\(.*?fracture_parties\s+p.*?p\.id\s*=\s*"
            r"fracture_endgame_reports\.party_id.*?p\.owner_user_id"
        )
        self.assertRegex(
            self.sql, r"(?is)fracture_player_documents.*?with\s+check"
            r"\s*\(.*?sinjira_rls_internal\.is_fracture_party_member"
        )

    def test_candidate_never_automatically_deployed(self):
        self.assertIn("NON AUTORISÉ POUR LA PRODUCTION", self.candidate)
        self.assertIn("scripts/proposals/", self.fixture)
        self.assertNotIn("supabase db push", self.fixture)
        self.assertNotIn("gpvivleexywljowcqkru", self.candidate + self.fixture)
        self.assertRegex(self.fixture, r"V42-PASS")
        self.assertEqual(self.fixture.count("exception when insufficient_privilege"), 4)


if __name__ == "__main__":
    unittest.main()
