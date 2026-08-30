begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(16);

select ok(to_regnamespace('sinjira_privacy_moderation_internal') is null,'schéma intermédiaire redondant absent');
select ok(to_regnamespace('sinjira_user_rights_internal') is not null,'frontière canonique droits utilisateur présente');

select is((select count(*)::int from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in ('moderation_my_decisions','moderation_submit_appeal','privacy_create_request','privacy_export_my_extended_data','privacy_my_requests') and not p.prosecdef),5,'5 wrappers publics sont SECURITY INVOKER');
select is((select count(*)::int from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='sinjira_user_rights_internal' and p.proname in ('moderation_my_decisions','moderation_submit_appeal','privacy_create_request','privacy_export_my_extended_data','privacy_my_requests') and p.prosecdef),5,'5 implémentations canoniques sont SECURITY DEFINER');
select is((select count(*)::int from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='sinjira_user_rights_internal' and p.proname in ('moderation_my_decisions','moderation_submit_appeal','privacy_create_request','privacy_export_my_extended_data','privacy_my_requests') and position('auth.uid()' in pg_get_functiondef(p.oid))>0),5,'5 implémentations conservent auth.uid()');

select ok(not has_function_privilege('anon','public.moderation_my_decisions(integer)','EXECUTE'),'anon ne peut pas lire les décisions');
select ok(not has_function_privilege('anon','public.moderation_submit_appeal(uuid,text)','EXECUTE'),'anon ne peut pas soumettre un appel');
select ok(not has_function_privilege('anon','public.privacy_create_request(text,text)','EXECUTE'),'anon ne peut pas créer une demande confidentialité');
select ok(not has_function_privilege('anon','public.privacy_export_my_extended_data()','EXECUTE'),'anon ne peut pas exporter des données privées');
select ok(not has_function_privilege('anon','public.privacy_my_requests(integer)','EXECUTE'),'anon ne peut pas lire les demandes confidentialité');

select ok(has_function_privilege('authenticated','public.moderation_my_decisions(integer)','EXECUTE'),'authenticated conserve accès décisions personnelles');
select ok(has_function_privilege('authenticated','public.moderation_submit_appeal(uuid,text)','EXECUTE'),'authenticated conserve droit d’appel');
select ok(has_function_privilege('authenticated','public.privacy_create_request(text,text)','EXECUTE'),'authenticated conserve création demande confidentialité');

select is(pg_get_function_arguments('public.moderation_my_decisions(integer)'::regprocedure),'p_limit integer DEFAULT 50','limite par défaut décisions restaurée');
select is(pg_get_function_arguments('public.privacy_create_request(text,text)'::regprocedure),'p_request_type text, p_details text DEFAULT NULL::text','détails facultatifs confidentialité restaurés');
select is(pg_get_function_arguments('public.privacy_my_requests(integer)'::regprocedure),'p_limit integer DEFAULT 20','limite par défaut demandes restaurée');

select * from finish();
rollback;
