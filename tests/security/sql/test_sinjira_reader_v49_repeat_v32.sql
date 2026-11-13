-- SINJIRA V49 — vérifier la réexécution de la V32 sans perdre des marque-pages.
-- BASE FICTIVE sinjira_reader_v48_test_only, issue du scénario V48.
-- Ce script ne doit JAMAIS être connecté à Supabase ou utilisé en production.
\set ON_ERROR_STOP on

-- Refuser d'opérer si le script n'est pas sur la base temporaire de CI.
DO $guard$
BEGIN
 IF current_database()<>'sinjira_reader_v48_test_only' THEN
  RAISE EXCEPTION 'V49: nom de base non jetable — arrêt';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n
   ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relname='sinjira_reader_library'
   AND c.relrowsecurity) THEN
  RAISE EXCEPTION 'V49: RLS absente avant répétition — arrêt';
 END IF;
END $guard$;

-- Nouvelle progression héritée : NULL signifie « page, mais défilement inconnu ».
-- Fausse identité, faux livre, jamais d'utilisateur ou de texte réels.
INSERT INTO public.sinjira_reader_library(
 user_id,novel_id,last_page,progress_percent,scroll_ratio
) VALUES(
 '00000000-0000-0000-0000-000000000001',
 '10000000-0000-0000-0000-000000000002',
 9,20,NULL
);

CREATE TEMP TABLE v49_before AS
SELECT user_id,novel_id,last_page,progress_percent,scroll_ratio,
 created_at,updated_at,last_opened_at
FROM public.sinjira_reader_library;

DO $pre$
DECLARE n int;
BEGIN
 SELECT count(*) INTO n FROM v49_before;
 IF n<>3 THEN RAISE EXCEPTION 'V49: trois marque-pages fictifs attendus, %',n; END IF;
 IF (SELECT count(*) FROM v49_before WHERE scroll_ratio IS NULL)<>1 THEN
  RAISE EXCEPTION 'V49: progression héritée NULL non représentée';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM v49_before
  WHERE user_id='00000000-0000-0000-0000-000000000001'
  AND novel_id='10000000-0000-0000-0000-000000000001'
  AND last_page=13 AND progress_percent=28 AND scroll_ratio=1.0000) THEN
  RAISE EXCEPTION 'V49: sauvegarde de A attendue non présente';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM v49_before
  WHERE user_id='00000000-0000-0000-0000-000000000002'
  AND novel_id='10000000-0000-0000-0000-000000000001'
  AND last_page=8 AND progress_percent=35 AND scroll_ratio=0.2500) THEN
  RAISE EXCEPTION 'V49: sauvegarde de B attendue non présente';
 END IF;
END $pre$;

-- Rejouer la migration originale, SANS éditeur de SQL alternatif.
\i supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql
\i supabase/migrations/20261107185500_sinjira_reader_progress_spot_v32.sql

DO $check$
DECLARE n int; r record;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library;
 IF n<>3 THEN RAISE EXCEPTION 'V49: marque-page supprimé ou dupliqué, %',n; END IF;
 IF EXISTS(
   SELECT user_id,novel_id,last_page,progress_percent,scroll_ratio,
   created_at,updated_at,last_opened_at
   FROM public.sinjira_reader_library
   EXCEPT
   SELECT * FROM v49_before
 ) OR EXISTS(
   SELECT * FROM v49_before
   EXCEPT
   SELECT user_id,novel_id,last_page,progress_percent,scroll_ratio,
   created_at,updated_at,last_opened_at
   FROM public.sinjira_reader_library
 ) THEN
  RAISE EXCEPTION 'V49: données, dates ou progression modifiées par réexécution';
 END IF;
 SELECT count(*) INTO n FROM pg_constraint
 WHERE conrelid='public.sinjira_reader_library'::regclass
 AND conname='sinjira_reader_library_scroll_ratio_range';
 IF n<>1 THEN RAISE EXCEPTION 'V49: contrainte absente ou dupliquée'; END IF;
 SELECT count(*) INTO n FROM pg_policies
 WHERE schemaname='public' AND tablename='sinjira_reader_library'
 AND policyname='sinjira reader library own';
 IF n<>1 THEN RAISE EXCEPTION 'V49: politique d accès à la ligne altérée'; END IF;
 IF (SELECT count(*) FROM public.sinjira_reader_library WHERE scroll_ratio IS NULL)<>1 THEN
  RAISE EXCEPTION 'V49: un NULL hérité a changé de signification';
 END IF;
END $check$;

-- Nouveau test de confidentialité, dans des connexions logiques simulées :
-- un compte A ne doit voir que les deux livres A, pas la progression B.
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';
DO $a$
DECLARE n int; affected int;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library;
 IF n<>2 THEN RAISE EXCEPTION 'V49: A ne voit pas exactement ses livres'; END IF;
 UPDATE public.sinjira_reader_library SET last_page=999
 WHERE user_id='00000000-0000-0000-0000-000000000002';
 GET DIAGNOSTICS affected=ROW_COUNT;
 IF affected<>0 THEN RAISE EXCEPTION 'V49: compte A a modifié le livre B'; END IF;
END $a$;
RESET ROLE;

SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000002';
DO $b$
DECLARE n int;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library;
 IF n<>1 THEN RAISE EXCEPTION 'V49: B voit des marque-pages du compte A'; END IF;
END $b$;
RESET ROLE;

SET ROLE anon;
SET request.jwt.claim.sub = '';
DO $anon$
BEGIN
 IF (SELECT count(*) FROM public.sinjira_reader_library)<>0 THEN
   RAISE EXCEPTION 'V49: progression privée lisible sans identité';
 END IF;
END $anon$;
RESET ROLE;

\echo 'V49-REPEAT-V32-PASS: migration répétée 2 fois, 3 marque-pages intacts, politiques RLS conservées'
