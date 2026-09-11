begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(11);

select ok(to_regclass('public.user_entitlements') is not null,'table user_entitlements existe');
select ok((select relrowsecurity from pg_class where oid='public.user_entitlements'::regclass),'RLS active sur user_entitlements');
select ok(has_table_privilege('authenticated','public.user_entitlements','select'),'authenticated peut lire ses droits');
select ok(not has_table_privilege('authenticated','public.user_entitlements','insert'),'authenticated ne peut pas s attribuer un droit');
select ok(not has_table_privilege('authenticated','public.user_entitlements','update'),'authenticated ne peut pas modifier ses droits');
select ok(not has_table_privilege('authenticated','public.user_entitlements','delete'),'authenticated ne peut pas supprimer ses droits');
select ok(not has_table_privilege('anon','public.user_entitlements','select'),'anon ne peut pas lire les droits numériques');
select is(
  (select count(*)::integer from pg_policies where schemaname='public' and tablename='user_entitlements' and cmd='SELECT' and 'authenticated'=any(roles)),
  1,
  'une seule politique SELECT authenticated gouverne user_entitlements'
);
select is(
  (select count(*)::integer from pg_policies where schemaname='public' and tablename='user_entitlements' and cmd in ('INSERT','UPDATE','DELETE','ALL') and 'authenticated'=any(roles)),
  0,
  'aucune politique RLS ne permet une mutation authenticated'
);
select ok(
  exists(
    select 1 from pg_policies
    where schemaname='public' and tablename='user_entitlements' and cmd='SELECT'
      and 'authenticated'=any(roles)
      and coalesce(qual,'') ilike '%auth.uid()%'
      and coalesce(qual,'') ilike '%user_id%'
  ),
  'la lecture est limitée aux droits de la personne connectée'
);
select ok(
  not exists(
    select 1 from information_schema.role_table_grants
    where table_schema='public' and table_name='user_entitlements'
      and grantee in ('anon','authenticated')
      and privilege_type in ('INSERT','UPDATE','DELETE','TRUNCATE','TRIGGER','REFERENCES')
  ),
  'aucun privilège de mutation implicite n est accordé aux rôles client'
);

select * from finish();
rollback;
