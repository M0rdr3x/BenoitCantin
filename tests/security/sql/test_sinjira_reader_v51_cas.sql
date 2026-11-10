-- V51: tests VRAI schéma PostgreSQL, DB sinjira_reader_v51_lab UNIQUEMENT.
-- Après V48 A/B/A: la page du compte A vaut 13, du compte B vaut 8.
\set ON_ERROR_STOP on
DO $check$
BEGIN
 IF current_database()<>'sinjira_reader_v51_lab' THEN
  RAISE EXCEPTION 'V51: base non jetable interdite';
 END IF;
 IF (SELECT count(*) FROM public.sinjira_reader_library)<>2 THEN
  RAISE EXCEPTION 'V51: deux marque-pages fictifs attendus';
 END IF;
END $check$;

-- Migration V51 originale, la V32 a déjà été chargée par V48.
\i supabase/migrations/20261110011500_sinjira_reader_progress_revision_cas_v51.sql

DO $permissions$
BEGIN
 IF has_table_privilege('authenticated','public.sinjira_reader_library','INSERT')
  OR has_table_privilege('authenticated','public.sinjira_reader_library','UPDATE')
  OR has_table_privilege('anon','public.sinjira_reader_library','INSERT')
  OR has_table_privilege('anon','public.sinjira_reader_library','UPDATE') THEN
  RAISE EXCEPTION 'V51: ancien client peut contourner CAS par écriture directe';
 END IF;
 IF NOT has_table_privilege('authenticated','public.sinjira_reader_library','SELECT') THEN
  RAISE EXCEPTION 'V51: lecture privée par propriétaire perdue';
 END IF;
 IF NOT has_function_privilege('authenticated',
  'public.sinjira_reader_save_progress_cas(uuid,bigint,integer,integer,numeric)','EXECUTE')
  OR has_function_privilege('anon',
  'public.sinjira_reader_save_progress_cas(uuid,bigint,integer,integer,numeric)','EXECUTE')
 THEN
  RAISE EXCEPTION 'V51: permissions RPC mal configurées';
 END IF;
 IF (SELECT count(*) FROM public.sinjira_reader_library WHERE revision<>0)<>0 THEN
  RAISE EXCEPTION 'V51: progression antérieure modifiée';
 END IF;
END $permissions$;

-- L'appareil B, dont la lecture est plus récente, écrit la page 42.
SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
DO $save$
DECLARE s text;r bigint; p integer;ratio numeric;at timestamptz;
BEGIN
 SELECT result_status,result_revision,result_page,result_ratio,result_updated_at
 INTO s,r,p,ratio,at FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000001',0,42,75,0.8250);
 IF s<>'saved' OR r<>1 OR p<>42 OR ratio<>0.8250 OR at IS NULL THEN
  RAISE EXCEPTION 'V51: sauvegarde de page 42 incorrecte';
 END IF;
END $save$;

-- Appareil A: même version attendue 0, donc refuse l'ancienne page 13.
DO $conflict$
DECLARE s text;r bigint;p integer;ratio numeric;
BEGIN
 SELECT result_status,result_revision,result_page,result_ratio
 INTO s,r,p,ratio FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000001',0,13,28,1.0000);
 IF s<>'conflict' OR r<>1 OR p<>42 OR ratio<>0.8250 THEN
  RAISE EXCEPTION 'V51: ancienne sauvegarde acceptée ou conflit non explicite';
 END IF;
END $conflict$;

-- Un nouvel appareil qui relit la révision 1 peut sauver la page 43.
DO $fresh$
DECLARE s text;r bigint;p integer;
BEGIN
 SELECT result_status,result_revision,result_page
 INTO s,r,p FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000001',1,43,76,0.2500);
 IF s<>'saved' OR r<>2 OR p<>43 THEN
  RAISE EXCEPTION 'V51: sauvegarde fraîche refusée';
 END IF;
END $fresh$;

-- Une nouvelle ligne avec expected=NULL est créée une fois sans UPDATE de repli.
DO $newbook$
DECLARE s text;r bigint;p integer;
BEGIN
 SELECT result_status,result_revision,result_page
 INTO s,r,p FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000002',NULL,9,22,NULL);
 IF s<>'saved' OR r<>0 OR p<>9 THEN
  RAISE EXCEPTION 'V51: première sauvegarde non créée';
 END IF;
 SELECT result_status,result_revision,result_page
 INTO s,r,p FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000002',NULL,100,90,1.0000);
 IF s<>'conflict' OR r<>0 OR p<>9 THEN
  RAISE EXCEPTION 'V51: appel initial rejoué a écrasé la nouvelle ligne';
 END IF;
END $newbook$;

-- Entrées incorrectes ne modifient pas la table.
DO $invalid$
DECLARE denied boolean;
BEGIN
 denied:=false;
 BEGIN
  PERFORM public.sinjira_reader_save_progress_cas(
   '10000000-0000-0000-0000-000000000001',2,10001,77,0.1);
 EXCEPTION WHEN invalid_parameter_value THEN denied:=true;
 END;
 IF NOT denied THEN RAISE EXCEPTION 'V51: page au-delà des bornes acceptée'; END IF;
 denied:=false;
 BEGIN
  PERFORM public.sinjira_reader_save_progress_cas(
   '10000000-0000-0000-0000-000000000001',2,45,77,1.1);
 EXCEPTION WHEN invalid_parameter_value THEN denied:=true;
 END;
 IF NOT denied THEN RAISE EXCEPTION 'V51: ratio invalide accepté'; END IF;
END $invalid$;
RESET ROLE;

-- Aucune identité anonyme n'a le droit d'appeler le RPC.
SET ROLE anon;
SET request.jwt.claim.sub='';
DO $anon$
DECLARE denied boolean:=false;
BEGIN
 BEGIN
  PERFORM public.sinjira_reader_save_progress_cas(
   '10000000-0000-0000-0000-000000000001',2,99,99,0.1);
 EXCEPTION WHEN insufficient_privilege THEN denied:=true;
 END;
 IF NOT denied THEN RAISE EXCEPTION 'V51: appel anonyme non refusé'; END IF;
END $anon$;
RESET ROLE;

-- Deuxième compte ne peut obtenir la progression du premier via le RPC.
SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000002';
DO $isolate$
DECLARE s text;r bigint;p integer;
BEGIN
 SELECT result_status,result_revision,result_page INTO s,r,p
 FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000001',0,8,35,0.2500);
 IF s<>'saved' OR r<>1 OR p<>8 THEN
  RAISE EXCEPTION 'V51: compte B ne peut mettre à jour sa propre progression';
 END IF;
 IF (SELECT count(*) FROM public.sinjira_reader_library)<>1 THEN
  RAISE EXCEPTION 'V51: compte B lit des lignes du compte A';
 END IF;
END $isolate$;
RESET ROLE;

-- Vérifier que les deux anciens marque-pages + une nouvelle ligne sont intacts.
CREATE TEMP TABLE v51_before_replay AS
 SELECT user_id,novel_id,last_page,progress_percent,scroll_ratio,
        revision,created_at,updated_at,last_opened_at
 FROM public.sinjira_reader_library;
\i supabase/migrations/20261110011500_sinjira_reader_progress_revision_cas_v51.sql
DO $verify$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library;
 IF n<>3 THEN RAISE EXCEPTION 'V51: migration répétée perd des positions'; END IF;
 IF EXISTS(SELECT * FROM v51_before_replay
  EXCEPT SELECT user_id,novel_id,last_page,progress_percent,scroll_ratio,
    revision,created_at,updated_at,last_opened_at FROM public.sinjira_reader_library)
 OR EXISTS(
  SELECT user_id,novel_id,last_page,progress_percent,scroll_ratio,
    revision,created_at,updated_at,last_opened_at FROM public.sinjira_reader_library
  EXCEPT SELECT * FROM v51_before_replay)
 THEN RAISE EXCEPTION 'V51: deuxième exécution a changé un marque-page'; END IF;
 SELECT count(*) INTO n FROM pg_constraint
 WHERE conrelid='public.sinjira_reader_library'::regclass
 AND conname='sinjira_reader_library_revision_nonnegative';
 IF n<>1 THEN RAISE EXCEPTION 'V51: contrainte révision absente ou dupliquée'; END IF;
 IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid='public.sinjira_reader_library'::regclass)
 THEN RAISE EXCEPTION 'V51: RLS désactivée'; END IF;
END $verify$;
\echo 'V51-CAS-PASS: ancien appel rejeté, page 42 conservée puis 43, 2 comptes isolés, 2 migrations intactes'
