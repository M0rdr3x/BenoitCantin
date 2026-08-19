begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, private, extensions;

select plan(16);

select ok(exists(
  select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='private' and p.proname='notify_social_comment_reply'
),'fonction privée avis social présente');

select ok(exists(
  select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='private' and p.proname='notify_social_comment_reply' and p.prosecdef
),'fonction avis social SECURITY DEFINER');

select ok(not exists(
  select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='private' and p.proname='notify_social_comment_reply'
    and has_function_privilege('anon',p.oid,'EXECUTE')
),'anon ne peut pas exécuter le trigger social');

select ok(not exists(
  select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='private' and p.proname='notify_social_comment_reply'
    and has_function_privilege('authenticated',p.oid,'EXECUTE')
),'authenticated ne peut pas exécuter le trigger social');

select ok(exists(
  select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='private' and p.proname='notify_social_comment_reply'
    and has_function_privilege('service_role',p.oid,'EXECUTE')
),'service_role conserve EXECUTE');

select is((select count(*) from pg_trigger where tgrelid='public.social_real_comments'::regclass and tgname='trg_user_notify_social_real_reply' and not tgisinternal),1::bigint,'trigger réponse réelle présent');
select is((select count(*) from pg_trigger where tgrelid='public.social_character_comments'::regclass and tgname='trg_user_notify_social_character_reply' and not tgisinternal),1::bigint,'trigger réponse personnage présent');

select ok(position('community_activity' in pg_get_functiondef(p.oid))>0,'préférence activité communauté respectée')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='notify_social_comment_reply';
select ok(position('v_owner_user_id = new.user_id' in pg_get_functiondef(p.oid))>0,'auto-commentaire ignoré')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='notify_social_comment_reply';
select ok(position('social_real_reply' in pg_get_functiondef(p.oid))>0,'type avis Communauté présent')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='notify_social_comment_reply';
select ok(position('social_character_reply' in pg_get_functiondef(p.oid))>0,'type avis rôle-play présent')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='notify_social_comment_reply';
select ok(position('/compte/communaute.html?post=' in pg_get_functiondef(p.oid))>0,'route ciblée Communauté présente')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='notify_social_comment_reply';
select ok(position('/compte/reseau-personnage.html?post=' in pg_get_functiondef(p.oid))>0,'route ciblée rôle-play présente')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='notify_social_comment_reply';
select ok(position('insert into public.user_notifications' in lower(pg_get_functiondef(p.oid)))>0,'avis écrit uniquement dans user_notifications')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='notify_social_comment_reply';
select ok(position('new.body' in lower(pg_get_functiondef(p.oid)))=0,'aucun texte libre du commentaire copié dans l’avis')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='notify_social_comment_reply';
select ok(exists(
  select 1
  from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  cross join lateral unnest(coalesce(p.proconfig,array[]::text[])) cfg
  where n.nspname='private'
    and p.proname='notify_social_comment_reply'
    and cfg='search_path=pg_catalog, public'
),'search_path du trigger fixé');

select * from finish();
rollback;
