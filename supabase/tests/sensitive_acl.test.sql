begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(14);

-- V24.4.36 : les rôles anonymes ne conservent aucun privilège SQL direct
-- sur les tables familiales/sociales sensibles. Les politiques RLS restent en plus actives.
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='guardian_links'), 0::bigint, 'anon: guardian_links scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='guardian_signup_invites'), 0::bigint, 'anon: guardian_signup_invites scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='private_family_links'), 0::bigint, 'anon: private_family_links scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='social_real_messages'), 0::bigint, 'anon: social_real_messages scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='social_character_messages'), 0::bigint, 'anon: social_character_messages scellée');

-- Principe du moindre privilège pour le rôle navigateur authentifié.
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='guardian_links'), 1::bigint, 'authenticated: guardian_links en lecture seule');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='guardian_signup_invites'), 1::bigint, 'authenticated: guardian_signup_invites en lecture seule');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='private_family_links'), 4::bigint, 'authenticated: private_family_links conserve uniquement le CRUD nécessaire');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='social_real_messages'), 2::bigint, 'authenticated: social_real_messages limite à SELECT/INSERT');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='social_character_messages'), 2::bigint, 'authenticated: social_character_messages limite à SELECT/INSERT');

-- Le diagnostic ACL reste strictement serveur.
select ok(not has_function_privilege('anon', 'public.sinjira_sensitive_acl_health()', 'EXECUTE'), 'anon ne peut pas appeler le health ACL sensible');
select ok(not has_function_privilege('authenticated', 'public.sinjira_sensitive_acl_health()', 'EXECUTE'), 'authenticated ne peut pas appeler le health ACL sensible');
select ok(has_function_privilege('service_role', 'public.sinjira_sensitive_acl_health()', 'EXECUTE'), 'service_role peut appeler le health ACL sensible');
select ok((public.sinjira_sensitive_acl_health()->>'ok')::boolean, 'health ACL sensible retourne ok=true après reconstruction');

select * from finish();
rollback;
