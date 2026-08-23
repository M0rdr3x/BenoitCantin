begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(8);

select ok(to_regprocedure('public.admin_preorder_sale_readiness(text)') is not null,'wrapper public de préparation commerciale existe');
select ok(not (select prosecdef from pg_proc where oid='public.admin_preorder_sale_readiness(text)'::regprocedure),'wrapper public est SECURITY INVOKER');
select ok(not has_function_privilege('anon','public.admin_preorder_sale_readiness(text)','EXECUTE'),'anon ne peut pas exécuter la checklist de vente');
select ok(has_function_privilege('authenticated','public.admin_preorder_sale_readiness(text)','EXECUTE'),'authenticated peut atteindre le wrapper avant contrôle admin AAL2');
select ok(to_regprocedure('preorder_readiness_internal.sale_readiness(text)') is not null,'implémentation interne existe');
select ok((select prosecdef from pg_proc where oid='preorder_readiness_internal.sale_readiness(text)'::regprocedure),'implémentation interne reste SECURITY DEFINER');
select ok(position('require_sinjira_admin_aal2' in lower(pg_get_functiondef('preorder_readiness_internal.sale_readiness(text)'::regprocedure)))>0,'implémentation interne exige admin MFA/AAL2');
select ok(position('taxes_calculated_by_sinjira' in lower(pg_get_functiondef('preorder_readiness_internal.sale_readiness(text)'::regprocedure)))>0 and position("'taxes_calculated_by_sinjira', false" in lower(pg_get_functiondef('preorder_readiness_internal.sale_readiness(text)'::regprocedure)))>0,'SINJIRA déclare explicitement ne pas calculer les taxes dans V24.5.26');

select * from finish();
rollback;
