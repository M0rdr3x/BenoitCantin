begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, private, extensions;

select plan(20);

select ok(to_regprocedure('private.dating_contains_contact_info(text)') is not null,'détecteur coordonnées présent');
select ok(to_regprocedure('private.dating_array_contains_contact_info(text[])') is not null,'détecteur tableaux présent');
select ok(not has_function_privilege('authenticated','private.dating_contains_contact_info(text)','EXECUTE'),'détecteur privé non exécutable par client');

select ok(private.dating_contains_contact_info('Écrivez-moi à test@example.com'),'courriel détecté');
select ok(private.dating_contains_contact_info('Téléphone: +1 514 555 1234'),'téléphone détecté');
select ok(private.dating_contains_contact_info('Mon site est https://example.com/profil'),'URL détectée');
select ok(private.dating_contains_contact_info('Mon pseudo est @abyss_time'),'@identifiant détecté');
select ok(private.dating_contains_contact_info('discord: abyss123'),'identifiant social explicite détecté');
select ok(not private.dating_contains_contact_info('J’aime lire, cuisiner et marcher à Montréal.'),'texte normal accepté');
select ok(not private.dating_contains_contact_info('Je cherche une relation stable et honnête.'),'présentation normale acceptée');

select is((select count(*) from pg_trigger where tgrelid='public.dating_profiles'::regclass and tgname='dating_profile_contact_guard' and not tgisinternal),1::bigint,'trigger profil coordonnées présent');
select is((select count(*) from pg_trigger where tgrelid='public.dating_preferences'::regclass and tgname='dating_preferences_contact_guard' and not tgisinternal),1::bigint,'trigger préférences coordonnées présent');
select is((select count(*) from pg_trigger where tgrelid='public.social_blocks'::regclass and tgname='dating_social_block_guard' and not tgisinternal),1::bigint,'blocage communautaire ferme Rencontres');

select ok(position('dating_contains_contact_info' in lower(pg_get_functiondef('private.dating_is_eligible(uuid)'::regprocedure)))>0,'admissibilité vérifie les coordonnées');
select ok(position('dating_contact_info_forbidden_before_reveal' in lower(pg_get_functiondef('sinjira_dating_internal.dating_send_message(uuid,text)'::regprocedure)))>0,'chat bloque coordonnées avant dévoilement');
select ok(position('dating_rate_limit' in lower(pg_get_functiondef('sinjira_dating_internal.dating_send_message(uuid,text)'::regprocedure)))>0,'chat possède anti-spam serveur');
select ok(position('social_blocks' in lower(pg_get_functiondef('sinjira_dating_internal.dating_send_message(uuid,text)'::regprocedure)))>0,'chat respecte les blocages communautaires');
select ok(position('dating_contains_contact_info(o.intro)' in lower(pg_get_functiondef('sinjira_dating_internal.dating_connections_overview()'::regprocedure)))>0,'aperçu assainit introduction historique');
select ok(position('dating_contains_contact_info(o.region)' in lower(pg_get_functiondef('sinjira_dating_internal.dating_connections_overview()'::regprocedure)))>0,'aperçu assainit région historique');
select ok(position('v_my_count>=10' in replace(lower(pg_get_functiondef('sinjira_dating_internal.dating_send_message(uuid,text)'::regprocedure)),' ',''))>0 and position('v_their_count>=10' in replace(lower(pg_get_functiondef('sinjira_dating_internal.dating_send_message(uuid,text)'::regprocedure)),' ',''))>0,'chat conserve le seuil 10+10 avant coordonnées');

select * from finish();
rollback;
