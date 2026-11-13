-- NOVA Civic Poll V7 : BANC FICTIF, utilisation PostgreSQL jetable UNIQUEMENT.
-- Aucun Supabase distant, aucune réponse politique réelle ni secret HMAC/CAPTCHA.
\set ON_ERROR_STOP on
DO $roles$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='service_role') THEN
    CREATE ROLE service_role NOLOGIN;
  END IF;
END $roles$;
GRANT USAGE ON SCHEMA public TO anon,authenticated,service_role;
-- Migration originale GIT pour une BASE TEMPORAIRE seulement.
\i supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql
DO $check$
BEGIN
  IF (SELECT count(*) FROM public.nova_poll_questions
      WHERE poll_version='nova-consultation-v1')<>8 THEN
    RAISE EXCEPTION 'V7: corpus fictif non initialisé avec 8 questions officielles';
  END IF;
  IF (SELECT count(*) FROM public.nova_poll_receipts)<>0 THEN
    RAISE EXCEPTION 'V7: base jetable non vide';
  END IF;
END $check$;
\echo 'NOVA-V7-LAB-SETUP-PASS: 8 questions, 0 bulletins, migration Git chargée en local'
