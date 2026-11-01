#!/usr/bin/env python3
"""Régressions statiques de la frontière d'identité; aucun accès au réseau."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_private_role_identity_guard import (  # noqa: E402
    CANDIDATE, errors_in_candidate, stripped_sql,
)


class PrivateIdentityGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CANDIDATE.read_text("utf-8")

    def assert_rejected(self, old: str, new: str) -> None:
        self.assertIn(old, self.source, "Mutation cible absente")
        changed = self.source.replace(old, new, 1)
        self.assertTrue(errors_in_candidate(changed),
                        f"La mutation n'a pas été rejetée: {old!r}")

    def test_candidate_contract_passes(self):
        self.assertEqual(errors_in_candidate(self.source), [])

    def test_admin_requires_caller_identity(self):
        self.assert_rejected("OR p_user_id = (SELECT auth.uid())", "OR true")

    def test_admin_only_service_role_can_inspect_other_users(self):
        self.assert_rejected(
            "COALESCE(auth.jwt()->>'role', '') = 'service_role'",
            "COALESCE(auth.jwt()->>'role', '') <> 'service_role'"
        )

    def test_admin_identity_null_never_grants_admin(self):
        self.assert_rejected("p_user_id IS NOT NULL", "true")

    def test_rank_forbids_third_party_user_id(self):
        self.assert_rejected(
            "p_user_id IS DISTINCT FROM (SELECT auth.uid())", "false")

    def test_rank_must_deny_before_reading_roles(self):
        marker = "WHEN private.is_sinjira_admin(p_user_id)"
        self.assert_rejected(marker, "WHEN true THEN 100\n        " + marker)

    def test_rank_null_public_anonymous_path_kept(self):
        self.assert_rejected("p.visibility = 'public'", "p.visibility = 'account'")

    def test_rank_returns_zero_on_denial(self):
        self.assert_rejected("THEN 0\n        WHEN private.is_sinjira_admin", "THEN 100\n        WHEN private.is_sinjira_admin")

    def test_no_ddl_privilege_modifications(self):
        for extra in (
            "\nGRANT EXECUTE ON FUNCTION private.is_sinjira_admin(uuid) TO PUBLIC;",
            "\nREVOKE ALL ON SCHEMA private FROM anon;",
            "\nDROP TABLE public.internal_admin_users;",
            "\nDELETE FROM public.project_access;",
            "\nALTER TABLE public.documents DISABLE ROW LEVEL SECURITY;",
        ):
            with self.subTest(extra=extra[:35]):
                self.assertTrue(errors_in_candidate(self.source + extra))

    def test_no_new_definer_surface(self):
        extra = "\nCREATE OR REPLACE FUNCTION private.unsafe() RETURNS boolean LANGUAGE sql AS $$ SELECT true $$;"
        self.assertTrue(errors_in_candidate(self.source + extra))

    def test_two_existing_signatures_stay_same(self):
        self.assert_rejected("p_project_id uuid,", "p_project_id text,")
        self.assert_rejected("RETURNS boolean", "RETURNS text")

    def test_no_broad_set_search_path(self):
        self.assert_rejected(
            "SET search_path = pg_catalog, auth, public, private, pg_temp",
            "SET search_path = public",
        )

    def test_comments_do_not_count_as_security_guards(self):
        sql = self.source.replace(
            "OR p_user_id = (SELECT auth.uid())",
            "OR true -- p_user_id = (SELECT auth.uid())",
            1
        )
        self.assertTrue(errors_in_candidate(sql))

    def test_readonly_remediation_only_not_direct_migration(self):
        self.assertIn("candidate-migrations", str(CANDIDATE))
        self.assertNotIn("/migrations/", str(CANDIDATE))
        self.assertEqual(stripped_sql("-- GRANT\nSELECT 1;").strip(), "SELECT 1;")


if __name__ == "__main__":
    unittest.main(verbosity=2)
