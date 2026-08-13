-- SINJIRA V19 PRO — lecture, commentaires, workflow personnages et journal admin
alter table public.reader_library add column if not exists last_page integer;
alter table public.reader_library add column if not exists progress_percent integer;
alter table public.reader_library drop constraint if exists reader_library_last_page_check;
alter table public.reader_library add constraint reader_library_last_page_check check(last_page is null or last_page between 1 and 10000);
alter table public.reader_library drop constraint if exists reader_library_progress_check;
alter table public.reader_library add constraint reader_library_progress_check check(progress_percent is null or progress_percent between 0 and 100);

alter table public.novel_comments add column if not exists contains_spoilers boolean not null default false;
alter table public.novel_comments drop constraint if exists novel_comments_body_length;
alter table public.novel_comments add constraint novel_comments_body_length check(char_length(body) between 3 and 3000);
drop policy if exists comments_update_own_pending on public.novel_comments;
create policy comments_update_own_pending on public.novel_comments for update to authenticated using(auth.uid()=user_id and status='pending') with check(auth.uid()=user_id and status='pending');

create table if not exists public.character_status_events(
 id uuid primary key default gen_random_uuid(), submission_id uuid not null references public.character_submissions(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade, status text not null, note text, created_at timestamptz not null default now()
);
alter table public.character_status_events enable row level security;
drop policy if exists character_events_own_read on public.character_status_events;
create policy character_events_own_read on public.character_status_events for select to authenticated using(auth.uid()=user_id);
create index if not exists character_status_events_submission_idx on public.character_status_events(submission_id,created_at);

create table if not exists public.admin_audit_log(
 id bigserial primary key, admin_user_id uuid references auth.users(id) on delete set null, action text not null, entity_type text,
 entity_id text, summary text, metadata jsonb not null default '{}'::jsonb, created_at timestamptz not null default now()
);
alter table public.admin_audit_log enable row level security;
revoke all on public.admin_audit_log from anon,authenticated;
create index if not exists admin_audit_log_created_idx on public.admin_audit_log(created_at desc);

-- Initial timeline event for existing submissions that have no history.
insert into public.character_status_events(submission_id,user_id,status,note,created_at)
select s.id,s.user_id,s.status,'Dossier importé dans le suivi V19.',s.created_at from public.character_submissions s
where not exists(select 1 from public.character_status_events e where e.submission_id=s.id);
