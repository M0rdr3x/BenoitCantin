begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(20);

select ok(to_regprocedure('public.social_report_content(text,text,uuid,text,text,boolean)') is not null,'RPC signalement communautaire existe');
select ok(to_regprocedure('public.social_my_blocks()') is not null,'RPC liste blocages existe');
select ok(to_regprocedure('public.social_unblock_user(uuid)') is not null,'RPC déblocage existe');
select ok(to_regprocedure('public.social_my_reports(integer)') is not null,'RPC historique signalements existe');

select ok(has_function_privilege('authenticated','public.social_report_content(text,text,uuid,text,text,boolean)','EXECUTE'),'authenticated peut signaler');
select ok(not has_function_privilege('anon','public.social_report_content(text,text,uuid,text,text,boolean)','EXECUTE'),'anon ne peut pas signaler');
select ok(has_function_privilege('authenticated','public.social_my_blocks()','EXECUTE'),'authenticated peut gérer ses blocages');
select ok(not has_function_privilege('anon','public.social_my_blocks()','EXECUTE'),'anon ne liste pas les blocages');
select ok(has_function_privilege('authenticated','public.social_my_reports(integer)','EXECUTE'),'authenticated peut voir ses signalements');
select ok(not has_function_privilege('anon','public.social_my_reports(integer)','EXECUTE'),'anon ne voit pas les signalements');

select ok(position('insert into public.social_reports' in lower(pg_get_functiondef('public.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure)))>0,'signalement utilise social_reports canonique');
select ok(position($q$'snapshot_source','server'$q$ in replace(pg_get_functiondef('public.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure),' ',''))>0,'snapshot marqué serveur');
select ok(position('social_real_posts' in pg_get_functiondef('public.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,'publication réelle résolue côté serveur');
select ok(position('social_real_comments' in pg_get_functiondef('public.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,'commentaire réel résolu côté serveur');
select ok(position('social_character_posts' in pg_get_functiondef('public.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,'publication personnage résolue côté serveur');
select ok(position('social_character_comments' in pg_get_functiondef('public.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,'commentaire personnage résolu côté serveur');
select ok(position($q$interval'1hour'$q$ in replace(pg_get_functiondef('public.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure),' ',''))>0,'anti-spam horaire présent');
select ok(position('SOCIAL_REPORT_ALREADY_OPEN' in pg_get_functiondef('public.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,'doublon ouvert bloqué');
select ok(position('where b.blocker_user_id=auth.uid()' in replace(pg_get_functiondef('public.social_my_blocks()'::regprocedure),' ',''))>0,'liste blocages limitée à auth.uid');
select ok(position('where r.reporter_user_id=auth.uid()' in replace(pg_get_functiondef('public.social_my_reports(integer)'::regprocedure),' ',''))>0,'historique signalements limité à auth.uid');

select * from finish();
rollback;