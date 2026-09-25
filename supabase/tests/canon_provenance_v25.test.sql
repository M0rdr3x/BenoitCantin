begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,private,auth,extensions;

select plan(126);

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


select ok(
  (select pg_get_functiondef(p.oid) ilike '%newer.supersedes_source_id=old.id%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'une source déjà remplacée devient elle aussi un historique immuable'
);


select ok(not has_function_privilege('anon','public.admin_sinjira_promote_extended_story(uuid)','EXECUTE'),
  'anon ne peut pas promouvoir une Chronique vers CANON_ETENDU');

select ok(has_function_privilege('authenticated','public.admin_sinjira_promote_extended_story(uuid)','EXECUTE'),
  'authenticated atteint le RPC de promotion qui exige ensuite admin AAL2');

select ok(not has_function_privilege('anon','public.admin_sinjira_publish_extended_story(uuid,text)','EXECUTE'),
  'anon ne peut pas publier une Chronique');

select ok(has_function_privilege('authenticated','public.admin_sinjira_publish_extended_story(uuid,text)','EXECUTE'),
  'authenticated atteint le RPC de publication qui exige ensuite admin AAL2');


select has_function('private','sinjira_demote_extended_story_on_edit',array[]::text[],
  'le garde de rétrogradation des Chroniques modifiées existe');

select has_function('private','sinjira_demote_story_from_child_change',array[]::text[],
  'le garde de rétrogradation après modification des faits ou segments existe');

select ok(exists(
  select 1 from pg_trigger tr
  join pg_class t on t.oid=tr.tgrelid
  join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_extended_stories'
    and tr.tgname='sinjira_extended_stories_demote_on_edit'
    and not tr.tgisinternal
),'une modification structurelle du récit force une nouvelle canonisation');

select ok(exists(
  select 1 from pg_trigger tr
  join pg_class t on t.oid=tr.tgrelid
  join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_story_character_presence'
    and tr.tgname='sinjira_story_presence_demote_canon'
    and not tr.tgisinternal
),'une modification de segment retire CANON_ETENDU');

select ok(exists(
  select 1 from pg_trigger tr
  join pg_class t on t.oid=tr.tgrelid
  join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_story_claims'
    and tr.tgname='sinjira_story_claims_demote_canon'
    and not tr.tgisinternal
),'une modification de provenance retire CANON_ETENDU');

select ok(
  (select pg_get_functiondef(p.oid) ilike '%new.canon_status:=''PROVISOIRE''%'
          and pg_get_functiondef(p.oid) ilike '%new.status:=''author_review''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_demote_extended_story_on_edit' limit 1),
  'une édition structurelle rétrograde le récit en PROVISOIRE / author_review'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%where canon_status=''CANON_ETENDU''%'
          and pg_get_functiondef(p.oid) ilike '%audience=''private''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_invalidate_published_extended_stories' limit 1),
  'un changement global du canon rétrograde aussi les Chroniques validées'
);

select ok(
  not has_function_privilege('authenticated','private.sinjira_demote_story_from_child_change()','EXECUTE'),
  'le navigateur ne peut pas invoquer directement le garde de rétrogradation'
);


select has_function('private','sinjira_story_readiness_report',array['uuid'],
  'le rapport privé unique de readiness existe');

select ok(not has_function_privilege('authenticated','private.sinjira_story_readiness_report(uuid)','EXECUTE'),
  'le navigateur ne peut pas invoquer directement le rapport privé de readiness');

select has_function('private','sinjira_require_story_canon_transition',array[]::text[],
  'le garde SQL de transition vers Canon/publication existe');

select ok(not has_function_privilege('authenticated','private.sinjira_require_story_canon_transition()','EXECUTE'),
  'le navigateur ne peut pas invoquer directement le garde de transition');

select ok(exists(
  select 1 from pg_trigger tr
  join pg_class t on t.oid=tr.tgrelid
  join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_extended_stories'
    and tr.tgname='sinjira_extended_stories_canon_transition_guard'
    and not tr.tgisinternal
),'toute transition de récit passe par le garde SQL de readiness');

select ok(exists(
  select 1 from pg_constraint c
  join pg_class t on t.oid=c.conrelid
  join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public' and t.relname='sinjira_extended_stories'
    and c.conname='sinjira_extended_stories_canon_workflow_check'
    and pg_get_constraintdef(c.oid) ilike '%CANON_ETENDU%'
    and pg_get_constraintdef(c.oid) ilike '%validated%'
    and pg_get_constraintdef(c.oid) ilike '%published%'
),'CANON_ETENDU ne peut exister qu avec un état validated ou published');

select ok(
  (select pg_get_functiondef(p.oid) ilike '%sinjira_story_readiness_report%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_story_validation_check' limit 1),
  'la prévalidation admin utilise la source unique de readiness'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_CANON_INSERT_FORBIDDEN%'
          and pg_get_functiondef(p.oid) ilike '%STORY_SAVE_BEFORE_CANON_TRANSITION%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_require_story_canon_transition' limit 1),
  'une insertion canonique directe et une canonisation avec édition simultanée sont interdites'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_PROMOTION_REQUIRED%'
          and pg_get_functiondef(p.oid) ilike '%STORY_PUBLICATION_TIMESTAMP_REQUIRED%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_require_story_canon_transition' limit 1),
  'la publication exige une promotion préalable et un horodatage'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%STORY_PROVENANCE_REQUIRED%'
          and pg_get_functiondef(p.oid) ilike '%STORY_CONTINUITY_CONFLICT%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_require_story_canon_transition' limit 1),
  'le garde SQL réapplique provenance et continuité même hors interface'
);


select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_RETIRE_REPLACEMENT_REQUIRED%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'une source engagée ne peut passer RETIRED sans remplacement vérifié'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%newer.scope=old.scope%'
          and pg_get_functiondef(p.oid) ilike '%sinjira_source_is_verified(newer.id)%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'le remplacement autorisant RETIRED doit être vérifié et de même période'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%new.verification_status=''RETIRED''%'
          and pg_get_functiondef(p.oid) ilike '%v_has_verified_replacement%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'RETIRED devient une transition contrôlée plutôt qu une suppression de l historique'
);


select ok(exists(
  select 1
  from pg_trigger tr
  join pg_class t on t.oid=tr.tgrelid
  join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public'
    and t.relname='sinjira_canon_sources'
    and tr.tgname='sinjira_canon_sources_guard_authority'
    and not tr.tgisinternal
    and pg_get_triggerdef(tr.oid) ilike '%supersedes_source_id%'
),'le garde d autorité se déclenche aussi lors d un changement de source remplacée');

select ok(
  (select pg_get_functiondef(p.oid) ilike '%new.supersedes_source_id is distinct from old.supersedes_source_id%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'une source engagée ne peut pas faire réécrire sa chaîne de remplacement'
);


select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_RETIRE_REFERENCES_REMAIN%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'une source ne peut pas passer RETIRED tant que des références directes subsistent'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%v_direct_use%'
          and pg_get_functiondef(p.oid) ilike '%sinjira_story_claims%'
          and pg_get_functiondef(p.oid) ilike '%sinjira_canon_event_characters%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'les références directes couvrent faits, lieux, trajets, événements et présences'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%v_has_verified_replacement%'
          and pg_get_functiondef(p.oid) ilike '%not v_direct_use%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'RETIRED exige à la fois un remplacement vérifié et zéro référence directe'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%supersedes_source_id%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_in_use' limit 1),
  'la relation de remplacement reste conservée dans l historique après migration des références'
);


select has_function('public','admin_sinjira_migrate_canon_source_references',array['uuid','uuid'],
  'le RPC atomique de migration des références de source existe');

select ok(not has_function_privilege('anon','public.admin_sinjira_migrate_canon_source_references(uuid,uuid)','EXECUTE'),
  'anon ne peut pas migrer les références de source');

select ok(has_function_privilege('authenticated','public.admin_sinjira_migrate_canon_source_references(uuid,uuid)','EXECUTE'),
  'authenticated atteint le RPC qui impose ensuite admin AAL2');

select ok(exists(
  select 1
  from pg_indexes
  where schemaname='public'
    and tablename='sinjira_canon_sources'
    and indexname='sinjira_canon_sources_one_verified_successor_idx'
    and indexdef ilike '%unique%'
),'une source ne peut avoir qu un seul successeur canonique vérifié actif');

select ok(
  (select pg_get_functiondef(p.oid) ilike '%supersedes_source_id is distinct from v_old.id%'
          and pg_get_functiondef(p.oid) ilike '%v_new.scope is distinct from v_old.scope%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'la migration exige un remplacement explicitement relié et de même période'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%sinjira_source_is_verified(v_new.id)%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'la migration exige un remplacement encore vérifié'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%update public.sinjira_world_locations set source_id=v_new.id%'
          and pg_get_functiondef(p.oid) ilike '%update public.sinjira_world_travel_rules set source_id=v_new.id%'
          and pg_get_functiondef(p.oid) ilike '%update public.sinjira_canon_events set source_id=v_new.id%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'la migration couvre lieux, trajets et événements'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%update public.sinjira_canon_event_characters set source_id=v_new.id%'
          and pg_get_functiondef(p.oid) ilike '%update public.sinjira_story_claims set source_id=v_new.id%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'la migration couvre présences et faits de provenance'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%status=''validated''%'
          and pg_get_functiondef(p.oid) ilike '%canon_status=''PROVISOIRE''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'les Chroniques dépendantes sont sorties de publication et rétrogradées avant migration'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_MIGRATION_INCOMPLETE%'
          and pg_get_functiondef(p.oid) ilike '%remaining_references%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'la transaction échoue si une référence directe subsiste après migration'
);


select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_SUPERSEDES_SCOPE_MISMATCH%'
          and pg_get_functiondef(p.oid) ilike '%v_previous_scope%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_prevent_source_supersedes_cycle' limit 1),
  'une relation de remplacement est refusée si les périodes canoniques diffèrent'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_SUPERSEDES_NOT_FOUND%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_prevent_source_supersedes_cycle' limit 1),
  'une relation de remplacement ne peut pas viser une source inexistante'
);

select ok(exists(
  select 1 from pg_trigger tr
  join pg_class t on t.oid=tr.tgrelid
  join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public'
    and t.relname='sinjira_canon_sources'
    and tr.tgname='sinjira_canon_sources_prevent_supersedes_cycle'
    and not tr.tgisinternal
    and pg_get_triggerdef(tr.oid) ilike '%supersedes_source_id%'
    and pg_get_triggerdef(tr.oid) ilike '%scope%'
),'le garde de remplacement se relance aussi lors d un changement de période');


select ok(
  (select pg_get_functiondef(p.oid) ilike '%set verification_status=''RETIRED''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'la migration atomique passe l ancienne source à RETIRED dans la même transaction'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%''source_status'',''RETIRED''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'le résultat de migration confirme explicitement le retrait de l ancienne source'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%aucune nouvelle référence%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'le contrat SQL documente la fermeture de la fenêtre entre migration et retrait'
);


select ok(exists(
  select 1
  from pg_indexes
  where schemaname='public'
    and tablename='sinjira_canon_sources'
    and indexname='sinjira_canon_sources_one_successor_idx'
    and indexdef ilike '%unique%'
),'la chaîne de remplacement interdit toute fourche, même provisoire');

select ok(not exists(
  select 1
  from pg_indexes
  where schemaname='public'
    and tablename='sinjira_canon_sources'
    and indexname='sinjira_canon_sources_one_verified_successor_idx'
),'l ancien index limité aux successeurs vérifiés est remplacé par la contrainte de chaîne stricte');

select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_SUPERSEDES_ALREADY_EXISTS%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_prevent_source_supersedes_cycle' limit 1),
  'le garde SQL renvoie une erreur explicite lorsqu une source possède déjà un successeur'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%other.supersedes_source_id=new.supersedes_source_id%'
          and pg_get_functiondef(p.oid) ilike '%other.id<>new.id%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_prevent_source_supersedes_cycle' limit 1),
  'l édition de la relation existante reste possible sans autoriser un second successeur'
);


select has_function('private','sinjira_guard_canon_source_lifecycle',array[]::text[],
  'le garde de cycle de vie des sources existe');

select ok(exists(
  select 1 from pg_trigger tr
  join pg_class t on t.oid=tr.tgrelid
  join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public'
    and t.relname='sinjira_canon_sources'
    and tr.tgname='sinjira_canon_sources_guard_lifecycle'
    and not tr.tgisinternal
),'toute création ou modification pertinente passe par le garde de cycle de vie');

select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_CREATE_RETIRED_FORBIDDEN%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_lifecycle' limit 1),
  'une source ne peut pas être créée directement en RETIRED'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_SUPERSEDES_KIND_INVALID%'
          and pg_get_functiondef(p.oid) ilike '%source_kind not in (''roman'',''bible'',''author_decision'',''archive'')%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_lifecycle' limit 1),
  'une source research ne peut pas devenir un maillon de remplacement canonique'
);

select ok(not has_function_privilege('authenticated','private.sinjira_guard_canon_source_lifecycle()','EXECUTE'),
  'le navigateur ne peut pas invoquer directement le garde de cycle de vie');


select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_SUPERSEDES_BOOK_MISMATCH%'
          and pg_get_functiondef(p.oid) ilike '%new.book_number is distinct from v_previous_book%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_prevent_source_supersedes_cycle' limit 1),
  'deux sources roman ne peuvent se remplacer que dans le même numéro de livre'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%v_previous_kind=''roman''%'
          and pg_get_functiondef(p.oid) ilike '%new.source_kind=''roman''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_prevent_source_supersedes_cycle' limit 1),
  'le verrou de numéro de livre ne s applique que lorsque les deux sources sont des romans'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%select s.scope,s.source_kind,s.book_number%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_prevent_source_supersedes_cycle' limit 1),
  'le garde de remplacement lit périmètre, type et numéro de livre de la source précédente'
);


select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_RETIRED_FINAL%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_lifecycle' limit 1),
  'RETIRED est un état terminal irréversible'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%old.verification_status=''RETIRED''%'
          and pg_get_functiondef(p.oid) ilike '%new.verification_status is distinct from ''RETIRED''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_lifecycle' limit 1),
  'une source RETIRED ne peut pas redevenir active'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%tg_op=''UPDATE''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='private' and p.proname='sinjira_guard_canon_source_lifecycle' limit 1),
  'le verrou terminal RETIRED s applique explicitement aux mises à jour'
);


select ok(exists(
  select 1 from pg_trigger tr
  join pg_class t on t.oid=tr.tgrelid
  join pg_namespace n on n.oid=t.relnamespace
  where n.nspname='public'
    and t.relname='sinjira_canon_sources'
    and tr.tgname='sinjira_canon_sources_prevent_supersedes_cycle'
    and not tr.tgisinternal
    and pg_get_triggerdef(tr.oid) ilike '%source_kind%'
    and pg_get_triggerdef(tr.oid) ilike '%book_number%'
),'la relation remplace est revalidée après changement de type ou numéro de livre');

select ok(
  (select pg_get_triggerdef(tr.oid) ilike '%supersedes_source_id%'
          and pg_get_triggerdef(tr.oid) ilike '%scope%'
          and pg_get_triggerdef(tr.oid) ilike '%source_kind%'
          and pg_get_triggerdef(tr.oid) ilike '%book_number%'
   from pg_trigger tr
   join pg_class t on t.oid=tr.tgrelid
   join pg_namespace n on n.oid=t.relnamespace
   where n.nspname='public' and t.relname='sinjira_canon_sources'
     and tr.tgname='sinjira_canon_sources_prevent_supersedes_cycle'
     and not tr.tgisinternal limit 1),
  'toutes les colonnes qui déterminent la compatibilité du remplacement relancent le garde'
);


select ok(
  (select pg_get_functiondef(p.oid) ilike '%CANON_SOURCE_MIGRATION_BOOK_MISMATCH%'
          and pg_get_functiondef(p.oid) ilike '%v_new.book_number is distinct from v_old.book_number%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'la migration atomique revérifie aussi le numéro du livre'
);

select ok(
  (select pg_get_functiondef(p.oid) ilike '%v_old.source_kind=''roman''%'
          and pg_get_functiondef(p.oid) ilike '%v_new.source_kind=''roman''%'
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname='admin_sinjira_migrate_canon_source_references' limit 1),
  'le contrôle de livre pendant migration ne s applique que lorsque les deux sources sont des romans'
);

select * from finish();
rollback;
