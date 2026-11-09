-- SINJIRA V50: PROTOTYPE CAS SUR LA BASE JETABLE V49 UNIQUEMENT.
-- Repart de la fixture V48; ne doit JAMAIS etre applique a Supabase.
\set ON_ERROR_STOP on
ALTER TABLE public.sinjira_reader_library
  ADD COLUMN local_test_revision bigint NOT NULL DEFAULT 0
  CHECK (local_test_revision >= 0);
-- Remise a zero du seul lecteur FICTIF du banc d'essai.
UPDATE public.sinjira_reader_library
SET last_page=4, progress_percent=18, scroll_ratio=NULL,
    local_test_revision=0,updated_at='2026-11-09T13:00:00Z'
WHERE user_id='00000000-0000-0000-0000-000000000001'
AND novel_id='10000000-0000-0000-0000-000000000001';

-- Illustrer une condition atomique de concurrence, qui respecte la RLS.
-- Aucune fonction SECURITY DEFINER, aucun role service_role.
CREATE FUNCTION public.sinjira_reader_v50_try_save(
  novel_uuid uuid,
  expected_revision bigint,
  next_page integer,
  next_percent integer,
  next_ratio numeric
) RETURNS boolean LANGUAGE plpgsql SECURITY INVOKER
SET search_path = public, pg_temp AS $func$
DECLARE changed integer;
BEGIN
  UPDATE public.sinjira_reader_library
  SET last_page=next_page,
      progress_percent=next_percent,
      scroll_ratio=next_ratio,
      local_test_revision=local_test_revision+1,
      updated_at=now()
  WHERE user_id=(SELECT auth.uid())
    AND novel_id=novel_uuid
    AND local_test_revision=expected_revision;
  GET DIAGNOSTICS changed=ROW_COUNT;
  RETURN changed=1;
END $func$;
REVOKE ALL ON FUNCTION public.sinjira_reader_v50_try_save(
  uuid,bigint,integer,integer,numeric) FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.sinjira_reader_v50_try_save(
  uuid,bigint,integer,integer,numeric) TO authenticated;
DO $assert$
BEGIN
  IF has_function_privilege('anon',
    'public.sinjira_reader_v50_try_save(uuid,bigint,integer,integer,numeric)',
    'EXECUTE') THEN
    RAISE EXCEPTION 'V50: anon peut appeler le prototype CAS';
  END IF;
END $assert$;
\echo 'V50-SETUP-PASS: prototype CAS atomique/security invoker uniquement local'
