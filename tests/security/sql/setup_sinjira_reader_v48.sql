-- SINJIRA V48 — fixture PostgreSQL FICTIVE et éphémère, JAMAIS PRODUCTION.
-- Les UUID de compte et de roman ci-dessous ne désignent aucun utilisateur réel.
\set ON_ERROR_STOP on
CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE SCHEMA auth;
CREATE TABLE auth.users (id uuid PRIMARY KEY);
CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE
AS $$ SELECT nullif(current_setting('request.jwt.claim.sub', true),'')::uuid $$;
GRANT USAGE ON SCHEMA auth TO anon, authenticated;
GRANT EXECUTE ON FUNCTION auth.uid() TO anon, authenticated;

CREATE TABLE public.sinjira_novels (id uuid PRIMARY KEY);
CREATE TABLE public.sinjira_reader_library (
 user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 novel_id uuid NOT NULL REFERENCES public.sinjira_novels(id) ON DELETE CASCADE,
 last_page integer NOT NULL DEFAULT 1 CHECK(last_page >= 1 AND last_page <= 10000),
 progress_percent integer NOT NULL DEFAULT 0
   CHECK(progress_percent >= 0 AND progress_percent <= 100),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 last_opened_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT sinjira_reader_library_pkey PRIMARY KEY(user_id,novel_id)
);
ALTER TABLE public.sinjira_reader_library ENABLE ROW LEVEL SECURITY;
CREATE POLICY "sinjira reader library own" ON public.sinjira_reader_library
 FOR ALL TO authenticated
 USING ((SELECT auth.uid()) = user_id)
 WITH CHECK ((SELECT auth.uid()) = user_id);

-- Reproduit volontairement la situation de GRANT observée en production :
-- la RLS doit cacher toutes les lignes à anon, même avec les GRANT.
GRANT SELECT,INSERT,UPDATE,DELETE ON public.sinjira_reader_library TO anon, authenticated;

INSERT INTO auth.users(id) VALUES
 ('00000000-0000-0000-0000-000000000001'),
 ('00000000-0000-0000-0000-000000000002');
INSERT INTO public.sinjira_novels(id) VALUES
 ('10000000-0000-0000-0000-000000000001'),
 ('10000000-0000-0000-0000-000000000002');

-- Progressions héritées avant V32, NULL implicite attendu après migration.
INSERT INTO public.sinjira_reader_library(user_id,novel_id,last_page,progress_percent)
VALUES
 ('00000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',4,18),
 ('00000000-0000-0000-0000-000000000002',
  '10000000-0000-0000-0000-000000000001',7,30);

-- Applique la migration ORIGINALE du dépôt uniquement à cette base jetable.
\i supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql

DO $test$
DECLARE p integer; s integer; n integer;
BEGIN
 SELECT numeric_precision, numeric_scale INTO p,s
 FROM information_schema.columns
 WHERE table_schema='public' AND table_name='sinjira_reader_library'
 AND column_name='scroll_ratio';
 IF p IS DISTINCT FROM 5 OR s IS DISTINCT FROM 4 THEN
   RAISE EXCEPTION 'V48: le ratio doit être numeric(5,4), obtenu %,%',p,s;
 END IF;
 SELECT count(*) INTO n FROM pg_constraint
 WHERE conrelid='public.sinjira_reader_library'::regclass
 AND conname='sinjira_reader_library_scroll_ratio_range';
 IF n<>1 THEN RAISE EXCEPTION 'V48: la contrainte de ratio est absente'; END IF;
 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE scroll_ratio IS NULL;
 IF n<>2 THEN RAISE EXCEPTION 'V48: les deux progressions héritées ne sont pas conservées'; END IF;
END $test$;
\echo 'V48-SETUP-PASS: migration originale V32 appliquée à deux lignes fictives héritées'
