begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, private, extensions;

select plan(16);

select ok(exists(select 1 from information_schema.columns where table_schema='public' and table_name='product_preorders' and column_name='disclosure_version'),'version de transparence présente');
select ok(exists(select 1 from information_schema.columns where table_schema='public' and table_name='product_preorders' and column_name='disclosure_acknowledged_at'),'date de confirmation présente');
select ok(exists(select 1 from pg_constraint where conrelid='public.product_preorders'::regclass and conname='product_preorders_disclosure_pair_chk'),'paire version/date cohérente');

select ok(to_regprocedure('public.product_preorder_reserve(text,text,integer,boolean)') is not null,'ancien RPC de réservation existe encore pour échec sûr');
select ok(not (select prosecdef from pg_proc where oid='public.product_preorder_reserve(text,text,integer,boolean)'::regprocedure),'ancien wrapper public est SECURITY INVOKER');
select ok(not has_function_privilege('anon','public.product_preorder_reserve(text,text,integer,boolean)','EXECUTE'),'ancien wrapper interdit à anon');

select ok(to_regprocedure('public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)') is not null,'nouveau RPC confirmé existe');
select ok(not (select prosecdef from pg_proc where oid='public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)'::regprocedure),'nouveau wrapper public est SECURITY INVOKER');
select ok(not has_function_privilege('anon','public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)','EXECUTE'),'nouveau wrapper interdit à anon');
select ok(has_function_privilege('authenticated','public.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)','EXECUTE'),'authenticated peut réserver après confirmation');

select ok((select prosecdef from pg_proc where oid='preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)'::regprocedure),'implémentation interne reste SECURITY DEFINER');
select ok(position('auth.uid()' in lower(pg_get_functiondef('preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)'::regprocedure)))>0,'implémentation vérifie auth.uid()');
select ok(position('preorder-disclosure-v24.5.31' in lower(pg_get_functiondef('preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)'::regprocedure)))>0,'version exacte V24.5.31 exigée');
select ok(position('p_disclosure_acknowledged is distinct from true' in lower(pg_get_functiondef('preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)'::regprocedure)))>0,'confirmation explicite true exigée');
select ok(position('financial_commitment = false' in lower(pg_get_functiondef('preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)'::regprocedure)))>0 and position($q$payment_status = 'not_collected'$q$ in lower(pg_get_functiondef('preorder_user_internal.product_preorder_reserve_confirmed(text,text,integer,boolean,text,boolean)'::regprocedure)))>0,'réservation reste sans paiement ni engagement financier');
select ok(position('preorder_disclosure_required' in lower(pg_get_functiondef('preorder_user_internal.product_preorder_reserve(text,text,integer,boolean)'::regprocedure)))>0 and position('insert into public.product_preorders' in lower(pg_get_functiondef('preorder_user_internal.product_preorder_reserve(text,text,integer,boolean)'::regprocedure)))=0,'ancien chemin ne peut plus écrire sans accusé');

select * from finish();
rollback;
