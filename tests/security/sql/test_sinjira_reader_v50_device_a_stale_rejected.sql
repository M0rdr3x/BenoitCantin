-- Appareil A fictif : sauvegarde ancienne de revision 0 arrive apres B.
-- Sa proposition DOIT etre rejetee SANS ecraser la position B.
\set ON_ERROR_STOP on
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';
DO $assert$
DECLARE wrote boolean; page integer; ratio numeric; rev bigint;
BEGIN
  SELECT public.sinjira_reader_v50_try_save(
    '10000000-0000-0000-0000-000000000001',
    0,12,25,0.2100) INTO wrote;
  IF wrote IS DISTINCT FROM false THEN
    RAISE EXCEPTION 'V50-A: une ecriture perimee a ete acceptee';
  END IF;
  SELECT last_page,scroll_ratio,local_test_revision INTO page,ratio,rev
  FROM public.sinjira_reader_library
  WHERE user_id=(SELECT auth.uid()) AND
        novel_id='10000000-0000-0000-0000-000000000001';
  IF page<>31 OR ratio<>0.8123 OR rev<>1 THEN
    RAISE EXCEPTION 'V50-A: une ecriture perimee a ecrase B';
  END IF;
END $assert$;
RESET ROLE;
\echo 'V50-STALE-REJECTED-PASS: position B preservee, ancien CAS refuse'
