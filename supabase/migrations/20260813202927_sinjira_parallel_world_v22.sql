create table if not exists public.parallel_world_memberships(
  character_id uuid primary key references public.characters(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  pioneer_number integer unique check(pioneer_number between 1 and 40),
  main_canon_eligible boolean not null default false,
  parallel_world_only boolean not null default true,
  joined_at timestamptz not null default now(),
  status text not null default 'active' check(status in ('active','paused','memorial'))
);
create table if not exists public.parallel_world_cycles(
  id uuid primary key default gen_random_uuid(),
  cycle_month date not null unique,
  title text not null,
  collective_story text,
  monthly_question text not null,
  response_mode text not null default 'solo_or_group' check(response_mode in ('solo','group','solo_or_group')),
  opens_at timestamptz not null,
  closes_at timestamptz not null,
  published_at timestamptz,
  status text not null default 'draft' check(status in ('draft','open','closed','published','archived')),
  created_at timestamptz not null default now()
);
create table if not exists public.parallel_groups(
  id uuid primary key default gen_random_uuid(),
  name text not null,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'active' check(status in ('active','closed')),
  created_at timestamptz not null default now()
);
create table if not exists public.parallel_group_members(
  group_id uuid not null references public.parallel_groups(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  character_id uuid not null references public.characters(id) on delete cascade,
  role text not null default 'member' check(role in ('owner','member')),
  joined_at timestamptz not null default now(),
  primary key(group_id,user_id)
);
create table if not exists public.parallel_cycle_responses(
  id uuid primary key default gen_random_uuid(),
  cycle_id uuid not null references public.parallel_world_cycles(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  character_id uuid not null references public.characters(id) on delete cascade,
  group_id uuid references public.parallel_groups(id) on delete set null,
  response_text text not null,
  response_kind text not null default 'solo' check(response_kind in ('solo','group')),
  submitted_at timestamptz not null default now(),
  unique(cycle_id,user_id)
);
create table if not exists public.parallel_story_installments(
  id uuid primary key default gen_random_uuid(),
  cycle_id uuid not null references public.parallel_world_cycles(id) on delete cascade,
  story_kind text not null check(story_kind in ('collective','individual')),
  character_id uuid references public.characters(id) on delete cascade,
  title text not null,
  content text not null,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  check((story_kind='collective' and character_id is null) or (story_kind='individual' and character_id is not null))
);
create table if not exists public.parallel_character_state(
  character_id uuid primary key references public.characters(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  life_state text not null default 'active' check(life_state in ('active','missing','memorial')),
  location_name text,
  faction_name text,
  reputation integer not null default 0,
  state_data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
create table if not exists public.fictional_relationships(
  id uuid primary key default gen_random_uuid(),
  character_a_id uuid not null references public.characters(id) on delete cascade,
  character_b_id uuid references public.characters(id) on delete set null,
  relationship_type text not null check(relationship_type in ('partner','spouse','separated','divorced','parent','child','sibling','friend','rival','other')),
  started_on date,
  ended_on date,
  source text not null default 'fictional' check(source in ('fictional','consented_real_event')),
  status text not null default 'active' check(status in ('pending','active','ended')),
  created_at timestamptz not null default now()
);
alter table public.parallel_world_memberships enable row level security;
alter table public.parallel_world_cycles enable row level security;
alter table public.parallel_groups enable row level security;
alter table public.parallel_group_members enable row level security;
alter table public.parallel_cycle_responses enable row level security;
alter table public.parallel_story_installments enable row level security;
alter table public.parallel_character_state enable row level security;
alter table public.fictional_relationships enable row level security;
create policy parallel_membership_own_read on public.parallel_world_memberships for select to authenticated using(auth.uid()=user_id);
create policy parallel_cycles_public_read on public.parallel_world_cycles for select to anon,authenticated using(published_at is not null or status='open');
create policy parallel_groups_member_read on public.parallel_groups for select to authenticated using(owner_user_id=auth.uid() or exists(select 1 from public.parallel_group_members m where m.group_id=id and m.user_id=auth.uid()));
create policy parallel_groups_owner_write on public.parallel_groups for all to authenticated using(owner_user_id=auth.uid()) with check(owner_user_id=auth.uid());
create policy parallel_group_members_read on public.parallel_group_members for select to authenticated using(user_id=auth.uid() or exists(select 1 from public.parallel_groups g where g.id=group_id and g.owner_user_id=auth.uid()));
create policy parallel_group_members_own_insert on public.parallel_group_members for insert to authenticated with check(user_id=auth.uid());
create policy parallel_responses_own on public.parallel_cycle_responses for all to authenticated using(user_id=auth.uid()) with check(user_id=auth.uid());
create policy parallel_stories_public on public.parallel_story_installments for select to anon,authenticated using(published_at is not null);
create policy parallel_state_own on public.parallel_character_state for select to authenticated using(user_id=auth.uid());
create policy fictional_relationships_participants_read on public.fictional_relationships for select to authenticated using(exists(select 1 from public.characters c where c.id in (character_a_id,character_b_id) and c.user_id=auth.uid()));
create or replace function public.assign_parallel_world_membership() returns trigger language plpgsql security definer set search_path=public as $$
declare n integer;
begin
  if new.status not in ('approved','assigned','future','published') then return new; end if;
  if exists(select 1 from public.parallel_world_memberships where character_id=new.id) then return new; end if;
  select min(gs) into n from generate_series(1,40) gs where not exists(select 1 from public.parallel_world_memberships p where p.pioneer_number=gs);
  insert into public.parallel_world_memberships(character_id,user_id,pioneer_number,main_canon_eligible,parallel_world_only)
  values(new.id,new.user_id,n,n is not null,n is null);
  insert into public.parallel_character_state(character_id,user_id) values(new.id,new.user_id) on conflict(character_id) do nothing;
  return new;
end $$;
drop trigger if exists trg_assign_parallel_world_membership on public.characters;
create trigger trg_assign_parallel_world_membership after insert or update of status on public.characters for each row execute function public.assign_parallel_world_membership();
create or replace function public.protect_parallel_character_life() returns trigger language plpgsql security definer set search_path=public as $$
begin
  if new.life_state='memorial' and old.life_state is distinct from 'memorial' then
    if not exists(select 1 from public.memorial_records m where m.character_id=new.character_id and m.published_at is not null) then
      raise exception 'Un personnage du Monde parallèle ne peut être placé en mémoire sans mémorial vérifié.';
    end if;
  end if;
  return new;
end $$;
drop trigger if exists trg_protect_parallel_character_life on public.parallel_character_state;
create trigger trg_protect_parallel_character_life before update of life_state on public.parallel_character_state for each row execute function public.protect_parallel_character_life();
