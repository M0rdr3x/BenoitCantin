-- SINJIRA™ — politique AAL2 additive pour les deux buckets privés du Registre.
-- Attention : SQL de déploiement contrôlé, jamais exécuté automatiquement en CI.
-- Fichier conservé sous son nom historique pour ne pas casser les validations.
-- Toute opération SELECT/INSERT/UPDATE/DELETE de photos du Registre par un
-- utilisateur doit avoir AAL2, EN PLUS des politiques propriétaires existantes.
-- Les opérations service_role existantes restent inchangées.
BEGIN;

DO $sinjira_preflight$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='storage' AND c.relname='objects' AND c.relrowsecurity=true
  ) THEN
    RAISE EXCEPTION 'SINJIRA: storage.objects RLS indisponible';
  END IF;

  IF (SELECT count(*) FROM storage.buckets
      WHERE id IN ('sinjira-character-sources','sinjira-character-submissions')
        AND public=false) <> 2 THEN
    RAISE EXCEPTION 'SINJIRA: deux buckets de photos du Registre prives obligatoires';
  END IF;

  -- Les politiques propriétaires ne doivent JAMAIS être acceptées sur des
  -- fragments de texte : (... AND auth.uid()) OR TRUE reste une faille.
  -- Comparer les expressions complètes de pg_policies en lecture seule,
  -- après normalisation des espaces PostgreSQL. Tout changement de forme
  -- (y compris une évolution légitime de la représentation SQL) exige une
  -- revue explicite AVANT l'application de cette migration.
  IF EXISTS (
    SELECT 1 FROM (
      VALUES
        ('char_source_insert_own','INSERT','((bucket_id = ''sinjira-character-sources''::text) AND ((storage.foldername(name))[1] = (auth.uid())::text))'),
        ('char_source_select_own','SELECT','((bucket_id = ''sinjira-character-sources''::text) AND ((storage.foldername(name))[1] = (auth.uid())::text))'),
        ('char_source_delete_own','DELETE','((bucket_id = ''sinjira-character-sources''::text) AND ((storage.foldername(name))[1] = (auth.uid())::text))'),
        ('sinjira character photo own insert','INSERT','((bucket_id = ''sinjira-character-submissions''::text) AND ((storage.foldername(name))[1] = (( SELECT auth.uid() AS uid))::text))'),
        ('sinjira character photo own select','SELECT','((bucket_id = ''sinjira-character-submissions''::text) AND ((storage.foldername(name))[1] = (( SELECT auth.uid() AS uid))::text))'),
        ('sinjira character photo own update','UPDATE','((bucket_id = ''sinjira-character-submissions''::text) AND ((storage.foldername(name))[1] = (( SELECT auth.uid() AS uid))::text))'),
        ('sinjira character photo own delete','DELETE','((bucket_id = ''sinjira-character-submissions''::text) AND ((storage.foldername(name))[1] = (( SELECT auth.uid() AS uid))::text))')
    ) AS expected(policy_name,policy_cmd,owner_predicate)
    WHERE NOT EXISTS (
      SELECT 1 FROM pg_policies p
      WHERE p.schemaname='storage' AND p.tablename='objects'
        AND p.policyname=expected.policy_name
        AND p.cmd=expected.policy_cmd
        AND p.permissive='PERMISSIVE'
        AND p.roles=ARRAY['authenticated'::name]
        AND coalesce(regexp_replace(p.qual,'[[:space:]]','','g'),'') =
          CASE WHEN expected.policy_cmd IN ('SELECT','UPDATE','DELETE')
            THEN regexp_replace(expected.owner_predicate,'[[:space:]]','','g')
            ELSE '' END
        AND coalesce(regexp_replace(p.with_check,'[[:space:]]','','g'),'') =
          CASE WHEN expected.policy_cmd IN ('INSERT','UPDATE')
            THEN regexp_replace(expected.owner_predicate,'[[:space:]]','','g')
            ELSE '' END
    )
  ) THEN
    RAISE EXCEPTION 'SINJIRA: politique proprietaire drift ou affaiblissement, migration refusee';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='storage' AND tablename='objects'
      AND policyname IN (
        'sinjira_character_sources_insert_requires_aal2',
        'sinjira_character_photos_select_requires_aal2',
        'sinjira_character_photos_update_requires_aal2',
        'sinjira_character_photos_delete_requires_aal2'
      )
  ) THEN
    RAISE EXCEPTION 'SINJIRA: une politique AAL2 existe deja, verifier avant toute migration';
  END IF;
END
$sinjira_preflight$;

-- Nom historique conservé : concerne aussi le bucket submissions.
CREATE POLICY sinjira_character_sources_insert_requires_aal2
ON storage.objects AS RESTRICTIVE FOR INSERT TO authenticated
WITH CHECK (
  bucket_id NOT IN ('sinjira-character-sources','sinjira-character-submissions')
  OR ((SELECT auth.jwt()->>'aal') = 'aal2')
);

CREATE POLICY sinjira_character_photos_select_requires_aal2
ON storage.objects AS RESTRICTIVE FOR SELECT TO authenticated
USING (
  bucket_id NOT IN ('sinjira-character-sources','sinjira-character-submissions')
  OR ((SELECT auth.jwt()->>'aal') = 'aal2')
);

CREATE POLICY sinjira_character_photos_update_requires_aal2
ON storage.objects AS RESTRICTIVE FOR UPDATE TO authenticated
USING (
  bucket_id NOT IN ('sinjira-character-sources','sinjira-character-submissions')
  OR ((SELECT auth.jwt()->>'aal') = 'aal2')
)
WITH CHECK (
  bucket_id NOT IN ('sinjira-character-sources','sinjira-character-submissions')
  OR ((SELECT auth.jwt()->>'aal') = 'aal2')
);

CREATE POLICY sinjira_character_photos_delete_requires_aal2
ON storage.objects AS RESTRICTIVE FOR DELETE TO authenticated
USING (
  bucket_id NOT IN ('sinjira-character-sources','sinjira-character-submissions')
  OR ((SELECT auth.jwt()->>'aal') = 'aal2')
);

COMMENT ON POLICY sinjira_character_sources_insert_requires_aal2 ON storage.objects IS
  'Registre SINJIRA : AAL2 pour INSERT dans les deux buckets privés, en plus des politiques propriétaire.';
COMMENT ON POLICY sinjira_character_photos_select_requires_aal2 ON storage.objects IS
  'Registre SINJIRA : AAL2 pour SELECT dans les deux buckets privés, en plus des politiques propriétaire.';
COMMENT ON POLICY sinjira_character_photos_update_requires_aal2 ON storage.objects IS
  'Registre SINJIRA : AAL2 pour UPDATE dans les deux buckets privés (USING et WITH CHECK).';
COMMENT ON POLICY sinjira_character_photos_delete_requires_aal2 ON storage.objects IS
  'Registre SINJIRA : AAL2 pour DELETE dans les deux buckets privés, en plus des politiques propriétaire.';
COMMIT;
