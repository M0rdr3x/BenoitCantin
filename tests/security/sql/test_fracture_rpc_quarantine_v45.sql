-- Fracture V45 — authentification fictive dans PostgreSQL éphémère.
-- Tous les objets et comptes ci-dessous sont de TEST; aucun serveur lié.
\set ON_ERROR_STOP on
CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN;
CREATE SCHEMA sinjira_fracture_internal;
GRANT USAGE ON SCHEMA public, sinjira_fracture_internal TO anon, authenticated, service_role;
CREATE FUNCTION public.fracture_engine_start(text) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
REVOKE ALL ON FUNCTION public.fracture_engine_start(text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.fracture_engine_start(text) TO authenticated, service_role;
CREATE FUNCTION public.fracture_engine_pick(text, bigint) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
REVOKE ALL ON FUNCTION public.fracture_engine_pick(text, bigint) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.fracture_engine_pick(text, bigint) TO authenticated, service_role;
CREATE FUNCTION public.fracture_engine_submit_keep(text, bigint[]) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
REVOKE ALL ON FUNCTION public.fracture_engine_submit_keep(text, bigint[]) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.fracture_engine_submit_keep(text, bigint[]) TO authenticated, service_role;
CREATE FUNCTION public.fracture_engine_submit_report(text, text, integer, bigint) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
REVOKE ALL ON FUNCTION public.fracture_engine_submit_report(text, text, integer, bigint) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.fracture_engine_submit_report(text, text, integer, bigint) TO authenticated, service_role;
CREATE FUNCTION public.fracture_engine_submit_accusation(text, integer[]) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
REVOKE ALL ON FUNCTION public.fracture_engine_submit_accusation(text, integer[]) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.fracture_engine_submit_accusation(text, integer[]) TO authenticated, service_role;
CREATE FUNCTION sinjira_fracture_internal.fracture_engine_start(text) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
REVOKE ALL ON FUNCTION sinjira_fracture_internal.fracture_engine_start(text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_start(text) TO authenticated, service_role;
CREATE FUNCTION sinjira_fracture_internal.fracture_engine_pick(text, bigint) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
REVOKE ALL ON FUNCTION sinjira_fracture_internal.fracture_engine_pick(text, bigint) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_pick(text, bigint) TO authenticated, service_role;
CREATE FUNCTION sinjira_fracture_internal.fracture_engine_submit_keep(text, bigint[]) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
REVOKE ALL ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_keep(text, bigint[]) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_keep(text, bigint[]) TO authenticated, service_role;
CREATE FUNCTION sinjira_fracture_internal.fracture_engine_submit_report(text, text, integer, bigint) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
REVOKE ALL ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_report(text, text, integer, bigint) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_report(text, text, integer, bigint) TO authenticated, service_role;
CREATE FUNCTION sinjira_fracture_internal.fracture_engine_submit_accusation(text, integer[]) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
REVOKE ALL ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_accusation(text, integer[]) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_accusation(text, integer[]) TO authenticated, service_role;
CREATE FUNCTION public.fracture_engine_get_state(text) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
GRANT EXECUTE ON FUNCTION public.fracture_engine_get_state(text) TO authenticated;
CREATE FUNCTION public.fracture_engine_health() RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$;
GRANT EXECUTE ON FUNCTION public.fracture_engine_health() TO authenticated;
DO $check$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n
 FROM pg_proc p JOIN pg_namespace s ON s.oid=p.pronamespace
 WHERE s.nspname IN ('public','sinjira_fracture_internal')
 AND p.proname IN ('fracture_engine_start','fracture_engine_pick',
   'fracture_engine_submit_keep','fracture_engine_submit_report',
   'fracture_engine_submit_accusation')
 AND has_function_privilege('authenticated',p.oid,'EXECUTE')
 AND NOT has_function_privilege('anon',p.oid,'EXECUTE')
 AND has_function_privilege('service_role',p.oid,'EXECUTE');
 IF n<>10 THEN RAISE EXCEPTION 'V45: précondition de 10 fonctions inexacte: %',n; END IF;
END $check$;
\i scripts/proposals/sinjira_fracture_v45_mutation_rpc_quarantine_candidate.sql
DO $check$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n
 FROM pg_proc p JOIN pg_namespace s ON s.oid=p.pronamespace
 WHERE s.nspname IN ('public','sinjira_fracture_internal')
 AND p.proname IN ('fracture_engine_start','fracture_engine_pick',
   'fracture_engine_submit_keep','fracture_engine_submit_report',
   'fracture_engine_submit_accusation')
 AND NOT has_function_privilege('authenticated',p.oid,'EXECUTE')
 AND NOT has_function_privilege('anon',p.oid,'EXECUTE')
 AND has_function_privilege('service_role',p.oid,'EXECUTE');
 IF n<>10 THEN RAISE EXCEPTION 'V45: fonctions non confinées ou maintenance bloquée: %',n; END IF;
 IF NOT has_function_privilege('authenticated','public.fracture_engine_get_state(text)','EXECUTE')
 OR NOT has_function_privilege('authenticated','public.fracture_engine_health()','EXECUTE')
 THEN RAISE EXCEPTION 'V45: RPC de lecture innocentes bloquées'; END IF;
END $check$;
SET ROLE authenticated;
DO $check$
DECLARE denied boolean:=false;
BEGIN
 BEGIN
   PERFORM public.fracture_engine_start('fake');
 EXCEPTION WHEN insufficient_privilege THEN denied:=true;
 END;
 IF NOT denied THEN RAISE EXCEPTION 'V45: le démarrage public reste callable'; END IF;
 denied:=false;
 BEGIN
   PERFORM sinjira_fracture_internal.fracture_engine_submit_report('fake','R',1,1);
 EXCEPTION WHEN insufficient_privilege THEN denied:=true;
 END;
 IF NOT denied THEN RAISE EXCEPTION 'V45: le rapport interne reste callable'; END IF;
END $check$;
RESET ROLE;
SET ROLE service_role;
DO $check$
BEGIN
 IF public.fracture_engine_start('fake')<>1 OR
    sinjira_fracture_internal.fracture_engine_submit_report('fake','R',1,1)<>1
 THEN RAISE EXCEPTION 'V45: maintenance service_role bloquée'; END IF;
END $check$;
RESET ROLE;
\echo 'V45-PASS: mutations denied to authenticated and anon, service_role preserved, readonly RPC unchanged'
