begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(10);

select ok(to_regprocedure('public.invite_sinjira_playtest_participant(uuid,uuid)') is not null, 'RPC invitation admin présente');
select ok(to_regprocedure('public.accept_sinjira_playtest_invitation(uuid)') is not null, 'RPC acceptation membre présente');

select ok(not has_function_privilege('anon','public.invite_sinjira_playtest_participant(uuid,uuid)','EXECUTE'), 'anon ne peut pas inviter un participant');
select ok(has_function_privilege('authenticated','public.invite_sinjira_playtest_participant(uuid,uuid)','EXECUTE'), 'authenticated peut appeler le RPC invitation, dont le contrôle admin reste interne');
select ok(not has_function_privilege('anon','public.accept_sinjira_playtest_invitation(uuid)','EXECUTE'), 'anon ne peut pas accepter une invitation');
select ok(has_function_privilege('authenticated','public.accept_sinjira_playtest_invitation(uuid)','EXECUTE'), 'authenticated peut accepter sa propre invitation via le RPC');

select ok((select prosecdef from pg_proc where oid='public.invite_sinjira_playtest_participant(uuid,uuid)'::regprocedure), 'RPC invitation est SECURITY DEFINER');
select ok((select prosecdef from pg_proc where oid='public.accept_sinjira_playtest_invitation(uuid)'::regprocedure), 'RPC acceptation est SECURITY DEFINER');
select is((select array_to_string(proconfig,',') from pg_proc where oid='public.invite_sinjira_playtest_participant(uuid,uuid)'::regprocedure), 'search_path=pg_catalog, public', 'RPC invitation possède un search_path fixe');
select is((select array_to_string(proconfig,',') from pg_proc where oid='public.accept_sinjira_playtest_invitation(uuid)'::regprocedure), 'search_path=pg_catalog, public', 'RPC acceptation possède un search_path fixe');

select * from finish();
rollback;
