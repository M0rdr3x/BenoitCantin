-- SINJIRA — comptes joueurs, sauvegardes et programme contributeur
-- Exécuter dans Supabase SQL Editor ou via supabase db push.

create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  pseudo text not null default 'Joueur SINJIRA',
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.research_consents (
  user_id uuid primary key references auth.users(id) on delete cascade,
  participate boolean not null default false,
  share_free_text boolean not null default false,
  consent_version text not null default 'sinjira-gameplay-v1',
  consented_at timestamptz,
  revoked_at timestamptz,
  updated_at timestamptz not null default now()
);

create table if not exists public.game_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  game_slug text not null default 'fracture-du-reseau-mere',
  title text not null default 'Partie Fracture du Réseau-Mère',
  status text not null default 'in_progress' check (status in ('in_progress','finished')),
  player_count integer check (player_count is null or player_count between 1 and 30),
  duration_minutes integer check (duration_minutes is null or duration_minutes between 1 and 1440),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.player_sheets (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null unique references public.game_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  fields jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.session_feedback (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null unique references public.game_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  rating integer check (rating is null or rating between 1 and 5),
  difficulty text check (difficulty is null or difficulty in ('Trop facile','Équilibrée','Trop difficile')),
  favorite_mechanic text,
  unclear_text text,
  extension_idea text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.player_reports (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references public.game_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  delivery text not null check (delivery in ('download','email')),
  generated_at timestamptz not null default now()
);

-- Tables internes. RLS est activé sans politique utilisateur.
-- Seules les Edge Functions utilisant service_role peuvent y accéder.
create table if not exists public.internal_gameplay_contributions (
  id uuid primary key default gen_random_uuid(),
  game_slug text not null,
  metrics jsonb not null,
  feedback jsonb not null default '{}'::jsonb,
  contribution_version text not null default '1.0',
  created_at timestamptz not null default now()
);

create table if not exists public.internal_contribution_ownership (
  contribution_id uuid primary key references public.internal_gameplay_contributions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  session_id uuid not null references public.game_sessions(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique(user_id, session_id)
);

create table if not exists public.contribution_receipts (
  session_id uuid primary key references public.game_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  contributed_at timestamptz not null default now(),
  contribution_version text not null default '1.0'
);

create table if not exists public.internal_admin_users (
  user_id uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

create index if not exists game_sessions_user_idx on public.game_sessions(user_id);
create index if not exists player_sheets_user_idx on public.player_sheets(user_id);
create index if not exists player_sheets_session_idx on public.player_sheets(session_id);
create index if not exists feedback_user_idx on public.session_feedback(user_id);
create index if not exists contribution_owner_user_idx on public.internal_contribution_ownership(user_id);

drop trigger if exists profiles_updated_at on public.profiles;
create trigger profiles_updated_at before update on public.profiles
for each row execute function public.set_updated_at();

drop trigger if exists consents_updated_at on public.research_consents;
create trigger consents_updated_at before update on public.research_consents
for each row execute function public.set_updated_at();

drop trigger if exists sessions_updated_at on public.game_sessions;
create trigger sessions_updated_at before update on public.game_sessions
for each row execute function public.set_updated_at();

drop trigger if exists sheets_updated_at on public.player_sheets;
create trigger sheets_updated_at before update on public.player_sheets
for each row execute function public.set_updated_at();

drop trigger if exists feedback_updated_at on public.session_feedback;
create trigger feedback_updated_at before update on public.session_feedback
for each row execute function public.set_updated_at();

-- Création automatique du profil et du consentement initial à l'inscription.
create or replace function public.handle_new_sinjira_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  wants_contribution boolean := coalesce((new.raw_user_meta_data ->> 'initial_contributor_opt_in')::boolean, false);
  wants_free_text boolean := coalesce((new.raw_user_meta_data ->> 'initial_share_free_text')::boolean, false);
begin
  insert into public.profiles(user_id, pseudo, display_name)
  values (
    new.id,
    coalesce(nullif(new.raw_user_meta_data ->> 'pseudo',''), 'Joueur SINJIRA'),
    nullif(new.raw_user_meta_data ->> 'display_name','')
  )
  on conflict (user_id) do nothing;

  insert into public.research_consents(
    user_id, participate, share_free_text, consent_version, consented_at
  )
  values (
    new.id,
    wants_contribution,
    wants_contribution and wants_free_text,
    'sinjira-gameplay-v1',
    case when wants_contribution then now() else null end
  )
  on conflict (user_id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created_sinjira on auth.users;
create trigger on_auth_user_created_sinjira
after insert on auth.users
for each row execute procedure public.handle_new_sinjira_user();

-- RLS
alter table public.profiles enable row level security;
alter table public.research_consents enable row level security;
alter table public.game_sessions enable row level security;
alter table public.player_sheets enable row level security;
alter table public.session_feedback enable row level security;
alter table public.player_reports enable row level security;
alter table public.contribution_receipts enable row level security;
alter table public.internal_gameplay_contributions enable row level security;
alter table public.internal_contribution_ownership enable row level security;
alter table public.internal_admin_users enable row level security;

-- Profils
drop policy if exists "profile select own" on public.profiles;
create policy "profile select own" on public.profiles for select to authenticated
using ((select auth.uid()) = user_id);
drop policy if exists "profile update own" on public.profiles;
create policy "profile update own" on public.profiles for update to authenticated
using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

-- Consentements
drop policy if exists "consent select own" on public.research_consents;
create policy "consent select own" on public.research_consents for select to authenticated
using ((select auth.uid()) = user_id);
drop policy if exists "consent insert own" on public.research_consents;
create policy "consent insert own" on public.research_consents for insert to authenticated
with check ((select auth.uid()) = user_id);
drop policy if exists "consent update own" on public.research_consents;
create policy "consent update own" on public.research_consents for update to authenticated
using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

-- Parties
drop policy if exists "sessions select own" on public.game_sessions;
create policy "sessions select own" on public.game_sessions for select to authenticated
using ((select auth.uid()) = user_id);
drop policy if exists "sessions insert own" on public.game_sessions;
create policy "sessions insert own" on public.game_sessions for insert to authenticated
with check ((select auth.uid()) = user_id);
drop policy if exists "sessions update own" on public.game_sessions;
create policy "sessions update own" on public.game_sessions for update to authenticated
using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "sessions delete own" on public.game_sessions;
create policy "sessions delete own" on public.game_sessions for delete to authenticated
using ((select auth.uid()) = user_id);

-- Fiches
drop policy if exists "sheets select own" on public.player_sheets;
create policy "sheets select own" on public.player_sheets for select to authenticated
using ((select auth.uid()) = user_id);
drop policy if exists "sheets insert own" on public.player_sheets;
create policy "sheets insert own" on public.player_sheets for insert to authenticated
with check ((select auth.uid()) = user_id);
drop policy if exists "sheets update own" on public.player_sheets;
create policy "sheets update own" on public.player_sheets for update to authenticated
using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "sheets delete own" on public.player_sheets;
create policy "sheets delete own" on public.player_sheets for delete to authenticated
using ((select auth.uid()) = user_id);

-- Feedback
drop policy if exists "feedback select own" on public.session_feedback;
create policy "feedback select own" on public.session_feedback for select to authenticated
using ((select auth.uid()) = user_id);
drop policy if exists "feedback insert own" on public.session_feedback;
create policy "feedback insert own" on public.session_feedback for insert to authenticated
with check ((select auth.uid()) = user_id);
drop policy if exists "feedback update own" on public.session_feedback;
create policy "feedback update own" on public.session_feedback for update to authenticated
using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "feedback delete own" on public.session_feedback;
create policy "feedback delete own" on public.session_feedback for delete to authenticated
using ((select auth.uid()) = user_id);

-- Journal de rapports
drop policy if exists "reports select own" on public.player_reports;
create policy "reports select own" on public.player_reports for select to authenticated
using ((select auth.uid()) = user_id);

-- Reçus de contribution
drop policy if exists "receipts select own" on public.contribution_receipts;
create policy "receipts select own" on public.contribution_receipts for select to authenticated
using ((select auth.uid()) = user_id);

-- AUCUNE politique anon/authenticated sur internal_*.

-- Transaction serveur pour enregistrer une contribution.
create or replace function public.record_sinjira_contribution(
  p_user_id uuid,
  p_session_id uuid,
  p_game_slug text,
  p_metrics jsonb,
  p_feedback jsonb,
  p_version text default '1.0'
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  contribution_uuid uuid := gen_random_uuid();
begin
  if exists (
    select 1 from public.internal_contribution_ownership
    where user_id = p_user_id and session_id = p_session_id
  ) then
    raise exception 'Cette partie a déjà été partagée.';
  end if;

  insert into public.internal_gameplay_contributions(
    id, game_slug, metrics, feedback, contribution_version
  ) values (
    contribution_uuid, p_game_slug, p_metrics, coalesce(p_feedback, '{}'::jsonb), p_version
  );

  insert into public.internal_contribution_ownership(
    contribution_id, user_id, session_id
  ) values (
    contribution_uuid, p_user_id, p_session_id
  );

  insert into public.contribution_receipts(
    session_id, user_id, contribution_version
  ) values (
    p_session_id, p_user_id, p_version
  )
  on conflict (session_id) do update set
    contributed_at = now(),
    contribution_version = excluded.contribution_version;

  return contribution_uuid;
end;
$$;

revoke all on function public.record_sinjira_contribution(uuid,uuid,text,jsonb,jsonb,text) from public, anon, authenticated;
grant execute on function public.record_sinjira_contribution(uuid,uuid,text,jsonb,jsonb,text) to service_role;

create or replace function public.revoke_sinjira_contributions(
  p_user_id uuid,
  p_session_id uuid default null
)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  removed integer := 0;
begin
  with targets as (
    select contribution_id, session_id
    from public.internal_contribution_ownership
    where user_id = p_user_id
      and (p_session_id is null or session_id = p_session_id)
  ),
  deleted as (
    delete from public.internal_gameplay_contributions c
    using targets t
    where c.id = t.contribution_id
    returning c.id
  )
  select count(*) into removed from deleted;

  delete from public.contribution_receipts
  where user_id = p_user_id
    and (p_session_id is null or session_id = p_session_id);

  return removed;
end;
$$;

revoke all on function public.revoke_sinjira_contributions(uuid,uuid) from public, anon, authenticated;
grant execute on function public.revoke_sinjira_contributions(uuid,uuid) to service_role;
