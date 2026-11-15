-- SINJIRA™ — prévol Storage AAL2 strictement READ-ONLY.
-- Ce fichier SELECT compare l'état réel avant la migration ciblée #1002.
-- READY_FOR_REVIEW = prérequis SQL vérifiés, PAS approbation de production.
-- Ne lance aucune migration et ne contient aucune écriture.
WITH expected (policy_name,cmd,predicate) AS (
  VALUES
        ('char_source_insert_own','INSERT','((bucket_id = ''sinjira-character-sources''::text) AND ((storage.foldername(name))[1] = (auth.uid())::text))'),
        ('char_source_select_own','SELECT','((bucket_id = ''sinjira-character-sources''::text) AND ((storage.foldername(name))[1] = (auth.uid())::text))'),
        ('char_source_delete_own','DELETE','((bucket_id = ''sinjira-character-sources''::text) AND ((storage.foldername(name))[1] = (auth.uid())::text))'),
        ('sinjira character photo own insert','INSERT','((bucket_id = ''sinjira-character-submissions''::text) AND ((storage.foldername(name))[1] = (( SELECT auth.uid() AS uid))::text))'),
        ('sinjira character photo own select','SELECT','((bucket_id = ''sinjira-character-submissions''::text) AND ((storage.foldername(name))[1] = (( SELECT auth.uid() AS uid))::text))'),
        ('sinjira character photo own update','UPDATE','((bucket_id = ''sinjira-character-submissions''::text) AND ((storage.foldername(name))[1] = (( SELECT auth.uid() AS uid))::text))'),
        ('sinjira character photo own delete','DELETE','((bucket_id = ''sinjira-character-submissions''::text) AND ((storage.foldername(name))[1] = (( SELECT auth.uid() AS uid))::text))')
),
owner_rules AS (
  SELECT e.policy_name,
    (p.policyname IS NOT NULL
      AND p.cmd=e.cmd
      AND p.permissive='PERMISSIVE'
      AND p.roles=ARRAY['authenticated'::name]
      AND coalesce(regexp_replace(p.qual,'[[:space:]]','','g'),'') =
        CASE WHEN e.cmd IN ('SELECT','UPDATE','DELETE')
          THEN regexp_replace(e.predicate,'[[:space:]]','','g') ELSE '' END
      AND coalesce(regexp_replace(p.with_check,'[[:space:]]','','g'),'') =
        CASE WHEN e.cmd IN ('INSERT','UPDATE')
          THEN regexp_replace(e.predicate,'[[:space:]]','','g') ELSE '' END
    ) AS valid
  FROM expected e
  LEFT JOIN pg_policies p ON p.schemaname='storage'
    AND p.tablename='objects' AND p.policyname=e.policy_name
),
status AS (
  SELECT
    (SELECT count(*)::int FROM owner_rules WHERE valid) AS owner_rules_valid,
    (SELECT count(*)::int FROM storage.buckets
      WHERE id IN ('sinjira-character-sources','sinjira-character-submissions')
      AND public=false) AS private_buckets,
    (SELECT coalesce(bool_or(c.relrowsecurity),false)
      FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='storage' AND c.relname='objects') AS storage_rls_active,
    (SELECT count(*)::int FROM pg_policies
      WHERE schemaname='storage' AND tablename='objects'
      AND policyname IN (
        'sinjira_character_sources_insert_requires_aal2',
        'sinjira_character_photos_select_requires_aal2',
        'sinjira_character_photos_update_requires_aal2',
        'sinjira_character_photos_delete_requires_aal2'
      )) AS existing_new_policies,
    (SELECT count(*)::int FROM storage.objects
      WHERE bucket_id IN ('sinjira-character-sources','sinjira-character-submissions')) AS current_photo_objects
)
SELECT owner_rules_valid,private_buckets,storage_rls_active,
  existing_new_policies,current_photo_objects,
  CASE WHEN owner_rules_valid=7 AND private_buckets=2
    AND storage_rls_active AND existing_new_policies=0
    THEN 'READY_FOR_REVIEW' ELSE 'BLOCKED' END AS migration_preflight_status
FROM status;
