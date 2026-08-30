begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(5);

select ok(to_regprocedure('public.admin_preorder_logistics_queue(text,integer)') is not null,'RPC logistique existe');
select ok(not (select prosecdef from pg_proc where oid='public.admin_preorder_logistics_queue(text,integer)'::regprocedure),'wrapper public est SECURITY INVOKER');
select ok(not has_function_privilege('anon','public.admin_preorder_logistics_queue(text,integer)','EXECUTE'),'anon ne peut pas exécuter la RPC logistique');
select ok(position('require_sinjira_admin_aal2' in pg_get_functiondef('preorder_admin_internal.admin_preorder_logistics_queue(text,integer)'::regprocedure))>0,'implémentation interne exige admin + MFA/AAL2');
select ok(position('user_id' in pg_get_function_result('public.admin_preorder_logistics_queue(text,integer)'::regprocedure))=0 and position('email' in pg_get_function_result('public.admin_preorder_logistics_queue(text,integer)'::regprocedure))=0 and position('address' in pg_get_function_result('public.admin_preorder_logistics_queue(text,integer)'::regprocedure))=0 and position('uuid' in pg_get_function_result('public.admin_preorder_logistics_queue(text,integer)'::regprocedure))=0,'aucun champ sensible dans le type de retour');

select * from finish();
rollback;
