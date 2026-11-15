-- V48 : client B fictif, DEUXIÈME connexion PostgreSQL indépendante.
\set ON_ERROR_STOP on
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000002';

DO $test$
DECLARE n integer; page integer; ratio numeric; affected integer;
DECLARE denied boolean:=false;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library;
 IF n<>1 THEN RAISE EXCEPTION 'V48-B: B voit les données de A'; END IF;
 SELECT last_page,scroll_ratio INTO page,ratio
 FROM public.sinjira_reader_library
 WHERE user_id=(SELECT auth.uid())
 AND novel_id='10000000-0000-0000-0000-000000000001';
 IF page<>7 OR ratio IS NOT NULL THEN
   RAISE EXCEPTION 'V48-B: progression B héritée invalide';
 END IF;

 -- A reste invisible : cette modification ne doit toucher aucune ligne.
 UPDATE public.sinjira_reader_library SET scroll_ratio=0.9999
 WHERE user_id='00000000-0000-0000-0000-000000000001';
 GET DIAGNOSTICS affected=ROW_COUNT;
 IF affected<>0 THEN RAISE EXCEPTION 'V48-B: B modifie le marque-page de A'; END IF;

 -- La politique WITH CHECK interdit de créer une ligne pour l'identité A.
 BEGIN
   INSERT INTO public.sinjira_reader_library
     (user_id,novel_id,last_page,progress_percent,scroll_ratio)
   VALUES
     ('00000000-0000-0000-0000-000000000001',
      '10000000-0000-0000-0000-000000000002',1,0,0.1111);
 EXCEPTION WHEN insufficient_privilege THEN denied:=true;
 END;
 IF NOT denied THEN RAISE EXCEPTION 'V48-B: fausse insertion au nom de A acceptée'; END IF;
END $test$;

UPDATE public.sinjira_reader_library
 SET last_page=8, progress_percent=35,scroll_ratio=0.2500
 WHERE user_id=(SELECT auth.uid())
 AND novel_id='10000000-0000-0000-0000-000000000001';
DO $test$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE user_id=(SELECT auth.uid()) AND last_page=8 AND scroll_ratio=0.2500;
 IF n<>1 THEN RAISE EXCEPTION 'V48-B: B ne peut sauvegarder sa propre position'; END IF;
END $test$;
RESET ROLE;

-- Malgré les GRANT de table hérités, anon n'a aucune politique RLS permissive.
SET ROLE anon;
SET request.jwt.claim.sub = '';
DO $test$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library;
 IF n<>0 THEN RAISE EXCEPTION 'V48-B: anon peut lire des positions privées'; END IF;
END $test$;
RESET ROLE;
\echo 'V48-CLIENT-B-PASS: identité distincte, usurpation refusée, compte A invisible, anon isolé'
