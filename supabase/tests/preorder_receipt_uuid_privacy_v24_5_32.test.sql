begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, private, extensions;

select plan(14);

select ok(exists(select 1 from information_schema.columns where table_schema='public' and table_name='product_preorders' and column_name='reservation_reference'),'référence de réservation présente');
select ok(exists(select 1 from pg_constraint where conrelid='public.product_preorders'::regclass and conname='product_preorders_reservation_reference_chk'),'format de référence contraint');
select ok(exists(select 1 from pg_indexes where schemaname='public' and tablename='product_preorders' and indexname='product_preorders_reservation_reference_uidx'),'référence unique indexée');

select ok(to_regprocedure('public.product_preorder_my_status(text)') is not null,'RPC statut précommande existe');
select ok(not (select prosecdef from pg_proc where oid='public.product_preorder_my_status(text)'::regprocedure),'wrapper public SECURITY INVOKER');
select ok(not has_function_privilege('anon','public.product_preorder_my_status(text)','EXECUTE'),'anon ne peut pas lire un statut de précommande');
select ok(has_function_privilege('authenticated','public.product_preorder_my_status(text)','EXECUTE'),'authenticated conserve le statut de sa réservation');
select ok(has_function_privilege('service_role','public.product_preorder_my_status(text)','EXECUTE'),'service_role conserve EXECUTE');

select ok(position('reservation_reference text' in lower(pg_get_function_result('public.product_preorder_my_status(text)'::regprocedure)))>0,'résultat public contient la référence indépendante');
select ok(position('uuid' in lower(pg_get_function_result('public.product_preorder_my_status(text)'::regprocedure)))=0,'résultat public ne contient aucun UUID');
select ok(position('preorder_id' in lower(pg_get_function_result('public.product_preorder_my_status(text)'::regprocedure)))=0,'preorder_id interne non exposé');
select ok(position('disclosure_version text' in lower(pg_get_function_result('public.product_preorder_my_status(text)'::regprocedure)))>0 and position('disclosure_acknowledged_at timestamp with time zone' in lower(pg_get_function_result('public.product_preorder_my_status(text)'::regprocedure)))>0,'preuve de transparence disponible');
select ok((select prosecdef from pg_proc where oid='preorder_user_internal.product_preorder_my_status(text)'::regprocedure),'implémentation interne SECURITY DEFINER');
select ok(position('auth.uid()' in lower(pg_get_functiondef('preorder_user_internal.product_preorder_my_status(text)'::regprocedure)))>0,'implémentation interne reste self-only via auth.uid()');

select * from finish();
rollback;
