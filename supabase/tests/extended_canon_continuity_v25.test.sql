begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,private,auth,extensions;

select plan(58);

select has_table('public','sinjira_extended_stories','les récits du Canon étendu existent');
select has_table('public','sinjira_story_character_presence','les présences de Chroniques existent');
select has_table('public','sinjira_world_locations','l Atlas canonique existe');
select has_table('public','sinjira_world_travel_rules','les règles de déplacement existent');
select has_table('public','sinjira_canon_events','le Calendrier-Monde existe');
select has_table('public','sinjira_canon_event_characters','les présences du Calendrier-Monde existent');

select has_view('private','sinjira_effective_story_presence','la vue de présence effective existe');

select has_column('public','sinjira_extended_stories','location_id','une Chronique peut être reliée à l Atlas');
select has_column('public','sinjira_story_character_presence','segment_key','les présences supportent plusieurs segments');
select has_column('public','sinjira_story_character_presence','presence_kind','le type de segment est explicite');
select has_column('public','sinjira_story_character_presence','location_id','chaque segment peut avoir un lieu normalisé');
select has_column('public','sinjira_world_travel_rules','bidirectional','le sens du trajet est explicite');

select has_function('public','admin_sinjira_story_continuity_check',array['uuid'],'la vérification de continuité auteur existe');
select has_function('public','admin_sinjira_promote_extended_story',array['uuid'],'la promotion vers CANON_ETENDU existe');
select has_function('public','admin_sinjira_publish_extended_story',array['uuid','text'],'la publication atomique existe');
select has_function('public','admin_sinjira_unpublish_extended_story',array['uuid'],'le retrait de publication existe');
select has_function('private','sinjira_story_continuity_report',array['uuid'],'le moteur privé de continuité existe');
select has_function('private','sinjira_locations_compatible',array['uuid','uuid'],'le moteur compare les lieux hiérarchiques');
select has_function('private','sinjira_guard_published_story_update',array[]::text[],'le verrou SQL des Chroniques publiées existe');
select has_function('private','sinjira_guard_published_story_presence',array[]::text[],'le verrou SQL des segments publiés existe');
select has_function('private','sinjira_invalidate_published_extended_stories',array[]::text[],'l invalidation automatique des publications existe');

select ok(not has_function_privilege('anon','public.admin_sinjira_story_continuity_check(uuid)','EXECUTE'),
  'anon ne peut pas lancer le contrôle auteur');
select ok(has_function_privilege('authenticated','public.admin_sinjira_story_continuity_check(uuid)','EXECUTE'),
  'authenticated peut atteindre le wrapper qui impose ensuite admin AAL2');
select ok(not has_function_privilege('anon','public.admin_sinjira_promote_extended_story(uuid)','EXECUTE'),
  'anon ne peut pas promouvoir une Chronique');
select ok(has_function_privilege('authenticated','public.admin_sinjira_promote_extended_story(uuid)','EXECUTE'),
  'authenticated peut atteindre le wrapper de promotion protégé par admin AAL2');
select ok(not has_function_privilege('anon','public.admin_sinjira_publish_extended_story(uuid,text)','EXECUTE'),
  'anon ne peut pas publier une Chronique');
select ok(has_function_privilege('authenticated','public.admin_sinjira_publish_extended_story(uuid,text)','EXECUTE'),
  'authenticated peut atteindre le wrapper de publication protégé par admin AAL2');
select ok(not has_function_privilege('anon','public.admin_sinjira_unpublish_extended_story(uuid)','EXECUTE'),
  'anon ne peut pas retirer une Chronique de publication');
select ok(has_function_privilege('authenticated','public.admin_sinjira_unpublish_extended_story(uuid)','EXECUTE'),
  'authenticated peut atteindre le wrapper de retrait protégé par admin AAL2');

select ok(not has_function_privilege('authenticated','private.sinjira_story_continuity_report(uuid)','EXECUTE'),
  'le moteur privé de continuité n est pas directement invocable par le navigateur');
select ok(not has_function_privilege('authenticated','private.sinjira_locations_compatible(uuid,uuid)','EXECUTE'),
  'le helper privé de lieux n est pas directement invocable par le navigateur');
select ok(not has_function_privilege('authenticated','private.sinjira_guard_published_story_update()','EXECUTE'),
  'le verrou de Chronique publiée n est pas invocable directement');
select ok(not has_function_privilege('authenticated','private.sinjira_guard_published_story_presence()','EXECUTE'),
  'le verrou de segments publiés n est pas invocable directement');
select ok(not has_function_privilege('authenticated','private.sinjira_invalidate_published_extended_stories()','EXECUTE'),
  'l invalidation automatique n est pas invocable directement');

select ok(
  (select relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='public' and c.relname='sinjira_extended_stories'),
  'RLS est actif sur les Chroniques'
);
select ok(
  (select relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='public' and c.relname='sinjira_story_character_presence'),
  'RLS est actif sur les segments de présence'
);

select ok(
  not has_table_privilege('anon','public.sinjira_world_locations','SELECT')
  and not has_table_privilege('authenticated','public.sinjira_world_locations','SELECT'),
  'l Atlas privé n est pas lisible directement par les clients'
);
select ok(
  not has_table_privilege('anon','public.sinjira_canon_events','SELECT')
  and not has_table_privilege('authenticated','public.sinjira_canon_events','SELECT'),
  'le Calendrier-Monde privé n est pas lisible directement par les clients'
);

select ok(
  exists(
    select 1 from pg_constraint c
    join pg_class t on t.oid=c.conrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_story_character_presence'
      and c.contype='u'
      and pg_get_constraintdef(c.oid) like '%story_id, character_id, segment_key%'
  ),
  'un personnage peut avoir plusieurs segments mais pas deux fois la même clé dans une Chronique'
);

select ok(
  exists(
    select 1 from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.proname='admin_sinjira_promote_extended_story'
      and p.prosecdef
      and array_to_string(p.proconfig,',') like '%search_path=%'
  ),
  'la promotion est SECURITY DEFINER avec search_path figé'
);

select ok(
  exists(
    select 1 from pg_constraint c
    join pg_class t on t.oid=c.conrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_extended_stories'
      and c.contype='c'
      and pg_get_constraintdef(c.oid) ilike '%status <> ''published''%'
      and pg_get_constraintdef(c.oid) ilike '%CANON_ETENDU%'
  ),
  'une Chronique publiée doit être CANON_ETENDU'
);

select ok(
  exists(
    select 1 from pg_constraint c
    join pg_class t on t.oid=c.conrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_extended_stories'
      and c.contype='c'
      and pg_get_constraintdef(c.oid) ilike '%published_at%'
      and pg_get_constraintdef(c.oid) ilike '%status%'
  ),
  'published_at est lié à l état published par contrainte SQL'
);

select ok(
  exists(
    select 1 from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.proname='admin_sinjira_publish_extended_story'
      and p.prosecdef
      and array_to_string(p.proconfig,',') like '%search_path=%'
  ),
  'la publication est SECURITY DEFINER avec search_path figé'
);

select ok(
  exists(
    select 1 from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.proname='admin_sinjira_unpublish_extended_story'
      and p.prosecdef
      and array_to_string(p.proconfig,',') like '%search_path=%'
  ),
  'le retrait de publication est SECURITY DEFINER avec search_path figé'
);


select ok(
  exists(
    select 1 from pg_constraint c
    join pg_class t on t.oid=c.conrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_extended_stories'
      and c.conname='sinjira_extended_stories_published_metadata_check'
      and c.contype='c'
  ),
  'la base exige les métadonnées canoniques avant publication'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_extended_stories'
      and tr.tgname='sinjira_extended_stories_guard_published'
      and not tr.tgisinternal
  ),
  'un trigger verrouille les Chroniques publiées'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_story_character_presence'
      and tr.tgname='sinjira_story_presence_guard_published'
      and not tr.tgisinternal
  ),
  'un trigger verrouille les segments des Chroniques publiées'
);


select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_world_locations'
      and tr.tgname='sinjira_world_locations_invalidate_extended_update'
      and not tr.tgisinternal
  ),
  'l Atlas invalide les publications après changement de hiérarchie ou statut'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_world_locations'
      and tr.tgname='sinjira_world_locations_invalidate_extended_delete'
      and not tr.tgisinternal
  ),
  'la suppression d un lieu invalide les publications'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_world_travel_rules'
      and tr.tgname='sinjira_world_travel_invalidate_extended'
      and not tr.tgisinternal
  ),
  'les règles de trajet invalident les publications'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_events'
      and tr.tgname='sinjira_canon_events_invalidate_extended_insert_delete'
      and not tr.tgisinternal
  ),
  'les événements canoniques ajoutés ou retirés invalident les publications'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_events'
      and tr.tgname='sinjira_canon_events_invalidate_extended_update'
      and not tr.tgisinternal
  ),
  'les changements temporels ou géographiques d événements invalident les publications'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_event_characters'
      and tr.tgname='sinjira_canon_event_characters_invalidate_extended'
      and not tr.tgisinternal
  ),
  'les présences canoniques invalident les publications'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_context'
      and tr.tgname='sinjira_canon_context_invalidate_extended'
      and not tr.tgisinternal
  ),
  'le contexte du Canon central invalide les publications'
);


select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_LOCATION_NOT_CANON%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_publish_extended_story' limit 1),
  'la publication exige un lieu principal CANON'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%location_not_canon%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_story_continuity_report' limit 1),
  'le rapport de continuité bloque les segments dans un lieu non CANON'
);


select ok(
  (select pg_get_functiondef(p.oid) ilike '%central_presence_uncertain%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_story_continuity_report' limit 1),
  'les présences centrales incertaines deviennent des avertissements bloquants'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%cp.certainty=''confirmed''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_story_continuity_report' limit 1),
  'seules les présences centrales confirmées produisent une collision ferme'
);

select * from finish();
rollback;
