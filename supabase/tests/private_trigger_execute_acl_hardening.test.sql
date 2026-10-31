-- Exécuter dans une base locale reconstruite avec la migration 20261031094000.
begin;
create extension if not exists pgtap with schema extensions;
set local search_path=pg_catalog,public,private,extensions;
select plan(8);

select ok(not has_function_privilege('anon','private.privacy_incident_retention_guard()','EXECUTE'),
  'anon ne peut plus exécuter directement le guard de rétention');
select ok(not has_function_privilege('authenticated','private.privacy_incident_retention_guard()','EXECUTE'),
  'authenticated ne peut plus exécuter directement le guard de rétention');
select ok(not has_function_privilege('anon','private.safety_create_escalation_case()','EXECUTE'),
  'anon ne peut plus exécuter directement le trigger escalation');
select ok(not has_function_privilege('authenticated','private.safety_create_escalation_case()','EXECUTE'),
  'authenticated ne peut plus exécuter directement le trigger escalation');

select ok(exists (
  select 1 from pg_trigger t
  where t.tgfoid='private.privacy_incident_retention_guard()'::regprocedure
    and t.tgrelid='private.privacy_incident_register'::regclass
    and t.tgenabled <> 'D' and not t.tgisinternal
), 'le trigger de conservation demeure actif');
select ok(exists (
  select 1 from pg_trigger t
  where t.tgfoid='private.safety_create_escalation_case()'::regprocedure
    and t.tgrelid='public.social_reports'::regclass
    and t.tgenabled <> 'D' and not t.tgisinternal
), 'le trigger de sécurité demeure actif');

select ok(exists (
  select 1 from pg_proc p
  where p.oid='private.privacy_incident_retention_guard()'::regprocedure
    and p.prosecdef and p.prorettype='pg_catalog.trigger'::regtype
), 'la définition du guard reste SECURITY DEFINER et trigger');
select ok(exists (
  select 1 from pg_proc p
  where p.oid='private.safety_create_escalation_case()'::regprocedure
    and p.prosecdef and p.prorettype='pg_catalog.trigger'::regtype
), 'la définition d’escalade reste SECURITY DEFINER et trigger');

select * from finish();
rollback;
