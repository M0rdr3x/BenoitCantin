begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(12);

select ok(to_regprocedure('public.admin_preorder_find_by_reference(text)') is not null,'wrapper public de recherche par référence présent');
select ok(to_regprocedure('preorder_admin_internal.admin_preorder_find_by_reference(text)') is not null,'implémentation interne de recherche par référence présente');
select ok(not (select prosecdef from pg_proc where oid='public.admin_preorder_find_by_reference(text)'::regprocedure),'wrapper public est SECURITY INVOKER');
select ok((select prosecdef from pg_proc where oid='preorder_admin_internal.admin_preorder_find_by_reference(text)'::regprocedure),'implémentation interne est SECURITY DEFINER');
select ok(not has_function_privilege('anon','public.admin_preorder_find_by_reference(text)','EXECUTE'),'anon ne peut pas rechercher une réservation');
select ok(has_function_privilege('authenticated','public.admin_preorder_find_by_reference(text)','EXECUTE'),'authenticated atteint le wrapper avant le contrôle admin AAL2');
select ok(has_function_privilege('service_role','public.admin_preorder_find_by_reference(text)','EXECUTE'),'service_role conserve le contrat serveur');
select ok(position('require_sinjira_admin_aal2' in pg_get_functiondef('preorder_admin_internal.admin_preorder_find_by_reference(text)'::regprocedure))>0,'implémentation exige admin + MFA/AAL2');
select ok(position('^PR-[0-9A-F]{16}$' in pg_get_functiondef('preorder_admin_internal.admin_preorder_find_by_reference(text)'::regprocedure))>0,'référence PR strictement validée');
select ok(to_regclass('public.product_preorders_reservation_reference_uidx') is not null,'index unique de référence présent');
select ok(position('uuid' in lower(pg_get_function_result('public.admin_preorder_find_by_reference(text)'::regprocedure)))=0 and position('email' in lower(pg_get_function_result('public.admin_preorder_find_by_reference(text)'::regprocedure)))=0,'résultat public ne contient ni UUID ni courriel');
select ok(position('address' in lower(pg_get_function_result('public.admin_preorder_find_by_reference(text)'::regprocedure)))=0 and position('payment' in lower(pg_get_function_result('public.admin_preorder_find_by_reference(text)'::regprocedure)))=0,'résultat public ne contient ni adresse ni donnée de paiement');

select * from finish();
rollback;
