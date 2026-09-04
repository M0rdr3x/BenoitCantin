-- SINJIRA V25 — Fondation Emploi
-- L'humain avant tout : ce module est volontaire, privé par défaut et séparé
-- du Registre personnel, de Rencontres et des signaux de sécurité/voyage.

create table if not exists public.employment_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  professional_title text,
  summary text,
  search_status text not null default 'not_looking'
    check (search_status in ('not_looking','open','actively_looking')),
  preferred_location text,
  remote_preference text not null default 'flexible'
    check (remote_preference in ('onsite','hybrid','remote','flexible')),
  skills text[] not null default '{}'::text[]
    check (cardinality(skills) <= 30)
    check (char_length(array_to_string(skills, ',')) <= 2400),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (professional_title is null or char_length(professional_title) <= 120),
  check (summary is null or char_length(summary) <= 3000),
  check (preferred_location is null or char_length(preferred_location) <= 160)
);

comment on table public.employment_profiles is
  'Profil professionnel privé et volontaire. Ne doit pas être enrichi automatiquement depuis le Registre personnel, Rencontres, les données de sécurité/voyage, ni utilisé pour la publicité sans consentement séparé.';
comment on column public.employment_profiles.skills is
  'Compétences saisies volontairement par la personne; aucune inférence automatique depuis les autres modules SINJIRA.';

create table if not exists public.employment_applications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  employer_name text not null check (char_length(employer_name) between 1 and 160),
  role_title text not null check (char_length(role_title) between 1 and 160),
  location_label text check (location_label is null or char_length(location_label) <= 160),
  source_url text check (
    source_url is null or (
      char_length(source_url) <= 2048 and
      source_url ~* '^https?://'
    )
  ),
  status text not null default 'saved'
    check (status in ('saved','applied','interview','offer','rejected','withdrawn','accepted')),
  applied_on date,
  next_step_on date,
  private_notes text check (private_notes is null or char_length(private_notes) <= 5000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists employment_applications_user_created_idx
  on public.employment_applications (user_id, created_at desc);
create index if not exists employment_applications_user_status_idx
  on public.employment_applications (user_id, status);

comment on table public.employment_applications is
  'Suivi personnel de candidatures saisi par la personne. SINJIRA ne fabrique aucune offre et ne recopie pas ce contenu vers le Registre personnel, Rencontres, Histoire de vie, la sécurité ou la publicité.';

alter table public.employment_profiles enable row level security;
alter table public.employment_profiles force row level security;
alter table public.employment_applications enable row level security;
alter table public.employment_applications force row level security;

revoke all on table public.employment_profiles from public, anon;
revoke all on table public.employment_applications from public, anon;
grant select, insert, update, delete on table public.employment_profiles to authenticated;
grant select, insert, update, delete on table public.employment_applications to authenticated;

create policy employment_profiles_select_own
  on public.employment_profiles for select to authenticated
  using ((select auth.uid()) = user_id);
create policy employment_profiles_insert_own
  on public.employment_profiles for insert to authenticated
  with check ((select auth.uid()) = user_id);
create policy employment_profiles_update_own
  on public.employment_profiles for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
create policy employment_profiles_delete_own
  on public.employment_profiles for delete to authenticated
  using ((select auth.uid()) = user_id);

create policy employment_applications_select_own
  on public.employment_applications for select to authenticated
  using ((select auth.uid()) = user_id);
create policy employment_applications_insert_own
  on public.employment_applications for insert to authenticated
  with check ((select auth.uid()) = user_id);
create policy employment_applications_update_own
  on public.employment_applications for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
create policy employment_applications_delete_own
  on public.employment_applications for delete to authenticated
  using ((select auth.uid()) = user_id);
