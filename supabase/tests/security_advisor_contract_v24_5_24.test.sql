begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(4);

select is(
  (
    select count(*)::int
    from pg_class c
    join pg_namespace n on n.oid=c.relnamespace
    where n.nspname in ('public','private')
      and c.relkind='r'
      and c.relrowsecurity
      and not exists(select 1 from pg_policy pol where pol.polrelid=c.oid)
      and (
        has_table_privilege('anon',c.oid,'SELECT')
        or has_table_privilege('anon',c.oid,'INSERT')
        or has_table_privilege('anon',c.oid,'UPDATE')
        or has_table_privilege('anon',c.oid,'DELETE')
        or has_table_privilege('authenticated',c.oid,'SELECT')
        or has_table_privilege('authenticated',c.oid,'INSERT')
        or has_table_privilege('authenticated',c.oid,'UPDATE')
        or has_table_privilege('authenticated',c.oid,'DELETE')
      )
  ),
  0,
  'toute table SINJIRA RLS sans policy reste sans CRUD direct anon/authenticated'
);

select is(
  (
    select string_agg(p.oid::regprocedure::text, ', ' order by p.oid::regprocedure::text)
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.prosecdef
      and has_function_privilege('anon',p.oid,'EXECUTE')
  ),
  null::text,
  'aucune fonction SECURITY DEFINER public n’est exécutable par anon'
);

select is(
  (
    select string_agg(p.oid::regprocedure::text, ', ' order by p.oid::regprocedure::text)
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.prosecdef
      and has_function_privilege('authenticated',p.oid,'EXECUTE')
  ),
  null::text,
  'aucune fonction SECURITY DEFINER public n’est exécutable directement par authenticated'
);

select is(
  (
    select count(*)::int
    from pg_class c
    where c.oid='public.private_profiles'::regclass
      and (
        has_table_privilege('anon',c.oid,'SELECT')
        or has_table_privilege('anon',c.oid,'INSERT')
        or has_table_privilege('anon',c.oid,'UPDATE')
        or has_table_privilege('anon',c.oid,'DELETE')
        or has_table_privilege('authenticated',c.oid,'SELECT')
        or has_table_privilege('authenticated',c.oid,'INSERT')
        or has_table_privilege('authenticated',c.oid,'UPDATE')
        or has_table_privilege('authenticated',c.oid,'DELETE')
      )
  ),
  0,
  'le coffre private_profiles reste sans CRUD direct navigateur'
);

select * from finish();
rollback;
