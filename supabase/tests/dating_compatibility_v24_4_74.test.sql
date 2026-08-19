begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, private, extensions;

select plan(34);

select ok(to_regclass('public.dating_profiles') is not null,'dating_profiles existe');
select ok(to_regclass('public.dating_preferences') is not null,'dating_preferences existe');
select ok(to_regclass('public.dating_connections') is not null,'dating_connections existe');
select ok(to_regclass('public.dating_messages') is not null,'dating_messages existe');

select ok((select relrowsecurity from pg_class where oid='public.dating_profiles'::regclass),'RLS profils activé');
select ok((select relrowsecurity from pg_class where oid='public.dating_preferences'::regclass),'RLS préférences activé');
select ok((select relrowsecurity from pg_class where oid='public.dating_connections'::regclass),'RLS connexions activé');
select ok((select relrowsecurity from pg_class where oid='public.dating_messages'::regclass),'RLS messages activé');

select ok(not has_table_privilege('anon','public.dating_profiles','SELECT'),'anon ne lit pas les profils dating');
select ok(not has_table_privilege('anon','public.dating_preferences','SELECT'),'anon ne lit pas les préférences dating');
select ok(not has_table_privilege('anon','public.dating_connections','SELECT'),'anon ne lit pas les connexions dating');
select ok(not has_table_privilege('anon','public.dating_messages','SELECT'),'anon ne lit pas les messages dating');
select ok(not has_table_privilege('authenticated','public.dating_connections','SELECT'),'authenticated ne lit pas directement les connexions');
select ok(not has_table_privilege('authenticated','public.dating_messages','SELECT'),'authenticated ne lit pas directement les messages');
select ok(has_table_privilege('authenticated','public.dating_profiles','SELECT'),'authenticated peut lire son profil via RLS');
select ok(has_table_privilege('authenticated','public.dating_preferences','SELECT'),'authenticated peut lire ses préférences via RLS');

select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='dating_profiles' and policyname='dating_profiles_self'),'politique self-only profil présente');
select ok(exists(select 1 from pg_policies where schemaname='public' and tablename='dating_preferences' and policyname='dating_preferences_self'),'politique self-only préférences présente');

select ok(has_function_privilege('authenticated','public.dating_compatibility_candidates(integer)','EXECUTE'),'RPC compatibilité exécutable par authenticated');
select ok(not has_function_privilege('anon','public.dating_compatibility_candidates(integer)','EXECUTE'),'RPC compatibilité interdite à anon');
select ok(has_function_privilege('authenticated','public.dating_send_message(uuid,text)','EXECUTE'),'RPC message exécutable par authenticated');
select ok(not has_function_privilege('anon','public.dating_send_message(uuid,text)','EXECUTE'),'RPC message interdite à anon');
select ok(has_function_privilege('authenticated','public.dating_close_connection(uuid)','EXECUTE'),'RPC fermeture exécutable par authenticated');
select ok(not has_function_privilege('anon','public.dating_close_connection(uuid)','EXECUTE'),'RPC fermeture interdite à anon');
select ok(has_function_privilege('authenticated','public.dating_block_connection(uuid)','EXECUTE'),'RPC blocage exécutable par authenticated');
select ok(not has_function_privilege('anon','public.dating_block_connection(uuid)','EXECUTE'),'RPC blocage interdite à anon');

select ok(position($q$relationship_status='single'$q$ in replace(pg_get_functiondef('private.dating_is_eligible(uuid)'::regprocedure),' ',''))>0,'admissibilité exige célibataire');
select ok(position('>=18' in replace(pg_get_functiondef('private.dating_is_eligible(uuid)'::regprocedure),' ',''))>0,'admissibilité exige 18+');
select ok(position($q$interval'90days'$q$ in replace(pg_get_functiondef('private.dating_is_eligible(uuid)'::regprocedure),' ',''))>0,'confirmation célibataire expire après 90 jours');
select ok(position('v_my<10orv_their<10' in replace(pg_get_functiondef('public.dating_set_photo_consent(uuid,boolean)'::regprocedure),' ',''))>0,'dévoilement exige 10 messages chacun');
select ok(position($q$'dating'$q$ in pg_get_functiondef('public.dating_request_conversation(uuid)'::regprocedure))>0,'proposition produit un avis interne dating');
select ok(not exists(select 1 from information_schema.columns where table_schema='public' and table_name='dating_messages' and (column_name ilike '%photo%' or column_name ilike '%image%' or column_name ilike '%attachment%')),'messagerie dating ne stocke aucune image ou pièce jointe');
select ok(position('insert into public.social_blocks' in lower(pg_get_functiondef('public.dating_block_connection(uuid)'::regprocedure)))>0,'blocage dating utilise social_blocks sans révéler l’identité');
select ok(position($q$status = 'closed'$q$ in pg_get_functiondef('public.dating_close_connection(uuid)'::regprocedure))>0,'fermeture dating clôt la connexion');

select * from finish();
rollback;
