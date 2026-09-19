begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,private,auth,extensions;

select plan(59);

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


select ok(
  exists(
    select 1
    from pg_constraint c
    join pg_class t on t.oid=c.conrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_sources'
      and c.contype='c'
      and pg_get_constraintdef(c.oid) ilike '%chapter_reference%'
      and pg_get_constraintdef(c.oid) ilike '%passage_reference%'
      and pg_get_constraintdef(c.oid) ilike '%source_version%'
  ),
  'une source vérifiée doit conserver un repère précis'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%CLAIM_SOURCE_SCOPE_MISMATCH%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_require_verified_story_claim' limit 1),
  'un fait d ancrage bloque une source provenant de la mauvaise période'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_SCOPE_MISMATCH%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_require_verified_provenance' limit 1),
  'un événement bloque une source provenant de la mauvaise période'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_events'
      and tr.tgname='sinjira_canon_events_guard_source_scope'
      and not tr.tgisinternal
  ),
  'un changement de période d événement protège les sources des présences existantes'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_events'
      and tr.tgname='sinjira_canon_events_scope_invalidate_extended'
      and not tr.tgisinternal
  ),
  'un changement de période d événement invalide les publications'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_PROVENANCE_SCOPE_MISMATCH%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_publish_extended_story' limit 1),
  'la publication exige un fait d ancrage de la bonne période'
);


select ok(
  exists(
    select 1
    from pg_constraint c
    join pg_class t on t.oid=c.conrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_sources'
      and c.contype='c'
      and pg_get_constraintdef(c.oid) ilike '%book_number between 1 and 12%'
      and pg_get_constraintdef(c.oid) ilike '%ORIGINES_13_14%'
  ),
  'le numéro du roman détermine automatiquement sa période canonique'
);


select has_function('private','sinjira_prevent_source_supersedes_cycle',array[]::text[],
  'le garde anti-cycle de remplacement des sources existe');

select has_function('private','sinjira_guard_canon_source_in_use',array[]::text[],
  'le garde d autorité des sources utilisées existe');

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_sources'
      and tr.tgname='sinjira_canon_sources_prevent_supersedes_cycle'
      and not tr.tgisinternal
  ),
  'la chaîne de remplacement des sources ne peut pas former de cycle'
);

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_sources'
      and tr.tgname='sinjira_canon_sources_guard_authority'
      and not tr.tgisinternal
  ),
  'les sources utilisées protègent leur autorité et leurs repères'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_KEY_IMMUTABLE%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'la clé stable d une source utilisée est immuable'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%chapter_reference is distinct from old.chapter_reference%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'le repère exact d une source canonique utilisée est immuable'
);


select has_function('private','sinjira_story_provenance_report',array['uuid'],
  'le rapport privé de provenance d une Chronique existe');

select ok(not has_function_privilege('authenticated','private.sinjira_story_provenance_report(uuid)','EXECUTE'),
  'le rapport privé de provenance n est pas directement invocable par le navigateur');

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_PROVENANCE_REQUIRED%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_promote_extended_story' limit 1),
  'la promotion CANON_ETENDU exige un fait d ancrage vérifié'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_PROVENANCE_INCOMPLETE%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_promote_extended_story' limit 1),
  'la promotion CANON_ETENDU bloque tout fait de provenance non résolu'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_PROVENANCE_SCOPE_MISMATCH%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_promote_extended_story' limit 1),
  'la promotion CANON_ETENDU exige un ancrage de la bonne période'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%sinjira_story_provenance_report%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_publish_extended_story' limit 1),
  'la publication réutilise le même rapport de provenance que la canonisation'
);


select has_function('public','admin_sinjira_story_validation_check',array['uuid'],
  'la prévalidation combinée provenance et continuité existe');

select ok(not has_function_privilege('anon','public.admin_sinjira_story_validation_check(uuid)','EXECUTE'),
  'anon ne peut pas lancer la prévalidation auteur');

select ok(has_function_privilege('authenticated','public.admin_sinjira_story_validation_check(uuid)','EXECUTE'),
  'authenticated atteint le wrapper qui impose ensuite admin AAL2');

select ok(
  (select pg_get_functiondef(p.oid) ilike '%sinjira_story_provenance_report%'
          and pg_get_functiondef(p.oid) ilike '%sinjira_story_continuity_report%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_story_validation_check' limit 1),
  'la prévalidation combine le rapport de provenance et le rapport de continuité'
);


select ok(
  (select pg_get_functiondef(p.oid) ilike '%''metadata'',jsonb_build_object%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_story_validation_check' limit 1),
  'la prévalidation inclut l état détaillé des métadonnées'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_METADATA_INCOMPLETE%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_promote_extended_story' limit 1),
  'CANON_ETENDU exige une période et un lieu renseignés'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_LOCATION_NOT_CANON%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_promote_extended_story' limit 1),
  'CANON_ETENDU exige un lieu CANON dans l Atlas'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_CONTENT_REQUIRED%'
          and pg_get_functiondef(p.oid) ilike '%status=''validated''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_promote_extended_story' limit 1),
  'CANON_ETENDU exige un contenu et produit toujours le statut validated'
);


select has_function('private','sinjira_prevent_canon_source_delete',array[]::text[],
  'le garde contre la suppression physique des sources existe');

select ok(
  exists(
    select 1 from pg_trigger tr
    join pg_class t on t.oid=tr.tgrelid
    join pg_namespace n on n.oid=t.relnamespace
    where n.nspname='public' and t.relname='sinjira_canon_sources'
      and tr.tgname='sinjira_canon_sources_prevent_delete'
      and not tr.tgisinternal
  ),
  'la suppression physique des sources canoniques est bloquée'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_DELETE_FORBIDDEN%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_prevent_canon_source_delete' limit 1),
  'une source doit être retirée logiquement au lieu d être supprimée'
);


select ok(
  (select pg_get_functiondef(p.oid) ilike '%supersedes_source_id is distinct from old.supersedes_source_id%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'la lignée de remplacement d une source canonique utilisée est immuable'
);

select * from finish();
rollback;
