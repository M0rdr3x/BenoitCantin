begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(15);

select ok(to_regnamespace('sinjira_user_rights_internal') is not null,'schéma canonique droits utilisateur existe');
select ok(to_regnamespace('sinjira_privacy_moderation_internal') is null,'schéma intermédiaire redondant supprimé');

select ok(not (select prosecdef from pg_proc where oid='public.moderation_my_decisions(integer)'::regprocedure),'moderation_my_decisions public est SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.moderation_submit_appeal(uuid,text)'::regprocedure),'moderation_submit_appeal public est SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.privacy_create_request(text,text)'::regprocedure),'privacy_create_request public est SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.privacy_export_my_extended_data()'::regprocedure),'privacy_export_my_extended_data public est SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.privacy_my_requests(integer)'::regprocedure),'privacy_my_requests public est SECURITY INVOKER');

select ok(not has_function_privilege('anon','public.moderation_my_decisions(integer)','EXECUTE'),'anon ne lit pas les décisions de modération');
select ok(not has_function_privilege('anon','public.moderation_submit_appeal(uuid,text)','EXECUTE'),'anon ne soumet pas un appel');
select ok(not has_function_privilege('anon','public.privacy_create_request(text,text)','EXECUTE'),'anon ne crée pas une demande de confidentialité');
select ok(not has_function_privilege('anon','public.privacy_export_my_extended_data()','EXECUTE'),'anon n’exporte pas les données privées');
select ok(not has_function_privilege('anon','public.privacy_my_requests(integer)','EXECUTE'),'anon ne lit pas les demandes privées');

select is((select count(*)::int from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='sinjira_user_rights_internal' and p.proname in ('moderation_my_decisions','moderation_submit_appeal','privacy_create_request','privacy_export_my_extended_data','privacy_my_requests') and p.prosecdef),5,'5 implémentations internes SECURITY DEFINER conservées');
select is((select count(*)::int from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='sinjira_user_rights_internal' and p.proname in ('moderation_my_decisions','moderation_submit_appeal','privacy_create_request','privacy_export_my_extended_data','privacy_my_requests') and position('auth.uid()' in pg_get_functiondef(p.oid))>0),5,'5 contrôles auth.uid() conservés');
select ok(position('DEFAULT 20' in pg_get_function_arguments('public.privacy_my_requests(integer)'::regprocedure))>0,'privacy_my_requests conserve DEFAULT 20');

select * from finish();
rollback;
