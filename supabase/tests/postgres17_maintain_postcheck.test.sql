begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,extensions;
select plan(4);
select ok(current_setting('server_version_num')::int >= 170000,
          'remediation actually tested on PG17+');
select is(
  (select count(*)::int from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname in ('public','private') and c.relkind in ('r','p')
     and (has_table_privilege('anon',c.oid,'MAINTAIN')
       or has_table_privilege('authenticated',c.oid,'MAINTAIN'))),
  0, 'no effective browser MAINTAIN after migration'
);
select is(
  (select count(*)::int from pg_default_acl d
   left join pg_namespace n on n.oid=d.defaclnamespace
   cross join lateral aclexplode(d.defaclacl) a
   where d.defaclrole='postgres'::regrole and (d.defaclnamespace=0 or n.nspname in ('public','private'))
     and d.defaclobjtype='r' and a.privilege_type='MAINTAIN'
     and a.grantee in (0,'anon'::regrole::oid,'authenticated'::regrole::oid)),
  0, 'postgres default MAINTAIN absent'
);
set local role postgres;
create table public.security_maintain_future_acl_probe (id integer);
alter table public.security_maintain_future_acl_probe enable row level security;
select ok(
  not has_table_privilege('anon','public.security_maintain_future_acl_probe','MAINTAIN')
  and not has_table_privilege('authenticated','public.security_maintain_future_acl_probe','MAINTAIN'),
  'new postgres-owned table does not inherit browser MAINTAIN'
);
select * from finish();
rollback;
