#!/usr/bin/env python3
"""Mutation tests for the actual candidate extracted from production pg_get_functiondef."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from validate_trusted_device_live_session import CANDIDATE,GUARD,errors


class SessionLivenessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql=CANDIDATE.read_text("utf-8")
        cls.checks=[
            "sinjira_security_internal.security_resolve_connection_challenge",
            "sinjira_security_internal.security_set_device_trust",
        ]

    def expect_reject(self,before:str,after:str,replace_all:bool=False):
        self.assertIn(before,self.sql)
        mutated=self.sql.replace(before,after) if replace_all else self.sql.replace(before,after,1)
        self.assertTrue(errors(mutated),f"Mutation dangereuse non détectée: {before!r}")

    def test_candidate_passes(self):
        self.assertEqual(errors(self.sql),[])

    def test_both_functions_have_live_session_guards(self):
        self.assertEqual(len(GUARD.findall(self.sql)),2)

    def test_missing_live_session_row_is_rejected(self):
        self.expect_reject("not exists (","exists (")

    def test_session_belongs_to_current_user(self):
        self.expect_reject("live_session.user_id = v_user","live_session.user_id is not null")

    def test_live_session_id_matches_jwt(self):
        self.expect_reject("live_session.id = v_session","live_session.id is not null")

    def test_session_not_after_must_be_future(self):
        self.expect_reject("live_session.not_after > now()","live_session.not_after < now()")

    def test_session_no_expiration_is_supported(self):
        self.expect_reject("live_session.not_after is null","live_session.not_after is not null")

    def test_invalid_session_raises_permission_error(self):
        self.expect_reject("'ACTIVE_SESSION_REQUIRED'","'NOTICE_ONLY'")

    def test_uses_sql_state_not_just_jwt_claim(self):
        self.expect_reject("from auth.sessions as live_session","from public.security_devices as live_session")

    def test_refuse_guard_after_mfa(self):
        # Déplacer le vrai bloc de garde APRÈS la validation MFA :
        # le validateur doit refuser une garde trop tardive.
        match = GUARD.search(self.sql)
        self.assertIsNotNone(match)
        guard = match.group(0)
        removed = self.sql[:match.start()] + self.sql[match.end():]
        anchor = "  perform private.security_require_aal2_if_available(v_user);"
        self.assertIn(anchor, removed)
        moved = removed.replace(anchor, anchor + "\n  " + guard, 1)
        self.assertTrue(errors(moved))

    def test_untrusted_device_cannot_approve(self):
        self.expect_reject("    and is_trusted\n","    and true\n")

    def test_key_must_match_current_session(self):
        self.expect_reject("    and last_session_id=v_session;","    and last_session_id is not null;")

    def test_challenge_not_same_device(self):
        self.expect_reject("if v_device.id=v_ch.request_device_id then","if false then")

    def test_trust_reauth_requires_aal2(self):
        self.expect_reject("if p_trusted and coalesce(auth.jwt()->>'aal','aal1') <> 'aal2' then",
                           "if false then")

    def test_trust_binds_current_device_session(self):
        self.expect_reject("v_row.last_session_id is distinct from v_session",
                           "v_row.last_session_id is null")

    def test_request_challenge_no_approval_without_trusted_other(self):
        self.expect_reject("if not v_recent_approved then","if false then")

    def test_unexpected_third_function_rejected(self):
        self.assertTrue(errors(self.sql+"\nCREATE OR REPLACE FUNCTION public.evil() RETURNS int LANGUAGE SQL AS $$ SELECT 1 $$;"))

    def test_unexpected_grants_refused(self):
        self.assertTrue(errors(self.sql+"\nGRANT ALL ON ALL TABLES IN SCHEMA public TO anon;"))

    def test_changed_signature_refused(self):
        self.expect_reject(
            "CREATE OR REPLACE FUNCTION sinjira_security_internal.security_resolve_connection_challenge(p_challenge_id uuid, p_device_key text, p_decision text)",
            "CREATE OR REPLACE FUNCTION sinjira_security_internal.security_resolve_connection_challenge(p_challenge_id text, p_device_key text, p_decision text)",
        )

    def test_changed_security_definer_refused(self):
        self.expect_reject("SECURITY DEFINER","SECURITY INVOKER")

    def test_only_comments_are_not_sufficient(self):
        self.expect_reject("if v_session is null or not exists (",
                           "-- if v_session is null or not exists (")

    def test_file_is_review_only(self):
        self.assertIn("candidate-migrations",str(CANDIDATE))
        self.assertNotIn("/migrations/",str(CANDIDATE))
        self.assertIn("REVIEW_ONLY",CANDIDATE.name)


if __name__=="__main__":
    unittest.main(verbosity=2)
