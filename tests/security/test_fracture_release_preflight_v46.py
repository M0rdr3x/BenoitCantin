"""SINJIRA Fracture V46 — contrat d'un prévol de catalogues à refus fermé."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / "scripts/audits/sinjira_fracture_v46_release_preflight_readonly.sql"
V45 = ROOT / "scripts/proposals/sinjira_fracture_v45_mutation_rpc_quarantine_candidate.sql"
V42 = ROOT / "scripts/proposals/sinjira_fracture_v42_rls_update_candidate.sql"


def strip_literals_comments(sql: str) -> str:
    # Une chaîne littérale est neutralisée par deux guillemets SQL;
    # les commentaires doivent être remplacés par des espaces, sinon
    # un commentaire placé avant WITH ferait échouer une requête sûre.
    def mask(m: re.Match[str]) -> str:
        return "''" if m.group(0).startswith("'") else " "

    return re.sub(
        r"'(?:''|[^'])*'|--[^\n]*|/\*[\s\S]*?\*/",
        mask,
        sql,
    )


class FractureV46Preflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = PREFLIGHT.read_text(encoding="utf-8")
        cls.clean = strip_literals_comments(cls.sql)
        cls.v45 = V45.read_text(encoding="utf-8")
        cls.v42 = V42.read_text(encoding="utf-8")

    def test_only_catalogue_read_and_single_select(self):
        s = self.clean.strip()
        self.assertRegex(s, r"(?i)^WITH\b")
        self.assertTrue(s.endswith("ORDER BY check_id;"))
        self.assertEqual(s.count(";"), 1)
        self.assertNotRegex(
            s,
            r"(?i)\b(?:INSERT|UPDATE|DELETE|UPSERT|ALTER|CREATE|DROP|TRUNCATE|"
            r"GRANT|REVOKE|COPY|DO|CALL|VACUUM|REFRESH|EXECUTE|PERFORM|COMMIT|"
            r"ROLLBACK|SET|RESET|MERGE)\b",
        )

    def test_query_sources_are_postgres_metadata_only(self):
        found = {n.lower() for n in re.findall(
            r"(?i)\b(?:from|join)\s+([a-z_][a-z0-9_]*)\b", self.clean
        )}
        expected = {
            "rpc", "expected_rpc", "inventory", "policy", "write_policies", "checks",
            "pg_proc", "pg_namespace", "pg_policies", "pg_class",
        }
        self.assertTrue(found)
        self.assertTrue(found <= expected, f"Source non autorisée : {found - expected}")
        self.assertFalse(re.search(
            r"(?i)\b(?:pg_read_file|pg_ls_dir|lo_import|dblink)\s*\(",
            self.clean,
        ))
        self.assertNotIn("pg_get_functiondef", self.sql)

    def test_ten_rpc_signatures_match_v45_exactly(self):
        expected = re.findall(
            r"(?m)^REVOKE EXECUTE ON FUNCTION ([\w.]+\([^)]*\))"
            r" FROM PUBLIC, anon, authenticated;",
            self.v45,
        )
        self.assertEqual(len(expected), 10)
        head = self.sql.split("\nrpc AS (", 1)[0]
        actual = re.findall(
            r"\('(public|sinjira_fracture_internal)',"
            r"'(fracture_engine_[a-z_]+)','([^']+)'\)",
            head,
        )
        self.assertEqual(len(actual), 10)
        signatures = {f"{schema}.{name}({args})" for schema, name, args in actual}
        self.assertEqual(signatures, set(expected))

    def test_catches_surprise_overloads_and_role_inheritance(self):
        for required in (
            "rpc_unreviewed_overloads",
            "rpc_signature_inventory",
            "rpc_authenticated_denied",
            "rpc_anon_denied",
            "rpc_service_role_preserved",
            "has_function_privilege('authenticated',oid,'EXECUTE')",
            "has_function_privilege('anon',oid,'EXECUTE')",
            "has_function_privilege('service_role',oid,'EXECUTE')",
            "to_regprocedure",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.sql)

    def test_two_rls_policies_match_v42_proposal(self):
        for name, field in (
            ("fracture endgame owner update", "fracture_endgame_reports"),
            ("fracture docs own update", "fracture_player_documents"),
        ):
            with self.subTest(name=name):
                self.assertIn(name, self.sql)
                self.assertIn(name, self.v42)
                self.assertIn(field, self.sql)
        for key in (
            "rls_both_target_tables", "rls_endgame_update_destination",
            "rls_player_document_destination", "is_fracture_party_member",
            "fracture_parties", "owner_user_id", "auth.uid",
        ):
            self.assertIn(key, self.sql)

    def test_all_checks_and_refusal_closed_gate(self):
        checks = re.findall(
            r"(?m)^\s*SELECT '([a-z_]+)'(?:::text)?\s+AS\s+check_id",
            self.sql,
        )
        checks += re.findall(
            r"(?m)^\s*SELECT '([a-z_]+)',\s*\n\s*CASE",
            self.sql,
        )
        self.assertEqual(set(checks), {
            "rpc_signature_inventory", "rpc_unreviewed_overloads",
            "rpc_anon_denied", "rpc_authenticated_denied",
            "rpc_service_role_preserved", "rls_both_target_tables",
            "rls_endgame_update_destination", "rls_player_document_destination",
            "rls_no_unreviewed_write_policies", "release_decision",
        })
        self.assertEqual(len(checks), 10)
        self.assertIn("CASE WHEN EXISTS (SELECT 1 FROM checks WHERE status='BLOCK')", self.sql)
        self.assertIn("THEN 'NO_GO'", self.sql)
        self.assertIn("ELSE 'REVIEW_REQUIRED'", self.sql)
        self.assertNotIn("THEN 'GO'", self.sql)

    def test_no_auto_deployment_or_private_identifiers(self):
        self.assertEqual(PREFLIGHT.parent.name, "audits")
        self.assertNotIn("gpvivleexywljowcqkru", self.sql)
        self.assertNotIn("supabase db push", self.sql)
        self.assertNotIn("service_role_key", self.sql)
        self.assertNotRegex(self.sql, r"(?i)\bselect\s+user_id\b")
        self.assertIn("Aucun compte", self.sql)


if __name__ == "__main__":
    unittest.main()
