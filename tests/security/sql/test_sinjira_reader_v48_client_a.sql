-- V48 : client A fictif, PREMIÈRE connexion PostgreSQL indépendante.
\set ON_ERROR_STOP on
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';

DO $test$
DECLARE n integer; page integer; ratio numeric;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library;
 IF n<>1 THEN RAISE EXCEPTION 'V48-A: A lit une progression étrangère'; END IF;
 SELECT last_page,scroll_ratio INTO page,ratio
 FROM public.sinjira_reader_library
 WHERE user_id=(SELECT auth.uid())
 AND novel_id='10000000-0000-0000-0000-000000000001';
 IF page<>4 OR ratio IS NOT NULL THEN
   RAISE EXCEPTION 'V48-A: rétrocompatibilité du marque-page perdue';
 END IF;
END $test$;

-- Simulation d'une lecture sur A, puis sauvegarde répétée en UPSERT.
UPDATE public.sinjira_reader_library
SET last_page=12, progress_percent=27, scroll_ratio=0.4123,updated_at=now()
WHERE novel_id='10000000-0000-0000-0000-000000000001'
AND user_id=(SELECT auth.uid());

INSERT INTO public.sinjira_reader_library(
 user_id,novel_id,last_page,progress_percent,scroll_ratio
) VALUES (
 (SELECT auth.uid()),'10000000-0000-0000-0000-000000000001',13,28,0.5678
)
ON CONFLICT (user_id,novel_id) DO UPDATE SET
 last_page=excluded.last_page,
 progress_percent=excluded.progress_percent,
 scroll_ratio=excluded.scroll_ratio,
 updated_at=now();

DO $test$
DECLARE n integer; denied boolean;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE user_id=(SELECT auth.uid()) AND last_page=13
 AND scroll_ratio=0.5678 AND progress_percent=28;
 IF n<>1 THEN RAISE EXCEPTION 'V48-A: UPSERT de progression non conservé'; END IF;

 -- Même avec une ligne A authentifiée, les bornes 0..1 doivent être appliquées.
 denied:=false;
 BEGIN
   UPDATE public.sinjira_reader_library SET scroll_ratio=1.0001
   WHERE user_id=(SELECT auth.uid());
 EXCEPTION WHEN check_violation THEN denied:=true;
 END;
 IF NOT denied THEN RAISE EXCEPTION 'V48-A: ratio supérieur à 1 accepté'; END IF;

 denied:=false;
 BEGIN
   UPDATE public.sinjira_reader_library SET scroll_ratio=-0.0001
   WHERE user_id=(SELECT auth.uid());
 EXCEPTION WHEN check_violation THEN denied:=true;
 END;
 IF NOT denied THEN RAISE EXCEPTION 'V48-A: ratio négatif accepté'; END IF;

 SELECT count(*) INTO n FROM public.sinjira_reader_library
 WHERE user_id='00000000-0000-0000-0000-000000000002';
 IF n<>0 THEN RAISE EXCEPTION 'V48-A: progression du compte B visible'; END IF;
END $test$;
RESET ROLE;
\echo 'V48-CLIENT-A-PASS: UPSERT sauvegardé, ancien NULL conservé, ratio borné, compte B invisible'
