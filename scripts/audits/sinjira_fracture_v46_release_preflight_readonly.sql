-- SINJIRA Fracture V46 — prévol distant en lecture SEULE.
-- Aucun compte, aucune partie, aucun bulletin ni identité consulté.
-- Ce contrôle ne donne jamais un feu vert automatique de production.
WITH expected_rpc(schema_name, function_name, signature) AS (
  VALUES
    ('public','fracture_engine_start','text'),
    ('public','fracture_engine_pick','text, bigint'),
    ('public','fracture_engine_submit_keep','text, bigint[]'),
    ('public','fracture_engine_submit_report','text, text, integer, bigint'),
    ('public','fracture_engine_submit_accusation','text, integer[]'),
    ('sinjira_fracture_internal','fracture_engine_start','text'),
    ('sinjira_fracture_internal','fracture_engine_pick','text, bigint'),
    ('sinjira_fracture_internal','fracture_engine_submit_keep','text, bigint[]'),
    ('sinjira_fracture_internal','fracture_engine_submit_report','text, text, integer, bigint'),
    ('sinjira_fracture_internal','fracture_engine_submit_accusation','text, integer[]')
),
rpc AS (
  SELECT e.*, to_regprocedure(format('%I.%I(%s)',
           e.schema_name,e.function_name,e.signature)) AS oid
  FROM expected_rpc e
),
inventory AS (
  SELECT n.nspname AS schema_name,p.proname AS function_name,p.oid
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname IN ('public','sinjira_fracture_internal')
    AND p.proname IN (
      'fracture_engine_start','fracture_engine_pick',
      'fracture_engine_submit_keep','fracture_engine_submit_report',
      'fracture_engine_submit_accusation'
    )
),
policy AS (
  SELECT tablename,policyname,roles,cmd,qual,with_check
  FROM pg_policies
  WHERE schemaname='public'
    AND (
      (tablename='fracture_endgame_reports'
        AND policyname='fracture endgame owner update')
      OR
      (tablename='fracture_player_documents'
        AND policyname='fracture docs own update')
    )
),
write_policies AS (
  SELECT tablename,policyname,cmd FROM pg_policies
  WHERE schemaname='public'
    AND tablename IN ('fracture_endgame_reports','fracture_player_documents')
    AND cmd IN ('UPDATE','ALL')
),
checks AS (
  SELECT 'rpc_signature_inventory'::text AS check_id,
    CASE WHEN (SELECT count(*) FROM rpc WHERE oid IS NOT NULL)=10
      THEN 'PASS' ELSE 'BLOCK' END::text AS status,
    'Les 10 signatures de mutation historiques doivent exister.'::text AS finding
  UNION ALL
  SELECT 'rpc_unreviewed_overloads',
    CASE WHEN (SELECT count(*) FROM inventory)=10 THEN 'PASS'
      ELSE 'BLOCK' END,
    'Aucune surcharge de fonction de mutation non couverte par la quarantaine.'
  UNION ALL
  SELECT 'rpc_anon_denied',
    CASE WHEN (SELECT count(*) FROM rpc WHERE oid IS NOT NULL)=10
      AND NOT EXISTS (
        SELECT 1 FROM rpc
        WHERE oid IS NOT NULL AND has_function_privilege('anon',oid,'EXECUTE')
      ) THEN 'PASS' ELSE 'BLOCK' END,
    'anon ne peut exécuter aucune des 10 mutations.'
  UNION ALL
  SELECT 'rpc_authenticated_denied',
    CASE WHEN (SELECT count(*) FROM rpc WHERE oid IS NOT NULL)=10
      AND NOT EXISTS (
        SELECT 1 FROM rpc
        WHERE oid IS NOT NULL AND has_function_privilege('authenticated',oid,'EXECUTE')
      ) THEN 'PASS' ELSE 'BLOCK' END,
    'Les 10 mutations sont interdites à authenticated, y compris via PUBLIC.'
  UNION ALL
  SELECT 'rpc_service_role_preserved',
    CASE WHEN (SELECT count(*) FROM rpc WHERE oid IS NOT NULL)=10
      AND NOT EXISTS (
        SELECT 1 FROM rpc WHERE oid IS NOT NULL
          AND NOT has_function_privilege('service_role',oid,'EXECUTE')
      ) THEN 'PASS' ELSE 'BLOCK' END,
    'Le rôle technique de maintenance conserve les permissions nécessaires.'
  UNION ALL
  SELECT 'rls_both_target_tables',
    CASE WHEN (
      SELECT count(*) FROM pg_class c
      JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='public'
        AND c.relname IN ('fracture_endgame_reports','fracture_player_documents')
        AND c.relrowsecurity
    )=2 THEN 'PASS' ELSE 'BLOCK' END,
    'RLS active sur les deux tables de documents concernés.'
  UNION ALL
  SELECT 'rls_no_unreviewed_write_policies',
    CASE WHEN (SELECT count(*) FROM write_policies)=2
      AND NOT EXISTS (
        SELECT 1 FROM write_policies WHERE NOT (
          (tablename='fracture_endgame_reports'
            AND policyname='fracture endgame owner update' AND cmd='UPDATE')
          OR (tablename='fracture_player_documents'
            AND policyname='fracture docs own update' AND cmd='UPDATE')
        )
      ) THEN 'PASS' ELSE 'BLOCK' END,
    'Refuser toute politique UPDATE ou ALL non revue sur les deux tables.'
  UNION ALL
  SELECT 'rls_endgame_update_destination',
    CASE WHEN EXISTS (
      SELECT 1 FROM policy WHERE tablename='fracture_endgame_reports'
        AND cmd='UPDATE' AND 'authenticated'=ANY(roles)
        AND position('auth.uid' IN lower(coalesce(qual,'')))>0
        AND position('auth.uid' IN lower(coalesce(with_check,'')))>0
        AND position('fracture_parties' IN lower(coalesce(with_check,'')))>0
        AND position('owner_user_id' IN lower(coalesce(with_check,'')))>0
        AND position('party_id' IN lower(coalesce(with_check,'')))>0
    ) THEN 'PASS' ELSE 'BLOCK' END,
    'Le propriétaire du rapport doit aussi contrôler la partie cible; revue sémantique toujours requise.'
  UNION ALL
  SELECT 'rls_player_document_destination',
    CASE WHEN EXISTS (
      SELECT 1 FROM policy WHERE tablename='fracture_player_documents'
        AND cmd='UPDATE' AND 'authenticated'=ANY(roles)
        AND position('auth.uid' IN lower(coalesce(qual,'')))>0
        AND position('auth.uid' IN lower(coalesce(with_check,'')))>0
        AND position('is_fracture_party_member' IN lower(coalesce(with_check,'')))>0
        AND position('party_id' IN lower(coalesce(with_check,'')))>0
    ) THEN 'PASS' ELSE 'BLOCK' END,
    'Le document ne peut cibler qu’une partie autorisée; revue sémantique toujours requise.'
)
SELECT check_id,status,finding FROM checks
UNION ALL
SELECT 'release_decision' AS check_id,
 CASE WHEN EXISTS (SELECT 1 FROM checks WHERE status='BLOCK') THEN 'NO_GO'
      ELSE 'REVIEW_REQUIRED' END AS status,
 'Même sans blocage statique, publication soumise à approbation et recette multicomptes.' AS finding
ORDER BY check_id;
