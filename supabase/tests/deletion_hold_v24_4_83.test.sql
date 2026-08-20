begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(13);

select ok(to_regprocedure('private.privacy_has_active_legal_hold(uuid)') is not null,'fonction privée de hold existe');
select ok(to_regprocedure('public.privacy_service_can_delete_user(uuid)') is not null,'contrat service de suppression existe');
select ok(not has_function_privilege('authenticated','public.privacy_service_can_delete_user(uuid)','execute'),'membre ne peut pas sonder les holds');
select ok(not has_function_privilege('anon','public.privacy_service_can_delete_user(uuid)','execute'),'anon ne peut pas sonder les holds');
select ok(has_function_privilege('service_role','public.privacy_service_can_delete_user(uuid)','execute'),'service_role peut vérifier le droit de suppression');
select is((select confdeltype::text from pg_constraint where conname='privacy_requests_user_id_fkey'),'n','historique demandes utilise ON DELETE SET NULL');
select is((select confdeltype::text from pg_constraint where conname='safety_escalation_cases_source_report_id_fkey'),'n','dossier escalade utilise ON DELETE SET NULL');
select ok((select is_nullable='YES' from information_schema.columns where table_schema='private' and table_name='privacy_requests' and column_name='user_id'),'demande vie privée survit à la suppression du compte');
select ok((select is_nullable='YES' from information_schema.columns where table_schema='private' and table_name='safety_escalation_cases' and column_name='source_report_id'),'dossier escalade peut subsister sans le signalement source');
select ok(to_regprocedure('public.privacy_export_my_extended_data()') is not null,'RPC export étendu existe');
select ok(has_function_privilege('authenticated','public.privacy_export_my_extended_data()','execute'),'membre authentifié peut exporter ses données récentes');
select ok(not has_function_privilege('anon','public.privacy_export_my_extended_data()','execute'),'anon ne peut pas exporter des données privées');
select ok(position("-'snapshot'" in replace(pg_get_functiondef('public.privacy_export_my_extended_data()'::regprocedure),' ',''))>0,'export automatique exclut les snapshots tiers des signalements');

select * from finish();
rollback;