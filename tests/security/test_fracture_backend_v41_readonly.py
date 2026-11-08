"""SINJIRA V41 — tests du prévol SQL purement catalogues, zéro secret."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "scripts/audits/sinjira_fracture_backend_v41_readonly.sql"


def scrub_literals_and_comments(source: str) -> str:
    """Retire les chaînes SQL et commentaires pour contrôler les verbes exécutables."""
    return re.sub(
        r"'(?:''|[^'])*'|--[^\n]*|/\*[\s\S]*?\*/",
        " ",
        source,
    )


class FractureV41AuditContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PROBE.read_text(encoding="utf-8")
        cls.executable = scrub_literals_and_comments(cls.source)

    def test_only_one_readonly_select_query(self):
        sql = self.executable.strip()
        self.assertRegex(sql, r"(?i)^WITH\b")
        self.assertRegex(sql, r"(?i)\bSELECT\s+check_id\s*,\s*status\s*,\s*finding\s+FROM\s+checks\b")
        self.assertEqual(sql.count(";"), 1)
        self.assertTrue(sql.endswith(";"))
        self.assertNotRegex(
            sql,
            r"(?i)\b(?:ALTER|CREATE|DROP|TRUNCATE|INSERT|UPDATE|DELETE|"
            r"GRANT|REVOKE|EXECUTE|CALL|COPY|VACUUM|REFRESH|"
            r"DO|PERFORM|COMMIT|ROLLBACK|SET|RESET)\b",
        )

    def test_only_postgres_metadata_not_user_rows(self):
        refs = set(
            name.lower() for name in re.findall(
                r"(?i)\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)\b",
                self.executable,
            )
        )
        allowed = {
            "pg_class", "pg_namespace", "pg_proc", "pg_policies",
            "engine_tables", "routines", "checks",
        }
        self.assertTrue(refs, "La requête doit inspecter les catalogues.")
        self.assertTrue(refs <= allowed, f"Sources inattendues : {refs - allowed}")
        self.assertNotRegex(
            self.executable, r"(?i)\b(?:pg_read_file|pg_ls_dir|lo_import)\s*\("
        )

    def test_required_check_ids_unique(self):
        checks = re.findall(
            r"(?i)\bSELECT\s+'([a-z][a-z0-9_]*)'(?:::text)?\s*(?:AS\s+check_id)?\s*,",
            self.source,
        )
        expected = {
            "engine_internal_rls", "engine_no_web_table_grants",
            "public_engine_rpc_anon", "legacy_final_bonus",
            "legacy_automatic_seats", "legacy_engine_version",
            "endgame_update_party_integrity",
            "player_documents_update_membership",
            "raw_state_member_boundary", "active_session_validation",
        }
        self.assertEqual(set(checks), expected)
        self.assertEqual(len(checks), len(expected), "Contrôle dupliqué.")

    def test_no_automatic_pass_for_unresolved_rules_or_policies(self):
        source = self.source
        for sentinel in (
            "then 5 else 0", "seat_kind=''bot''", "24.4.6",
            "fracture_parties", "is_fracture_party_member",
            "session_id", "NOT_A_MEMBER",
        ):
            with self.subTest(sentinel=sentinel):
                self.assertIn(sentinel, source)
        self.assertIn("'BLOCK'", source)
        self.assertIn("'REVIEW'", source)
        self.assertIn("'PASS'", source)

    def test_evidence_does_not_export_function_body(self):
        self.assertNotIn("pg_get_functiondef", self.source)
        # prosrc n'est utilisé que dans les prédicats; le résultat exposé
        # reste limité aux identifiants, statuts et conclusions génériques.
        self.assertRegex(
            self.executable,
            r"(?i)\bSELECT\s+check_id\s*,\s*status\s*,\s*finding\s+FROM\s+checks\b",
        )


if __name__ == "__main__":
    unittest.main()
