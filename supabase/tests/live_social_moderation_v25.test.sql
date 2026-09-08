begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(17);

select ok(
  pg_get_constraintdef((select oid from pg_constraint where conrelid='public.social_reports'::regclass and conname='social_reports_network_check')) ilike '%live%',
  'social_reports accepte le réseau live'
);
select ok(
  pg_get_constraintdef((select oid from pg_constraint where conrelid='private.moderation_decisions'::regclass and conname='moderation_decisions_network_check')) ilike '%live%',
  'les décisions humaines acceptent le réseau live'
);

select ok(
  not (select prosecdef from pg_proc where oid='public.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure),
  'wrapper public social_report_content reste SECURITY INVOKER'
);
select ok(
  (select prosecdef from pg_proc where oid='sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure),
  'implémentation sociale interne reste SECURITY DEFINER hors schéma public'
);
select ok(
  has_function_privilege('authenticated','public.social_report_content(text,text,uuid,text,text,boolean)','EXECUTE'),
  'authenticated peut utiliser le wrapper de signalement'
);
select ok(
  not has_function_privilege('anon','public.social_report_content(text,text,uuid,text,text,boolean)','EXECUTE'),
  'anon ne peut pas signaler'
);

select ok(
  position("p_network='live'" in pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,
  'implémentation reconnaît explicitement live'
);
select ok(
  position('public.social_live_messages' in pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,
  'cible live résolue depuis la table serveur des messages'
);
select ok(
  position('public.social_live_room_members' in pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,
  'reporter live doit être membre du salon'
);
select ok(
  position("p_target_type<>'message'" in pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,
  'live ne permet que le signalement de messages dans cet incrément'
);
select ok(
  position("'snapshot_source','server'" in pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,
  'preuve de signalement reconstruite côté serveur'
);
select ok(
  position("'identity_data_included',false" in pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,
  'snapshot n inclut pas de donnée identité supplémentaire'
);
select ok(
  position('pg_advisory_xact_lock' in pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,
  'signalements sérialisés par compte contre les rafales'
);
select ok(
  position('interval ''1 hour''' in pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure))>0,
  'limite temporelle de signalement conservée'
);

select ok(
  exists(
    select 1 from pg_policies
    where schemaname='public' and tablename='social_live_messages'
      and policyname='social_live_messages_read'
      and qual ilike '%moderation_content_visible%'
      and qual ilike '%live%'
      and qual ilike '%message%'
  ),
  'RLS des messages live applique le masquage de modération'
);
select ok(
  position('inet_client_addr' in lower(pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure)))=0,
  'signalement live ne collecte pas l IP'
);
select ok(
  position('latitude' in lower(pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure)))=0
  and position('longitude' in lower(pg_get_functiondef('sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)'::regprocedure)))=0,
  'signalement live ne collecte pas de GPS'
);

select * from finish();
rollback;
