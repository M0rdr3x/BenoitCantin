-- SINJIRA V28 : marque-pages, extraits surlignés et notes STRICTEMENT privés.
-- Ne contient aucune édition intégrale du roman : seulement des repères personnels.
create table if not exists public.sinjira_reader_marks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  novel_id uuid not null references public.sinjira_novels(id) on delete cascade,
  page integer not null check (page between 1 and 520),
  kind text not null check (kind in ('bookmark','highlight','note')),
  quote text not null default '' check (char_length(quote) <= 280),
  note text not null default '' check (char_length(note) <= 1500),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint sinjira_reader_marks_valid_content check (
    (kind='bookmark' and quote='' and note='') or
    (kind='highlight' and char_length(btrim(quote)) between 1 and 280 and note='') or
    (kind='note' and char_length(btrim(note)) between 1 and 1500)
  )
);
comment on table public.sinjira_reader_marks is
 'Notes, surlignages et marque-pages privés du lecteur : aucune donnée du PDF intégral ni partage public.';
alter table public.sinjira_reader_marks enable row level security;
revoke all on table public.sinjira_reader_marks from public, anon;
grant select, insert, update, delete on table public.sinjira_reader_marks to authenticated;
create index if not exists sinjira_reader_marks_user_novel_page_idx
  on public.sinjira_reader_marks (user_id, novel_id, page, created_at);
create unique index if not exists sinjira_reader_marks_one_bookmark_per_page
  on public.sinjira_reader_marks (user_id, novel_id, page) where kind='bookmark';
drop policy if exists "sinjira reader marks select own" on public.sinjira_reader_marks;
create policy "sinjira reader marks select own" on public.sinjira_reader_marks for select
  to authenticated using (user_id = (select auth.uid()));
drop policy if exists "sinjira reader marks insert own" on public.sinjira_reader_marks;
create policy "sinjira reader marks insert own" on public.sinjira_reader_marks for insert
  to authenticated with check (user_id = (select auth.uid()));
drop policy if exists "sinjira reader marks update own" on public.sinjira_reader_marks;
create policy "sinjira reader marks update own" on public.sinjira_reader_marks for update
  to authenticated using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));
drop policy if exists "sinjira reader marks delete own" on public.sinjira_reader_marks;
create policy "sinjira reader marks delete own" on public.sinjira_reader_marks for delete
  to authenticated using (user_id = (select auth.uid()));
