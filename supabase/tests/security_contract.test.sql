begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(40);

-- V24.4.19 : les tables internes ne doivent exposer aucun privilège direct
-- aux rôles navigateur. Les accès autorisés passent uniquement par RPC/Edge.
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='character_generation_runs'), 0::bigint, 'anon: character_generation_runs scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='character_generation_runs'), 0::bigint, 'authenticated: character_generation_runs scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='fracture_engine_actions'), 0::bigint, 'anon: fracture_engine_actions scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='fracture_engine_actions'), 0::bigint, 'authenticated: fracture_engine_actions scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='fracture_engine_cards'), 0::bigint, 'anon: fracture_engine_cards scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='fracture_engine_cards'), 0::bigint, 'authenticated: fracture_engine_cards scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='fracture_engine_events'), 0::bigint, 'anon: fracture_engine_events scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='fracture_engine_events'), 0::bigint, 'authenticated: fracture_engine_events scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='fracture_engine_games'), 0::bigint, 'anon: fracture_engine_games scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='fracture_engine_games'), 0::bigint, 'authenticated: fracture_engine_games scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='fracture_engine_rounds'), 0::bigint, 'anon: fracture_engine_rounds scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='fracture_engine_rounds'), 0::bigint, 'authenticated: fracture_engine_rounds scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='fracture_engine_seats'), 0::bigint, 'anon: fracture_engine_seats scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='fracture_engine_seats'), 0::bigint, 'authenticated: fracture_engine_seats scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='fracture_engine_votes'), 0::bigint, 'anon: fracture_engine_votes scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='fracture_engine_votes'), 0::bigint, 'authenticated: fracture_engine_votes scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='internal_admin_users'), 0::bigint, 'anon: internal_admin_users scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='internal_admin_users'), 0::bigint, 'authenticated: internal_admin_users scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='internal_contribution_ownership'), 0::bigint, 'anon: internal_contribution_ownership scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='internal_contribution_ownership'), 0::bigint, 'authenticated: internal_contribution_ownership scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='internal_gameplay_contributions'), 0::bigint, 'anon: internal_gameplay_contributions scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='internal_gameplay_contributions'), 0::bigint, 'authenticated: internal_gameplay_contributions scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='sinjira_canon_context'), 0::bigint, 'anon: sinjira_canon_context scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='sinjira_canon_context'), 0::bigint, 'authenticated: sinjira_canon_context scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='sinjira_security_settings'), 0::bigint, 'anon: sinjira_security_settings scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='sinjira_security_settings'), 0::bigint, 'authenticated: sinjira_security_settings scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='anon' and table_schema='public' and table_name='social_suspensions'), 0::bigint, 'anon: social_suspensions scellée');
select is((select count(*) from information_schema.role_table_grants where grantee='authenticated' and table_schema='public' and table_name='social_suspensions'), 0::bigint, 'authenticated: social_suspensions scellée');

-- Les diagnostics et l’état brut Fracture restent exclusivement serveur.
select ok(not has_function_privilege('anon', 'public._fracture_engine_get_state_raw(text)', 'EXECUTE'), 'anon ne peut pas lire l état brut Fracture');
select ok(not has_function_privilege('authenticated', 'public._fracture_engine_get_state_raw(text)', 'EXECUTE'), 'authenticated ne peut pas lire l état brut Fracture');
select ok(has_function_privilege('service_role', 'public._fracture_engine_get_state_raw(text)', 'EXECUTE'), 'service_role peut lire l état brut Fracture');

select ok(not has_function_privilege('anon', 'public.sinjira_security_contract_health()', 'EXECUTE'), 'anon ne peut pas appeler le health sécurité');
select ok(not has_function_privilege('authenticated', 'public.sinjira_security_contract_health()', 'EXECUTE'), 'authenticated ne peut pas appeler le health sécurité');
select ok(has_function_privilege('service_role', 'public.sinjira_security_contract_health()', 'EXECUTE'), 'service_role peut appeler le health sécurité');

select ok(not has_function_privilege('anon', 'public.sinjira_owner_character_health()', 'EXECUTE'), 'anon ne peut pas appeler le health propriétaire');
select ok(not has_function_privilege('authenticated', 'public.sinjira_owner_character_health()', 'EXECUTE'), 'authenticated ne peut pas appeler le health propriétaire');
select ok(has_function_privilege('service_role', 'public.sinjira_owner_character_health()', 'EXECUTE'), 'service_role peut appeler le health propriétaire');

-- La réparation propriétaire est exposée aux utilisateurs connectés mais se protège
-- elle-même avec auth.uid(); anon ne doit jamais pouvoir l’invoquer.
select ok(not has_function_privilege('anon', 'public.ensure_sinjira_owner_character()', 'EXECUTE'), 'anon ne peut pas appeler la réparation propriétaire');
select ok(has_function_privilege('authenticated', 'public.ensure_sinjira_owner_character()', 'EXECUTE'), 'authenticated peut entrer dans la garde propriétaire');
select ok(has_function_privilege('service_role', 'public.ensure_sinjira_owner_character()', 'EXECUTE'), 'service_role peut réparer le propriétaire');

select * from finish();
rollback;
