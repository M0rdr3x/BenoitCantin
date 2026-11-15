-- SINJIRA / Fracture V41 — prévol reproductible en lecture seule.
-- Ne consulte aucune partie, aucun bulletin, aucune identité ni aucun journal.
-- La présence d'un PASS ne remplace PAS un essai multicomptes ni une revue RLS.
-- Ne pas placer dans supabase/migrations/ et ne jamais l'appliquer comme DDL.
WITH
  engine_tables AS (
    SELECT c.oid,c.relname,c.relrowsecurity
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relkind IN ('r','p')
      AND c.relname = ANY(ARRAY[
        'fracture_engine_actions','fracture_engine_cards',
        'fracture_engine_events','fracture_engine_games',
        'fracture_engine_rounds','fracture_engine_seats',
        'fracture_engine_votes'
      ]::text[])
  ),
  routines AS (
    SELECT n.nspname AS routine_schema,p.proname,p.prosrc,p.oid
    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
    WHERE n.nspname IN ('public','sinjira_fracture_internal')
      AND (p.proname LIKE 'fracture_%' OR p.proname LIKE '_fracture_%')
  ),
  checks AS (
    SELECT 'engine_internal_rls'::text AS check_id,
      CASE WHEN (SELECT count(*) FROM engine_tables)=7 AND
        (SELECT count(*) FROM engine_tables WHERE relrowsecurity)=7
        THEN 'PASS' ELSE 'BLOCK' END::text AS status,
      'Sept tables internes attendues avec RLS active.'::text AS finding
    UNION ALL
    SELECT 'engine_no_web_table_grants',
      CASE WHEN (SELECT count(*) FROM engine_tables)=7 AND NOT EXISTS (
        SELECT 1 FROM engine_tables t WHERE
          has_table_privilege('anon',t.oid,'SELECT') OR
          has_table_privilege('anon',t.oid,'INSERT') OR
          has_table_privilege('anon',t.oid,'UPDATE') OR
          has_table_privilege('anon',t.oid,'DELETE') OR
          has_table_privilege('authenticated',t.oid,'SELECT') OR
          has_table_privilege('authenticated',t.oid,'INSERT') OR
          has_table_privilege('authenticated',t.oid,'UPDATE') OR
          has_table_privilege('authenticated',t.oid,'DELETE')
      ) THEN 'PASS' ELSE 'BLOCK' END,
      'Aucun droit direct de lecture/écriture Web sur les sept tables internes.'
    UNION ALL
    SELECT 'public_engine_rpc_anon',
      CASE WHEN NOT EXISTS (
        SELECT 1 FROM routines r
        WHERE r.routine_schema='public'
          AND r.proname = ANY(ARRAY[
            'fracture_engine_get_state','fracture_engine_get_state_safe',
            'fracture_engine_start','fracture_engine_pick',
            'fracture_engine_submit_keep','fracture_engine_submit_report',
            'fracture_engine_submit_accusation'
          ]::text[])
          AND has_function_privilege('anon',r.oid,'EXECUTE')
      ) THEN 'PASS' ELSE 'BLOCK' END,
      'Les points d’entrée du moteur ne doivent pas être exécutables par anon.'
    UNION ALL
    SELECT 'legacy_final_bonus',
      CASE WHEN EXISTS (
        SELECT 1 FROM routines
        WHERE routine_schema='public'
          AND proname='_fracture_resolve_final_vote'
          AND position('then 5 else 0' IN lower(prosrc))>0
      ) THEN 'BLOCK' ELSE 'REVIEW' END,
      'Le moteur historique contient +5; le manuel courant indique +3, dont le mode de décompte reste à arbitrer.'
    UNION ALL
    SELECT 'legacy_automatic_seats',
      CASE WHEN EXISTS (
        SELECT 1 FROM routines
        WHERE routine_schema='public'
          AND proname='_fracture_start_round'
          AND position('seat_kind=''bot''' IN lower(prosrc))>0
      ) THEN 'BLOCK' ELSE 'REVIEW' END,
      'Le moteur historique commande des sièges bots; l’édition Solo/Duo exige un contrôle humain.'
    UNION ALL
    SELECT 'legacy_engine_version',
      CASE WHEN EXISTS (
        SELECT 1 FROM routines
        WHERE routine_schema='sinjira_fracture_internal'
          AND proname='fracture_engine_start'
          AND position('24.4.6' IN prosrc)>0
      ) THEN 'BLOCK' ELSE 'REVIEW' END,
      'Version serveur historique; réconcilier avec les règles modernes V36–V40.'
    UNION ALL
    SELECT 'endgame_update_party_integrity',
      CASE WHEN EXISTS (
        SELECT 1 FROM pg_policies WHERE schemaname='public'
          AND tablename='fracture_endgame_reports' AND cmd='UPDATE'
          AND position('fracture_parties' IN lower(coalesce(with_check,'')))>0
      ) THEN 'REVIEW' ELSE 'BLOCK' END,
      'La politique UPDATE doit vérifier aussi les droits sur la partie cible (pas seulement owner_user_id).'
    UNION ALL
    SELECT 'player_documents_update_membership',
      CASE WHEN EXISTS (
        SELECT 1 FROM pg_policies WHERE schemaname='public'
          AND tablename='fracture_player_documents' AND cmd='UPDATE'
          AND position('is_fracture_party_member' IN lower(coalesce(with_check,'')))>0
      ) THEN 'REVIEW' ELSE 'BLOCK' END,
      'La politique UPDATE doit vérifier aussi l’appartenance à la partie cible.'
    UNION ALL
    SELECT 'raw_state_member_boundary',
      CASE WHEN EXISTS (
        SELECT 1 FROM routines WHERE routine_schema='public'
          AND proname='_fracture_engine_get_state_raw'
          AND position('_fracture_member_seat' IN prosrc)>0
          AND position('NOT_A_MEMBER' IN prosrc)>0
      ) THEN 'REVIEW' ELSE 'BLOCK' END,
      'Indices de contrôle d’adhésion, sans preuve de non-divulgation inter-comptes.'
    UNION ALL
    SELECT 'active_session_validation',
      CASE WHEN EXISTS (
        SELECT 1 FROM routines WHERE routine_schema='sinjira_fracture_internal'
          AND proname='fracture_engine_submit_report'
          AND (position('auth.sessions' IN lower(prosrc))>0
            OR position('session_id' IN lower(prosrc))>0)
      ) THEN 'REVIEW' ELSE 'BLOCK' END,
      'Vérifier la révocation des sessions sur les mutations sensibles, sans conclure sur le seul texte SQL.'
  )
SELECT check_id,status,finding FROM checks ORDER BY check_id;
