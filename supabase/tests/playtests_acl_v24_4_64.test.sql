begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(15);

select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='playtests'), 0::bigint, 'anon: playtests sans privilège SQL');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='playtest_participants'), 0::bigint, 'anon: playtest_participants sans privilège SQL');

select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='playtests'), 1::bigint, 'authenticated: playtests en lecture seule');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='playtest_participants'), 1::bigint, 'authenticated: participant conserve seulement SELECT au niveau table');
select ok(has_table_privilege('authenticated','public.playtests','SELECT'), 'authenticated peut lire les playtests autorisés');
select ok(not has_table_privilege('authenticated','public.playtests','INSERT'), 'authenticated ne peut pas créer un playtest');
select ok(not has_table_privilege('authenticated','public.playtests','UPDATE'), 'authenticated ne peut pas modifier un playtest');
select ok(not has_table_privilege('authenticated','public.playtests','DELETE'), 'authenticated ne peut pas supprimer un playtest');
select ok(has_table_privilege('authenticated','public.playtest_participants','SELECT'), 'authenticated peut lire sa participation via RLS');

select is((select count(*) from information_schema.column_privileges where grantee='authenticated' and table_schema='public' and table_name='playtest_participants' and privilege_type='INSERT'), 4::bigint, 'authenticated: quatre colonnes seulement sont insérables pour une candidature');
select is((select count(*) from information_schema.column_privileges where grantee='authenticated' and table_schema='public' and table_name='playtest_participants' and privilege_type='UPDATE'), 1::bigint, 'authenticated: une seule colonne est modifiable');
select ok(has_column_privilege('authenticated','public.playtest_participants','status','UPDATE'), 'authenticated peut modifier uniquement son statut via RLS');
select ok(not has_column_privilege('authenticated','public.playtest_participants','application_message','UPDATE'), 'authenticated ne peut pas réécrire son message après candidature');

select is((select count(*) from pg_policies where schemaname='public' and tablename='playtest_participants' and policyname='playtest_participants_apply' and cmd='INSERT'), 1::bigint, 'politique candidature V24.4.64 présente');
select is((select count(*) from pg_policies where schemaname='public' and tablename='playtest_participants' and policyname='playtest_participants_withdraw_own' and cmd='UPDATE'), 1::bigint, 'politique retrait self-only V24.4.64 présente');

select * from finish();
rollback;
