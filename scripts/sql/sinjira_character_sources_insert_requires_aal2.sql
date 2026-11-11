-- SINJIRA™ — extension restrictive de l'insertion de photos privées du Registre.
-- SQL de déploiement contrôlé : NE PAS appliquer en production depuis la CI.
-- Les politiques permissives existantes char_source_insert_own et la propriété
-- du dossier utilisateur restent obligatoires en plus de cette restriction.
-- Sources : Supabase Storage Access Control et Supabase Auth MFA RLS.
BEGIN;
DO $sinjira_preflight$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='storage' AND c.relname='objects' AND c.relrowsecurity=true
  ) THEN
    RAISE EXCEPTION 'SINJIRA: storage.objects RLS indisponible';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM storage.buckets WHERE id='sinjira-character-sources' AND public=false
  ) THEN
    RAISE EXCEPTION 'SINJIRA: bucket de photos prive absent ou public';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='storage' AND tablename='objects'
      AND policyname='char_source_insert_own' AND cmd='INSERT'
  ) THEN
    RAISE EXCEPTION 'SINJIRA: politique proprietaire INSERT non trouvee';
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='storage' AND tablename='objects'
      AND policyname='sinjira_character_sources_insert_requires_aal2'
  ) THEN
    RAISE EXCEPTION 'SINJIRA: politique deja presente, verifier son texte au lieu de la recreer';
  END IF;
END
$sinjira_preflight$;

CREATE POLICY sinjira_character_sources_insert_requires_aal2
ON storage.objects
AS RESTRICTIVE
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id <> 'sinjira-character-sources'
  OR ((SELECT auth.jwt()->>'aal') = 'aal2')
);

COMMENT ON POLICY sinjira_character_sources_insert_requires_aal2 ON storage.objects IS
  'SINJIRA Registry photo source insert needs AAL2 in signed access token; preserves owner-folder policy and all other buckets.';
COMMIT;
