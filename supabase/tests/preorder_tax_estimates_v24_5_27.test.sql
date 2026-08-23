begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(24);

select ok(to_regclass('public.preorder_tax_estimate_profiles') is not null,'table profils fiscaux existe');
select ok((select relrowsecurity from pg_class where oid='public.preorder_tax_estimate_profiles'::regclass),'RLS profils fiscaux active');
select ok(not has_table_privilege('anon','public.preorder_tax_estimate_profiles','SELECT'),'anon ne lit pas directement les profils fiscaux');
select ok(not has_table_privilege('authenticated','public.preorder_tax_estimate_profiles','SELECT'),'authenticated ne lit pas directement les profils fiscaux');
select ok(has_table_privilege('service_role','public.preorder_tax_estimate_profiles','SELECT'),'service_role peut gérer les profils fiscaux');
select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='preorder_tax_estimate_profiles' and policyname='preorder_tax_profiles_service_role'),'politique service_role présente');

select is((select numeric_scale::int from information_schema.columns where table_schema='public' and table_name='preorder_tax_estimate_profiles' and column_name='paper_rate_basis_points'),3,'taux papier conserve 3 décimales de points de base');
select is((select numeric_scale::int from information_schema.columns where table_schema='public' and table_name='preorder_tax_estimate_profiles' and column_name='digital_rate_basis_points'),3,'taux numérique conserve 3 décimales de points de base');
select is((select numeric_scale::int from information_schema.columns where table_schema='public' and table_name='preorder_tax_estimate_profiles' and column_name='shipping_rate_basis_points'),3,'taux livraison conserve 3 décimales de points de base');

select ok(not (select prosecdef from pg_proc where oid='public.admin_preorder_tax_get(text)'::regprocedure),'wrapper admin get est security invoker');
select ok(not (select prosecdef from pg_proc where oid='public.admin_preorder_tax_profile_save(text,text,text,text,text,numeric,numeric,numeric,text,date,text,boolean)'::regprocedure),'wrapper admin save est security invoker');
select ok(not (select prosecdef from pg_proc where oid='public.admin_preorder_tax_profile_publish(text,text)'::regprocedure),'wrapper admin publish est security invoker');
select ok(not has_function_privilege('anon','public.admin_preorder_tax_get(text)','EXECUTE'),'anon ne peut pas appeler admin tax');
select ok(position('require_sinjira_admin_aal2' in pg_get_functiondef('preorder_tax_internal.admin_preorder_tax_get(text)'::regprocedure))>0 and position('require_sinjira_admin_aal2' in pg_get_functiondef('preorder_tax_internal.admin_preorder_tax_profile_save(text,text,text,text,text,numeric,numeric,numeric,text,date,text,boolean)'::regprocedure))>0 and position('require_sinjira_admin_aal2' in pg_get_functiondef('preorder_tax_internal.admin_preorder_tax_profile_publish(text,text)'::regprocedure))>0,'les trois opérations admin gardent MFA/AAL2');

select ok(not (select prosecdef from pg_proc where oid='public.product_preorder_tax_options(text)'::regprocedure),'options fiscales publiques security invoker');
select ok(has_function_privilege('anon','public.product_preorder_tax_options(text)','EXECUTE'),'anon peut lire uniquement les profils fiscaux publiés via RPC');
select ok(not (select prosecdef from pg_proc where oid='public.product_preorder_tax_estimate(text,text,text,integer,text,text)'::regprocedure),'estimation fiscale publique security invoker');
select ok(has_function_privilege('anon','public.product_preorder_tax_estimate(text,text,text,integer,text,text)','EXECUTE'),'anon peut demander une estimation publiée');

select ok(position('external_tax_api_enabled' in pg_get_functiondef('preorder_tax_internal.product_preorder_tax_estimate(text,text,text,integer,text,text)'::regprocedure))>0 and position('billing_authoritative' in pg_get_functiondef('preorder_tax_internal.product_preorder_tax_estimate(text,text,text,integer,text,text)'::regprocedure))>0 and position('final_tax_confirmation_required' in pg_get_functiondef('preorder_tax_internal.product_preorder_tax_estimate(text,text,text,integer,text,text)'::regprocedure))>0,'contrat non facturable et confirmation finale présent');
select ok(position('p_format is null' in lower(pg_get_functiondef('preorder_tax_internal.product_preorder_tax_estimate(text,text,text,integer,text,text)'::regprocedure)))>0 and position('p_fulfillment_method is null' in lower(pg_get_functiondef('preorder_tax_internal.product_preorder_tax_estimate(text,text,text,integer,text,text)'::regprocedure)))>0,'les entrées nulles critiques sont refusées explicitement');
select ok(position('source_reference' in pg_get_functiondef('preorder_tax_internal.admin_preorder_tax_profile_publish(text,text)'::regprocedure))>0,'publication exige une source');
select ok(position('effective_on is not null' in lower(pg_get_functiondef('preorder_tax_internal.admin_preorder_tax_profile_publish(text,text)'::regprocedure)))>0,'publication exige une date effet');
select ok(position('tax_estimate_ready' in pg_get_functiondef('preorder_readiness_internal.sale_readiness(text)'::regprocedure))>0 and position('v_tax_profile_count>0' in replace(pg_get_functiondef('preorder_readiness_internal.sale_readiness(text)'::regprocedure),' ',''))>0,'la readiness exige un profil fiscal indicatif publié');
select is((select count(*)::int from public.preorder_tax_estimate_profiles),0,'aucun taux fiscal n est prérempli après reconstruction');

select * from finish();
rollback;
