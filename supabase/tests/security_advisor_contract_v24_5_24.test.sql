begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(8);

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

-- Couverture complémentaire: RLS de toutes les tables applicatives, y compris
-- les tables partitionnées, puis privilèges effectifs non CRUD et par colonne.
select is(
  (select string_agg(format('%I.%I',n.nspname,c.relname), ', ' order by n.nspname,c.relname)
   from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname in ('public','private') and c.relkind in ('r','p')
     and not c.relrowsecurity),
  null::text, 'toutes les tables public/private activent RLS'
);

select is(
  (select string_agg(format('%I.%I:%s',n.nspname,c.relname,r.role_name), ', ' order by n.nspname,c.relname,r.role_name)
   from pg_class c join pg_namespace n on n.oid=c.relnamespace
   cross join (values ('anon'),('authenticated')) r(role_name)
   where n.nspname in ('public','private') and c.relkind in ('r','p')
     and not exists(select 1 from pg_policy pol where pol.polrelid=c.oid)
     and has_table_privilege(r.role_name,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')),
  null::text, 'aucun privilège direct navigateur sur les tables sans policy'
);

select is(
  (select string_agg(format('%I.%I:%s',n.nspname,c.relname,r.role_name), ', ' order by n.nspname,c.relname,r.role_name)
   from pg_class c join pg_namespace n on n.oid=c.relnamespace
   cross join (values ('anon'),('authenticated')) r(role_name)
   where n.nspname in ('public','private') and c.relkind in ('r','p')
     and not exists(select 1 from pg_policy pol where pol.polrelid=c.oid)
     and has_any_column_privilege(r.role_name,c.oid,'SELECT,INSERT,UPDATE,REFERENCES')),
  null::text, 'aucun privilège par colonne navigateur sur les tables sans policy'
);

-- Sonde transactionnelle: vérifie que les droits par colonne et TRUNCATE
-- sont effectivement détectables; aucune donnée ni table persistante.
create table private.security_advisor_acl_probe (id integer);
alter table private.security_advisor_acl_probe enable row level security;
revoke all on private.security_advisor_acl_probe from public,anon,authenticated;
grant select(id) on private.security_advisor_acl_probe to authenticated;
grant truncate on private.security_advisor_acl_probe to anon;
select ok(
  has_any_column_privilege('authenticated','private.security_advisor_acl_probe','SELECT')
  and not has_table_privilege('authenticated','private.security_advisor_acl_probe','SELECT')
  and has_table_privilege('anon','private.security_advisor_acl_probe','TRUNCATE'),
  'les attributions accidentelles par colonne et TRUNCATE sont détectables'
);

select * from finish();
rollback;
