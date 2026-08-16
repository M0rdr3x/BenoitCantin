-- SINJIRA™ — reconstruction historique des romans V21/V22
-- Ces tables existent déjà en production. Le timestamp est volontairement
-- antérieur au cutoff du ledger afin que le workspace de production ne renvoie
-- pas ce DDL vers une base qui le possède déjà.

create extension if not exists pgcrypto;

create table if not exists public.sinjira_novels (
  id uuid default gen_random_uuid() not null,
  slug text not null,
  title text not null,
  subtitle text,
  description text,
  status text default 'draft'::text not null,
  cover_url text,
  public_path text,
  demo_path text,
  comments_enabled boolean default true not null,
  sort_order integer default 100 not null,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  constraint sinjira_novels_pkey primary key (id),
  constraint sinjira_novels_slug_key unique (slug),
  constraint sinjira_novels_status_check check (status = any (array['draft'::text,'announced'::text,'published'::text,'archived'::text]))
);
alter table public.sinjira_novels enable row level security;
drop policy if exists "sinjira novels public read" on public.sinjira_novels;
create policy "sinjira novels public read" on public.sinjira_novels for select to anon,authenticated
using (status=any(array['announced'::text,'published'::text]));

create table if not exists public.sinjira_reader_library (
  user_id uuid not null,
  novel_id uuid not null,
  last_opened_at timestamptz default now() not null,
  last_page integer default 1 not null,
  progress_percent integer default 0 not null,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
  constraint sinjira_reader_library_pkey primary key (user_id,novel_id),
  constraint sinjira_reader_library_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade,
  constraint sinjira_reader_library_novel_id_fkey foreign key (novel_id) references public.sinjira_novels(id) on delete cascade,
  constraint sinjira_reader_library_last_page_check check (last_page>=1 and last_page<=10000),
  constraint sinjira_reader_library_progress_percent_check check (progress_percent>=0 and progress_percent<=100)
);
create index if not exists fkidx_sinjira_reader_novel on public.sinjira_reader_library(novel_id);
create index if not exists sinjira_reader_user_idx on public.sinjira_reader_library(user_id,last_opened_at desc);
alter table public.sinjira_reader_library enable row level security;
drop policy if exists "sinjira reader library own" on public.sinjira_reader_library;
create policy "sinjira reader library own" on public.sinjira_reader_library for all to authenticated
using ((select auth.uid())=user_id)
with check ((select auth.uid())=user_id);
