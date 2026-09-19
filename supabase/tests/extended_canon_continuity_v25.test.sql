begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,private,auth,extensions;

select plan(28);

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
select has_function('private','sinjira_story_continuity_report',array['uuid'],'le moteur privé de continuité existe');
select has_function('private','sinjira_locations_compatible',array['uuid','uuid'],'le moteur compare les lieux hiérarchiques');

select ok(not has_function_privilege('anon','public.admin_sinjira_story_continuity_check(uuid)','EXECUTE'),
  'anon ne peut pas lancer le contrôle auteur');
select ok(has_function_privilege('authenticated','public.admin_sinjira_story_continuity_check(uuid)','EXECUTE'),
  'authenticated peut atteindre le wrapper qui impose ensuite admin AAL2');
select ok(not has_function_privilege('anon','public.admin_sinjira_promote_extended_story(uuid)','EXECUTE'),
  'anon ne peut pas promouvoir une Chronique');
select ok(has_function_privilege('authenticated','public.admin_sinjira_promote_extended_story(uuid)','EXECUTE'),
  'authenticated peut atteindre le wrapper de promotion protégé par admin AAL2');

select ok(not has_function_privilege('authenticated','private.sinjira_story_continuity_report(uuid)','EXECUTE'),
  'le moteur privé de continuité n est pas directement invocable par le navigateur');
select ok(not has_function_privilege('authenticated','private.sinjira_locations_compatible(uuid,uuid)','EXECUTE'),
  'le helper privé de lieux n est pas directement invocable par le navigateur');

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

select * from finish();
rollback;
