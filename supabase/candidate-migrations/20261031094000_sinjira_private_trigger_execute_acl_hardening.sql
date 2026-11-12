-- SINJIRA — droits minimaux des déclencheurs de confidentialité et de modération.
-- Nouvelle migration uniquement : ne jamais réécrire les versions de production existantes.
-- Vérification préalable basée sur le catalogue distant, en lecture seule (31 octobre 2026).
-- Aucun changement de définition, d'autorisation RLS, de donnée ou de déclencheur.
--
-- NOTE : l'exécution normale d'un trigger déjà créé ne dépend pas du droit
-- EXECUTE accordé aux rôles applicatifs sur sa fonction. Les droits
-- CREATE TRIGGER / remplacement des triggers sont une revue séparée.
-- GO production uniquement après revue indépendante et validation locale SQL/pgtap.

begin;

do $audit$
begin
  if not exists (
    select 1 from pg_proc p
    where p.oid='private.privacy_incident_retention_guard()'::regprocedure
      and p.prosecdef
      and p.prorettype='pg_catalog.trigger'::regtype
  ) then
    raise exception 'PRIVACY_INCIDENT_GUARD_NOT_VERIFIED';
  end if;
  if not exists (
    select 1 from pg_trigger t
    where t.tgfoid='private.privacy_incident_retention_guard()'::regprocedure
      and t.tgrelid='private.privacy_incident_register'::regclass
      and not t.tgisinternal
      and t.tgenabled <> 'D'
  ) then
    raise exception 'PRIVACY_INCIDENT_TRIGGER_NOT_VERIFIED';
  end if;
  if not exists (
    select 1 from pg_proc p
    where p.oid='private.safety_create_escalation_case()'::regprocedure
      and p.prosecdef
      and p.prorettype='pg_catalog.trigger'::regtype
  ) then
    raise exception 'SAFETY_ESCALATION_FUNCTION_NOT_VERIFIED';
  end if;
  if not exists (
    select 1 from pg_trigger t
    where t.tgfoid='private.safety_create_escalation_case()'::regprocedure
      and t.tgrelid='public.social_reports'::regclass
      and not t.tgisinternal
      and t.tgenabled <> 'D'
  ) then
    raise exception 'SAFETY_ESCALATION_TRIGGER_NOT_VERIFIED';
  end if;
end;
$audit$;

-- Les deux fonctions SECURITY DEFINER héritaient de EXECUTE pour PUBLIC.
-- Retirer les droits directs; ne pas toucher aux droits des tables ni des RPC.
revoke execute on function private.privacy_incident_retention_guard()
  from public, anon, authenticated;
revoke execute on function private.safety_create_escalation_case()
  from public, anon, authenticated;

do $verify$
begin
  if has_function_privilege('anon','private.privacy_incident_retention_guard()','EXECUTE')
     or has_function_privilege('authenticated','private.privacy_incident_retention_guard()','EXECUTE')
     or has_function_privilege('anon','private.safety_create_escalation_case()','EXECUTE')
     or has_function_privilege('authenticated','private.safety_create_escalation_case()','EXECUTE')
  then
    raise exception 'PRIVATE_TRIGGER_EXECUTE_ACL_STILL_EXPOSED';
  end if;
end;
$verify$;

commit;
