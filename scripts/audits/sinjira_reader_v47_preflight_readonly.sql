-- SINJIRA V47 — prévol de la reprise intrapage V32, LECTURE SEULE.
-- Inspecte uniquement les catalogues PostgreSQL et privilèges de relation.
-- Ne lit aucune ligne utilisateur, aucun roman, ni aucun historique de lecture.
-- NO_GO à conserver tant que la colonne, la contrainte et les tests réels manquent.
WITH t AS (
 SELECT c.oid,c.relrowsecurity,c.relname
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='public' AND c.relname='sinjira_reader_library'
 AND c.relkind IN ('r','p')
), columns AS (
 SELECT column_name,data_type,is_nullable,udt_name,column_default
 FROM information_schema.columns
 WHERE table_schema='public' AND table_name='sinjira_reader_library'
), constraints AS (
 SELECT conname,contype,pg_get_constraintdef(oid) AS definition
 FROM pg_constraint WHERE conrelid=(SELECT oid FROM t)
), policies AS (
 SELECT policyname,cmd,roles,qual,with_check
 FROM pg_policies WHERE schemaname='public'
 AND tablename='sinjira_reader_library'
), checks AS (
 SELECT 'reader_table_present'::text AS check_id,
 CASE WHEN (SELECT count(*) FROM t)=1 THEN 'PASS' ELSE 'BLOCK' END::text AS status,
 'La table de progression doit être présente.'::text AS finding
 UNION ALL
 SELECT 'reader_rls_enabled',
 CASE WHEN (SELECT count(*) FROM t WHERE relrowsecurity)=1 THEN 'PASS' ELSE 'BLOCK' END,
 'RLS doit être activée pour la bibliothèque de lecture.'
 UNION ALL
 SELECT 'reader_single_owner_policy',
 CASE WHEN (SELECT count(*) FROM policies)=1 AND EXISTS (
   SELECT 1 FROM policies WHERE policyname='sinjira reader library own'
   AND cmd='ALL' AND 'authenticated'=ANY(roles)
   AND position('auth.uid' in lower(coalesce(qual,'')))>0
   AND position('user_id' in lower(coalesce(qual,'')))>0
   AND position('auth.uid' in lower(coalesce(with_check,'')))>0
   AND position('user_id' in lower(coalesce(with_check,'')))>0
 ) THEN 'PASS' ELSE 'BLOCK' END,
 'Une seule politique propriétaire, pour authenticated, en lecture et écriture.'
 UNION ALL
 SELECT 'reader_primary_key',
 CASE WHEN EXISTS (
 SELECT 1 FROM constraints WHERE contype='p'
 AND definition ~* 'PRIMARY KEY \(user_id, novel_id\)'
 ) THEN 'PASS' ELSE 'BLOCK' END,
 'La progression doit être unique pour chaque couple lecteur/roman.'
 UNION ALL
 SELECT 'reader_legacy_bounds',
 CASE WHEN EXISTS (SELECT 1 FROM constraints
 WHERE conname='sinjira_reader_library_last_page_check'
 AND position('last_page' IN definition)>0)
 AND EXISTS (SELECT 1 FROM constraints
 WHERE conname='sinjira_reader_library_progress_percent_check'
 AND position('progress_percent' IN definition)>0)
 THEN 'PASS' ELSE 'BLOCK' END,
 'Les contraintes historiques sur page et pourcentage sont préservées.'
 UNION ALL
 SELECT 'reader_existing_fields',
 CASE WHEN EXISTS (SELECT 1 FROM columns WHERE column_name='user_id' AND udt_name='uuid')
 AND EXISTS (SELECT 1 FROM columns WHERE column_name='novel_id' AND udt_name='uuid')
 AND EXISTS (SELECT 1 FROM columns WHERE column_name='last_page' AND data_type='integer')
 AND EXISTS (SELECT 1 FROM columns WHERE column_name='progress_percent' AND data_type='integer')
 THEN 'PASS' ELSE 'BLOCK' END,
 'Champs de progression existants et types attendus.'
 UNION ALL
 SELECT 'reader_authenticated_read_write',
 CASE WHEN (SELECT count(*) FROM t)=1
 AND has_table_privilege('authenticated',(SELECT oid FROM t),'SELECT')
 AND has_table_privilege('authenticated',(SELECT oid FROM t),'UPDATE')
 THEN 'PASS' ELSE 'BLOCK' END,
 'Le lecteur authentifié dispose des droits de base, restreints par RLS.'
 UNION ALL
 SELECT 'reader_anon_direct_grants',
 CASE WHEN (SELECT count(*) FROM t)<>1 THEN 'BLOCK'
 WHEN has_table_privilege('anon',(SELECT oid FROM t),'SELECT')
 OR has_table_privilege('anon',(SELECT oid FROM t),'INSERT')
 OR has_table_privilege('anon',(SELECT oid FROM t),'UPDATE')
 OR has_table_privilege('anon',(SELECT oid FROM t),'DELETE')
 THEN 'REVIEW' ELSE 'PASS' END,
 'Des GRANT anon peuvent exister malgré la protection par RLS; revue du moindre privilège.'
 UNION ALL
 SELECT 'reader_scroll_ratio_column',
 CASE WHEN EXISTS (SELECT 1 FROM columns
 WHERE column_name='scroll_ratio' AND data_type='numeric'
 AND is_nullable='YES')
 THEN 'PASS' ELSE 'BLOCK' END,
 'La colonne V32 nullable de position intrapage doit être déployée.'
 UNION ALL
 SELECT 'reader_scroll_ratio_range',
 CASE WHEN EXISTS (SELECT 1 FROM constraints
 WHERE conname='sinjira_reader_library_scroll_ratio_range'
 AND position('scroll_ratio' IN definition)>0
 AND position('>= (0)' IN definition)>0
 AND position('<= (1)' IN definition)>0)
 THEN 'PASS' ELSE 'BLOCK' END,
 'Contrainte de position 0..1 à confirmer après application de V32.'
)
SELECT check_id,status,finding FROM checks
UNION ALL
SELECT 'reader_release_decision',
 CASE WHEN EXISTS(SELECT 1 FROM checks WHERE status='BLOCK')
 THEN 'NO_GO' ELSE 'REVIEW_REQUIRED' END,
 'Même avec tous les contrôles de catalogue satisfaits, des essais deux appareils et une approbation restent obligatoires.'
ORDER BY check_id;
