-- SINJIRA V50 : reproduction contrôlée d'un écrasement par UPSERT ancien.
-- EXCLUSIVEMENT la base jetable sinjira_reader_v50_lab, jamais Supabase.
-- Aucun utilisateur / roman réel, aucune preuve de production obtenue.
\set ON_ERROR_STOP on

DO $guard$
BEGIN
 IF current_database()<>'sinjira_reader_v50_lab' THEN
   RAISE EXCEPTION 'V50_REFUS: base non jetable : %', current_database();
 END IF;
 IF NOT EXISTS (
   SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relname='sinjira_reader_library'
   AND c.relrowsecurity
 ) THEN
   RAISE EXCEPTION 'V50_REFUS: RLS manquante avant tout essai';
 END IF;
 IF NOT EXISTS (
   SELECT 1 FROM public.sinjira_reader_library
   WHERE user_id='00000000-0000-0000-0000-000000000001'
   AND novel_id='10000000-0000-0000-0000-000000000001'
   AND last_page=13 AND scroll_ratio=1.0000
 ) THEN
   RAISE EXCEPTION 'V50_REFUS: fixture V48 A/B/A non initialisée';
 END IF;
END $guard$;

-- Snapshot logique : l'appareil A a lu la page 13 et n'a rien rechargé.
CREATE TEMP TABLE v50_before AS
SELECT last_page,scroll_ratio,updated_at FROM public.sinjira_reader_library
WHERE user_id='00000000-0000-0000-0000-000000000001'
AND novel_id='10000000-0000-0000-0000-000000000001';

-- Même compte fictif sur un deuxième appareil. Une progression PLUS récente
-- est transmise avant l'ancienne requête encore en attente de l'appareil A.
SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
DO $newer$
DECLARE changed integer;
BEGIN
 UPDATE public.sinjira_reader_library
 SET last_page=42,progress_percent=75,scroll_ratio=0.8250,
     updated_at=now()+interval '2 minutes'
 WHERE user_id=(SELECT auth.uid())
 AND novel_id='10000000-0000-0000-0000-000000000001';
 GET DIAGNOSTICS changed=ROW_COUNT;
 IF changed<>1 THEN RAISE EXCEPTION 'V50: nouvelle sauvegarde non écrite'; END IF;
END $newer$;
RESET ROLE;

-- L'ancien appareil ne connaît QUE la page 13. L'UPSERT actuel est dépourvu
-- de version attendue ; Postgres remplace donc la progression plus récente.
SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
INSERT INTO public.sinjira_reader_library
 (user_id,novel_id,last_page,progress_percent,scroll_ratio,updated_at,last_opened_at)
VALUES
 ('00000000-0000-0000-0000-000000000001',
  '10000000-0000-0000-0000-000000000001',
  13,28,1.0000,now(),now())
ON CONFLICT (user_id,novel_id) DO UPDATE SET
 last_page=excluded.last_page,
 progress_percent=excluded.progress_percent,
 scroll_ratio=excluded.scroll_ratio,
 updated_at=excluded.updated_at,
 last_opened_at=excluded.last_opened_at;
RESET ROLE;

DO $finding$
DECLARE page integer; ratio numeric; stamp timestamptz;
BEGIN
 SELECT last_page,scroll_ratio,updated_at INTO page,ratio,stamp
 FROM public.sinjira_reader_library
 WHERE user_id='00000000-0000-0000-0000-000000000001'
 AND novel_id='10000000-0000-0000-0000-000000000001';
 IF page<>13 OR ratio<>1.0000 OR stamp>=now()+interval '1 minute' THEN
   RAISE EXCEPTION 'V50: cette fixture ne reproduit pas l écrasement';
 END IF;
END $finding$;
\echo 'V50-RISK-REPRODUCED: upsert ancien page 13 ecrase page 42, aucun compare-and-swap'

-- PROTOTYPE DE SOLUTION UNIQUEMENT DANS LA BASE ÉPHÉMÈRE.
-- NE PAS COPIER EN PRODUCTION : il faut d'abord un plan de migration
-- dédié, le modèle de privilèges/RLS, les tests Supabase et approbation.
ALTER TABLE public.sinjira_reader_library
 ADD COLUMN v50_lab_revision bigint NOT NULL DEFAULT 0
 CHECK(v50_lab_revision>=0);

-- Appareil B, version observée 0 ; écriture atomique avec UPDATE conditionnel.
SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
DO $cas_new$
DECLARE changed integer;
BEGIN
 UPDATE public.sinjira_reader_library
 SET last_page=42,progress_percent=75,scroll_ratio=0.8250,
     updated_at=now(),v50_lab_revision=v50_lab_revision+1
 WHERE user_id=(SELECT auth.uid())
 AND novel_id='10000000-0000-0000-0000-000000000001'
 AND v50_lab_revision=0;
 GET DIAGNOSTICS changed=ROW_COUNT;
 IF changed<>1 THEN RAISE EXCEPTION 'V50: CAS courant rejeté'; END IF;
END $cas_new$;
RESET ROLE;

-- Appareil A veut écrire depuis le même état de départ (version 0).
-- La condition de version empêche la perte de la page 42.
SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
DO $cas_stale$
DECLARE changed integer; page integer; rev bigint;
BEGIN
 UPDATE public.sinjira_reader_library
 SET last_page=13,progress_percent=28,scroll_ratio=1.0000,
     updated_at=now(),v50_lab_revision=v50_lab_revision+1
 WHERE user_id=(SELECT auth.uid())
 AND novel_id='10000000-0000-0000-0000-000000000001'
 AND v50_lab_revision=0;
 GET DIAGNOSTICS changed=ROW_COUNT;
 IF changed<>0 THEN RAISE EXCEPTION 'V50: mise à jour périmée acceptée'; END IF;
 SELECT last_page,v50_lab_revision INTO page,rev
 FROM public.sinjira_reader_library
 WHERE user_id=(SELECT auth.uid())
 AND novel_id='10000000-0000-0000-0000-000000000001';
 IF page<>42 OR rev<>1 THEN
   RAISE EXCEPTION 'V50: nouvelle position effacée malgré garde revision';
 END IF;
END $cas_stale$;
RESET ROLE;

-- Un appareil qui recharge la revision 1 peut sauvegarder la prochaine page.
SET ROLE authenticated;
SET request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
DO $cas_fresh$
DECLARE changed integer;
BEGIN
 UPDATE public.sinjira_reader_library
 SET last_page=43,progress_percent=76,scroll_ratio=0.2500,
     updated_at=now(),v50_lab_revision=v50_lab_revision+1
 WHERE user_id=(SELECT auth.uid())
 AND novel_id='10000000-0000-0000-0000-000000000001'
 AND v50_lab_revision=1;
 GET DIAGNOSTICS changed=ROW_COUNT;
 IF changed<>1 THEN RAISE EXCEPTION 'V50: mise à jour fraîche bloquée'; END IF;
END $cas_fresh$;
RESET ROLE;

DO $final$
DECLARE page integer; rev bigint; count_bad integer;
BEGIN
 SELECT last_page,v50_lab_revision INTO page,rev
 FROM public.sinjira_reader_library
 WHERE user_id='00000000-0000-0000-0000-000000000001'
 AND novel_id='10000000-0000-0000-0000-000000000001';
 IF page<>43 OR rev<>2 THEN
   RAISE EXCEPTION 'V50: garde atomique de version non concluante';
 END IF;
 SELECT count(*) INTO count_bad FROM public.sinjira_reader_library
 WHERE user_id='00000000-0000-0000-0000-000000000002'
 AND novel_id='10000000-0000-0000-0000-000000000001'
 AND last_page<>8;
 IF count_bad<>0 THEN RAISE EXCEPTION 'V50: un autre utilisateur a été modifié'; END IF;
END $final$;
\echo 'V50-CAS-LAB-PASS: ecriture stale refusee, page 42 conservee, revision 1 puis page 43 revision 2'
\echo 'V50-NO_GO-PRODUCTION: risque constate, solution prototype test uniquement, approbation requise'
