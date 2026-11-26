-- CANDIDAT UNIQUEMENT : environnement isolé, jamais une migration automatique.
BEGIN;
SET LOCAL lock_timeout = '3s';
SET LOCAL statement_timeout = '10s';
DO $preflight$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='storage' AND c.relname='objects' AND c.relrowsecurity) THEN
    RAISE EXCEPTION 'STORAGE_RLS_REQUIRED';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM storage.buckets WHERE id='sinjira-character-sources'
    AND public IS FALSE AND file_size_limit=10485760
    AND cardinality(allowed_mime_types)=5
    AND allowed_mime_types @> ARRAY['image/jpeg','image/png','image/webp','image/avif','image/gif']::text[]) THEN
    RAISE EXCEPTION 'REGISTRY_BUCKET_DRIFT';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='storage' AND tablename='objects'
    AND policyname='char_source_insert_own' AND permissive='PERMISSIVE'
    AND cmd='INSERT' AND roles=ARRAY['authenticated']::name[]) THEN
    RAISE EXCEPTION 'REGISTRY_INSERT_POLICY_DRIFT';
  END IF;
END
$preflight$;
CREATE POLICY registry_source_insert_mfa_canonical_candidate
ON storage.objects AS RESTRICTIVE FOR INSERT TO authenticated
WITH CHECK (
  bucket_id <> 'sinjira-character-sources' OR (
    (SELECT auth.uid()) IS NOT NULL
    AND (SELECT auth.jwt()->>'aal') = 'aal2'
    AND COALESCE((SELECT auth.jwt()->>'is_anonymous'), 'false') = 'false'
    AND split_part(name, '/', 1) = (SELECT auth.uid())::text
    AND length(name) = length((SELECT auth.uid())::text) + 41
    AND split_part(name, '/', 2) COLLATE "C" ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}[.](jpg|png|webp|avif|gif)$'
  )
);
DO $assertion$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='storage' AND tablename='objects'
    AND policyname='registry_source_insert_mfa_canonical_candidate'
    AND permissive='RESTRICTIVE' AND cmd='INSERT'
    AND roles=ARRAY['authenticated']::name[] AND with_check IS NOT NULL) THEN
    RAISE EXCEPTION 'REGISTRY_RESTRICTIVE_POLICY_MISSING';
  END IF;
END
$assertion$;
ROLLBACK;
