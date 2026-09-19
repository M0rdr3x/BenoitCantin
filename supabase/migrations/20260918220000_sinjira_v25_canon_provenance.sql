-- SINJIRA V25 — provenance canonique structurée
-- Registre de sources + faits de continuité sourcés pour le Canon étendu.

create table if not exists public.sinjira_canon_sources(
  id uuid primary key default gen_random_uuid(),
  source_key text not null unique check(char_length(source_key) between 3 and 160),
  source_kind text not null check(source_kind in (
    'roman','bible','author_decision','archive','research'
  )),
  scope text not null check(scope in (
    'LIVRES_1_12','ORIGINES_13_14','CANON_ETENDU','META'
  )),
  title text not null check(char_length(btrim(title)) between 1 and 300),
  book_number smallint check(book_number is null or book_number between 1 and 14),
  chapter_reference text,
  passage_reference text,
  source_version text,
  verification_status text not null default 'PROVISOIRE' check(verification_status in (
    'PROVISOIRE','VERIFIED','SECRET_AUTEUR','A_ARBITRER','RETIRED'
  )),
  public_safe boolean not null default false,
  supersedes_source_id uuid references public.sinjira_canon_sources(id) on delete set null,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check(supersedes_source_id is null or supersedes_source_id<>id),
  check(source_kind<>'roman' or book_number is not null),
  check(
    verification_status not in ('VERIFIED','SECRET_AUTEUR')
    or chapter_reference is not null
    or passage_reference is not null
    or source_version is not null
  ),
  check(
    verification_status not in ('VERIFIED','SECRET_AUTEUR')
    or source_kind<>'roman'
    or chapter_reference is not null
  )
);

create table if not exists public.sinjira_story_claims(
  id uuid primary key default gen_random_uuid(),
  story_id uuid not null references public.sinjira_extended_stories(id) on delete cascade,
  claim_key text not null check(char_length(claim_key) between 1 and 160),
  claim_type text not null check(claim_type in (
    'anchor','character','time','location','event','technology','organization',
    'relationship','death','travel','other'
  )),
  statement text not null check(char_length(btrim(statement)) between 1 and 12000),
  source_id uuid references public.sinjira_canon_sources(id) on delete restrict,
  verification_status text not null default 'PROVISOIRE' check(verification_status in (
    'PROVISOIRE','VERIFIED','A_ARBITRER','REJECTED'
  )),
  author_note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(story_id,claim_key),
  check(verification_status<>'VERIFIED' or source_id is not null)
);

alter table public.sinjira_world_locations
  add column if not exists source_id uuid references public.sinjira_canon_sources(id) on delete restrict;
alter table public.sinjira_world_travel_rules
  add column if not exists source_id uuid references public.sinjira_canon_sources(id) on delete restrict;
alter table public.sinjira_canon_events
  add column if not exists source_id uuid references public.sinjira_canon_sources(id) on delete restrict;
alter table public.sinjira_canon_event_characters
  add column if not exists source_id uuid references public.sinjira_canon_sources(id) on delete restrict;

create index if not exists sinjira_canon_sources_scope_idx
  on public.sinjira_canon_sources(scope,verification_status,book_number);
create index if not exists sinjira_story_claims_story_idx
  on public.sinjira_story_claims(story_id,verification_status,claim_type);
create index if not exists sinjira_story_claims_source_idx
  on public.sinjira_story_claims(source_id);

drop trigger if exists sinjira_canon_sources_updated_at on public.sinjira_canon_sources;
create trigger sinjira_canon_sources_updated_at
before update on public.sinjira_canon_sources
for each row execute function public.set_updated_at();

drop trigger if exists sinjira_story_claims_updated_at on public.sinjira_story_claims;
create trigger sinjira_story_claims_updated_at
before update on public.sinjira_story_claims
for each row execute function public.set_updated_at();

alter table public.sinjira_canon_sources enable row level security;
alter table public.sinjira_story_claims enable row level security;
revoke all on public.sinjira_canon_sources from anon,authenticated;
revoke all on public.sinjira_story_claims from anon,authenticated;

create or replace function private.sinjira_source_is_verified(p_source_id uuid)
returns boolean
language sql
stable
set search_path=pg_catalog,public,private
as $$
  select exists(
    select 1
    from public.sinjira_canon_sources s
    where s.id=p_source_id
      and s.verification_status in ('VERIFIED','SECRET_AUTEUR')
      and s.source_kind in ('roman','bible','author_decision','archive')
  );
$$;

create or replace function private.sinjira_require_verified_provenance()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
declare
  v_source_id uuid;
  v_required boolean:=false;
  v_event_classification text;
  v_source_scope text;
begin
  if tg_table_name='sinjira_world_locations' then
    v_source_id:=new.source_id;
    v_required:=new.canon_status='CANON';
  elsif tg_table_name='sinjira_world_travel_rules' then
    v_source_id:=new.source_id;
    v_required:=new.canon_status='CANON';
  elsif tg_table_name='sinjira_canon_events' then
    v_source_id:=new.source_id;
    v_required:=new.classification in ('CANON','SECRET_AUTEUR');
  elsif tg_table_name='sinjira_canon_event_characters' then
    v_source_id:=new.source_id;
    select e.classification into v_event_classification
    from public.sinjira_canon_events e
    where e.id=new.event_id;
    v_required:=v_event_classification in ('CANON','SECRET_AUTEUR');
  else
    raise exception 'PROVENANCE_TRIGGER_TABLE_UNSUPPORTED';
  end if;

  if v_required and v_source_id is null then
    raise exception 'CANON_SOURCE_REQUIRED';
  end if;

  if v_required and not private.sinjira_source_is_verified(v_source_id) then
    raise exception 'CANON_SOURCE_NOT_VERIFIED';
  end if;

  if v_source_id is not null then
    select s.scope into v_source_scope from public.sinjira_canon_sources s where s.id=v_source_id;
    if tg_table_name='sinjira_canon_events'
       and v_source_scope is distinct from 'META'
       and v_source_scope is distinct from new.source_scope then
      raise exception 'CANON_SOURCE_SCOPE_MISMATCH';
    end if;
  end if;

  return new;
end;
$$;

create or replace function private.sinjira_require_verified_story_claim()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $
declare
  v_story_scope text;
  v_source_scope text;
begin
  if new.source_id is not null and new.claim_type='anchor' then
    select s.anchor_scope into v_story_scope from public.sinjira_extended_stories s where s.id=new.story_id;
    select s.scope into v_source_scope from public.sinjira_canon_sources s where s.id=new.source_id;
    if v_story_scope<>'MULTI_PERIODE'
       and v_source_scope<>'META'
       and v_story_scope is distinct from v_source_scope then
      raise exception 'CLAIM_SOURCE_SCOPE_MISMATCH';
    end if;
  end if;

  if new.verification_status='VERIFIED' then
    if new.source_id is null then raise exception 'CLAIM_SOURCE_REQUIRED'; end if;
    if not private.sinjira_source_is_verified(new.source_id) then
      raise exception 'CLAIM_SOURCE_NOT_VERIFIED';
    end if;
  end if;
  return new;
end;
$;

create or replace function private.sinjira_guard_published_story_claim()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
declare
  v_story_id uuid;
begin
  v_story_id:=case when tg_op='DELETE' then old.story_id else new.story_id end;

  if exists(
    select 1 from public.sinjira_extended_stories s
    where s.id=v_story_id and s.status='published'
  ) then
    raise exception 'STORY_UNPUBLISH_FIRST';
  end if;

  if tg_op='DELETE' then return old; end if;
  return new;
end;
$$;

drop trigger if exists sinjira_world_locations_require_provenance on public.sinjira_world_locations;
create trigger sinjira_world_locations_require_provenance
before insert or update of canon_status,source_id on public.sinjira_world_locations
for each row execute function private.sinjira_require_verified_provenance();

drop trigger if exists sinjira_world_travel_require_provenance on public.sinjira_world_travel_rules;
create trigger sinjira_world_travel_require_provenance
before insert or update of canon_status,source_id on public.sinjira_world_travel_rules
for each row execute function private.sinjira_require_verified_provenance();

drop trigger if exists sinjira_canon_events_require_provenance on public.sinjira_canon_events;
create trigger sinjira_canon_events_require_provenance
before insert or update of classification,source_id on public.sinjira_canon_events
for each row execute function private.sinjira_require_verified_provenance();

drop trigger if exists sinjira_canon_event_characters_require_provenance on public.sinjira_canon_event_characters;
create trigger sinjira_canon_event_characters_require_provenance
before insert or update of event_id,source_id on public.sinjira_canon_event_characters
for each row execute function private.sinjira_require_verified_provenance();

drop trigger if exists sinjira_story_claims_require_verified_source on public.sinjira_story_claims;
create trigger sinjira_story_claims_require_verified_source
before insert or update of source_id,verification_status on public.sinjira_story_claims
for each row execute function private.sinjira_require_verified_story_claim();

drop trigger if exists sinjira_story_claims_guard_published on public.sinjira_story_claims;
create trigger sinjira_story_claims_guard_published
before insert or update or delete on public.sinjira_story_claims
for each row execute function private.sinjira_guard_published_story_claim();

-- Toute modification d'une source qui peut changer son sens ou son autorité
-- oblige à revalider les Chroniques publiées.
drop trigger if exists sinjira_canon_sources_invalidate_extended on public.sinjira_canon_sources;
create trigger sinjira_canon_sources_invalidate_extended
after update of source_kind,scope,book_number,chapter_reference,passage_reference,source_version,verification_status,supersedes_source_id
or delete on public.sinjira_canon_sources
for each statement execute function private.sinjira_invalidate_published_extended_stories();

drop trigger if exists sinjira_world_locations_source_invalidate_extended on public.sinjira_world_locations;
create trigger sinjira_world_locations_source_invalidate_extended
after update of source_id on public.sinjira_world_locations
for each statement execute function private.sinjira_invalidate_published_extended_stories();

drop trigger if exists sinjira_canon_events_source_invalidate_extended on public.sinjira_canon_events;
create trigger sinjira_canon_events_source_invalidate_extended
after update of source_id on public.sinjira_canon_events
for each statement execute function private.sinjira_invalidate_published_extended_stories();

revoke all on function private.sinjira_source_is_verified(uuid) from public,anon,authenticated;
revoke all on function private.sinjira_require_verified_provenance() from public,anon,authenticated,service_role;
revoke all on function private.sinjira_require_verified_story_claim() from public,anon,authenticated,service_role;
revoke all on function private.sinjira_guard_published_story_claim() from public,anon,authenticated,service_role;

-- Renforce la publication : au moins un fait d'ancrage vérifié, aucun fait
-- non résolu, et toutes les sources utilisées doivent toujours être vérifiées.
create or replace function public.admin_sinjira_publish_extended_story(
  p_story_id uuid,
  p_audience text
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private,auth
as $$
declare
  v_admin uuid;
  v_report jsonb;
  v_story public.sinjira_extended_stories%rowtype;
begin
  v_admin:=private.require_sinjira_admin_aal2();

  if p_audience not in ('members','public') then
    raise exception 'STORY_PUBLIC_AUDIENCE_REQUIRED';
  end if;

  select * into v_story
  from public.sinjira_extended_stories
  where id=p_story_id
  for update;

  if v_story.id is null then raise exception 'STORY_NOT_FOUND'; end if;
  if v_story.canon_status<>'CANON_ETENDU' then raise exception 'STORY_NOT_CANON_EXTENDED'; end if;
  if v_story.status='archived' then raise exception 'STORY_ARCHIVED'; end if;
  if v_story.anchor_scope='UNASSIGNED' then raise exception 'STORY_ANCHOR_REQUIRED'; end if;
  if v_story.starts_at is null or v_story.ends_at is null or v_story.location_id is null then
    raise exception 'STORY_METADATA_INCOMPLETE';
  end if;
  if not exists(
    select 1 from public.sinjira_world_locations l
    where l.id=v_story.location_id and l.canon_status='CANON'
  ) then
    raise exception 'STORY_LOCATION_NOT_CANON';
  end if;
  if btrim(coalesce(v_story.content,''))='' then raise exception 'STORY_CONTENT_REQUIRED'; end if;

  if not exists(
    select 1 from public.sinjira_story_claims c
    where c.story_id=p_story_id
      and c.claim_type='anchor'
      and c.verification_status='VERIFIED'
      and private.sinjira_source_is_verified(c.source_id)
  ) then
    raise exception 'STORY_PROVENANCE_REQUIRED';
  end if;

  if not exists(
    select 1
    from public.sinjira_story_claims c
    join public.sinjira_canon_sources src on src.id=c.source_id
    where c.story_id=p_story_id
      and c.claim_type='anchor'
      and c.verification_status='VERIFIED'
      and private.sinjira_source_is_verified(c.source_id)
      and (
        v_story.anchor_scope='MULTI_PERIODE'
        or src.scope='META'
        or src.scope=v_story.anchor_scope
      )
  ) then
    raise exception 'STORY_PROVENANCE_SCOPE_MISMATCH';
  end if;

  if exists(
    select 1 from public.sinjira_story_claims c
    where c.story_id=p_story_id
      and (
        c.verification_status<>'VERIFIED'
        or c.source_id is null
        or not private.sinjira_source_is_verified(c.source_id)
      )
  ) then
    raise exception 'STORY_PROVENANCE_INCOMPLETE';
  end if;

  v_report:=private.sinjira_story_continuity_report(p_story_id);
  if coalesce((v_report->>'blocking_conflicts')::integer,0)>0 then
    raise exception 'STORY_CONTINUITY_CONFLICT';
  end if;
  if coalesce((v_report->>'warnings')::integer,0)>0 then
    raise exception 'STORY_CONTINUITY_INCOMPLETE';
  end if;

  update public.sinjira_extended_stories
  set status='published',
      audience=p_audience,
      published_at=now()
  where id=p_story_id
  returning * into v_story;

  return jsonb_build_object(
    'ok',true,
    'story_id',v_story.id,
    'canon_status',v_story.canon_status,
    'status',v_story.status,
    'audience',v_story.audience,
    'published_at',v_story.published_at,
    'continuity',v_report
  );
end;
$$;

comment on table public.sinjira_canon_sources is
  'Registre privé des sources canoniques SINJIRA. Les SECRET_AUTEUR peuvent servir de garde-fous sans être divulgués.';
comment on table public.sinjira_story_claims is
  'Faits de continuité d’une Chronique. Chaque fait vérifié pointe vers une source canonique vérifiée.';
comment on function private.sinjira_source_is_verified(uuid) is
  'Retourne vrai uniquement pour une source VERIFIED ou SECRET_AUTEUR.';
