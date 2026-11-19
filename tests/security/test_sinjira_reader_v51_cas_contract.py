"""Contrat statique V51 : migration additive + client CAS, aucun vrai compte."""

import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MIGRATION=(ROOT/"supabase/review-candidates/20261110011500_sinjira_reader_progress_revision_cas_v51.sql").read_text(encoding="utf-8")
SQL=(ROOT/"tests/security/sql/test_sinjira_reader_v51_cas.sql").read_text(encoding="utf-8")
CLIENT=(ROOT/"assets/js/sinjira-liseuse-v26.js").read_text(encoding="utf-8")
LEGACY=(ROOT/"assets/js/sinjira-reader-progress-v24-4-61.js").read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github/workflows/sinjira-reader-v51-cas.yml").read_text(encoding="utf-8")
CONCURRENT=(ROOT/"scripts/test_sinjira_reader_v51_concurrent_local.sh").read_text(encoding="utf-8")
REPLAY=(ROOT/"assets/js/sinjira-liseuse-position-v31.mjs").read_text(encoding="utf-8")
REPLAY_TEST=(ROOT/"tests/sinjira-reader-cas-retry-v51.test.mjs").read_text(encoding="utf-8")

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
    def test_v51_1_requires_real_book_entitlement_not_merely_auth_uid(self):
        # V51.1 / #955 : SECURITY DEFINER ne bénéficie pas de la RLS.
        # Interdire toute sauvegarde d'un livre non publié ou sans droit.
        for token in (
            "novel.status='published'",
            "public.is_sinjira_owner(v_user)",
            "public.is_sinjira_admin(v_user)",
            "public.user_entitlements entitlement",
            "public.products product",
            "product.active IS TRUE",
            "entitlement.user_id=v_user",
            "entitlement.product_id=novel.product_id",
            "'unavailable'::text",
        ):
            with self.subTest(token=token):
                self.assertIn(token,MIGRATION)
        # Les titres non autorisés, révoqués, non publiés et les comptes
        # sans licence ont maintenant des scénarios SQL JWT distincts.
        for marker in (
            "V51.1: titre non autorise",
            "V51.1: le marque-page existe, mais le droit est revoque",
            "V51.1: compte B enregistre un roman non attribue",
            "V51.1: admin autorise",
            "V51.1: un roman annonce reste interdit meme aux admins",
            "V51.1: proprietaire autorise",
            "v51_before_revocation",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker,SQL)

    def test_v51_2_serializes_revocation_and_save_across_sessions(self):
        # Le contrôle de droit doit survivre à un DELETE ou à une mise
        # hors ligne simultanés. Un simple EXISTS sans verrou est insuffisant.
        self.assertIn("FOR SHARE OF novel",MIGRATION)
        self.assertIn("FOR SHARE OF entitlement, product",MIGRATION)
        self.assertIn("V51-REVOKER-LOCK-HELD",CONCURRENT)
        self.assertIn("SELECT pg_sleep(4)",CONCURRENT)
        self.assertIn("V51.2-REVOCATION-PASS",CONCURRENT)
        self.assertIn("unavailable||",CONCURRENT)
        self.assertIn("rev<>3 OR page NOT IN (51,52)",CONCURRENT)
        self.assertIn("PGOPTIONS",CONCURRENT)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY",CONCURRENT)

    def test_v51_3_serializes_catalog_status_and_product_deactivation(self):
        # Pas de validation par simple inspection d'un statut avant l'UPDATE.
        # Deux vraies transactions doivent concurrencer une écriture CAS.
        for token in (
            "V51.3-$label-LOCK-HELD",
            "revoke_during_save 'NOVEL'",
            "revoke_during_save 'PRODUCT'",
            "V51.3-$label-PASS",
            "V51.3-CATALOGUE-PASS",
            "UPDATE public.products SET active=false",
            "UPDATE public.sinjira_novels SET status='archived'",
            "unavailable||",
            "last_page=12 AND revision=0",
            "V51.3: progression du compte B modifiée",
        ):
            with self.subTest(token=token):
                self.assertIn(token,CONCURRENT)
        self.assertIn("FOR SHARE OF entitlement, product",MIGRATION)
        self.assertIn("FOR SHARE OF novel",MIGRATION)

    def test_v51_4_role_revocation_is_serialized_under_lock(self):
        # Une fonction STABLE d'administration sans verrou ne protège pas
        # contre le DELETE d'un rôle pendant une sauvegarde CAS.
        for token in (
            "public.internal_admin_users staff",
            "staff.user_id=v_user",
            "staff.role IN ('owner','admin')",
            "public.is_sinjira_owner(v_user)",
            "public.is_sinjira_admin(v_user)",
            "FOR SHARE OF staff",
        ):
            with self.subTest(token=token):
                self.assertIn(token,MIGRATION)
        for token in (
            "V51.4-$label-ROLE-LOCK-HELD",
            "revoke_staff_during_save 'ADMIN'",
            "revoke_staff_during_save 'OWNER'",
            "DELETE FROM public.internal_admin_users",
            "V51.4-ROLE-REVOCATION-PASS",
            "V51.4: page altérée après révocation de rôle",
            "last_page=14 AND revision=0",
            "unavailable||",
        ):
            with self.subTest(token=token):
                self.assertIn(token,CONCURRENT)

    def test_v51_5_offline_retry_uses_server_revision_not_device_time(self):
        # À la reconnexion, la date de l'appareil est un simple marqueur
        # de brouillon local. Seule la révision PostgreSQL fait foi.
        for token in (
            "cloudRevisionDecision(state.cloudRevision,remote)",
            ".select('revision')",
            "decision==='conflict'",
            "decision==='invalid'",
            "state.cloudConflict=true",
            "const restored=await syncProgress()",
            "safeLocalGet(key+':pending')!==pendingAt",
        ):
            with self.subTest(token=token):
                self.assertIn(token,CLIENT)
        self.assertNotIn("shouldReplayReadingProgress(pendingAt",CLIENT)
        self.assertNotIn(".select('updated_at')",CLIENT)
        self.assertIn("export function cloudRevisionDecision(",REPLAY)
        for token in (
            "première sauvegarde sans ligne",
            "révision concurrente",
            "fail closed",
            "numéro sûr accepté",
        ):
            with self.subTest(token=token):
                self.assertIn(token,REPLAY_TEST)
        self.assertIn("node --test tests/sinjira-reader-cas-retry-v51.test.mjs",WORKFLOW)

    def test_v51_6_revoked_access_closes_previously_loaded_private_pdf(self):
        # Le statut SQL 'unavailable' est un refus de droits, pas une panne.
        # Le lecteur doit retirer immédiatement le texte et le PDF en RAM,
        # tout en gardant le brouillon de progression strictement numérique.
        for token in (
            "if(data?.result_status==='unavailable'){",
            "lockPrivateReader('rights');",
            "function lockPrivateReader(reason='session')",
            "state.accessInvalidated=true",
            "state.loadController?.abort()",
            "stopNarration(false)",
            "companion?.close()",
            "state.pdf=null;state.user=null;state.novelId=null",
            "$('reader-text').textContent=''",
            "$('reader-canvas').width=0",
            "$('reader-content').hidden=true",
            "book?.destroy?.()",
            "Votre droit d’accès à ce roman n’est plus disponible",
        ):
            with self.subTest(token=token):
                self.assertIn(token,CLIENT)
        self.assertIn("node --test tests/security/test_sinjira_reader_revocation_lock_v51.test.mjs",WORKFLOW)

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
