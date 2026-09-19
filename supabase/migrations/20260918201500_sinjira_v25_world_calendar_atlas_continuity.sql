-- SINJIRA™ V25 — Calendrier-Monde, Atlas canonique et contrôle de continuité
-- Structure uniquement : aucun événement des romans n'est inventé dans cette migration.
-- Les données doivent provenir des manuscrits / Bible canonique et être validées par Benoit Cantin.

create table if not exists public.sinjira_world_locations(
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  location_type text not null default 'place' check(location_type in (
    'world','continent','country','province_state','region','city','district','site','place'
  )),
  parent_id uuid references public.sinjira_world_locations(id) on delete set null,
  country_code text,
  timezone_name text,
  latitude numeric(9,6),
  longitude numeric(9,6),
  canon_status text not null default 'PROVISOIRE' check(canon_status in ('PROVISOIRE','CANON','A_ARBITRER')),
  source_reference text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check(latitude is null or (latitude between -90 and 90)),
  check(longitude is null or (longitude between -180 and 180))
);

create table if not exists public.sinjira_world_travel_rules(
  id uuid primary key default gen_random_uuid(),
  from_location_id uuid not null references public.sinjira_world_locations(id) on delete cascade,
  to_location_id uuid not null references public.sinjira_world_locations(id) on delete cascade,
  minimum_minutes integer not null check(minimum_minutes >= 0),
  travel_mode text not null default 'unspecified',
  valid_from timestamptz,
  valid_until timestamptz,
  canon_status text not null default 'PROVISOIRE' check(canon_status in ('PROVISOIRE','CANON','A_ARBITRER')),
  source_reference text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check(from_location_id <> to_location_id),
  check(valid_until is null or valid_from is null or valid_until >= valid_from)
);

create table if not exists public.sinjira_canon_events(
  id uuid primary key default gen_random_uuid(),
  event_key text unique,
  title text not null,
  summary text,
  starts_at timestamptz,
  ends_at timestamptz,
  timezone_name text,
  location_id uuid references public.sinjira_world_locations(id) on delete set null,
  location_name_snapshot text,
  source_scope text not null check(source_scope in (
    'LIVRES_1_12',
    'ORIGINES_13_14',
    'CANON_ETENDU'
  )),
  source_reference text not null,
  classification text not null default 'PROVISOIRE' check(classification in (
    'CANON','SECRET_AUTEUR','A_ARBITRER','PROVISOIRE'
  )),
  public_safe boolean not null default false,
  consequences jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check(ends_at is null or starts_at is null or ends_at >= starts_at)
);

create table if not exists public.sinjira_canon_event_characters(
  event_id uuid not null references public.sinjira_canon_events(id) on delete cascade,
  character_id uuid not null references public.characters(id) on delete cascade,
  role text,
  starts_at timestamptz,
  ends_at timestamptz,
  location_id uuid references public.sinjira_world_locations(id) on delete set null,
  location_name_snapshot text,
  certainty text not null default 'confirmed' check(certainty in ('confirmed','approximate','unknown')),
  source_reference text,
  created_at timestamptz not null default now(),
  primary key(event_id,character_id),
  check(ends_at is null or starts_at is null or ends_at >= starts_at)
);

alter table public.sinjira_extended_stories
  add column if not exists location_id uuid references public.sinjira_world_locations(id) on delete set null;

alter table public.sinjira_story_character_presence
  add column if not exists location_id uuid references public.sinjira_world_locations(id) on delete set null;

create index if not exists sinjira_world_locations_parent_idx
  on public.sinjira_world_locations(parent_id);
create index if not exists sinjira_world_travel_route_idx
  on public.sinjira_world_travel_rules(from_location_id,to_location_id,valid_from,valid_until);
create index if not exists sinjira_canon_events_time_idx
  on public.sinjira_canon_events(starts_at,ends_at);
create index if not exists sinjira_canon_events_location_idx
  on public.sinjira_canon_events(location_id,starts_at);
create index if not exists sinjira_canon_event_characters_character_time_idx
  on public.sinjira_canon_event_characters(character_id,starts_at,ends_at);
create index if not exists sinjira_story_presence_location_time_idx
  on public.sinjira_story_character_presence(location_id,starts_at,ends_at);

drop trigger if exists sinjira_world_locations_updated_at on public.sinjira_world_locations;
create trigger sinjira_world_locations_updated_at before update on public.sinjira_world_locations
for each row execute function public.set_updated_at();

drop trigger if exists sinjira_world_travel_rules_updated_at on public.sinjira_world_travel_rules;
create trigger sinjira_world_travel_rules_updated_at before update on public.sinjira_world_travel_rules
for each row execute function public.set_updated_at();

drop trigger if exists sinjira_canon_events_updated_at on public.sinjira_canon_events;
create trigger sinjira_canon_events_updated_at before update on public.sinjira_canon_events
for each row execute function public.set_updated_at();

alter table public.sinjira_world_locations enable row level security;
alter table public.sinjira_world_travel_rules enable row level security;
alter table public.sinjira_canon_events enable row level security;
alter table public.sinjira_canon_event_characters enable row level security;

-- Les tables du Calendrier-Monde et de l'Atlas sont privées par défaut.
-- Elles sont administrées via la fonction Edge avec service_role.
revoke all on public.sinjira_world_locations from anon,authenticated;
revoke all on public.sinjira_world_travel_rules from anon,authenticated;
revoke all on public.sinjira_canon_events from anon,authenticated;
revoke all on public.sinjira_canon_event_characters from anon,authenticated;

create or replace function private.sinjira_location_is_ancestor(
  p_ancestor uuid,
  p_descendant uuid
)
returns boolean
language sql
stable
set search_path=pg_catalog,public,private
as $$
  with recursive lineage(id,parent_id) as (
    select l.id,l.parent_id from public.sinjira_world_locations l where l.id=p_descendant
    union all
    select p.id,p.parent_id
    from public.sinjira_world_locations p
    join lineage x on x.parent_id=p.id
  )
  select p_ancestor is not null
    and p_descendant is not null
    and exists(select 1 from lineage where id=p_ancestor);
$$;

create or replace function private.sinjira_locations_compatible(
  p_a uuid,
  p_b uuid
)
returns boolean
language sql
stable
set search_path=pg_catalog,public,private
as $$
  select case
    when p_a is null or p_b is null then true
    when p_a=p_b then true
    when private.sinjira_location_is_ancestor(p_a,p_b) then true
    when private.sinjira_location_is_ancestor(p_b,p_a) then true
    else false
  end;
$$;

create or replace function private.sinjira_story_continuity_report(
  p_story_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private,auth
as $$
declare
  v_story public.sinjira_extended_stories%rowtype;
  v_conflicts jsonb:='[]'::jsonb;
  v_warnings jsonb:='[]'::jsonb;
  v_blocking integer:=0;
begin
  select * into v_story from public.sinjira_extended_stories where id=p_story_id;
  if v_story.id is null then
    return jsonb_build_object('ok',false,'code','STORY_NOT_FOUND','blocking_conflicts',0,'warnings',0,'conflicts','[]'::jsonb,'warning_items','[]'::jsonb);
  end if;

  -- Collision avec une présence issue du Canon central / calendrier maître.
  select coalesce(jsonb_agg(jsonb_build_object(
      'type','central_overlap',
      'character_id',sp.character_id,
      'story_presence_id',sp.id,
      'event_id',ce.id,
      'event_title',ce.title,
      'story_start',sp.starts_at,
      'story_end',sp.ends_at,
      'event_start',coalesce(cp.starts_at,ce.starts_at),
      'event_end',coalesce(cp.ends_at,ce.ends_at),
      'story_location_id',sp.location_id,
      'event_location_id',coalesce(cp.location_id,ce.location_id),
      'event_source',ce.source_reference
    )),'[]'::jsonb),count(*)
  into v_conflicts,v_blocking
  from public.sinjira_story_character_presence sp
  join public.sinjira_canon_event_characters cp on cp.character_id=sp.character_id
  join public.sinjira_canon_events ce on ce.id=cp.event_id and ce.classification='CANON'
  where sp.story_id=p_story_id
    and sp.starts_at is not null
    and sp.ends_at is not null
    and coalesce(cp.starts_at,ce.starts_at) is not null
    and coalesce(cp.ends_at,ce.ends_at) is not null
    and tstzrange(sp.starts_at,sp.ends_at,'[]') && tstzrange(coalesce(cp.starts_at,ce.starts_at),coalesce(cp.ends_at,ce.ends_at),'[]')
    and sp.location_id is not null
    and coalesce(cp.location_id,ce.location_id) is not null
    and not private.sinjira_locations_compatible(sp.location_id,coalesce(cp.location_id,ce.location_id));

  -- Collision avec une autre Chronique déjà canonisée.
  with ext as (
    select jsonb_build_object(
      'type','extended_overlap',
      'character_id',sp.character_id,
      'story_presence_id',sp.id,
      'other_story_id',os.id,
      'other_story_title',os.title,
      'story_start',sp.starts_at,
      'story_end',sp.ends_at,
      'other_start',op.starts_at,
      'other_end',op.ends_at,
      'story_location_id',sp.location_id,
      'other_location_id',op.location_id
    ) as item
    from public.sinjira_story_character_presence sp
    join public.sinjira_story_character_presence op
      on op.character_id=sp.character_id and op.story_id<>sp.story_id
    join public.sinjira_extended_stories os
      on os.id=op.story_id
      and os.canon_status='CANON_ETENDU'
      and os.status in ('validated','published')
    where sp.story_id=p_story_id
      and sp.starts_at is not null and sp.ends_at is not null
      and op.starts_at is not null and op.ends_at is not null
      and tstzrange(sp.starts_at,sp.ends_at,'[]') && tstzrange(op.starts_at,op.ends_at,'[]')
      and sp.location_id is not null and op.location_id is not null
      and not private.sinjira_locations_compatible(sp.location_id,op.location_id)
  )
  select v_conflicts || coalesce(jsonb_agg(item),'[]'::jsonb),
         v_blocking + count(*)
  into v_conflicts,v_blocking
  from ext;

  -- Avertissements : une période est définie mais le lieu canonique n'est pas encore normalisé.
  with warn as (
    select jsonb_build_object(
      'type','location_unresolved',
      'character_id',sp.character_id,
      'story_presence_id',sp.id,
      'location_name',sp.location_name,
      'message','La présence est datée mais sans location_id Atlas; les collisions géographiques ne peuvent pas être garanties.'
    ) as item
    from public.sinjira_story_character_presence sp
    where sp.story_id=p_story_id
      and sp.starts_at is not null
      and sp.ends_at is not null
      and sp.location_id is null
  )
  select coalesce(jsonb_agg(item),'[]'::jsonb) into v_warnings from warn;

  return jsonb_build_object(
    'ok',true,
    'story_id',p_story_id,
    'blocking_conflicts',v_blocking,
    'warnings',jsonb_array_length(v_warnings),
    'conflicts',v_conflicts,
    'warning_items',v_warnings
  );
end;
$$;

create or replace function public.admin_sinjira_story_continuity_check(
  p_story_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private,auth
as $$
declare
  v_admin uuid;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  return private.sinjira_story_continuity_report(p_story_id);
end;
$$;

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
  v_story public.sinjira_extended_stories%rowtype;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select * into v_story from public.sinjira_extended_stories where id=p_story_id for update;
  if v_story.id is null then raise exception 'STORY_NOT_FOUND'; end if;

  v_report:=private.sinjira_story_continuity_report(p_story_id);
  if coalesce((v_report->>'blocking_conflicts')::integer,0)>0 then
    raise exception 'STORY_CONTINUITY_CONFLICT';
  end if;

  update public.sinjira_extended_stories
  set canon_status='CANON_ETENDU',
      status=case when status in ('draft','author_review') then 'validated' else status end
  where id=p_story_id
  returning * into v_story;

  return jsonb_build_object(
    'ok',true,
    'story_id',v_story.id,
    'canon_status',v_story.canon_status,
    'status',v_story.status,
    'continuity',v_report
  );
end;
$$;

revoke all on function private.sinjira_location_is_ancestor(uuid,uuid) from public,anon,authenticated;
revoke all on function private.sinjira_locations_compatible(uuid,uuid) from public,anon,authenticated;
revoke all on function private.sinjira_story_continuity_report(uuid) from public,anon,authenticated;
revoke all on function public.admin_sinjira_story_continuity_check(uuid) from public,anon;
revoke all on function public.admin_sinjira_promote_extended_story(uuid) from public,anon;

grant execute on function public.admin_sinjira_story_continuity_check(uuid) to authenticated,service_role;
grant execute on function public.admin_sinjira_promote_extended_story(uuid) to authenticated,service_role;

comment on table public.sinjira_world_locations is
  'Atlas canonique SINJIRA. Les lieux sont hiérarchiques afin de distinguer une vraie collision de la présence dans une sous-zone compatible.';
comment on table public.sinjira_world_travel_rules is
  'Règles minimales de déplacement entre lieux du Calendrier-Monde. Les données doivent être sourcées; aucune durée n’est inventée automatiquement.';
comment on table public.sinjira_canon_events is
  'Calendrier-Monde maître. Chaque événement doit pointer vers une source canonique réelle.';
comment on table public.sinjira_canon_event_characters is
  'Présences de personnages dans les événements du Calendrier-Monde.';
comment on function public.admin_sinjira_story_continuity_check(uuid) is
  'Contrôle auteur : détecte les chevauchements géographiques incompatibles entre une Chronique, le Canon central et les Chroniques déjà canonisées.';
comment on function public.admin_sinjira_promote_extended_story(uuid) is
  'Promotion humaine vers CANON_ETENDU refusée si une collision de continuité bloquante est détectée.';
