-- Contrat de non-régression: privilégier les droits SQL effectifs et non les ACL directes.
begin;
create extension if not exists pgtap with schema extensions;
set local search_path=pg_catalog,public,extensions;

select plan(8);

select ok(exists(
  select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.prokind in ('f','p') and left(p.proname,8)='service_'
), 'le contrat des RPC serveur ne peut pas réussir sur un inventaire vide');

select is(
  (select string_agg(p.oid::regprocedure::text, ', ' order by p.oid::regprocedure::text)
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.prosecdef
     and has_function_privilege('anon',p.oid,'EXECUTE')),
  null::text, 'aucune fonction SECURITY DEFINER publique exécutable par anon'
);

select is(
  (select string_agg(p.oid::regprocedure::text, ', ' order by p.oid::regprocedure::text)
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.prosecdef
     and has_function_privilege('authenticated',p.oid,'EXECUTE')),
  null::text, 'aucune fonction SECURITY DEFINER publique exécutable par authenticated'
);

-- Une fonction serveur SECURITY INVOKER reste une surface privilégiée si elle
-- relaie vers une implémentation interne. Le préfixe service_ est réservé au serveur.
select is(
  (select string_agg(format('%s:%s',p.oid::regprocedure,r.role_name), ', ' order by p.oid::regprocedure::text,r.role_name)
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   cross join (values ('anon'),('authenticated')) as r(role_name)
   where n.nspname='public' and p.prokind in ('f','p')
     and left(p.proname,8)='service_'
     and has_function_privilege(r.role_name,p.oid,'EXECUTE')),
  null::text, 'aucun RPC service_ public directement exécutable par les rôles navigateur'
);

select is(
  (select string_agg(p.oid::regprocedure::text, ', ' order by p.oid::regprocedure::text)
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.prokind in ('f','p')
     and left(p.proname,8)='service_' and p.prosecdef
     and not exists(select 1 from unnest(p.proconfig) as cfg(setting) where left(cfg.setting,12)='search_path=')),
  null::text, 'les RPC service_ SECURITY DEFINER fixent explicitement leur search_path'
);

-- CREATE sur un schéma applicatif peut permettre des objets homonymes
-- ou une modification de la surface RPC; USAGE légitime reste distinct.
select is(
  (select string_agg(format('%I:%s',n.nspname,r.role_name), ', ' order by n.nspname,r.role_name)
   from pg_namespace n cross join (values ('anon'),('authenticated')) as r(role_name)
   where (n.nspname in ('public','private') or left(n.nspname,8)='sinjira_')
     and has_schema_privilege(r.role_name,n.oid,'CREATE')),
  null::text, 'aucun droit CREATE navigateur dans les schémas applicatifs'
);

select is(
  (select string_agg(format('%s:%s',p.oid::regprocedure,r.role_name), ', ' order by p.oid::regprocedure::text,r.role_name)
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   cross join (values ('anon'),('authenticated')) as r(role_name)
   where (n.nspname in ('public','private') or left(n.nspname,8)='sinjira_')
     and p.prokind in ('f','p')
     and has_function_privilege(r.role_name,p.oid,'EXECUTE WITH GRANT OPTION')),
  null::text, 'aucun rôle navigateur ne peut déléguer EXECUTE sur une fonction applicative'
);

-- La vérification négative simule une erreur d'ACL, uniquement dans la
-- transaction de test locale. ROLLBACK supprime intégralement la sonde.
create function public.service_acl_contract_probe() returns integer
language sql security invoker set search_path=pg_catalog as $$ select 1 $$;
revoke all on function public.service_acl_contract_probe() from public,anon,authenticated;
grant execute on function public.service_acl_contract_probe() to authenticated;
select ok(
  has_function_privilege('authenticated','public.service_acl_contract_probe()','EXECUTE')
  and exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and left(p.proname,8)='service_'
      and p.oid='public.service_acl_contract_probe()'::regprocedure
      and has_function_privilege('authenticated',p.oid,'EXECUTE')),
  'une attribution accidentelle de EXECUTE sur un RPC serveur est détectable'
);

select * from finish();
rollback;
