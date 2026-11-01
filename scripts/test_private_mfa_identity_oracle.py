#!/usr/bin/env python3
"""Tests de mutations négatives pour la frontière MFA privée, sans réseau."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_private_mfa_identity_oracle import CANDIDATE, normalize, validate  # noqa: E402


class IdentityOracleGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CANDIDATE.read_text("utf-8")

    def reject(self, old, new):
        self.assertIn(old, self.source, "Mutation sans cible")
        changed = self.source.replace(old, new, 1)
        self.assertNotEqual(changed, self.source)
        self.assertTrue(validate(changed), "Mutation non rejetée : " + old)

    def test_valid_candidate(self):
        self.assertEqual(validate(self.source), [])

    def test_non_service_cannot_query_other_user(self):
        self.reject("p_user_id IS DISTINCT FROM auth.uid()", "FALSE")

    def test_no_blanket_service_bypass(self):
        self.reject("COALESCE(auth.jwt()->>'role', '') <> 'service_role'",
                    "COALESCE(auth.jwt()->>'role', '') = 'service_role'")

    def test_null_user_denied(self):
        self.reject("IF p_user_id IS NULL THEN", "IF FALSE THEN")

    def test_mfa_check_uses_requested_user(self):
        self.reject("private.security_verified_mfa_exists(p_user_id)",
                    "private.security_verified_mfa_exists(auth.uid())")

    def test_correct_permission_denial(self):
        self.reject("RAISE EXCEPTION 'AUTH_CONTEXT_MISMATCH'",
                    "RAISE EXCEPTION 'AAL2_REQUIRED'")

    def test_deny_precedes_sensitive_lookup(self):
        self.reject("  IF private.security_verified_mfa_exists(p_user_id)",
                    "  IF private.security_verified_mfa_exists(p_user_id)")

        candidate = self.source
        identity = candidate.index("  IF COALESCE(auth.jwt()->>'role'")
        factor = candidate.index("  IF private.security_verified_mfa_exists")
        identity_end = candidate.index("  END IF;", identity) + len("  END IF;")
        factor_end = candidate.index("  END IF;", factor) + len("  END IF;")
        switched = (candidate[:identity] + candidate[factor:factor_end] +
                    candidate[identity_end:factor] + candidate[identity:identity_end] +
                    candidate[factor_end:])
        self.assertTrue(validate(switched))

    def test_signature_immutability(self):
        self.reject("p_user_id uuid)", "p_user_id text)")
        self.reject("RETURNS void", "RETURNS boolean")
        self.reject("STABLE", "VOLATILE")
        self.reject("SECURITY DEFINER", "SECURITY INVOKER")
        self.reject("SET search_path TO 'pg_catalog', 'auth', 'private'",
                    "SET search_path TO public")

    def test_no_privilege_expansion_or_data_writes(self):
        for statement in (
            "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA private TO PUBLIC;",
            "ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;",
            "DROP TABLE public.security_devices;",
            "INSERT INTO public.security_events DEFAULT VALUES;",
        ):
            with self.subTest(statement=statement[:42]):
                self.assertTrue(validate(self.source + "\n" + statement))

    def test_comments_cannot_fake_a_guard(self):
        replacement = (
            "-- IF COALESCE(auth.jwt()->>'role', '') <> 'service_role' "
            "AND p_user_id IS DISTINCT FROM auth.uid() THEN"
        )
        self.reject(
            "  IF COALESCE(auth.jwt()->>'role', '') <> 'service_role'\n"
            "     AND p_user_id IS DISTINCT FROM auth.uid() THEN",
            replacement
        )

    def test_review_only_outside_production_ledger(self):
        self.assertIn("/candidate-migrations/", CANDIDATE.as_posix())
        self.assertNotIn("/migrations/", CANDIDATE.as_posix())
        self.assertEqual(normalize("-- one\nSELECT 1;"), "select 1;")


if __name__ == "__main__":
    unittest.main(verbosity=2)
