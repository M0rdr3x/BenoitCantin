"""Contrat statique V51 : migration additive + client CAS, aucun vrai compte."""

import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MIGRATION=(ROOT/"supabase/review-candidates/20261110011500_sinjira_reader_progress_revision_cas_v51.sql").read_text(encoding="utf-8")
SQL=(ROOT/"tests/security/sql/test_sinjira_reader_v51_cas.sql").read_text(encoding="utf-8")
CLIENT=(ROOT/"assets/js/sinjira-liseuse-v26.js").read_text(encoding="utf-8")
LEGACY=(ROOT/"assets/js/sinjira-reader-progress-v24-4-61.js").read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github/workflows/sinjira-reader-v51-cas.yml").read_text(encoding="utf-8")

class ReaderV51CasContract(unittest.TestCase):
    def test_additive_migration_preserves_v32_and_existing_positions(self):
        self.assertIn("ADD COLUMN IF NOT EXISTS revision bigint NOT NULL DEFAULT 0",MIGRATION)
        self.assertIn("CHECK (revision >= 0)",MIGRATION)
        self.assertIn("CREATE OR REPLACE FUNCTION public.sinjira_reader_save_progress_cas",MIGRATION)
        self.assertNotIn("TRUNCATE",MIGRATION.upper())
        self.assertNotIn("DROP TABLE",MIGRATION.upper())
        self.assertNotIn("DROP COLUMN",MIGRATION.upper())
    def test_race_guard_is_atomic_not_check_then_upsert(self):
        self.assertIn("AND library.revision=p_expected_revision",MIGRATION)
        self.assertIn("revision=library.revision+1",MIGRATION)
        self.assertIn("ON CONFLICT (user_id,novel_id) DO NOTHING",MIGRATION)
        self.assertIn("RETURN QUERY SELECT 'conflict'",MIGRATION)
        self.assertIn("p_expected_revision IS NULL",MIGRATION)
        self.assertNotIn("ON CONFLICT (user_id,novel_id) DO UPDATE",MIGRATION)
    def test_function_is_explicit_identity_scoped_with_safe_search_path(self):
        self.assertIn("SECURITY DEFINER",MIGRATION)
        self.assertIn("SET search_path = ''",MIGRATION)
        self.assertIn("auth.uid()",MIGRATION)
        self.assertIn("library.user_id=v_user",MIGRATION)
        self.assertIn("WHERE user_id=v_user AND novel_id=p_novel_id",MIGRATION)
        self.assertNotIn("p_user_id",MIGRATION)
    def test_revoke_bypass_grants_and_no_anon_rpc(self):
        for term in (
          "REVOKE INSERT,UPDATE ON public.sinjira_reader_library FROM PUBLIC",
          "REVOKE INSERT,UPDATE ON public.sinjira_reader_library FROM anon",
          "REVOKE INSERT,UPDATE ON public.sinjira_reader_library FROM authenticated",
          "FROM PUBLIC;",
          "FROM anon;",
          "TO authenticated;",
        ):
            with self.subTest(term=term):
                self.assertIn(term,MIGRATION)
        self.assertIn("has_table_privilege('authenticated'",SQL)
        self.assertIn("has_function_privilege('anon'",SQL)
    def test_client_never_uses_unconditional_upsert_or_clock_as_version(self):
        self.assertIn(".rpc('sinjira_reader_save_progress_cas'",CLIENT)
        self.assertIn("p_expected_revision:expectedRevision",CLIENT)
        self.assertIn("state.cloudConflict=true",CLIENT)
        self.assertIn("state.cloudRevisionReady",CLIENT)
        self.assertNotIn(".upsert(payload,{onConflict:'user_id,novel_id'})",CLIENT)
        self.assertIn("aucune écriture non protégée",CLIENT)
    def test_legacy_bookmark_uses_same_cas_boundary(self):
        self.assertIn(".rpc('sinjira_reader_save_progress_cas'",LEGACY)
        self.assertIn("p_expected_revision:expected",LEGACY)
        self.assertNotIn(".upsert(",LEGACY)
        self.assertIn("data?.result_status==='saved'",LEGACY)
    def test_client_initializes_revision_only_after_real_server_read(self):
        self.assertIn(".select('last_page,scroll_ratio,updated_at,revision')",CLIENT)
        self.assertIn("Number.isSafeInteger(number)",CLIENT)
        self.assertIn("cloudRevisionReady:true",CLIENT.replace("state.cloudRevisionReady=true", "cloudRevisionReady:true"))
        self.assertIn("state.cloudRevision=null;state.cloudRevisionReady=false;state.cloudConflict=false;",CLIENT)
        self.assertIn("!state.cloudRevisionReady||state.cloudConflict",CLIENT)
    def test_sql_scenarios_stale_new_and_foreign_user(self):
        for token in (
            "V51-CAS-PASS","'conflict'","v51_before_replay",
            "AND conname='sinjira_reader_library_revision_nonnegative'",
            "SET ROLE authenticated;","SET ROLE anon;",
            "p_novel_id", # present in migration, not test? see below
        ):
            if token=="p_novel_id":
                self.assertIn(token,MIGRATION)
            else:
                self.assertIn(token,SQL)
        self.assertIn("last_page",SQL)
    def test_workflow_uses_original_schema_in_disposable_db(self):
        self.assertIn("POSTGRES_DB: sinjira_reader_v51_lab",WORKFLOW)
        self.assertIn("'127.0.0.1:5432:5432'",WORKFLOW)
        self.assertIn("permissions:\n  contents: read",WORKFLOW)
        self.assertIn("persist-credentials: false",WORKFLOW)
        self.assertLess(WORKFLOW.rindex("test_sinjira_reader_v48_client_a_return.sql"),
                        WORKFLOW.rindex("test_sinjira_reader_v51_cas.sql"))
    def test_no_production_deployment_or_fabricated_completion(self):
        joined=MIGRATION+SQL+WORKFLOW
        for token in ("supabase db push","postgresql://","service_role_key",
                      "SUPABASE_SERVICE_ROLE_KEY","apply_migration",
                      "reader_two_devices=PASS","reader_v32_prod=PASS"):
            with self.subTest(token=token):
                self.assertNotIn(token.lower(),joined.lower())
        self.assertIn("NO_GO",WORKFLOW)
    def test_fake_users_only_in_sql_test(self):
        self.assertIn("00000000-0000-0000-0000-000000000001",SQL)
        self.assertIn("00000000-0000-0000-0000-000000000002",SQL)
        self.assertNotIn("INSERT INTO auth.users",MIGRATION)

if __name__=="__main__":
    unittest.main()
