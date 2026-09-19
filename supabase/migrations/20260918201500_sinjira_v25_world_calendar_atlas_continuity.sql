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
  bidirectional boolean not null default true,
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

alter table public.sinjira_extended_stories
  drop constraint if exists sinjira_extended_stories_published_metadata_check;
alter table public.sinjira_extended_stories
  add constraint sinjira_extended_stories_published_metadata_check
  check(
    status <> 'published'
    or (
      canon_status='CANON_ETENDU'
      and anchor_scope<>'UNASSIGNED'
      and starts_at is not null
      and ends_at is not null
      and location_id is not null
      and btrim(coalesce(content,''))<>''
    )
  );

create or replace function private.sinjira_guard_published_story_update()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
begin
  if old.status='published' then
    if new.story_type is distinct from old.story_type
       or new.character_id is distinct from old.character_id
       or new.title is distinct from old.title
       or new.slug is distinct from old.slug
       or new.summary is distinct from old.summary
       or new.content is distinct from old.content
       or new.region_name is distinct from old.region_name
       or new.location_id is distinct from old.location_id
       or new.anchor_scope is distinct from old.anchor_scope
       or new.canon_status is distinct from old.canon_status
       or new.starts_at is distinct from old.starts_at
       or new.ends_at is distinct from old.ends_at
       or new.continuity_data is distinct from old.continuity_data
       or new.audience is distinct from old.audience
       or new.visible_to_character_owner is distinct from old.visible_to_character_owner then
      raise exception 'STORY_UNPUBLISH_FIRST';
    end if;

    if new.status='published' then
      if new.published_at is distinct from old.published_at then
        raise exception 'STORY_UNPUBLISH_FIRST';
      end if;
    elsif not (new.status='validated' and new.published_at is null) then
      raise exception 'STORY_UNPUBLISH_FIRST';
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists sinjira_extended_stories_guard_published on public.sinjira_extended_stories;
create trigger sinjira_extended_stories_guard_published
before update on public.sinjira_extended_stories
for each row execute function private.sinjira_guard_published_story_update();

create or replace function private.sinjira_guard_published_story_presence()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
begin
  if tg_op in ('UPDATE','DELETE') and exists(
    select 1 from public.sinjira_extended_stories s
    where s.id=old.story_id and s.status='published'
  ) then
    raise exception 'STORY_UNPUBLISH_FIRST';
  end if;

  if tg_op in ('INSERT','UPDATE') and exists(
    select 1 from public.sinjira_extended_stories s
    where s.id=new.story_id and s.status='published'
  ) then
    raise exception 'STORY_UNPUBLISH_FIRST';
  end if;

  if tg_op='DELETE' then return old; end if;
  return new;
end;
$$;

drop trigger if exists sinjira_story_presence_guard_published on public.sinjira_story_character_presence;
create trigger sinjira_story_presence_guard_published
before insert or update or delete on public.sinjira_story_character_presence
for each row execute function private.sinjira_guard_published_story_presence();

revoke all on function private.sinjira_guard_published_story_update() from public,anon,authenticated,service_role;
revoke all on function private.sinjira_guard_published_story_presence() from public,anon,authenticated,service_role;

create or replace function private.sinjira_invalidate_published_extended_stories()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
begin
  update public.sinjira_extended_stories
  set status='validated',
      published_at=null
  where status='published';

  return null;
end;
$$;

revoke all on function private.sinjira_invalidate_published_extended_stories() from public,anon,authenticated,service_role;

drop trigger if exists sinjira_world_locations_invalidate_extended_update on public.sinjira_world_locations;
create trigger sinjira_world_locations_invalidate_extended_update
after update of parent_id,canon_status on public.sinjira_world_locations
for each statement execute function private.sinjira_invalidate_published_extended_stories();

drop trigger if exists sinjira_world_locations_invalidate_extended_delete on public.sinjira_world_locations;
create trigger sinjira_world_locations_invalidate_extended_delete
after delete on public.sinjira_world_locations
for each statement execute function private.sinjira_invalidate_published_extended_stories();

drop trigger if exists sinjira_world_travel_invalidate_extended on public.sinjira_world_travel_rules;
create trigger sinjira_world_travel_invalidate_extended
after insert or update or delete on public.sinjira_world_travel_rules
for each statement execute function private.sinjira_invalidate_published_extended_stories();

drop trigger if exists sinjira_canon_events_invalidate_extended_insert_delete on public.sinjira_canon_events;
create trigger sinjira_canon_events_invalidate_extended_insert_delete
after insert or delete on public.sinjira_canon_events
for each statement execute function private.sinjira_invalidate_published_extended_stories();

drop trigger if exists sinjira_canon_events_invalidate_extended_update on public.sinjira_canon_events;
create trigger sinjira_canon_events_invalidate_extended_update
after update of starts_at,ends_at,location_id,classification on public.sinjira_canon_events
for each statement execute function private.sinjira_invalidate_published_extended_stories();

drop trigger if exists sinjira_canon_event_characters_invalidate_extended on public.sinjira_canon_event_characters;
create trigger sinjira_canon_event_characters_invalidate_extended
after insert or update or delete on public.sinjira_canon_event_characters
for each statement execute function private.sinjira_invalidate_published_extended_stories();

drop trigger if exists sinjira_canon_context_invalidate_extended on public.sinjira_canon_context;
create trigger sinjira_canon_context_invalidate_extended
after insert or update or delete on public.sinjira_canon_context
for each statement execute function private.sinjira_invalidate_published_extended_stories();

create or replace view private.sinjira_effective_story_presence as
select sp.*
from public.sinjira_story_character_presence sp
where sp.segment_key<>'primary'
   or not exists(
     select 1
     from public.sinjira_story_character_presence detailed
     where detailed.story_id=sp.story_id
       and detailed.character_id=sp.character_id
       and detailed.segment_key<>'primary'
   );

revoke all on private.sinjira_effective_story_presence from public,anon,authenticated;

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

create or replace function private.sinjira_prevent_location_cycle()
returns trigger
language plpgsql
set search_path=pg_catalog,public,private
as $$
declare
  v_cycle boolean:=false;
begin
  if new.parent_id is null then return new; end if;
  if new.parent_id=new.id then raise exception 'LOCATION_PARENT_SELF'; end if;

  with recursive ancestors(id,parent_id,path) as (
    select l.id,l.parent_id,array[l.id]
    from public.sinjira_world_locations l
    where l.id=new.parent_id
    union all
    select p.id,p.parent_id,a.path||p.id
    from public.sinjira_world_locations p
    join ancestors a on p.id=a.parent_id
    where not p.id=any(a.path)
  )
  select exists(select 1 from ancestors where id=new.id) into v_cycle;

  if v_cycle then raise exception 'LOCATION_HIERARCHY_CYCLE'; end if;
  return new;
end;
$$;

drop trigger if exists sinjira_world_locations_prevent_cycle on public.sinjira_world_locations;
create trigger sinjira_world_locations_prevent_cycle
before insert or update of parent_id on public.sinjira_world_locations
for each row execute function private.sinjira_prevent_location_cycle();

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
  from private.sinjira_effective_story_presence sp
  join public.sinjira_canon_event_characters cp on cp.character_id=sp.character_id and cp.certainty='confirmed'
  join public.sinjira_canon_events ce on ce.id=cp.event_id and ce.classification in ('CANON','SECRET_AUTEUR')
  where sp.story_id=p_story_id
    and sp.starts_at is not null
    and sp.ends_at is not null
    and coalesce(cp.starts_at,ce.starts_at) is not null
    and coalesce(cp.ends_at,ce.ends_at) is not null
    and tstzrange(sp.starts_at,sp.ends_at,'[]') && tstzrange(coalesce(cp.starts_at,ce.starts_at),coalesce(cp.ends_at,ce.ends_at),'[]')
    and sp.location_id is not null
    and coalesce(cp.location_id,ce.location_id) is not null
    and not private.sinjira_locations_compatible(sp.location_id,coalesce(cp.location_id,ce.location_id));

  -- Présence centrale incertaine ou incomplète : ne jamais l’ignorer silencieusement.
  with central_unresolved as (
    select jsonb_build_object(
      'type',case
        when cp.certainty<>'confirmed' then 'central_presence_uncertain'
        when coalesce(cp.starts_at,ce.starts_at) is null or coalesce(cp.ends_at,ce.ends_at) is null then 'central_time_incomplete'
        when coalesce(cp.location_id,ce.location_id) is null then 'central_location_incomplete'
        else 'central_presence_incomplete'
      end,
      'character_id',sp.character_id,
      'story_presence_id',sp.id,
      'event_id',ce.id,
      'event_title',ce.title,
      'event_source',ce.source_reference,
      'message',case
        when cp.certainty<>'confirmed' then 'Une présence du Canon central est encore approximative ou inconnue pour ce personnage.'
        when coalesce(cp.starts_at,ce.starts_at) is null or coalesce(cp.ends_at,ce.ends_at) is null then 'Une présence du Canon central n’a pas encore une période complète.'
        when coalesce(cp.location_id,ce.location_id) is null then 'Une présence du Canon central chevauchante n’a pas encore un lieu canonique.'
        else 'Une présence du Canon central doit être clarifiée avant canonisation.'
      end
    ) as item
    from private.sinjira_effective_story_presence sp
    join public.sinjira_canon_event_characters cp on cp.character_id=sp.character_id
    join public.sinjira_canon_events ce on ce.id=cp.event_id and ce.classification in ('CANON','SECRET_AUTEUR')
    where sp.story_id=p_story_id
      and (
        cp.certainty<>'confirmed'
        or coalesce(cp.starts_at,ce.starts_at) is null
        or coalesce(cp.ends_at,ce.ends_at) is null
        or coalesce(cp.location_id,ce.location_id) is null
      )
      and (
        coalesce(cp.starts_at,ce.starts_at) is null
        or coalesce(cp.ends_at,ce.ends_at) is null
        or sp.starts_at is null
        or sp.ends_at is null
        or tstzrange(sp.starts_at,sp.ends_at,'[]') && tstzrange(coalesce(cp.starts_at,ce.starts_at),coalesce(cp.ends_at,ce.ends_at),'[]')
      )
  )
  select v_warnings || coalesce(jsonb_agg(item),'[]'::jsonb)
  into v_warnings
  from central_unresolved;

  -- Collision interne : deux segments détaillés du même personnage ne peuvent pas
  -- se chevaucher dans deux lieux incompatibles au sein de la même Chronique.
  with internal_conflict as (
    select jsonb_build_object(
      'type','internal_overlap',
      'character_id',a.character_id,
      'story_presence_id',a.id,
      'other_story_presence_id',b.id,
      'story_start',a.starts_at,
      'story_end',a.ends_at,
      'other_start',b.starts_at,
      'other_end',b.ends_at,
      'story_location_id',a.location_id,
      'other_location_id',b.location_id
    ) as item
    from private.sinjira_effective_story_presence a
    join private.sinjira_effective_story_presence b
      on b.story_id=a.story_id
      and b.character_id=a.character_id
      and b.id>a.id
    where a.story_id=p_story_id
      and a.starts_at is not null and a.ends_at is not null
      and b.starts_at is not null and b.ends_at is not null
      and tstzrange(a.starts_at,a.ends_at,'[]') && tstzrange(b.starts_at,b.ends_at,'[]')
      and a.location_id is not null and b.location_id is not null
      and not private.sinjira_locations_compatible(a.location_id,b.location_id)
  )
  select v_conflicts || coalesce(jsonb_agg(item),'[]'::jsonb),
         v_blocking + count(*)
  into v_conflicts,v_blocking
  from internal_conflict;

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
    from private.sinjira_effective_story_presence sp
    join private.sinjira_effective_story_presence op
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

  -- Vérification du temps de déplacement avec les présences canoniques immédiatement
  -- précédentes et suivantes. Une absence de règle de trajet produit un avertissement
  -- bloquant pour la canonisation, afin de ne jamais inventer une durée.
  with known as (
    select cp.character_id,
           coalesce(cp.starts_at,ce.starts_at) as starts_at,
           coalesce(cp.ends_at,ce.ends_at) as ends_at,
           coalesce(cp.location_id,ce.location_id) as location_id,
           'central'::text as source_kind,
           ce.id as source_id,
           ce.title as source_title,
           null::uuid as source_presence_id
    from public.sinjira_canon_event_characters cp
    join public.sinjira_canon_events ce on ce.id=cp.event_id
    where ce.classification in ('CANON','SECRET_AUTEUR')
      and coalesce(cp.starts_at,ce.starts_at) is not null
      and coalesce(cp.ends_at,ce.ends_at) is not null
    union all
    select op.character_id,op.starts_at,op.ends_at,op.location_id,
           case when op.story_id=p_story_id then 'same_story' else 'extended' end::text,
           os.id,os.title,op.id
    from private.sinjira_effective_story_presence op
    join public.sinjira_extended_stories os on os.id=op.story_id
    where (
        op.story_id=p_story_id
        or (
          os.canon_status='CANON_ETENDU'
          and os.status in ('validated','published')
        )
      )
      and op.starts_at is not null and op.ends_at is not null
  ),
  transitions as (
    select sp.id as story_presence_id,sp.character_id,sp.starts_at,sp.ends_at,sp.location_id,
           prev.source_kind as prev_kind,prev.source_id as prev_id,prev.source_title as prev_title,
           prev.ends_at as prev_end,prev.location_id as prev_location_id,
           nxt.source_kind as next_kind,nxt.source_id as next_id,nxt.source_title as next_title,
           nxt.starts_at as next_start,nxt.location_id as next_location_id
    from private.sinjira_effective_story_presence sp
    left join lateral (
      select k.* from known k
      where k.character_id=sp.character_id
        and (k.source_presence_id is null or k.source_presence_id<>sp.id)
        and sp.starts_at is not null
        and k.ends_at<=sp.starts_at
      order by k.ends_at desc
      limit 1
    ) prev on true
    left join lateral (
      select k.* from known k
      where k.character_id=sp.character_id
        and (k.source_presence_id is null or k.source_presence_id<>sp.id)
        and sp.ends_at is not null
        and k.starts_at>=sp.ends_at
      order by k.starts_at asc
      limit 1
    ) nxt on true
    where sp.story_id=p_story_id
  ),
  travel_eval as (
    select t.*,
      case when t.prev_location_id is not null and t.location_id is not null
                 and not private.sinjira_locations_compatible(t.prev_location_id,t.location_id)
        then (
          select min(r.minimum_minutes)
          from public.sinjira_world_travel_rules r
          where ((r.from_location_id=t.prev_location_id and r.to_location_id=t.location_id)
              or (r.bidirectional and r.from_location_id=t.location_id and r.to_location_id=t.prev_location_id))
            and r.canon_status='CANON'
            and (r.valid_from is null or r.valid_from<=t.prev_end)
            and (r.valid_until is null or r.valid_until>=t.starts_at)
        ) else 0 end as prev_required_minutes,
      case when t.next_location_id is not null and t.location_id is not null
                 and not private.sinjira_locations_compatible(t.location_id,t.next_location_id)
        then (
          select min(r.minimum_minutes)
          from public.sinjira_world_travel_rules r
          where ((r.from_location_id=t.location_id and r.to_location_id=t.next_location_id)
              or (r.bidirectional and r.from_location_id=t.next_location_id and r.to_location_id=t.location_id))
            and r.canon_status='CANON'
            and (r.valid_from is null or r.valid_from<=t.ends_at)
            and (r.valid_until is null or r.valid_until>=t.next_start)
        ) else 0 end as next_required_minutes
    from transitions t
  ),
  travel_conflicts as (
    select jsonb_build_object(
      'type','travel_time',
      'direction','before',
      'character_id',character_id,
      'story_presence_id',story_presence_id,
      'other_source_kind',prev_kind,
      'other_source_id',prev_id,
      'other_title',prev_title,
      'available_minutes',floor(extract(epoch from (starts_at-prev_end))/60),
      'required_minutes',prev_required_minutes,
      'from_location_id',prev_location_id,
      'to_location_id',location_id
    ) as item
    from travel_eval
    where prev_required_minutes is not null and prev_required_minutes>0
      and extract(epoch from (starts_at-prev_end))/60 < prev_required_minutes
    union all
    select jsonb_build_object(
      'type','travel_time',
      'direction','after',
      'character_id',character_id,
      'story_presence_id',story_presence_id,
      'other_source_kind',next_kind,
      'other_source_id',next_id,
      'other_title',next_title,
      'available_minutes',floor(extract(epoch from (next_start-ends_at))/60),
      'required_minutes',next_required_minutes,
      'from_location_id',location_id,
      'to_location_id',next_location_id
    )
    from travel_eval
    where next_required_minutes is not null and next_required_minutes>0
      and extract(epoch from (next_start-ends_at))/60 < next_required_minutes
  )
  select v_conflicts || coalesce(jsonb_agg(item),'[]'::jsonb),
         v_blocking + count(*)
  into v_conflicts,v_blocking
  from travel_conflicts;

  with known as (
    select cp.character_id,
           coalesce(cp.starts_at,ce.starts_at) as starts_at,
           coalesce(cp.ends_at,ce.ends_at) as ends_at,
           coalesce(cp.location_id,ce.location_id) as location_id,
           ce.id as source_id,ce.title as source_title,
           null::uuid as source_presence_id
    from public.sinjira_canon_event_characters cp
    join public.sinjira_canon_events ce on ce.id=cp.event_id
    where ce.classification in ('CANON','SECRET_AUTEUR')
      and coalesce(cp.starts_at,ce.starts_at) is not null
      and coalesce(cp.ends_at,ce.ends_at) is not null
    union all
    select op.character_id,op.starts_at,op.ends_at,op.location_id,os.id,os.title,op.id
    from private.sinjira_effective_story_presence op
    join public.sinjira_extended_stories os on os.id=op.story_id
    where (
        op.story_id=p_story_id
        or (
          os.canon_status='CANON_ETENDU'
          and os.status in ('validated','published')
        )
      )
      and op.starts_at is not null and op.ends_at is not null
  ),
  transitions as (
    select sp.id as story_presence_id,sp.character_id,sp.starts_at,sp.ends_at,sp.location_id,
           prev.source_id as prev_id,prev.source_title as prev_title,prev.ends_at as prev_end,prev.location_id as prev_location_id,
           nxt.source_id as next_id,nxt.source_title as next_title,nxt.starts_at as next_start,nxt.location_id as next_location_id
    from private.sinjira_effective_story_presence sp
    left join lateral (
      select k.* from known k where k.character_id=sp.character_id and (k.source_presence_id is null or k.source_presence_id<>sp.id) and sp.starts_at is not null and k.ends_at<=sp.starts_at order by k.ends_at desc limit 1
    ) prev on true
    left join lateral (
      select k.* from known k where k.character_id=sp.character_id and (k.source_presence_id is null or k.source_presence_id<>sp.id) and sp.ends_at is not null and k.starts_at>=sp.ends_at order by k.starts_at asc limit 1
    ) nxt on true
    where sp.story_id=p_story_id
  ),
  missing as (
    select jsonb_build_object(
      'type','travel_rule_missing','direction','before','character_id',character_id,
      'story_presence_id',story_presence_id,'other_source_id',prev_id,'other_title',prev_title,
      'from_location_id',prev_location_id,'to_location_id',location_id,
      'message','Aucune durée minimale CANON n’est définie dans l’Atlas pour vérifier le déplacement précédent.'
    ) as item
    from transitions t
    where t.prev_location_id is not null and t.location_id is not null
      and not private.sinjira_locations_compatible(t.prev_location_id,t.location_id)
      and not exists(
        select 1 from public.sinjira_world_travel_rules r
        where ((r.from_location_id=t.prev_location_id and r.to_location_id=t.location_id)
            or (r.bidirectional and r.from_location_id=t.location_id and r.to_location_id=t.prev_location_id))
          and r.canon_status='CANON'
          and (r.valid_from is null or r.valid_from<=t.prev_end)
          and (r.valid_until is null or r.valid_until>=t.starts_at)
      )
    union all
    select jsonb_build_object(
      'type','travel_rule_missing','direction','after','character_id',character_id,
      'story_presence_id',story_presence_id,'other_source_id',next_id,'other_title',next_title,
      'from_location_id',location_id,'to_location_id',next_location_id,
      'message','Aucune durée minimale CANON n’est définie dans l’Atlas pour vérifier le déplacement suivant.'
    )
    from transitions t
    where t.next_location_id is not null and t.location_id is not null
      and not private.sinjira_locations_compatible(t.location_id,t.next_location_id)
      and not exists(
        select 1 from public.sinjira_world_travel_rules r
        where ((r.from_location_id=t.location_id and r.to_location_id=t.next_location_id)
            or (r.bidirectional and r.from_location_id=t.next_location_id and r.to_location_id=t.location_id))
          and r.canon_status='CANON'
          and (r.valid_from is null or r.valid_from<=t.ends_at)
          and (r.valid_until is null or r.valid_until>=t.next_start)
      )
  )
  select v_warnings || coalesce(jsonb_agg(item),'[]'::jsonb)
  into v_warnings
  from missing;

  -- Avertissements bloquants pour la promotion : la continuité ne peut pas être garantie.
  with warn as (
    select jsonb_build_object(
      'type',case
        when sp.starts_at is null or sp.ends_at is null then 'time_unresolved'
        when sp.location_id is null then 'location_unresolved'
        when sp.certainty<>'confirmed' then 'presence_uncertain'
        when wl.canon_status is distinct from 'CANON' then 'location_not_canon'
        else 'continuity_unresolved'
      end,
      'character_id',sp.character_id,
      'story_presence_id',sp.id,
      'location_name',sp.location_name,
      'message',case
        when sp.starts_at is null or sp.ends_at is null then 'La présence doit avoir un début et une fin avant canonisation.'
        when sp.location_id is null then 'Le lieu doit être relié à l’Atlas canonique avant canonisation.'
        when sp.certainty<>'confirmed' then 'La présence doit être confirmée avant canonisation.'
        when wl.canon_status is distinct from 'CANON' then 'Le lieu du segment doit être CANON dans l’Atlas avant canonisation.'
        else 'La continuité de cette présence reste incomplète.'
      end
    ) as item
    from private.sinjira_effective_story_presence sp
    left join public.sinjira_world_locations wl on wl.id=sp.location_id
    where sp.story_id=p_story_id
      and (
        sp.starts_at is null
        or sp.ends_at is null
        or sp.location_id is null
        or sp.certainty<>'confirmed'
        or wl.canon_status is distinct from 'CANON'
      )
  )
  select v_warnings || coalesce(jsonb_agg(item),'[]'::jsonb) into v_warnings from warn;

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
  if coalesce((v_report->>'warnings')::integer,0)>0 then
    raise exception 'STORY_CONTINUITY_INCOMPLETE';
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

create or replace function public.admin_sinjira_unpublish_extended_story(
  p_story_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private,auth
as $$
declare
  v_admin uuid;
  v_story public.sinjira_extended_stories%rowtype;
begin
  v_admin:=private.require_sinjira_admin_aal2();

  select * into v_story
  from public.sinjira_extended_stories
  where id=p_story_id
  for update;

  if v_story.id is null then raise exception 'STORY_NOT_FOUND'; end if;

  if v_story.status='published' then
    update public.sinjira_extended_stories
    set status='validated',
        published_at=null
    where id=p_story_id
    returning * into v_story;
  end if;

  return jsonb_build_object(
    'ok',true,
    'story_id',v_story.id,
    'canon_status',v_story.canon_status,
    'status',v_story.status,
    'audience',v_story.audience,
    'published_at',v_story.published_at
  );
end;
$$;

revoke all on function private.sinjira_prevent_location_cycle() from public,anon,authenticated;
revoke all on function private.sinjira_location_is_ancestor(uuid,uuid) from public,anon,authenticated;
revoke all on function private.sinjira_locations_compatible(uuid,uuid) from public,anon,authenticated;
revoke all on function private.sinjira_story_continuity_report(uuid) from public,anon,authenticated;
revoke all on function public.admin_sinjira_story_continuity_check(uuid) from public,anon;
revoke all on function public.admin_sinjira_promote_extended_story(uuid) from public,anon;
revoke all on function public.admin_sinjira_publish_extended_story(uuid,text) from public,anon;
revoke all on function public.admin_sinjira_unpublish_extended_story(uuid) from public,anon;

grant execute on function public.admin_sinjira_story_continuity_check(uuid) to authenticated,service_role;
grant execute on function public.admin_sinjira_promote_extended_story(uuid) to authenticated,service_role;
grant execute on function public.admin_sinjira_publish_extended_story(uuid,text) to authenticated,service_role;
grant execute on function public.admin_sinjira_unpublish_extended_story(uuid) to authenticated,service_role;

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
comment on function public.admin_sinjira_publish_extended_story(uuid,text) is
  'Publication atomique d’une Chronique déjà CANON_ETENDU; revalide continuité, ancrage, période, lieu et contenu.';
comment on function public.admin_sinjira_unpublish_extended_story(uuid) is
  'Retire une Chronique de publication avant toute nouvelle modification éditoriale.';
