-- V59 : toutes les requêtes sur la base de test PostgreSQL éphémère.
\set ON_ERROR_STOP on
DO $guard$
BEGIN
 IF current_database()<>'sinjira_reader_v51_lab' THEN
  RAISE EXCEPTION 'V59: refus hors de la base de laboratoire';
 END IF;
END $guard$;

SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
-- Les statuts non publiés, les produits inactifs, les fichiers non prêts,
-- un roman sans droit et un ID inconnu doivent donner la MEME réponse opaque.
DO $denied$
DECLARE
  novel uuid;
  status text; revision bigint; page integer; ratio numeric; stamped timestamptz;
BEGIN
 FOREACH novel IN ARRAY ARRAY[
   '10000000-0000-0000-0000-000000000003'::uuid, -- pas de droit
   '10000000-0000-0000-0000-000000000004'::uuid, -- non publié
   '10000000-0000-0000-0000-000000000005'::uuid, -- produit inactif
   '10000000-0000-0000-0000-000000000006'::uuid, -- PDF non prêt
   '10000000-0000-0000-0000-000000000009'::uuid  -- inexistant
 ] LOOP
  SELECT result_status,result_revision,result_page,result_ratio,result_updated_at
    INTO status,revision,page,ratio,stamped
    FROM public.sinjira_reader_save_progress_cas(novel,NULL,12,20,0.1250);
  IF status IS DISTINCT FROM 'unavailable'
     OR revision IS NOT NULL OR page IS NOT NULL
     OR ratio IS NOT NULL OR stamped IS NOT NULL THEN
    RAISE EXCEPTION 'V59: réponse non opaque pour un roman inaccessible';
  END IF;
 END LOOP;
 IF EXISTS(
   SELECT 1 FROM public.sinjira_reader_library
    WHERE user_id=auth.uid() AND novel_id IN (
      '10000000-0000-0000-0000-000000000003'::uuid,
      '10000000-0000-0000-0000-000000000004'::uuid,
      '10000000-0000-0000-0000-000000000005'::uuid,
      '10000000-0000-0000-0000-000000000006'::uuid
    )
 ) THEN
  RAISE EXCEPTION 'V59: écriture de métadonnées malgré refus';
 END IF;
END $denied$;

-- Compte A : progression autorisée sur livre 1, après conflit CAS V51.
DO $allowed$
DECLARE status text;rev bigint;pg integer;
BEGIN
 SELECT result_status,result_revision,result_page INTO status,rev,pg
 FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000001',3,53,85,0.45);
 IF status<>'saved' OR rev<>4 OR pg<>53 THEN
   RAISE EXCEPTION 'V59: client autorisé ne peut enregistrer la progression';
 END IF;
END $allowed$;
RESET ROLE;

-- Le retrait du droit doit prendre effet sur la prochaine invocation RPC.
DELETE FROM public.user_entitlements
 WHERE user_id='00000000-0000-0000-0000-000000000001'
   AND product_id='20000000-0000-0000-0000-000000000001';

SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
DO $revoked$
DECLARE status text; rev bigint; pg integer;
BEGIN
 SELECT result_status,result_revision,result_page INTO status,rev,pg
 FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000001',4,54,86,0.55);
 IF status IS DISTINCT FROM 'unavailable' OR rev IS NOT NULL OR pg IS NOT NULL THEN
  RAISE EXCEPTION 'V59: sauvegarde après révocation du droit';
 END IF;
END $revoked$;
RESET ROLE;
DO $unchanged$
BEGIN
 IF NOT EXISTS(
  SELECT 1 FROM public.sinjira_reader_library
   WHERE user_id='00000000-0000-0000-0000-000000000001'
     AND novel_id='10000000-0000-0000-0000-000000000001'
     AND last_page=53 AND revision=4
 ) THEN RAISE EXCEPTION 'V59: marque-page modifié après révocation'; END IF;
END $unchanged$;

-- Compte outsider : ne reçoit ni progression ni statut de lecture autorisée.
SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000004';
DO $outsider$
DECLARE status text;
BEGIN
 SELECT result_status INTO status
 FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000001',NULL,13,20,0.10);
 IF status IS DISTINCT FROM 'unavailable' THEN
  RAISE EXCEPTION 'V59: utilisateur extérieur a reçu un accès CAS';
 END IF;
END $outsider$;
RESET ROLE;

-- Les comptes internes explicitement autorisés peuvent sauvegarder un roman
-- PUBLIE et PRÊT malgré l'absence de droit d'achat dans le laboratoire.
SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000003';
DO $owner$
DECLARE status text;
BEGIN
 SELECT result_status INTO status FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000007',NULL,5,2,0.02);
 IF status IS DISTINCT FROM 'saved' THEN
  RAISE EXCEPTION 'V59: propriétaire autorisé refusé';
 END IF;
 SELECT result_status INTO status FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000004',NULL,5,2,0.02);
 IF status IS DISTINCT FROM 'unavailable' THEN
  RAISE EXCEPTION 'V59: propriétaire contourne statut non publié';
 END IF;
END $owner$;
RESET ROLE;
SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000005';
DO $admin$
DECLARE status text;
BEGIN
 SELECT result_status INTO status FROM public.sinjira_reader_save_progress_cas(
  '10000000-0000-0000-0000-000000000007',NULL,5,2,0.02);
 IF status IS DISTINCT FROM 'saved' THEN
  RAISE EXCEPTION 'V59: administrateur autorisé refusé';
 END IF;
END $admin$;
RESET ROLE;

-- Même si le rôle SQL est authenticated, une session sans UID doit échouer.
SET ROLE authenticated;
SET request.jwt.claim.sub='';
DO $anonymous_jwt$
DECLARE rejected boolean:=false;
BEGIN
 BEGIN
  PERFORM public.sinjira_reader_save_progress_cas(
   '10000000-0000-0000-0000-000000000001',4,55,88,0.88);
 EXCEPTION WHEN insufficient_privilege THEN rejected:=true;
 END;
 IF NOT rejected THEN RAISE EXCEPTION 'V59: JWT vide accepté'; END IF;
END $anonymous_jwt$;
RESET ROLE;

-- Nettoyage des deux marques des comptes de test internes; sans effet sur A/B.
DELETE FROM public.sinjira_reader_library
 WHERE user_id IN (
   '00000000-0000-0000-0000-000000000003',
   '00000000-0000-0000-0000-000000000005');
DO $endcheck$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n FROM public.sinjira_reader_library;
 IF n<>3 THEN RAISE EXCEPTION 'V59: pollution des 3 marque-pages fictifs existants'; END IF;
END $endcheck$;
\echo 'V59-ENTITLEMENT-PASS: accès valide, droits refusés, révocation, published, fichier prêt, comptes isolés'
