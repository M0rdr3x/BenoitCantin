-- Appareil B fictif : revision 0, commit le plus recent du meme compte.
\set ON_ERROR_STOP on
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';
DO $assert$
DECLARE wrote boolean; page integer; ratio numeric; rev bigint;
BEGIN
  SELECT public.sinjira_reader_v50_try_save(
    '10000000-0000-0000-0000-000000000001',
    0,31,60,0.8123) INTO wrote;
  IF wrote IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'V50-B: le premier CAS sur revision 0 est refuse';
  END IF;
  SELECT last_page,scroll_ratio,local_test_revision INTO page,ratio,rev
  FROM public.sinjira_reader_library
  WHERE user_id=(SELECT auth.uid()) AND
        novel_id='10000000-0000-0000-0000-000000000001';
  IF page<>31 OR ratio<>0.8123 OR rev<>1 THEN
    RAISE EXCEPTION 'V50-B: position B incorrecte ou revision non incrementee';
  END IF;
END $assert$;
RESET ROLE;
\echo 'V50-B-FRESH-PASS: revision 0->1, page31/ratio0.8123'
