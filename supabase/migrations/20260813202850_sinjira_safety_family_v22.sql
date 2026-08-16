create table if not exists public.account_safety_profiles(
  user_id uuid primary key references auth.users(id) on delete cascade,
  date_of_birth date not null,
  birthday_greeting_opt_in boolean not null default true,
  real_life_to_fiction_opt_in boolean not null default false,
  relationship_data_opt_in boolean not null default false,
  legacy_status text not null default 'active' check(legacy_status in ('active','memorial_pending','memorialized','locked')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists public.guardian_links(
  id uuid primary key default gen_random_uuid(),
  minor_user_id uuid not null references auth.users(id) on delete cascade,
  guardian_user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'pending' check(status in ('pending','verified','revoked')),
  guardian_role text not null default 'parent' check(guardian_role in ('parent','legal_guardian')),
  can_view_contact_metadata boolean not null default true,
  consented_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(minor_user_id,guardian_user_id)
);
create table if not exists public.private_family_links(
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  related_user_id uuid references auth.users(id) on delete set null,
  relationship_type text not null check(relationship_type in ('partner','spouse','separated','divorced','parent','child','sibling','other')),
  status text not null default 'pending' check(status in ('pending','confirmed','ended','revoked')),
  started_on date,
  ended_on date,
  mirror_to_fiction boolean not null default false,
  notes_private text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists public.legacy_directives(
  user_id uuid primary key references auth.users(id) on delete cascade,
  memorialize_account boolean not null default true,
  transfer_personal_story boolean not null default false,
  designated_family_user_id uuid references auth.users(id) on delete set null,
  final_story_tone text not null default 'peaceful' check(final_story_tone in ('heroic','tragic','peaceful','mysterious','open','custom')),
  final_story_instructions text,
  family_message text,
  public_memorial_opt_in boolean not null default true,
  updated_at timestamptz not null default now()
);
create table if not exists public.memorial_requests(
  id uuid primary key default gen_random_uuid(),
  subject_user_id uuid not null references auth.users(id) on delete cascade,
  requested_by_user_id uuid references auth.users(id) on delete set null,
  relationship_claim text,
  verification_note text,
  status text not null default 'pending' check(status in ('pending','verified','rejected','cancelled')),
  verified_by uuid references auth.users(id) on delete set null,
  verified_at timestamptz,
  date_of_death date,
  created_at timestamptz not null default now()
);
create table if not exists public.memorial_records(
  user_id uuid primary key references auth.users(id) on delete cascade,
  character_id uuid references public.characters(id) on delete set null,
  display_name text not null,
  memorial_year integer not null,
  date_of_death date,
  farewell_message text,
  family_message text,
  final_story_tone text,
  final_story_published boolean not null default false,
  published_at timestamptz,
  created_at timestamptz not null default now()
);
alter table public.account_safety_profiles enable row level security;
alter table public.guardian_links enable row level security;
alter table public.private_family_links enable row level security;
alter table public.legacy_directives enable row level security;
alter table public.memorial_requests enable row level security;
alter table public.memorial_records enable row level security;
drop policy if exists safety_own on public.account_safety_profiles;
create policy safety_own on public.account_safety_profiles for all to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists family_own on public.private_family_links;
create policy family_own on public.private_family_links for all to authenticated using(auth.uid()=owner_user_id) with check(auth.uid()=owner_user_id);
drop policy if exists legacy_own on public.legacy_directives;
create policy legacy_own on public.legacy_directives for all to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists guardian_read_parties on public.guardian_links;
create policy guardian_read_parties on public.guardian_links for select to authenticated using(auth.uid() in (minor_user_id,guardian_user_id));
drop policy if exists guardian_minor_request on public.guardian_links;
create policy guardian_minor_request on public.guardian_links for insert to authenticated with check(auth.uid()=minor_user_id and status='pending');
drop policy if exists guardian_guardian_update on public.guardian_links;
create policy guardian_guardian_update on public.guardian_links for update to authenticated using(auth.uid()=guardian_user_id) with check(auth.uid()=guardian_user_id);
drop policy if exists memorial_request_parties on public.memorial_requests;
create policy memorial_request_parties on public.memorial_requests for select to authenticated using(auth.uid()=subject_user_id or auth.uid()=requested_by_user_id);
drop policy if exists memorial_request_create on public.memorial_requests;
create policy memorial_request_create on public.memorial_requests for insert to authenticated with check(auth.uid()=requested_by_user_id);
drop policy if exists memorial_public on public.memorial_records;
create policy memorial_public on public.memorial_records for select to anon,authenticated using(published_at is not null);
create or replace function public.sinjira_age_band(p_user_id uuid default auth.uid()) returns text language sql stable security definer set search_path=public as $$
  select case
    when s.user_id is null then 'unverified'
    when s.legacy_status='memorialized' then 'memorial'
    when age(current_date,s.date_of_birth) < interval '12 years' then 'under12'
    when age(current_date,s.date_of_birth) < interval '18 years' then
      case when exists(select 1 from public.guardian_links g where g.minor_user_id=s.user_id and g.status='verified') then 'youth' else 'youth_pending' end
    else 'adult'
  end
  from (select p_user_id user_id) x left join public.account_safety_profiles s on s.user_id=x.user_id;
$$;
revoke all on function public.sinjira_age_band(uuid) from public,anon;
grant execute on function public.sinjira_age_band(uuid) to authenticated,service_role;
create or replace function public.sinjira_can_social_interact(p_a uuid,p_b uuid) returns boolean language sql stable security definer set search_path=public as $$
  select case
    when p_a is null or p_b is null then false
    when p_a=p_b then true
    when public.sinjira_age_band(p_a)='adult' and public.sinjira_age_band(p_b)='adult' then true
    when public.sinjira_age_band(p_a)='youth' and public.sinjira_age_band(p_b)='youth' then true
    else false end;
$$;
revoke all on function public.sinjira_can_social_interact(uuid,uuid) from public,anon;
grant execute on function public.sinjira_can_social_interact(uuid,uuid) to authenticated,service_role;
create or replace function public.sinjira_guardian_can_monitor(p_guardian uuid,p_minor uuid) returns boolean language sql stable security definer set search_path=public as $$
 select exists(select 1 from public.guardian_links g where g.guardian_user_id=p_guardian and g.minor_user_id=p_minor and g.status='verified' and g.can_view_contact_metadata=true);
$$;
revoke all on function public.sinjira_guardian_can_monitor(uuid,uuid) from public,anon;
grant execute on function public.sinjira_guardian_can_monitor(uuid,uuid) to authenticated,service_role;