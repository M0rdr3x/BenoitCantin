-- SINJIRA™ V24.4.12 — compatibilité autonome de la sécurité V22/V24.
-- Rend le dépôt reconstruisible sans dépendre d'objets présents uniquement dans l'ancienne production.

create table if not exists public.account_safety_profiles(
  user_id uuid primary key references auth.users(id) on delete cascade,
  date_of_birth date not null,
  sex text,
  birthday_greeting_opt_in boolean not null default true,
  real_life_to_fiction_opt_in boolean not null default false,
  relationship_data_opt_in boolean not null default false,
  legacy_status text not null default 'active',
  phone_validation_status text not null default 'unverified',
  phone_line_type text,
  phone_factor_verified_at timestamptz,
  public_birthday_opt_in boolean not null default false,
  relationship_status text not null default 'not_set',
  relationship_status_updated_at timestamptz,
  birthday_public_opt_in boolean not null default false,
  phone_screening_status text not null default 'not_checked',
  phone_screened_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.account_safety_profiles add column if not exists sex text;
alter table public.account_safety_profiles add column if not exists phone_validation_status text not null default 'unverified';
alter table public.account_safety_profiles add column if not exists phone_line_type text;
alter table public.account_safety_profiles add column if not exists phone_factor_verified_at timestamptz;
alter table public.account_safety_profiles add column if not exists public_birthday_opt_in boolean not null default false;
alter table public.account_safety_profiles add column if not exists relationship_status text not null default 'not_set';
alter table public.account_safety_profiles add column if not exists relationship_status_updated_at timestamptz;
alter table public.account_safety_profiles add column if not exists birthday_public_opt_in boolean not null default false;
alter table public.account_safety_profiles add column if not exists phone_screening_status text not null default 'not_checked';
alter table public.account_safety_profiles add column if not exists phone_screened_at timestamptz;
alter table public.account_safety_profiles drop constraint if exists account_safety_profiles_sex_check;
alter table public.account_safety_profiles add constraint account_safety_profiles_sex_check check(sex is null or sex in('female','male'));
alter table public.account_safety_profiles enable row level security;

create table if not exists public.guardian_links(
  id uuid primary key default gen_random_uuid(),
  minor_user_id uuid not null references auth.users(id) on delete cascade,
  guardian_user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'pending' check(status in('pending','verified','revoked')),
  guardian_role text not null default 'parent' check(guardian_role in('parent','legal_guardian')),
  can_view_contact_metadata boolean not null default true,
  consented_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(minor_user_id,guardian_user_id)
);
create index if not exists guardian_links_guardian_user_id_idx on public.guardian_links(guardian_user_id);
alter table public.guardian_links enable row level security;
drop policy if exists guardian_read_parties on public.guardian_links;
create policy guardian_read_parties on public.guardian_links for select to authenticated using(auth.uid()=minor_user_id or auth.uid()=guardian_user_id);
drop policy if exists guardian_minor_request on public.guardian_links;
create policy guardian_minor_request on public.guardian_links for insert to authenticated with check(auth.uid()=minor_user_id and status='pending');
drop policy if exists guardian_guardian_update on public.guardian_links;
create policy guardian_guardian_update on public.guardian_links for update to authenticated using(auth.uid()=guardian_user_id) with check(auth.uid()=guardian_user_id);

create table if not exists public.sinjira_security_settings(
  singleton_id integer primary key default 1 check(singleton_id=1),
  require_phone_mfa boolean not null default false,
  require_mobile_line boolean not null default true,
  youth_requires_guardian boolean not null default true,
  updated_at timestamptz not null default now()
);
insert into public.sinjira_security_settings(singleton_id,require_phone_mfa,require_mobile_line,youth_requires_guardian)
values(1,false,true,true) on conflict(singleton_id) do nothing;
alter table public.sinjira_security_settings enable row level security;
revoke all on public.sinjira_security_settings from anon,authenticated;
grant select on public.sinjira_security_settings to service_role;

create or replace function public.sinjira_phone_factor_verified(p_user_id uuid default auth.uid())
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select exists(select 1 from auth.mfa_factors f where f.user_id=p_user_id and f.factor_type::text='phone' and f.status::text='verified');
$$;
revoke all on function public.sinjira_phone_factor_verified(uuid) from public,anon;
grant execute on function public.sinjira_phone_factor_verified(uuid) to authenticated,service_role;

create or replace function public.sinjira_mfa_access_allowed(p_user_id uuid default auth.uid())
returns boolean
language plpgsql
stable
security definer
set search_path=public,auth
as $$
declare cfg public.sinjira_security_settings%rowtype; line_ok boolean;
begin
  select * into cfg from public.sinjira_security_settings where singleton_id=1;
  if coalesce(cfg.require_phone_mfa,false)=false then return true; end if;
  if p_user_id is null or p_user_id<>auth.uid() then return false; end if;
  if coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then return false; end if;
  if not public.sinjira_phone_factor_verified(p_user_id) then return false; end if;
  if coalesce(cfg.require_mobile_line,true)=false then return true; end if;
  select (s.phone_validation_status='approved' and s.phone_line_type='mobile') into line_ok from public.account_safety_profiles s where s.user_id=p_user_id;
  return coalesce(line_ok,false);
end;
$$;
revoke all on function public.sinjira_mfa_access_allowed(uuid) from public,anon;
grant execute on function public.sinjira_mfa_access_allowed(uuid) to authenticated,service_role;

-- Lecture du propre profil autorisée; l'écriture directe des attributs de sécurité est interdite.
drop policy if exists safety_own on public.account_safety_profiles;
drop policy if exists safety_own_read on public.account_safety_profiles;
create policy safety_own_read on public.account_safety_profiles for select to authenticated using(auth.uid()=user_id);
revoke insert,delete,update on public.account_safety_profiles from authenticated;
grant select on public.account_safety_profiles to authenticated;
grant update(birthday_greeting_opt_in,real_life_to_fiction_opt_in,relationship_data_opt_in,public_birthday_opt_in,birthday_public_opt_in,relationship_status,relationship_status_updated_at) on public.account_safety_profiles to authenticated;
grant all on public.account_safety_profiles to service_role;

revoke all on public.guardian_links from anon;
grant select,insert,update on public.guardian_links to authenticated;
grant all on public.guardian_links to service_role;
