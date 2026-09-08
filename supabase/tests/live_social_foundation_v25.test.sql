begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,extensions;

select plan(46);

-- Fondation : trois tables, toutes sous RLS, aucune présence persistante.
select has_table('public','social_live_rooms','salons En direct présents');
select has_table('public','social_live_room_members','adhésions En direct présentes');
select has_table('public','social_live_messages','messages En direct présents');
select ok((select relrowsecurity from pg_class where oid='public.social_live_rooms'::regclass),'RLS salons active');
select ok((select relrowsecurity from pg_class where oid='public.social_live_room_members'::regclass),'RLS adhésions active');
select ok((select relrowsecurity from pg_class where oid='public.social_live_messages'::regclass),'RLS messages active');
select ok(to_regclass('public.social_live_presence') is null,'aucune table de présence persistante');

-- Anon reste totalement fermé.
select ok(not has_table_privilege('anon','public.social_live_rooms','SELECT'),'anon ne lit pas les salons');
select ok(not has_table_privilege('anon','public.social_live_room_members','SELECT'),'anon ne lit pas les adhésions');
select ok(not has_table_privilege('anon','public.social_live_messages','SELECT'),'anon ne lit pas les messages');
select ok(not has_table_privilege('anon','public.social_live_messages','INSERT'),'anon ne publie pas de message');

-- Identité serveur : le navigateur ne peut fournir ni propriétaire, cohorte, auteur ni rôle.
select ok(has_column_privilege('authenticated','public.social_live_rooms','slug','INSERT'),'auth peut fournir le slug');
select ok(not has_column_privilege('authenticated','public.social_live_rooms','owner_user_id','INSERT'),'owner_user_id non injectable');
select ok(not has_column_privilege('authenticated','public.social_live_rooms','audience','INSERT'),'audience non injectable');
select ok(has_column_privilege('authenticated','public.social_live_room_members','room_id','INSERT'),'auth peut demander à rejoindre un salon');
select ok(not has_column_privilege('authenticated','public.social_live_room_members','user_id','INSERT'),'user_id adhésion non injectable');
select ok(not has_column_privilege('authenticated','public.social_live_room_members','role','INSERT'),'rôle adhésion non injectable');
select ok(has_column_privilege('authenticated','public.social_live_messages','body','INSERT'),'auth peut fournir le corps du message');
select ok(not has_column_privilege('authenticated','public.social_live_messages','user_id','INSERT'),'auteur message non injectable');
select ok(not has_table_privilege('authenticated','public.social_live_messages','UPDATE'),'messages non éditables directement en fondation');
select ok(not has_table_privilege('authenticated','public.social_live_messages','DELETE'),'messages non supprimables directement en fondation');

-- Valeurs par défaut dérivées du serveur.
select ok((select column_default ilike '%auth.uid%' from information_schema.columns where table_schema='public' and table_name='social_live_rooms' and column_name='owner_user_id'),'owner par défaut = auth.uid');
select ok((select column_default ilike '%sinjira_my_age_band%' from information_schema.columns where table_schema='public' and table_name='social_live_rooms' and column_name='audience'),'cohorte par défaut = cohorte propre canonique');
select ok((select column_default ilike '%auth.uid%' from information_schema.columns where table_schema='public' and table_name='social_live_messages' and column_name='user_id'),'auteur par défaut = auth.uid');

-- Politiques : cohorte, règles, suspension, blocages et membership privé restent dans la base.
select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='social_live_rooms' and policyname='social_live_rooms_read' and qual ilike '%sinjira_my_age_band%' and qual ilike '%social_is_blocked%' and qual ilike '%has_accepted_community_rules%' and qual ilike '%social_is_suspended%'),'lecture salons réutilise jeunesse + règles + suspension + blocages');
select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='social_live_rooms' and policyname='social_live_rooms_read' and qual ilike '%visibility%' and qual ilike '%social_live_is_room_member%'),'salon privé exige une adhésion via helper self-only sans récursion RLS');
select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='social_live_room_members' and policyname='social_live_members_public_join' and with_check ilike '%visibility%' and with_check ilike '%public%' and with_check ilike '%sinjira_my_age_band%'),'auto-join limité aux salons publics de même cohorte');
select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='social_live_room_members' and policyname='social_live_members_self_read' and qual ilike '%auth.uid%'),'adhésions lisibles uniquement par soi');
select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='social_live_messages' and policyname='social_live_messages_read' and qual ilike '%sinjira_can_social_interact%' and qual ilike '%social_is_blocked%'),'messages filtrés par cohorte et blocage');
select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='social_live_messages' and policyname='social_live_messages_insert' and with_check ilike '%social_live_room_members%' and with_check ilike '%has_accepted_community_rules%' and with_check ilike '%social_is_suspended%'),'écriture exige adhésion + règles + absence de suspension');

-- Garde-fous anti-spam/anti-raid sans IP/GPS.
select ok(position('pg_advisory_xact_lock' in pg_get_functiondef('public.social_live_room_insert_guard()'::regprocedure))>0,'création salon sérialisée par compte');
select ok(position('interval ''1 hour''' in pg_get_functiondef('public.social_live_room_insert_guard()'::regprocedure))>0,'création salon bornée dans le temps');
select ok(position('pg_advisory_xact_lock' in pg_get_functiondef('public.social_live_member_insert_guard()'::regprocedure))>0,'adhésion sérialisée par compte');
select ok(position('interval ''10 seconds''' in pg_get_functiondef('public.social_live_message_insert_guard()'::regprocedure))>0,'limite rafale messages présente');
select ok(position('interval ''1 minute''' in pg_get_functiondef('public.social_live_message_insert_guard()'::regprocedure))>0,'limite minute messages présente');
select ok(position('SOCIAL_LIVE_DUPLICATE_MESSAGE' in pg_get_functiondef('public.social_live_message_insert_guard()'::regprocedure))>0,'anti-duplication message présente');
select ok(position('SOCIAL_LIVE_AUTHOR_MISMATCH' in pg_get_functiondef('public.social_live_message_insert_guard()'::regprocedure))>0,'garde anti-usurpation présente');

-- Realtime : Broadcast minimal serveur + Presence privée, jamais un faux payload client de message.
select ok(exists(select 1 from pg_trigger where tgrelid='public.social_live_messages'::regclass and tgname='social_live_message_notify_trigger' and not tgisinternal),'trigger Realtime message présent');
select ok(position('realtime.send' in pg_get_functiondef('public.social_live_notify_message_insert()'::regprocedure))>0,'notification utilise Realtime Broadcast serveur');
select ok(position('''message_id''' in pg_get_functiondef('public.social_live_notify_message_insert()'::regprocedure))>0,'Broadcast contient identifiant message');
select ok(position('''body''' in pg_get_functiondef('public.social_live_notify_message_insert()'::regprocedure))=0,'Broadcast ne contient jamais le corps du message');
select ok(not has_function_privilege('authenticated','public.social_live_notify_message_insert()','EXECUTE'),'client ne peut pas invoquer le trigger Broadcast');

-- Realtime Authorization : les politiques restrictives protègent le namespace sinjira-live:*.
select ok(exists(select 1 from pg_policies where schemaname='realtime' and tablename='messages' and policyname='sinjira_live_realtime_read' and cmd='SELECT' and permissive='PERMISSIVE' and qual ilike '%broadcast%' and qual ilike '%presence%' and qual ilike '%sinjira-live:%'),'lecture Realtime privée au namespace live');
select ok(exists(select 1 from pg_policies where schemaname='realtime' and tablename='messages' and policyname='sinjira_live_realtime_read_guard' and cmd='SELECT' and permissive='RESTRICTIVE' and qual ilike '%sinjira-live:%'),'garde restrictive lecture Realtime présente');
select ok(exists(select 1 from pg_policies where schemaname='realtime' and tablename='messages' and policyname='sinjira_live_realtime_presence_write' and cmd='INSERT' and with_check ilike '%presence%' and with_check not ilike '%broadcast%'),'client ne peut écrire que Presence sur le canal live');
select ok(exists(select 1 from pg_policies where schemaname='realtime' and tablename='messages' and policyname='sinjira_live_realtime_write_guard' and cmd='INSERT' and permissive='RESTRICTIVE' and with_check ilike '%sinjira-live:%'),'garde restrictive écriture Realtime présente');

select * from finish();
rollback;