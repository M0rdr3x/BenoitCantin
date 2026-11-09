-- Identite B distincte : elle ne peut ni lire ni alterer A.
\set ON_ERROR_STOP on
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000002';
DO $assert$
DECLARE n integer; wrote boolean;
BEGIN
  SELECT count(*) INTO n FROM public.sinjira_reader_library
  WHERE user_id='00000000-0000-0000-0000-000000000001';
  IF n<>0 THEN RAISE EXCEPTION 'V50: B peut lire les positions privees de A'; END IF;
  -- La fonction choisit toujours auth.uid(), elle ne recoit pas de user_id cible.
  SELECT public.sinjira_reader_v50_try_save(
    '10000000-0000-0000-0000-000000000002',
    0,9,30,0.4000) INTO wrote;
  IF wrote IS DISTINCT FROM false THEN
    RAISE EXCEPTION 'V50: insertion implicite inattendue pour un roman absent';
  END IF;
END $assert$;
RESET ROLE;
-- Retour de A apres rejet : recuperation de la position B, puis
-- nouvelle demande explicitement choisie par A avec la revision 1.
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';
DO $assert$
DECLARE wrote boolean; page integer; ratio numeric; rev bigint;
BEGIN
  SELECT public.sinjira_reader_v50_try_save(
    '10000000-0000-0000-0000-000000000001',
    1,33,62,0.8500) INTO wrote;
  IF wrote IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'V50: une correction explicite sur revision 1 est refusee';
  END IF;
  SELECT last_page,scroll_ratio,local_test_revision INTO page,ratio,rev
  FROM public.sinjira_reader_library WHERE user_id=(SELECT auth.uid())
    AND novel_id='10000000-0000-0000-0000-000000000001';
  IF page<>33 OR ratio<>0.8500 OR rev<>2 THEN
    RAISE EXCEPTION 'V50: revision de la correction A incorrecte';
  END IF;
END $assert$;
RESET ROLE;
\echo 'V50-RLS-RECONCILE-PASS: droits propres, reprise volontaire revision1->2'
