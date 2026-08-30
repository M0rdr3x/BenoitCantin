begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(13);

select ok(to_regclass('private.preorder_admin_workflow') is not null,'table privée de suivi existe');
select ok((select relrowsecurity from pg_class where oid='private.preorder_admin_workflow'::regclass),'RLS suivi activée');
select ok(not has_table_privilege('anon','private.preorder_admin_workflow','SELECT'),'anon ne lit pas le suivi');
select ok(not has_table_privilege('authenticated','private.preorder_admin_workflow','SELECT'),'authenticated ne lit pas directement le suivi');
select ok((select count(*)=3 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in ('admin_preorder_workflow_by_reference','admin_preorder_set_workflow_state','admin_preorder_workflow_queue') and not p.prosecdef),'wrappers publics sont SECURITY INVOKER');
select ok((select count(*)=0 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in ('admin_preorder_workflow_by_reference','admin_preorder_set_workflow_state','admin_preorder_workflow_queue') and has_function_privilege('anon',p.oid,'EXECUTE')),'anon ne peut pas exécuter les RPC de suivi');
select ok((select count(*)=3 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in ('admin_preorder_workflow_by_reference','admin_preorder_set_workflow_state','admin_preorder_workflow_queue') and has_function_privilege('authenticated',p.oid,'EXECUTE')),'authenticated conserve les wrappers avant contrôle serveur');
select ok((select count(*)=3 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='preorder_admin_internal' and p.proname in ('admin_preorder_workflow_by_reference','admin_preorder_set_workflow_state','admin_preorder_workflow_queue') and p.prosecdef),'implémentations internes sont SECURITY DEFINER');
select ok((select count(*)=3 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='preorder_admin_internal' and p.proname in ('admin_preorder_workflow_by_reference','admin_preorder_set_workflow_state','admin_preorder_workflow_queue') and position('require_sinjira_admin_aal2' in pg_get_functiondef(p.oid))>0),'implémentations internes exigent admin + MFA/AAL2');
select ok(exists(select 1 from pg_constraint where conrelid='private.preorder_admin_workflow'::regclass and contype='c' and position('pending' in lower(pg_get_constraintdef(oid)))>0 and position('ready_for_future_contact' in lower(pg_get_constraintdef(oid)))>0 and position('completed' in lower(pg_get_constraintdef(oid)))>0),'les trois états sont contraints par la base');
select ok(not exists(select 1 from information_schema.columns where table_schema='private' and table_name='preorder_admin_workflow' and lower(column_name) in ('note','notes','details','email','address','phone','telephone')),'aucune colonne de note libre ou PII');
select ok(to_regprocedure('public.admin_preorder_set_workflow_state(text,text)') is not null,'RPC de changement d’état existe');
select ok(to_regprocedure('public.admin_preorder_workflow_queue(text,integer)') is not null,'RPC de file de suivi existe');

select * from finish();
rollback;
