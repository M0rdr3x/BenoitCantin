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
  ),
  check(
    source_kind<>'roman'
    or (book_number between 1 and 12 and scope='LIVRES_1_12')
    or (book_number between 13 and 14 and scope='ORIGINES_13_14')
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

create or replace function private.sinjira_guard_canon_source_lifecycle()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
begin
  if tg_op='INSERT' and new.verification_status='RETIRED' then
    raise exception 'CANON_SOURCE_CREATE_RETIRED_FORBIDDEN';
  end if;

  if tg_op='UPDATE'
     and old.verification_status='RETIRED'
     and new.verification_status is distinct from 'RETIRED' then
    raise exception 'CANON_SOURCE_RETIRED_FINAL';
  end if;

  if new.supersedes_source_id is not null
     and new.source_kind not in ('roman','bible','author_decision','archive') then
    raise exception 'CANON_SOURCE_SUPERSEDES_KIND_INVALID';
  end if;

  return new;
end;
$$;

drop trigger if exists sinjira_canon_sources_guard_lifecycle on public.sinjira_canon_sources;
create trigger sinjira_canon_sources_guard_lifecycle
before insert or update of source_kind,verification_status,supersedes_source_id
on public.sinjira_canon_sources
for each row execute function private.sinjira_guard_canon_source_lifecycle();

revoke all on function private.sinjira_guard_canon_source_lifecycle() from public,anon,authenticated,service_role;

create or replace function private.sinjira_prevent_source_supersedes_cycle()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
declare
  v_cycle boolean:=false;
  v_previous_scope text;
  v_previous_kind text;
  v_previous_book smallint;
begin
  if new.supersedes_source_id is null then return new; end if;
  if new.supersedes_source_id=new.id then raise exception 'CANON_SOURCE_SUPERSEDES_SELF'; end if;

  select s.scope,s.source_kind,s.book_number
  into v_previous_scope,v_previous_kind,v_previous_book
  from public.sinjira_canon_sources s
  where s.id=new.supersedes_source_id;

  if v_previous_scope is null then raise exception 'CANON_SOURCE_SUPERSEDES_NOT_FOUND'; end if;
  if new.scope is distinct from v_previous_scope then
    raise exception 'CANON_SOURCE_SUPERSEDES_SCOPE_MISMATCH';
  end if;
  if new.source_kind='roman'
     and v_previous_kind='roman'
     and new.book_number is distinct from v_previous_book then
    raise exception 'CANON_SOURCE_SUPERSEDES_BOOK_MISMATCH';
  end if;
  if exists(
    select 1
    from public.sinjira_canon_sources other
    where other.supersedes_source_id=new.supersedes_source_id
      and other.id<>new.id
  ) then
    raise exception 'CANON_SOURCE_SUPERSEDES_ALREADY_EXISTS';
  end if;

  with recursive chain(id,supersedes_source_id,path) as (
    select s.id,s.supersedes_source_id,array[s.id]
    from public.sinjira_canon_sources s
    where s.id=new.supersedes_source_id
    union all
    select p.id,p.supersedes_source_id,c.path||p.id
    from public.sinjira_canon_sources p
    join chain c on p.id=c.supersedes_source_id
    where not p.id=any(c.path)
  )
  select exists(select 1 from chain where id=new.id) into v_cycle;

  if v_cycle then raise exception 'CANON_SOURCE_SUPERSEDES_CYCLE'; end if;
  return new;
end;
$$;

create or replace function private.sinjira_guard_canon_source_in_use()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
declare
  v_in_use boolean:=false;
  v_any_use boolean:=false;
  v_direct_use boolean:=false;
  v_new_qualifies boolean:=false;
  v_has_verified_replacement boolean:=false;
begin
  select
    exists(select 1 from public.sinjira_world_locations l where l.source_id=old.id)
    or exists(select 1 from public.sinjira_world_travel_rules r where r.source_id=old.id)
    or exists(select 1 from public.sinjira_canon_events e where e.source_id=old.id)
    or exists(select 1 from public.sinjira_canon_event_characters p where p.source_id=old.id)
    or exists(select 1 from public.sinjira_story_claims c where c.source_id=old.id)
  into v_direct_use;

  v_any_use:=
    v_direct_use
    or exists(select 1 from public.sinjira_canon_sources newer where newer.supersedes_source_id=old.id);

  select
    exists(select 1 from public.sinjira_world_locations l where l.source_id=old.id and l.canon_status='CANON')
    or exists(select 1 from public.sinjira_world_travel_rules r where r.source_id=old.id and r.canon_status='CANON')
    or exists(select 1 from public.sinjira_canon_events e where e.source_id=old.id and e.classification in ('CANON','SECRET_AUTEUR'))
    or exists(
      select 1
      from public.sinjira_canon_event_characters p
      join public.sinjira_canon_events e on e.id=p.event_id
      where p.source_id=old.id and e.classification in ('CANON','SECRET_AUTEUR')
    )
    or exists(select 1 from public.sinjira_story_claims c where c.source_id=old.id and c.verification_status='VERIFIED')
    or exists(select 1 from public.sinjira_canon_sources newer where newer.supersedes_source_id=old.id)
  into v_in_use;

  v_new_qualifies:=
    new.verification_status in ('VERIFIED','SECRET_AUTEUR')
    and new.source_kind in ('roman','bible','author_decision','archive');

  select exists(
    select 1
    from public.sinjira_canon_sources newer
    where newer.supersedes_source_id=old.id
      and newer.scope=old.scope
      and private.sinjira_source_is_verified(newer.id)
  ) into v_has_verified_replacement;

  if v_any_use and new.source_key is distinct from old.source_key then
    raise exception 'CANON_SOURCE_KEY_IMMUTABLE';
  end if;

  if new.verification_status='RETIRED' and old.verification_status<>'RETIRED' then
    if not v_has_verified_replacement then
      raise exception 'CANON_SOURCE_RETIRE_REPLACEMENT_REQUIRED';
    end if;
    if v_direct_use then
      raise exception 'CANON_SOURCE_RETIRE_REFERENCES_REMAIN';
    end if;
  end if;

  if v_in_use and (
    new.source_kind is distinct from old.source_kind
    or new.scope is distinct from old.scope
    or new.book_number is distinct from old.book_number
    or new.chapter_reference is distinct from old.chapter_reference
    or new.passage_reference is distinct from old.passage_reference
    or new.source_version is distinct from old.source_version
    or new.supersedes_source_id is distinct from old.supersedes_source_id
    or (
      not v_new_qualifies
      and not (
        new.verification_status='RETIRED'
        and v_has_verified_replacement
        and not v_direct_use
      )
    )
  ) then
    if new.verification_status='RETIRED' and not v_has_verified_replacement then
      raise exception 'CANON_SOURCE_RETIRE_REPLACEMENT_REQUIRED';
    end if;
    if new.verification_status='RETIRED' and v_direct_use then
      raise exception 'CANON_SOURCE_RETIRE_REFERENCES_REMAIN';
    end if;
    raise exception 'CANON_SOURCE_IN_USE';
  end if;

  return new;
end;
$$;

drop trigger if exists sinjira_canon_sources_prevent_supersedes_cycle on public.sinjira_canon_sources;
create trigger sinjira_canon_sources_prevent_supersedes_cycle
before insert or update of supersedes_source_id,scope,source_kind,book_number on public.sinjira_canon_sources
for each row execute function private.sinjira_prevent_source_supersedes_cycle();

drop trigger if exists sinjira_canon_sources_guard_authority on public.sinjira_canon_sources;
create trigger sinjira_canon_sources_guard_authority
before update of source_key,source_kind,scope,book_number,chapter_reference,passage_reference,source_version,verification_status,supersedes_source_id on public.sinjira_canon_sources
for each row execute function private.sinjira_guard_canon_source_in_use();

revoke all on function private.sinjira_prevent_source_supersedes_cycle() from public,anon,authenticated,service_role;
revoke all on function private.sinjira_guard_canon_source_in_use() from public,anon,authenticated,service_role;

create or replace function private.sinjira_prevent_canon_source_delete()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
begin
  raise exception 'CANON_SOURCE_DELETE_FORBIDDEN';
end;
$$;

drop trigger if exists sinjira_canon_sources_prevent_delete on public.sinjira_canon_sources;
create trigger sinjira_canon_sources_prevent_delete
before delete on public.sinjira_canon_sources
for each row execute function private.sinjira_prevent_canon_source_delete();

revoke all on function private.sinjira_prevent_canon_source_delete() from public,anon,authenticated,service_role;

-- CANON_ETENDU signifie toujours « actuellement validé ».
-- Toute modification du récit, de ses faits, de ses segments ou d'une dépendance
-- canonique force une nouvelle prévalidation avant de retrouver ce statut.
create or replace function private.sinjira_demote_extended_story_on_edit()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
begin
  if old.canon_status='CANON_ETENDU'
     and (
       new.story_type is distinct from old.story_type
       or new.character_id is distinct from old.character_id
       or new.title is distinct from old.title
       or new.slug is distinct from old.slug
       or new.summary is distinct from old.summary
       or new.content is distinct from old.content
       or new.region_name is distinct from old.region_name
       or new.location_id is distinct from old.location_id
       or new.anchor_scope is distinct from old.anchor_scope
       or new.starts_at is distinct from old.starts_at
       or new.ends_at is distinct from old.ends_at
       or new.continuity_data is distinct from old.continuity_data
     ) then
    -- Une Chronique publiée reste bloquée par le garde existant :
    -- elle doit d'abord être retirée de publication explicitement.
    if old.status<>'published' then
      new.canon_status:='PROVISOIRE';
      new.status:='author_review';
      new.audience:='private';
      new.published_at:=null;
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists sinjira_extended_stories_demote_on_edit on public.sinjira_extended_stories;
create trigger sinjira_extended_stories_demote_on_edit
before update on public.sinjira_extended_stories
for each row execute function private.sinjira_demote_extended_story_on_edit();

create or replace function private.sinjira_demote_story_from_child_change()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_old_story uuid;
  v_new_story uuid;
begin
  if tg_op<>'INSERT' then v_old_story:=old.story_id; end if;
  if tg_op<>'DELETE' then v_new_story:=new.story_id; end if;

  update public.sinjira_extended_stories
  set canon_status='PROVISOIRE',
      status='author_review',
      audience='private',
      published_at=null
  where canon_status='CANON_ETENDU'
    and status<>'published'
    and (id=v_old_story or id=v_new_story);

  if tg_op='DELETE' then return old; end if;
  return new;
end;
$$;

drop trigger if exists sinjira_story_presence_demote_canon on public.sinjira_story_character_presence;
create trigger sinjira_story_presence_demote_canon
after insert or update or delete on public.sinjira_story_character_presence
for each row execute function private.sinjira_demote_story_from_child_change();

drop trigger if exists sinjira_story_claims_demote_canon on public.sinjira_story_claims;
create trigger sinjira_story_claims_demote_canon
after insert or update or delete on public.sinjira_story_claims
for each row execute function private.sinjira_demote_story_from_child_change();

-- Les dépendances globales du Calendrier-Monde, de l'Atlas, des sources et du
-- Canon central utilisent déjà cette fonction via les triggers V25. On la
-- renforce ici pour retirer aussi le statut CANON_ETENDU, pas seulement publier.
create or replace function private.sinjira_invalidate_published_extended_stories()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
begin
  -- Première passe autorisée par le verrou des récits publiés.
  update public.sinjira_extended_stories
  set status='validated',
      published_at=null
  where status='published';

  -- Deuxième passe : tout Canon étendu doit être prévalidé de nouveau.
  update public.sinjira_extended_stories
  set canon_status='PROVISOIRE',
      status='author_review',
      audience='private',
      published_at=null
  where canon_status='CANON_ETENDU';

  return null;
end;
$$;

revoke all on function private.sinjira_demote_extended_story_on_edit() from public,anon,authenticated,service_role;
revoke all on function private.sinjira_demote_story_from_child_change() from public,anon,authenticated,service_role;
revoke all on function private.sinjira_invalidate_published_extended_stories() from public,anon,authenticated,service_role;

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

drop index if exists public.sinjira_canon_sources_one_verified_successor_idx;
create unique index if not exists sinjira_canon_sources_one_successor_idx
  on public.sinjira_canon_sources(supersedes_source_id)
  where supersedes_source_id is not null;

create or replace function public.admin_sinjira_migrate_canon_source_references(
  p_source_id uuid,
  p_replacement_source_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private,auth
as $$
declare
  v_admin uuid;
  v_old public.sinjira_canon_sources%rowtype;
  v_new public.sinjira_canon_sources%rowtype;
  v_story_count integer:=0;
  v_location_count integer:=0;
  v_travel_count integer:=0;
  v_event_count integer:=0;
  v_presence_count integer:=0;
  v_claim_count integer:=0;
  v_remaining integer:=0;
begin
  v_admin:=private.require_sinjira_admin_aal2();

  if p_source_id is null or p_replacement_source_id is null or p_source_id=p_replacement_source_id then
    raise exception 'CANON_SOURCE_MIGRATION_REQUIRED_FIELDS';
  end if;

  select * into v_old
  from public.sinjira_canon_sources
  where id=p_source_id
  for update;
  if v_old.id is null then raise exception 'CANON_SOURCE_MIGRATION_SOURCE_NOT_FOUND'; end if;

  select * into v_new
  from public.sinjira_canon_sources
  where id=p_replacement_source_id
  for update;
  if v_new.id is null then raise exception 'CANON_SOURCE_MIGRATION_REPLACEMENT_NOT_FOUND'; end if;

  if v_old.verification_status='RETIRED' then
    raise exception 'CANON_SOURCE_ALREADY_RETIRED';
  end if;
  if v_new.supersedes_source_id is distinct from v_old.id then
    raise exception 'CANON_SOURCE_MIGRATION_REPLACEMENT_INVALID';
  end if;
  if v_new.scope is distinct from v_old.scope then
    raise exception 'CANON_SOURCE_MIGRATION_SCOPE_MISMATCH';
  end if;
  if v_old.source_kind='roman'
     and v_new.source_kind='roman'
     and v_new.book_number is distinct from v_old.book_number then
    raise exception 'CANON_SOURCE_MIGRATION_BOOK_MISMATCH';
  end if;
  if not private.sinjira_source_is_verified(v_new.id) then
    raise exception 'CANON_SOURCE_MIGRATION_REPLACEMENT_NOT_VERIFIED';
  end if;

  -- Les faits d'une Chronique publiée doivent d'abord sortir de l'état publié.
  update public.sinjira_extended_stories st
  set status='validated',
      published_at=null
  where st.status='published'
    and exists(
      select 1 from public.sinjira_story_claims c
      where c.story_id=st.id and c.source_id=v_old.id
    );
  get diagnostics v_story_count = row_count;

  update public.sinjira_extended_stories st
  set canon_status='PROVISOIRE',
      status='author_review',
      audience='private',
      published_at=null
  where st.canon_status='CANON_ETENDU'
    and exists(
      select 1 from public.sinjira_story_claims c
      where c.story_id=st.id and c.source_id=v_old.id
    );

  if exists(select 1 from public.sinjira_world_locations where source_id=v_old.id) then
    update public.sinjira_world_locations set source_id=v_new.id where source_id=v_old.id;
    get diagnostics v_location_count = row_count;
  end if;

  if exists(select 1 from public.sinjira_world_travel_rules where source_id=v_old.id) then
    update public.sinjira_world_travel_rules set source_id=v_new.id where source_id=v_old.id;
    get diagnostics v_travel_count = row_count;
  end if;

  if exists(select 1 from public.sinjira_canon_events where source_id=v_old.id) then
    update public.sinjira_canon_events set source_id=v_new.id where source_id=v_old.id;
    get diagnostics v_event_count = row_count;
  end if;

  if exists(select 1 from public.sinjira_canon_event_characters where source_id=v_old.id) then
    update public.sinjira_canon_event_characters set source_id=v_new.id where source_id=v_old.id;
    get diagnostics v_presence_count = row_count;
  end if;

  if exists(select 1 from public.sinjira_story_claims where source_id=v_old.id) then
    update public.sinjira_story_claims set source_id=v_new.id where source_id=v_old.id;
    get diagnostics v_claim_count = row_count;
  end if;

  select
      (select count(*) from public.sinjira_world_locations where source_id=v_old.id)
    + (select count(*) from public.sinjira_world_travel_rules where source_id=v_old.id)
    + (select count(*) from public.sinjira_canon_events where source_id=v_old.id)
    + (select count(*) from public.sinjira_canon_event_characters where source_id=v_old.id)
    + (select count(*) from public.sinjira_story_claims where source_id=v_old.id)
  into v_remaining;

  if v_remaining<>0 then
    raise exception 'CANON_SOURCE_MIGRATION_INCOMPLETE';
  end if;

  -- Ferme immédiatement l'ancienne source dans la même transaction afin
  -- qu'aucune nouvelle référence ne puisse être créée entre migration et retrait.
  update public.sinjira_canon_sources
  set verification_status='RETIRED'
  where id=v_old.id;

  return jsonb_build_object(
    'ok',true,
    'source_id',v_old.id,
    'replacement_source_id',v_new.id,
    'source_status','RETIRED',
    'published_stories_unpublished',v_story_count,
    'migrated',jsonb_build_object(
      'world_locations',v_location_count,
      'travel_rules',v_travel_count,
      'events',v_event_count,
      'presences',v_presence_count,
      'claims',v_claim_count
    ),
    'remaining_references',v_remaining
  );
end;
$$;

revoke all on function public.admin_sinjira_migrate_canon_source_references(uuid,uuid) from public,anon;
grant execute on function public.admin_sinjira_migrate_canon_source_references(uuid,uuid) to authenticated,service_role;

create or replace function private.sinjira_require_verified_provenance()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
declare
  v_source_id uuid;
  v_required boolean:=false;
  v_event_classification text;
  v_event_scope text;
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
    select e.classification,e.source_scope into v_event_classification,v_event_scope
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
    if tg_table_name='sinjira_canon_event_characters'
       and v_source_scope is distinct from 'META'
       and v_source_scope is distinct from v_event_scope then
      raise exception 'CANON_PRESENCE_SOURCE_SCOPE_MISMATCH';
    end if;
  end if;

  return new;
end;
$$;

create or replace function private.sinjira_require_verified_story_claim()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
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
$$;

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

create or replace function private.sinjira_guard_event_source_scope()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
begin
  if tg_op='UPDATE' and new.source_scope is distinct from old.source_scope and exists(
    select 1
    from public.sinjira_canon_event_characters p
    join public.sinjira_canon_sources src on src.id=p.source_id
    where p.event_id=old.id
      and src.scope<>'META'
      and src.scope<>new.source_scope
  ) then
    raise exception 'CANON_PRESENCE_SOURCE_SCOPE_MISMATCH';
  end if;
  return new;
end;
$$;

revoke all on function private.sinjira_guard_event_source_scope() from public,anon,authenticated,service_role;

drop trigger if exists sinjira_canon_events_guard_source_scope on public.sinjira_canon_events;
create trigger sinjira_canon_events_guard_source_scope
before update of source_scope on public.sinjira_canon_events
for each row execute function private.sinjira_guard_event_source_scope();

drop trigger if exists sinjira_canon_events_require_provenance on public.sinjira_canon_events;
create trigger sinjira_canon_events_require_provenance
before insert or update of classification,source_id,source_scope on public.sinjira_canon_events
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

drop trigger if exists sinjira_canon_events_scope_invalidate_extended on public.sinjira_canon_events;
create trigger sinjira_canon_events_scope_invalidate_extended
after update of source_scope on public.sinjira_canon_events
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
create or replace function private.sinjira_story_provenance_report(p_story_id uuid)
returns jsonb
language plpgsql
stable
set search_path=pg_catalog,public,private
as $$
declare
  v_scope text;
  v_total integer:=0;
  v_verified integer:=0;
  v_unresolved integer:=0;
  v_anchor_verified integer:=0;
  v_anchor_matching integer:=0;
begin
  select anchor_scope into v_scope
  from public.sinjira_extended_stories
  where id=p_story_id;

  if v_scope is null then
    return jsonb_build_object(
      'ok',false,
      'story_id',p_story_id,
      'code','STORY_NOT_FOUND'
    );
  end if;

  select
    count(*)::integer,
    count(*) filter(
      where c.verification_status='VERIFIED'
        and c.source_id is not null
        and private.sinjira_source_is_verified(c.source_id)
    )::integer,
    count(*) filter(
      where c.verification_status<>'VERIFIED'
         or c.source_id is null
         or not private.sinjira_source_is_verified(c.source_id)
    )::integer,
    count(*) filter(
      where c.claim_type='anchor'
        and c.verification_status='VERIFIED'
        and c.source_id is not null
        and private.sinjira_source_is_verified(c.source_id)
    )::integer,
    count(*) filter(
      where c.claim_type='anchor'
        and c.verification_status='VERIFIED'
        and c.source_id is not null
        and private.sinjira_source_is_verified(c.source_id)
        and (
          v_scope='MULTI_PERIODE'
          or src.scope='META'
          or src.scope=v_scope
        )
    )::integer
  into v_total,v_verified,v_unresolved,v_anchor_verified,v_anchor_matching
  from public.sinjira_story_claims c
  left join public.sinjira_canon_sources src on src.id=c.source_id
  where c.story_id=p_story_id;

  return jsonb_build_object(
    'ok',true,
    'story_id',p_story_id,
    'anchor_scope',v_scope,
    'total_claims',v_total,
    'verified_claims',v_verified,
    'unresolved_claims',v_unresolved,
    'verified_anchor_claims',v_anchor_verified,
    'matching_anchor_claims',v_anchor_matching,
    'ready',v_anchor_verified>0 and v_anchor_matching>0 and v_unresolved=0
  );
end;
$$;

revoke all on function private.sinjira_story_provenance_report(uuid) from public,anon,authenticated;

create or replace function private.sinjira_story_readiness_report(p_story_id uuid)
returns jsonb
language plpgsql
stable
set search_path=pg_catalog,public,private
as $$
declare
  v_story public.sinjira_extended_stories%rowtype;
  v_location_canon boolean:=false;
  v_metadata_ready boolean:=false;
  v_provenance jsonb;
  v_continuity jsonb;
  v_ready boolean:=false;
begin
  select * into v_story
  from public.sinjira_extended_stories
  where id=p_story_id;

  if v_story.id is null then
    return jsonb_build_object('ok',false,'story_id',p_story_id,'code','STORY_NOT_FOUND');
  end if;

  if v_story.location_id is not null then
    select exists(
      select 1 from public.sinjira_world_locations l
      where l.id=v_story.location_id and l.canon_status='CANON'
    ) into v_location_canon;
  end if;

  v_metadata_ready:=
    v_story.anchor_scope<>'UNASSIGNED'
    and v_story.starts_at is not null
    and v_story.ends_at is not null
    and v_story.location_id is not null
    and v_location_canon
    and btrim(coalesce(v_story.content,''))<>'';

  v_provenance:=private.sinjira_story_provenance_report(p_story_id);
  v_continuity:=private.sinjira_story_continuity_report(p_story_id);

  v_ready:=
    v_metadata_ready
    and coalesce((v_provenance->>'ready')::boolean,false)
    and coalesce((v_continuity->>'blocking_conflicts')::integer,0)=0
    and coalesce((v_continuity->>'warnings')::integer,0)=0;

  return jsonb_build_object(
    'ok',true,
    'story_id',p_story_id,
    'ready',v_ready,
    'metadata',jsonb_build_object(
      'ready',v_metadata_ready,
      'anchor_assigned',v_story.anchor_scope<>'UNASSIGNED',
      'time_complete',v_story.starts_at is not null and v_story.ends_at is not null,
      'location_assigned',v_story.location_id is not null,
      'location_canon',v_location_canon,
      'content_present',btrim(coalesce(v_story.content,''))<>''
    ),
    'provenance',v_provenance,
    'continuity',v_continuity
  );
end;
$$;

revoke all on function private.sinjira_story_readiness_report(uuid) from public,anon,authenticated;

alter table public.sinjira_extended_stories
  drop constraint if exists sinjira_extended_stories_canon_workflow_check;
alter table public.sinjira_extended_stories
  add constraint sinjira_extended_stories_canon_workflow_check
  check(
    (canon_status='CANON_ETENDU' and status in ('validated','published'))
    or
    (canon_status<>'CANON_ETENDU' and status<>'published')
  );

create or replace function private.sinjira_require_story_canon_transition()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_structural_changed boolean:=false;
  v_entering_canon boolean:=false;
  v_entering_publish boolean:=false;
  v_readiness jsonb;
  v_metadata jsonb;
  v_provenance jsonb;
  v_continuity jsonb;
begin
  if tg_op='INSERT' then
    if new.canon_status='CANON_ETENDU' or new.status='published' then
      raise exception 'STORY_CANON_INSERT_FORBIDDEN';
    end if;
    return new;
  end if;

  v_structural_changed:=
    new.story_type is distinct from old.story_type
    or new.character_id is distinct from old.character_id
    or new.title is distinct from old.title
    or new.slug is distinct from old.slug
    or new.summary is distinct from old.summary
    or new.content is distinct from old.content
    or new.region_name is distinct from old.region_name
    or new.location_id is distinct from old.location_id
    or new.anchor_scope is distinct from old.anchor_scope
    or new.starts_at is distinct from old.starts_at
    or new.ends_at is distinct from old.ends_at
    or new.continuity_data is distinct from old.continuity_data;

  v_entering_canon:=new.canon_status='CANON_ETENDU' and old.canon_status<>'CANON_ETENDU';
  v_entering_publish:=new.status='published' and old.status<>'published';

  if not v_entering_canon and not v_entering_publish then
    return new;
  end if;

  if v_structural_changed then
    raise exception 'STORY_SAVE_BEFORE_CANON_TRANSITION';
  end if;

  if v_entering_publish and old.canon_status<>'CANON_ETENDU' then
    raise exception 'STORY_PROMOTION_REQUIRED';
  end if;

  if v_entering_canon and new.status<>'validated' then
    raise exception 'STORY_CANON_STATUS_INVALID';
  end if;

  if v_entering_publish then
    if new.canon_status<>'CANON_ETENDU' then raise exception 'STORY_NOT_CANON_EXTENDED'; end if;
    if new.audience not in ('members','public') then raise exception 'STORY_PUBLIC_AUDIENCE_REQUIRED'; end if;
    if new.published_at is null then raise exception 'STORY_PUBLICATION_TIMESTAMP_REQUIRED'; end if;
  end if;

  v_readiness:=private.sinjira_story_readiness_report(old.id);
  if coalesce((v_readiness->>'ok')::boolean,false) is not true then
    raise exception 'STORY_NOT_FOUND';
  end if;

  v_metadata:=v_readiness->'metadata';
  v_provenance:=v_readiness->'provenance';
  v_continuity:=v_readiness->'continuity';

  if coalesce((v_metadata->>'ready')::boolean,false) is not true then
    raise exception 'STORY_METADATA_INCOMPLETE';
  end if;
  if coalesce((v_provenance->>'verified_anchor_claims')::integer,0)=0 then
    raise exception 'STORY_PROVENANCE_REQUIRED';
  end if;
  if coalesce((v_provenance->>'matching_anchor_claims')::integer,0)=0 then
    raise exception 'STORY_PROVENANCE_SCOPE_MISMATCH';
  end if;
  if coalesce((v_provenance->>'unresolved_claims')::integer,0)>0 then
    raise exception 'STORY_PROVENANCE_INCOMPLETE';
  end if;
  if coalesce((v_continuity->>'blocking_conflicts')::integer,0)>0 then
    raise exception 'STORY_CONTINUITY_CONFLICT';
  end if;
  if coalesce((v_continuity->>'warnings')::integer,0)>0 then
    raise exception 'STORY_CONTINUITY_INCOMPLETE';
  end if;

  return new;
end;
$$;

drop trigger if exists sinjira_extended_stories_canon_transition_guard on public.sinjira_extended_stories;
create trigger sinjira_extended_stories_canon_transition_guard
before insert or update on public.sinjira_extended_stories
for each row execute function private.sinjira_require_story_canon_transition();

revoke all on function private.sinjira_require_story_canon_transition() from public,anon,authenticated,service_role;

create or replace function public.admin_sinjira_story_validation_check(
  p_story_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private,auth
as $$
declare
  v_admin uuid;
  v_readiness jsonb;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  v_readiness:=private.sinjira_story_readiness_report(p_story_id);

  if coalesce((v_readiness->>'ok')::boolean,false) is not true then
    raise exception 'STORY_NOT_FOUND';
  end if;

  return v_readiness;
end;
$$;

revoke all on function public.admin_sinjira_story_validation_check(uuid) from public,anon;
grant execute on function public.admin_sinjira_story_validation_check(uuid) to authenticated,service_role;

create or replace function public.admin_sinjira_promote_extended_story(
  p_story_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private,auth
as $$
declare
  v_admin uuid;
  v_report jsonb;
  v_provenance jsonb;
  v_story public.sinjira_extended_stories%rowtype;
begin
  v_admin:=private.require_sinjira_admin_aal2();

  select * into v_story
  from public.sinjira_extended_stories
  where id=p_story_id
  for update;

  if v_story.id is null then raise exception 'STORY_NOT_FOUND'; end if;
  if v_story.status='published' then raise exception 'STORY_UNPUBLISH_FIRST'; end if;
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
  if btrim(coalesce(v_story.content,''))='' then
    raise exception 'STORY_CONTENT_REQUIRED';
  end if;

  v_provenance:=private.sinjira_story_provenance_report(p_story_id);

  if coalesce((v_provenance->>'verified_anchor_claims')::integer,0)=0 then
    raise exception 'STORY_PROVENANCE_REQUIRED';
  end if;
  if coalesce((v_provenance->>'matching_anchor_claims')::integer,0)=0 then
    raise exception 'STORY_PROVENANCE_SCOPE_MISMATCH';
  end if;
  if coalesce((v_provenance->>'unresolved_claims')::integer,0)>0 then
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
  set canon_status='CANON_ETENDU',
      status='validated',
      published_at=null
  where id=p_story_id
  returning * into v_story;

  return jsonb_build_object(
    'ok',true,
    'story_id',v_story.id,
    'canon_status',v_story.canon_status,
    'status',v_story.status,
    'provenance',v_provenance,
    'continuity',v_report
  );
end;
$$;

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
  v_provenance jsonb;
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
  if btrim(coalesce(v_story.content,''))='' then
    raise exception 'STORY_CONTENT_REQUIRED';
  end if;

  v_provenance:=private.sinjira_story_provenance_report(p_story_id);

  if coalesce((v_provenance->>'verified_anchor_claims')::integer,0)=0 then
    raise exception 'STORY_PROVENANCE_REQUIRED';
  end if;
  if coalesce((v_provenance->>'matching_anchor_claims')::integer,0)=0 then
    raise exception 'STORY_PROVENANCE_SCOPE_MISMATCH';
  end if;
  if coalesce((v_provenance->>'unresolved_claims')::integer,0)>0 then
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
    'provenance',v_provenance,
    'continuity',v_report
  );
end;
$$;

revoke all on function public.admin_sinjira_promote_extended_story(uuid) from public,anon;
revoke all on function public.admin_sinjira_publish_extended_story(uuid,text) from public,anon;
grant execute on function public.admin_sinjira_promote_extended_story(uuid) to authenticated,service_role;
grant execute on function public.admin_sinjira_publish_extended_story(uuid,text) to authenticated,service_role;

comment on table public.sinjira_canon_sources is
  'Registre privé des sources canoniques SINJIRA. Les SECRET_AUTEUR peuvent servir de garde-fous sans être divulgués.';
comment on table public.sinjira_story_claims is
  'Faits de continuité d’une Chronique. Chaque fait vérifié pointe vers une source canonique vérifiée.';
comment on function private.sinjira_source_is_verified(uuid) is
  'Retourne vrai uniquement pour une source VERIFIED ou SECRET_AUTEUR.';
comment on function private.sinjira_guard_canon_source_lifecycle() is
  'Interdit la création directe en RETIRED, rend RETIRED irréversible et empêche une source research de devenir un maillon de remplacement canonique.';
comment on function private.sinjira_prevent_source_supersedes_cycle() is
  'Empêche auto-remplacement, cycles, références absentes, fourches de succession, croisements de périmètre et remplacement direct entre deux romans de numéros différents.';
comment on function public.admin_sinjira_migrate_canon_source_references(uuid,uuid) is
  'Migration atomique auteur : déplace toutes les références directes vers l’unique remplacement vérifié de même période puis passe immédiatement l’ancienne source à RETIRED dans la même transaction.';
comment on function private.sinjira_guard_canon_source_in_use() is
  'Protège les sources engagées; RETIRED exige un remplacement vérifié de même période et aucune référence directe restante vers l’ancienne source.';
comment on function private.sinjira_demote_extended_story_on_edit() is
  'Une modification structurelle retire automatiquement CANON_ETENDU et exige une nouvelle prévalidation.';
comment on function private.sinjira_demote_story_from_child_change() is
  'Toute modification d’un fait de provenance ou d’un segment retire CANON_ETENDU du récit concerné.';
comment on function private.sinjira_invalidate_published_extended_stories() is
  'Toute modification d’une dépendance canonique dépublie et repasse les Chroniques CANON_ETENDU en PROVISOIRE / author_review.';
comment on function private.sinjira_story_provenance_report(uuid) is
  'Rapport unique de provenance d’une Chronique : ancrages vérifiés, période correspondante et faits non résolus.';
comment on function private.sinjira_story_readiness_report(uuid) is
  'Source unique de vérité avant canonisation/publication : métadonnées, provenance et continuité.';
comment on function private.sinjira_require_story_canon_transition() is
  'Garde SQL : toute entrée dans CANON_ETENDU ou published exige une version déjà enregistrée et entièrement prête.';
comment on function public.admin_sinjira_story_validation_check(uuid) is
  'Prévalidation auteur combinée : provenance structurée et continuité doivent être prêtes avant CANON_ETENDU.';
comment on function public.admin_sinjira_promote_extended_story(uuid) is
  'Promotion auteur vers CANON_ETENDU : exige métadonnées complètes, provenance vérifiée et continuité sans conflit ni avertissement.';
comment on function public.admin_sinjira_publish_extended_story(uuid,text) is
  'Publication atomique d’une Chronique CANON_ETENDU; revalide métadonnées, provenance et continuité avant exposition membres/public.';
