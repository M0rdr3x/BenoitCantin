begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(18);

select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='privacy_settings'),0::bigint,'anon: privacy_settings sans privilège SQL');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='notification_preferences'),0::bigint,'anon: notification_preferences sans privilège SQL');

select ok(has_table_privilege('authenticated','public.privacy_settings','SELECT'),'authenticated peut lire ses paramètres via RLS');
select ok(not has_table_privilege('authenticated','public.privacy_settings','INSERT'),'privacy_settings: aucun INSERT table-wide');
select ok(not has_table_privilege('authenticated','public.privacy_settings','UPDATE'),'privacy_settings: aucun UPDATE table-wide');
select ok(not has_table_privilege('authenticated','public.privacy_settings','DELETE'),'privacy_settings: aucun DELETE');
select ok(has_table_privilege('authenticated','public.notification_preferences','SELECT'),'authenticated peut lire ses préférences via RLS');
select ok(not has_table_privilege('authenticated','public.notification_preferences','INSERT'),'notification_preferences: aucun INSERT table-wide');
select ok(not has_table_privilege('authenticated','public.notification_preferences','UPDATE'),'notification_preferences: aucun UPDATE table-wide');
select ok(not has_table_privilege('authenticated','public.notification_preferences','DELETE'),'notification_preferences: aucun DELETE');

select is((select count(*) from information_schema.column_privileges where grantee='authenticated' and table_schema='public' and table_name='privacy_settings' and privilege_type='INSERT'),8::bigint,'privacy_settings: huit colonnes insérables');
select is((select count(*) from information_schema.column_privileges where grantee='authenticated' and table_schema='public' and table_name='privacy_settings' and privilege_type='UPDATE'),8::bigint,'privacy_settings: huit colonnes modifiables');
select is((select count(*) from information_schema.column_privileges where grantee='authenticated' and table_schema='public' and table_name='notification_preferences' and privilege_type='INSERT'),7::bigint,'notification_preferences: sept colonnes insérables');
select is((select count(*) from information_schema.column_privileges where grantee='authenticated' and table_schema='public' and table_name='notification_preferences' and privilege_type='UPDATE'),7::bigint,'notification_preferences: sept colonnes modifiables');

select is((select count(*) from pg_policies where schemaname='public' and tablename='privacy_settings' and policyname like 'privacy_settings_self_%'),3::bigint,'privacy_settings: trois politiques self-only');
select is((select count(*) from pg_policies where schemaname='public' and tablename='notification_preferences' and policyname like 'notification_preferences_self_%'),3::bigint,'notification_preferences: trois politiques self-only');
select ok(has_column_privilege('authenticated','public.privacy_settings','allow_ai_personal_data','UPDATE'),'colonne IA techniquement modifiable mais contrainte SQL impose false');
select ok(exists(select 1 from pg_constraint where conrelid='public.privacy_settings'::regclass and contype='c' and conname='privacy_settings_allow_ai_personal_data_check'),'privacy_settings: contrainte IA forcée à false présente');

select * from finish();
rollback;
