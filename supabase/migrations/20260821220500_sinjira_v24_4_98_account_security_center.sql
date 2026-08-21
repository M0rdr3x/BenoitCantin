-- SINJIRA™ V24.4.98 — Centre Ma sécurité, Mode Voyage et Bouclier de connexion
-- Canon : CAHIER_MAITRE_SINJIRA.md
-- Principe : protéger sans surveiller. Aucune adresse IP brute ni GPS ne sont stockés ici.

begin;

create table if not exists public.security_user_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  remember_usual_region boolean not null default false,
  sensitive_step_up boolean not null default true,
  notify_new_device boolean not null default true,
  notify_high_risk boolean not null default true,
  notify_security_changes boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.security_devices (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  device_key text not null check (char_length(device_key) between 16 and 128),
  display_name text not null default 'Appareil SINJIRA' check (char_length(display_name) between 1 and 120),
  device_type text not null default 'browser' check (device_type in ('browser','ios','android','tablet','other')),
  platform text not null default '' check (char_length(platform) <= 120),
  is_trusted boolean not null default false,
  is_primary boolean not null default false,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  last_session_id uuid,
  last_country_code text check (last_country_code is null or last_country_code ~ '^[A-Z]{2}$'),
  last_region_code text check (last_region_code is null or char_length(last_region_code) <= 80),
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, device_key)
);

create unique index if not exists security_devices_one_primary_idx
  on public.security_devices(user_id)
  where is_primary and revoked_at is null;
create index if not exists security_devices_user_seen_idx
  on public.security_devices(user_id, last_seen_at desc);

create table if not exists public.security_travel_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  destinations text[] not null default '{}'::text[],
  multi_country boolean not null default false,
  status text not null default 'active' check (status in ('active','cancelled','expired')),
  cancelled_at timestamptz,
  delete_after timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (ends_at > starts_at),
  check (ends_at <= starts_at + interval '180 days'),
  check (cardinality(destinations) between 1 and 12)
);
create index if not exists security_travel_plans_user_period_idx
  on public.security_travel_plans(user_id, starts_at, ends_at);

create table if not exists public.security_connection_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  device_id uuid references public.security_devices(id) on delete set null,
  occurred_at timestamptz not null default now(),
  event_type text not null default 'session_seen' check (event_type in ('session_seen','login_context','sensitive_access','challenge','blocked','approved','denied')),
  country_code text check (country_code is null or country_code ~ '^[A-Z]{2}$'),
  region_code text check (region_code is null or char_length(region_code) <= 80),
  client_type text not null default '' check (char_length(client_type) <= 80),
  platform text not null default '' check (char_length(platform) <= 120),
  action_name text not null default 'session' check (char_length(action_name) between 1 and 80),
  risk_score smallint not null default 0 check (risk_score between 0 and 100),
  risk_reasons text[] not null default '{}'::text[],
  outcome text not null default 'allow' check (outcome in ('allow','challenge','block','approved','denied')),
  retention_until timestamptz not null default (now() + interval '90 days')
);
create index if not exists security_connection_events_user_time_idx
  on public.security_connection_events(user_id, occurred_at desc);
create index if not exists security_connection_events_retention_idx
  on public.security_connection_events(retention_until);

create table if not exists public.security_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  device_id uuid references public.security_devices(id) on delete set null,
  event_type text not null check (char_length(event_type) between 1 and 80),
  summary text not null default '' check (char_length(summary) <= 300),
  severity text not null default 'info' check (severity in ('info','warning','critical')),
  created_at timestamptz not null default now(),
  retention_until timestamptz not null default (now() + interval '180 days')
);
create index if not exists security_events_user_time_idx
  on public.security_events(user_id, created_at desc);
create index if not exists security_events_retention_idx
  on public.security_events(retention_until);

create table if not exists public.security_connection_challenges (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  connection_event_id uuid references public.security_connection_events(id) on delete cascade,
  request_device_id uuid references public.security_devices(id) on delete set null,
  display_code smallint not null check (display_code between 10 and 99),
  status text not null default 'pending' check (status in ('pending','approved','denied','expired')),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default (now() + interval '10 minutes'),
  resolved_at timestamptz,
  resolved_device_id uuid references public.security_devices(id) on delete set null,
  delete_after timestamptz not null default (now() + interval '7 days')
);
create index if not exists security_connection_challenges_user_pending_idx
  on public.security_connection_challenges(user_id, created_at desc)
  where status = 'pending';
create index if not exists security_connection_challenges_delete_idx
  on public.security_connection_challenges(delete_after);

create or replace function public.security_touch_updated_at()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

for each row execute function public.security_touch_updated_at();
