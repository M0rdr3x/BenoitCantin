begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,private,auth,extensions;

select plan(28);

select has_table('public','sinjira_canon_sources','le Registre des sources canoniques existe');
select has_table('public','sinjira_story_claims','les faits de provenance des Chroniques existent');

select has_column('public','sinjira_world_locations','source_id','les lieux peuvent pointer vers une source structurée');
select has_column('public','sinjira_world_travel_rules','source_id','les trajets peuvent pointer vers une source structurée');
select has_column('public','sinjira_canon_events','source_id','les événements peuvent pointer vers une source structurée');
select has_column('public','sinjira_canon_event_characters','source_id','les présences peuvent pointer vers une source structurée');

select has_function('private','sinjira_source_is_verified',array['uuid'],'le vérificateur privé de source existe');
select has_function('private','sinjira_require_verified_provenance',array[]::text[],'le trigger de provenance canonique existe');
select has_function('private','sinjira_require_verified_story_claim',array[]::text[],'le trigger de fait vérifié existe');
select has_function('private','sinjira_guard_published_story_claim',array[]::text[],'le verrou des faits de Chronique publiée existe');

select ok(
  (select relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='public' and c.relname='sinjira_canon_sources'),
  'RLS est actif sur les sources canoniques'
);
select ok(
  (select relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='public' and c.relname='sinjira_story_claims'),
  'RLS est actif sur les faits de provenance'
);

select ok(
  not has_table_privilege('anon','public.sinjira_canon_sources','SELECT')
  and not has_table_privilege('authenticated','public.sinjira_canon_sources','SELECT'),
  'les sources privées ne sont pas lisibles directement par les clients'
);
select ok(
  not has_table_privilege('anon','public.sinjira_story_claims','SELECT')
  and not has_table_privilege('authenticated','public.sinjira_story_claims','SELECT'),
  'les faits privés ne sont pas lisibles directement par les clients'
);

select ok(not has_function_privilege('authenticated','private.sinjira_source_is_verified(uuid)','EXECUTE'),
  'le vérificateur de source reste privé');
select ok(not has_function_privilege('authenticated','private.sinjira_require_verified_provenance()','EXECUTE'),
  'le trigger de provenance reste privé');
select ok(not has_function_privilege('authenticated','private.sinjira_require_verified_story_claim()','EXECUTE'),
  'le trigger de fait reste privé');
select ok(not has_function_privilege('authenticated','private.sinjira_guard_published_story_claim()','EXECUTE'),
  'le verrou des faits reste privé');

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_PROVENANCE_REQUIRED%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_publish_extended_story' limit 1),
  'la publication exige au moins un fait d ancrage vérifié'
);
select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_PROVENANCE_INCOMPLETE%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_publish_extended_story' limit 1),
  'la publication bloque les faits non résolus'
);

select ok(exists(
  select 1 from pg_trigger tr join pg_class t on t.oid=tr.tgrelid join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_world_locations'
    and tr.tgname='sinjira_world_locations_require_provenance' and not tr.tgisinternal
),'les lieux CANON vérifient leur source');

select ok(exists(
  select 1 from pg_trigger tr join pg_class t on t.oid=tr.tgrelid join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_world_travel_rules'
    and tr.tgname='sinjira_world_travel_require_provenance' and not tr.tgisinternal
),'les trajets CANON vérifient leur source');

select ok(exists(
  select 1 from pg_trigger tr join pg_class t on t.oid=tr.tgrelid join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_canon_events'
    and tr.tgname='sinjira_canon_events_require_provenance' and not tr.tgisinternal
),'les événements canoniques vérifient leur source');

select ok(exists(
  select 1 from pg_trigger tr join pg_class t on t.oid=tr.tgrelid join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_canon_event_characters'
    and tr.tgname='sinjira_canon_event_characters_require_provenance' and not tr.tgisinternal
),'les présences canoniques vérifient leur source');

select ok(exists(
  select 1 from pg_trigger tr join pg_class t on t.oid=tr.tgrelid join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_story_claims'
    and tr.tgname='sinjira_story_claims_require_verified_source' and not tr.tgisinternal
),'un fait VERIFIED exige une source vérifiée');

select ok(exists(
  select 1 from pg_trigger tr join pg_class t on t.oid=tr.tgrelid join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_story_claims'
    and tr.tgname='sinjira_story_claims_guard_published' and not tr.tgisinternal
),'les faits d une Chronique publiée sont verrouillés');

select ok(exists(
  select 1 from pg_trigger tr join pg_class t on t.oid=tr.tgrelid join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_canon_sources'
    and tr.tgname='sinjira_canon_sources_invalidate_extended' and not tr.tgisinternal
),'un changement de source invalide les publications');

select ok(
  (select pg_get_functiondef(p.oid) ilike '%source_kind in (''roman'',''bible'',''author_decision'',''archive'')%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_source_is_verified' limit 1),
  'les sources research ne peuvent pas prouver le canon'
);

select * from finish();
rollback;
