-- SINJIRA™ — reconstruction historique V21/V22
--
-- Ces tables existent déjà en production Supabase mais leur DDL d'origine n'était
-- plus présent dans l'historique GitHub. Ce fichier restaure un historique autonome
-- pour les installations neuves et les validations de reconstruction.
--
-- IMPORTANT : son timestamp est antérieur au cutoff du ledger de production.
-- scripts/build_supabase_production_workspace.py ne l'envoie donc pas comme DDL
-- vers la production déjà synchronisée.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Préférences privées et événements de vie
-- ---------------------------------------------------------------------------
create table if not exists public.account_legacy_preferences (
  user_id uuid not null,
  account_after_death text default 'memorialize'::text not null,
  final_story_tone text default 'peaceful'::text not null,
  final_story_custom_note text,
  memorial_public_opt_in boolean default true not null,
  transfer_private_story_to_family boolean default false not null,
  legacy_contact_user_id uuid,
  farewell_note text,
  family_note text,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  constraint account_legacy_preferences_pkey primary key (user_id),
  constraint account_legacy_preferences_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade,
  constraint account_legacy_preferences_legacy_contact_user_id_fkey foreign key (legacy_contact_user_id) references auth.users(id) on delete set null
);
create index if not exists fkidx_account_legacy_contact on public.account_legacy_preferences(legacy_contact_user_id);
alter table public.account_legacy_preferences enable row level security;
drop policy if exists legacy_pref_own on public.account_legacy_preferences;
create policy legacy_pref_own on public.account_legacy_preferences for all to authenticated
using ((select auth.uid())=user_id)
with check ((select auth.uid())=user_id);

create table if not exists public.private_life_events (
  id uuid default gen_random_uuid() not null,
  user_id uuid not null,
  event_type text not null,
  related_user_id uuid,
  event_date date not null,
  use_in_private_story boolean default false not null,
  notes_private text,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  constraint private_life_events_pkey primary key (id),
  constraint private_life_events_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade,
  constraint private_life_events_related_user_id_fkey foreign key (related_user_id) references auth.users(id) on delete set null
);
create index if not exists fkidx_private_life_user on public.private_life_events(user_id);
create index if not exists fkidx_private_life_related_user on public.private_life_events(related_user_id);
alter table public.private_life_events enable row level security;
drop policy if exists life_events_own on public.private_life_events;
create policy life_events_own on public.private_life_events for all to authenticated
using ((select auth.uid())=user_id)
with check ((select auth.uid())=user_id);

-- ---------------------------------------------------------------------------
-- Ancienne couche Lecteur / Registre (conservée pour compatibilité et données)
-- ---------------------------------------------------------------------------
create table if not exists public.reader_works (
  id uuid default gen_random_uuid() not null,
  slug text not null,
  title text not null,
  series_title text,
  volume_label text,
  description text,
  cover_url text,
  public_path text,
  status text default 'active'::text not null,
  comments_enabled boolean default true not null,
  sort_order integer default 100 not null,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  constraint reader_works_pkey primary key (id),
  constraint reader_works_slug_key unique (slug),
  constraint reader_works_status_check check (status = any (array['draft'::text,'active'::text,'archived'::text]))
);
alter table public.reader_works enable row level security;
drop policy if exists reader_works_anon_read on public.reader_works;
create policy reader_works_anon_read on public.reader_works for select to anon using (status='active'::text);
drop policy if exists reader_works_authenticated_read on public.reader_works;
create policy reader_works_authenticated_read on public.reader_works for select to authenticated
using (status='active'::text or public.is_sinjira_admin((select auth.uid())));

create table if not exists public.reader_character_submissions (
  id uuid default gen_random_uuid() not null,
  user_id uuid not null,
  account_pseudo text,
  account_email text,
  questionnaire_version text default 'web-2.0'::text not null,
  answers jsonb default '{}'::jsonb not null,
  status text default 'submitted'::text not null,
  ai_draft jsonb,
  ai_model text,
  ai_generated_at timestamptz,
  ai_error text,
  source_data_deleted_at timestamptz,
  admin_note text,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  ai_consent boolean default false not null,
  ai_consent_at timestamptz,
  constraint reader_character_submissions_pkey primary key (id),
  constraint reader_character_submissions_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade,
  constraint reader_character_submissions_status_check check (status = any (array['submitted'::text,'ai_draft_ready'::text,'in_review'::text,'approved'::text,'rejected'::text,'character_assigned'::text,'source_deleted'::text]))
);
create index if not exists reader_character_submissions_status_idx on public.reader_character_submissions(status,created_at desc);
create index if not exists reader_character_submissions_user_idx on public.reader_character_submissions(user_id,created_at desc);
alter table public.reader_character_submissions enable row level security;
drop policy if exists reader_character_submissions_admin_read on public.reader_character_submissions;
create policy reader_character_submissions_admin_read on public.reader_character_submissions for select to authenticated
using (public.is_sinjira_admin((select auth.uid())));
drop policy if exists reader_character_submissions_insert_own on public.reader_character_submissions;
create policy reader_character_submissions_insert_own on public.reader_character_submissions for insert to authenticated
with check (user_id=(select auth.uid()));

create table if not exists public.reader_characters (
  id uuid default gen_random_uuid() not null,
  user_id uuid not null,
  work_id uuid,
  character_name text not null,
  status text default 'planned'::text not null,
  role_summary text,
  official_description text,
  appearance_summary text,
  personality_summary text,
  first_appearance text,
  placement_note text,
  is_public boolean default false not null,
  source_data_deleted_at timestamptz,
  created_by uuid,
  updated_by uuid,
  published_at timestamptz,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  source_submission_id uuid,
  bible_json jsonb default '{}'::jsonb not null,
  ai_model text,
  ai_generated_at timestamptz,
  admin_approved_at timestamptz,
  constraint reader_characters_pkey primary key (id),
  constraint reader_characters_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade,
  constraint reader_characters_work_id_fkey foreign key (work_id) references public.reader_works(id) on delete set null,
  constraint reader_characters_created_by_fkey foreign key (created_by) references auth.users(id) on delete set null,
  constraint reader_characters_updated_by_fkey foreign key (updated_by) references auth.users(id) on delete set null,
  constraint reader_characters_source_submission_id_fkey foreign key (source_submission_id) references public.reader_character_submissions(id) on delete set null,
  constraint reader_characters_status_check check (status = any (array['planned'::text,'draft'::text,'approved'::text,'published'::text,'archived'::text]))
);
create index if not exists fkidx_reader_characters_created_by on public.reader_characters(created_by);
create index if not exists fkidx_reader_characters_updated_by on public.reader_characters(updated_by);
create unique index if not exists reader_characters_source_submission_unique on public.reader_characters(source_submission_id) where source_submission_id is not null;
create index if not exists reader_characters_user_idx on public.reader_characters(user_id,status);
create index if not exists reader_characters_work_idx on public.reader_characters(work_id,status);
alter table public.reader_characters enable row level security;
drop policy if exists reader_characters_anon_read on public.reader_characters;
create policy reader_characters_anon_read on public.reader_characters for select to anon
using (is_public=true and status='published'::text);
drop policy if exists reader_characters_authenticated_read on public.reader_characters;
create policy reader_characters_authenticated_read on public.reader_characters for select to authenticated
using (public.is_sinjira_admin((select auth.uid())) or user_id=(select auth.uid()) or (is_public=true and status='published'::text));

create table if not exists public.reader_comments (
  id uuid default gen_random_uuid() not null,
  work_id uuid not null,
  user_id uuid not null,
  author_display_name text default 'Lecteur SINJIRA'::text not null,
  author_avatar_path text,
  chapter_ref text,
  body text not null,
  is_spoiler boolean default false not null,
  status text default 'pending'::text not null,
  moderation_note text,
  moderated_by uuid,
  moderated_at timestamptz,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  constraint reader_comments_pkey primary key (id),
  constraint reader_comments_work_id_fkey foreign key (work_id) references public.reader_works(id) on delete cascade,
  constraint reader_comments_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade,
  constraint reader_comments_moderated_by_fkey foreign key (moderated_by) references auth.users(id) on delete set null,
  constraint reader_comments_status_check check (status = any (array['pending'::text,'approved'::text,'refused'::text,'deleted'::text])),
  constraint reader_comments_body_check check (char_length(body)>=1 and char_length(body)<=3000),
  constraint reader_comments_body_length_check check (char_length(body)>=2 and char_length(body)<=3000)
);
create index if not exists fkidx_reader_comments_moderated_by on public.reader_comments(moderated_by);
create index if not exists reader_comments_user_idx on public.reader_comments(user_id,created_at desc);
create index if not exists reader_comments_work_status_idx on public.reader_comments(work_id,status,created_at desc);
alter table public.reader_comments enable row level security;
drop policy if exists reader_comments_anon_read on public.reader_comments;
create policy reader_comments_anon_read on public.reader_comments for select to anon using (status='approved'::text);
drop policy if exists reader_comments_authenticated_read on public.reader_comments;
create policy reader_comments_authenticated_read on public.reader_comments for select to authenticated
using (public.is_sinjira_admin((select auth.uid())) or user_id=(select auth.uid()) or status='approved'::text);
drop policy if exists reader_comments_delete_own on public.reader_comments;
create policy reader_comments_delete_own on public.reader_comments for delete to authenticated
using (user_id=(select auth.uid()) and status=any(array['pending'::text,'approved'::text,'refused'::text]));
drop policy if exists reader_comments_insert_own on public.reader_comments;
create policy reader_comments_insert_own on public.reader_comments for insert to authenticated
with check (user_id=(select auth.uid()) and status='pending'::text);
drop policy if exists reader_comments_update_own_pending on public.reader_comments;
create policy reader_comments_update_own_pending on public.reader_comments for update to authenticated
using (user_id=(select auth.uid()) and status='pending'::text)
with check (user_id=(select auth.uid()) and status='pending'::text);

create table if not exists public.registry_account_links (
  id uuid default gen_random_uuid() not null,
  user_id uuid not null,
  account_pseudo_snapshot text,
  account_email_snapshot text,
  status text default 'questionnaire_received'::text not null,
  target_work_id uuid,
  target_note text,
  character_id uuid,
  source_data_deleted_at timestamptz,
  admin_note text,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  constraint registry_account_links_pkey primary key (id),
  constraint registry_account_links_user_id_key unique (user_id),
  constraint registry_account_links_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade,
  constraint registry_account_links_target_work_id_fkey foreign key (target_work_id) references public.reader_works(id) on delete set null,
  constraint registry_account_links_character_id_fkey foreign key (character_id) references public.reader_characters(id) on delete set null,
  constraint registry_account_links_status_check check (status = any (array['questionnaire_received'::text,'under_review'::text,'character_creation'::text,'waiting_future_novel'::text,'assigned'::text,'published'::text,'closed'::text]))
);
create index if not exists fkidx_registry_links_character on public.registry_account_links(character_id);
create index if not exists fkidx_registry_links_target_work on public.registry_account_links(target_work_id);
create index if not exists registry_account_links_status_idx on public.registry_account_links(status,updated_at desc);
alter table public.registry_account_links enable row level security;
drop policy if exists registry_links_read_authorized on public.registry_account_links;
create policy registry_links_read_authorized on public.registry_account_links for select to authenticated
using (user_id=(select auth.uid()) or public.is_sinjira_admin((select auth.uid())));

-- ---------------------------------------------------------------------------
-- Ancienne couche SINJIRA personnages / commentaires (compatibilité historique)
-- ---------------------------------------------------------------------------
create table if not exists public.sinjira_character_applications (
  id uuid default gen_random_uuid() not null,
  user_id uuid not null,
  status text default 'submitted'::text not null,
  account_pseudo_snapshot text,
  account_email_snapshot text,
  questionnaire_version text default 'registre-web-2.0'::text not null,
  answers jsonb default '{}'::jsonb not null,
  photo_path text,
  ai_model text,
  ai_error text,
  ai_generated_at timestamptz,
  submitted_at timestamptz default now() not null,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  source_purged_at timestamptz,
  ai_consent boolean default false not null,
  ai_consent_at timestamptz,
  ai_prompt_version text,
  constraint sinjira_character_applications_pkey primary key (id),
  constraint sinjira_character_applications_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade,
  constraint sinjira_character_applications_status_check check (status = any (array['submitted'::text,'ai_processing'::text,'ai_draft'::text,'admin_review'::text,'approved'::text,'assigned'::text,'future'::text,'rejected'::text]))
);
create index if not exists sinjira_character_app_user_idx on public.sinjira_character_applications(user_id,submitted_at desc);
create index if not exists sinjira_character_applications_status_idx on public.sinjira_character_applications(status,submitted_at desc);
alter table public.sinjira_character_applications enable row level security;
drop policy if exists "sinjira applications own insert" on public.sinjira_character_applications;
create policy "sinjira applications own insert" on public.sinjira_character_applications for insert to authenticated
with check ((select auth.uid())=user_id and status='submitted'::text);
drop policy if exists "sinjira applications own select" on public.sinjira_character_applications;
create policy "sinjira applications own select" on public.sinjira_character_applications for select to authenticated
using ((select auth.uid())=user_id);

create table if not exists public.sinjira_characters (
  id uuid default gen_random_uuid() not null,
  application_id uuid not null,
  user_id uuid not null,
  status text default 'ai_draft'::text not null,
  canonical_name text,
  short_description text,
  narrative_role text,
  target_novel_id uuid,
  future_novel_note text,
  bible jsonb default '{}'::jsonb not null,
  admin_notes text,
  approved_by uuid,
  approved_at timestamptz,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  constraint sinjira_characters_pkey primary key (id),
  constraint sinjira_characters_application_id_key unique (application_id),
  constraint sinjira_characters_application_id_fkey foreign key (application_id) references public.sinjira_character_applications(id) on delete cascade,
  constraint sinjira_characters_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade,
  constraint sinjira_characters_target_novel_id_fkey foreign key (target_novel_id) references public.sinjira_novels(id) on delete set null,
  constraint sinjira_characters_approved_by_fkey foreign key (approved_by) references auth.users(id) on delete set null,
  constraint sinjira_characters_status_check check (status = any (array['ai_draft'::text,'review'::text,'approved'::text,'assigned'::text,'future'::text,'published'::text,'archived'::text]))
);
create index if not exists fkidx_sinjira_characters_approved_by on public.sinjira_characters(approved_by);
create index if not exists sinjira_characters_novel_idx on public.sinjira_characters(target_novel_id,status);
create index if not exists sinjira_characters_user_idx on public.sinjira_characters(user_id,status,updated_at desc);
alter table public.sinjira_characters enable row level security;
drop policy if exists "sinjira characters owner final read" on public.sinjira_characters;
create policy "sinjira characters owner final read" on public.sinjira_characters for select to authenticated
using ((select auth.uid())=user_id and status=any(array['approved'::text,'assigned'::text,'future'::text,'published'::text]));

create table if not exists public.sinjira_novel_comments (
  id uuid default gen_random_uuid() not null,
  novel_id uuid not null,
  user_id uuid not null,
  body text not null,
  spoiler boolean default false not null,
  status text default 'pending'::text not null,
  moderated_by uuid,
  moderated_at timestamptz,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  display_name_snapshot text default 'Lecteur SINJIRA'::text not null,
  constraint sinjira_novel_comments_pkey primary key (id),
  constraint sinjira_novel_comments_novel_id_fkey foreign key (novel_id) references public.sinjira_novels(id) on delete cascade,
  constraint sinjira_novel_comments_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade,
  constraint sinjira_novel_comments_moderated_by_fkey foreign key (moderated_by) references auth.users(id) on delete set null,
  constraint sinjira_novel_comments_status_check check (status = any (array['pending'::text,'approved'::text,'rejected'::text])),
  constraint sinjira_novel_comments_body_check check (char_length(body)>=3 and char_length(body)<=3000)
);
create index if not exists fkidx_sinjira_comments_moderated_by on public.sinjira_novel_comments(moderated_by);
create index if not exists sinjira_comments_novel_status_idx on public.sinjira_novel_comments(novel_id,status,created_at desc);
create index if not exists sinjira_novel_comments_user_idx on public.sinjira_novel_comments(user_id,created_at desc);
alter table public.sinjira_novel_comments enable row level security;
drop policy if exists "sinjira comments own delete" on public.sinjira_novel_comments;
create policy "sinjira comments own delete" on public.sinjira_novel_comments for delete to authenticated using ((select auth.uid())=user_id);
drop policy if exists "sinjira comments own insert" on public.sinjira_novel_comments;
create policy "sinjira comments own insert" on public.sinjira_novel_comments for insert to authenticated
with check ((select auth.uid())=user_id and status='pending'::text);
drop policy if exists "sinjira comments own pending update" on public.sinjira_novel_comments;
create policy "sinjira comments own pending update" on public.sinjira_novel_comments for update to authenticated
using ((select auth.uid())=user_id and status='pending'::text)
with check ((select auth.uid())=user_id and status='pending'::text);
drop policy if exists "sinjira comments read approved or own" on public.sinjira_novel_comments;
create policy "sinjira comments read approved or own" on public.sinjira_novel_comments for select to anon,authenticated
using (status='approved'::text or (select auth.uid())=user_id);
