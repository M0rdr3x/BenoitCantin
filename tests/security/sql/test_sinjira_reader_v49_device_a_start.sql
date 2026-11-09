-- SINJIRA V49: appareil A, même compte fictif que l'appareil B.
-- Le paquet de sauvegarde à 13:00 est préparé, non transmis avant B.
-- Aucun login ni UUID réel. Base PostgreSQL éphémère seulement.
\set ON_ERROR_STOP on
SET ROLE authenticated;
SET request.jwt.claim.sub = '00000000-0000-0000-0000-000000000001';
DO $test$
DECLARE n integer;
BEGIN
  SELECT count(*) INTO n FROM public.sinjira_reader_library
  WHERE user_id=(SELECT auth.uid()) AND last_page=4 AND scroll_ratio IS NULL;
  IF n<>1 THEN RAISE EXCEPTION 'V49: fixture initiale A incorrecte'; END IF;
END $test$;
RESET ROLE;
\echo 'V49-DEVICE-A-START-PASS: demande A ancienne (13:00) prete, pas encore envoyee'
