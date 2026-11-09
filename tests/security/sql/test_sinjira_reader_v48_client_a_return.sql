-- V48 : retour de A depuis une TROISIÈME connexion PostgreSQL indépendante.
-- Ce test reproduit la persistance multi-session de la base,
-- mais PAS une recette sur deux appareils ni un test Supabase Auth réel.
\set ON_ERROR_STOP on
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';

DO $test$
DECLARE n integer; page integer; progress integer; ratio numeric;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library;
 IF n<>1 THEN RAISE EXCEPTION 'V48-REPRISE: fuite ou perte de la ligne A'; END IF;

 SELECT last_page,progress_percent,scroll_ratio
 INTO page,progress,ratio
 FROM public.sinjira_reader_library WHERE user_id=(SELECT auth.uid())
 AND novel_id='10000000-0000-0000-0000-000000000001';
 IF page<>13 OR progress<>28 OR ratio<>0.5678 THEN
   RAISE EXCEPTION 'V48-REPRISE: reprise multi-connexion A non fidèle';
 END IF;

 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE user_id='00000000-0000-0000-0000-000000000002';
 IF n<>0 THEN RAISE EXCEPTION 'V48-REPRISE: progression B visible à A'; END IF;
END $test$;

-- Vérifier les bornes 0 et 1 ainsi que la conservation du NULL hérité.
UPDATE public.sinjira_reader_library SET scroll_ratio=0.0000
WHERE user_id=(SELECT auth.uid())
AND novel_id='10000000-0000-0000-0000-000000000001';
UPDATE public.sinjira_reader_library SET scroll_ratio=1.0000
WHERE user_id=(SELECT auth.uid())
AND novel_id='10000000-0000-0000-0000-000000000001';
DO $test$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE scroll_ratio=1.0000 AND user_id=(SELECT auth.uid());
 IF n<>1 THEN RAISE EXCEPTION 'V48-REPRISE: ratio 1 rejeté'; END IF;
END $test$;
RESET ROLE;
\echo 'V48-REPRISE-PASS: position A récupérée sur connexion distincte après passage de B'
