begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(14);

select ok(to_regprocedure('public.dating_report_connection(uuid,text,text,boolean)') is not null,'RPC signalement dating existe');
select ok(has_function_privilege('authenticated','public.dating_report_connection(uuid,text,text,boolean)','EXECUTE'),'authenticated peut signaler une rencontre');
select ok(not has_function_privilege('anon','public.dating_report_connection(uuid,text,text,boolean)','EXECUTE'),'anon ne peut pas signaler une rencontre');

select ok(position('social_suspensions' in pg_get_functiondef('private.dating_is_eligible(uuid)'::regprocedure))>0,'admissibilité dating tient compte des suspensions sociales');
select ok(position('until_at>now()' in replace(pg_get_functiondef('private.dating_is_eligible(uuid)'::regprocedure),' ',''))>0,'suspension sociale active exclut Rencontres');

select ok(position('insert into public.social_reports' in lower(pg_get_functiondef('sinjira_dating_internal.dating_report_connection(uuid,text,text,boolean)'::regprocedure)))>0,'signalement utilise le pipeline social_reports canonique');
select ok(position($q$'source','dating'$q$ in replace(pg_get_functiondef('sinjira_dating_internal.dating_report_connection(uuid,text,text,boolean)'::regprocedure),' ',''))>0,'snapshot identifie la source dating');
select ok(position('limit 30' in lower(pg_get_functiondef('sinjira_dating_internal.dating_report_connection(uuid,text,text,boolean)'::regprocedure)))>0,'preuve limitée aux 30 derniers messages');
select ok(position($q$interval'1hour'$q$ in replace(pg_get_functiondef('sinjira_dating_internal.dating_report_connection(uuid,text,text,boolean)'::regprocedure),' ',''))>0,'anti-spam signalement horaire présent');
select ok(position('DATING_REPORT_ALREADY_OPEN' in pg_get_functiondef('sinjira_dating_internal.dating_report_connection(uuid,text,text,boolean)'::regprocedure))>0,'doublon de signalement ouvert bloqué');
select ok(position('insert into public.social_blocks' in lower(pg_get_functiondef('sinjira_dating_internal.dating_report_connection(uuid,text,text,boolean)'::regprocedure)))>0,'signalement peut aussi bloquer via social_blocks');
select ok(position($q$status='closed'$q$ in replace(pg_get_functiondef('sinjira_dating_internal.dating_report_connection(uuid,text,text,boolean)'::regprocedure),' ',''))>0,'blocage ferme la rencontre');
select ok(position('a_photo_consent=false' in replace(pg_get_functiondef('sinjira_dating_internal.dating_report_connection(uuid,text,text,boolean)'::regprocedure),' ',''))>0,'fermeture révoque consentement A');
select ok(position('b_photo_consent=false' in replace(pg_get_functiondef('sinjira_dating_internal.dating_report_connection(uuid,text,text,boolean)'::regprocedure),' ',''))>0,'fermeture révoque consentement B');

select * from finish();
rollback;