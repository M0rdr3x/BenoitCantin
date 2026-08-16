-- SINJIRA V18 — comptes lecteurs, commentaires et personnages des fans
create extension if not exists pgcrypto;

create table if not exists public.novels(
 id uuid primary key default gen_random_uuid(), slug text not null unique, title text not null, volume_label text,
 description text, status text not null default 'announced' check(status in('announced','demo','published','archived')),
 public_path text, demo_path text, comments_enabled boolean not null default true, sort_order integer not null default 100,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
insert into public.novels(slug,title,volume_label,description,status,public_path,demo_path,comments_enabled,sort_order)
values('la-cendre-du-jugement','La Cendre du Jugement','SINJIRA — Livre I','Premier roman de la franchise SINJIRA. La démo officielle contient le prologue et les trois premiers chapitres.','demo','/projets/sinjira/romans/index.html','/projets/sinjira/romans/lire-demo.html',true,10)
on conflict(slug) do update set title=excluded.title,volume_label=excluded.volume_label,description=excluded.description,status=excluded.status,public_path=excluded.public_path,demo_path=excluded.demo_path,comments_enabled=excluded.comments_enabled,sort_order=excluded.sort_order;

create table if not exists public.reader_library(
 user_id uuid not null references auth.users(id) on delete cascade, novel_id uuid not null references public.novels(id) on delete cascade,
 last_opened_at timestamptz not null default now(), created_at timestamptz not null default now(), primary key(user_id,novel_id)
);
create table if not exists public.novel_comments(
 id uuid primary key default gen_random_uuid(), novel_id uuid not null references public.novels(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade, display_name_snapshot text not null, body text not null,
 status text not null default 'pending' check(status in('pending','approved','refused','removed')),
 moderated_by uuid references auth.users(id) on delete set null, moderated_at timestamptz,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.character_submissions(
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 account_pseudo text, account_email text, status text not null default 'submitted' check(status in('submitted','ai_draft','author_review','approved','assigned','future','published','refused','archived')),
 source_payload jsonb, photo_path text, source_purged_at timestamptz, created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.characters(
 id uuid primary key default gen_random_uuid(), submission_id uuid unique references public.character_submissions(id) on delete set null,
 user_id uuid not null references auth.users(id) on delete cascade, public_name text, public_description text,
 status text not null default 'author_review' check(status in('ai_draft','author_review','approved','assigned','future','published','archived')),
 novel_id uuid references public.novels(id) on delete set null, novel_note text, bible jsonb not null default '{}'::jsonb,
 ai_generated boolean not null default false, visible_to_user boolean not null default true,
 canon_status text not null default 'PROVISOIRE' check(canon_status in('PROVISOIRE','CANON','SECRET_AUTEUR','A_ARBITRER')),
 canon_version text not null default 'v1.0',
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.character_generation_runs(
 id uuid primary key default gen_random_uuid(), submission_id uuid not null references public.character_submissions(id) on delete cascade,
 character_id uuid references public.characters(id) on delete set null, model text, status text not null, error_text text,
 created_at timestamptz not null default now()
);

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('sinjira-character-sources','sinjira-character-sources',false,10485760,array['image/jpeg','image/png','image/webp','image/avif','image/gif'])
on conflict(id) do update set public=false;

do $$ declare t text; begin foreach t in array array['novels','novel_comments','character_submissions','characters'] loop
 execute format('drop trigger if exists %I_updated_at on public.%I',t,t);
 execute format('create trigger %I_updated_at before update on public.%I for each row execute function public.set_updated_at()',t,t);
end loop; end $$;

alter table public.novels enable row level security;
alter table public.reader_library enable row level security;
alter table public.novel_comments enable row level security;
alter table public.character_submissions enable row level security;
alter table public.characters enable row level security;
alter table public.character_generation_runs enable row level security;

drop policy if exists novels_public_read on public.novels;
create policy novels_public_read on public.novels for select to anon,authenticated using(status in('announced','demo','published'));
drop policy if exists reader_library_own on public.reader_library;
create policy reader_library_own on public.reader_library for all to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);
drop policy if exists comments_read on public.novel_comments;
create policy comments_read on public.novel_comments for select to anon,authenticated using(status='approved' or auth.uid()=user_id);
drop policy if exists comments_insert_own on public.novel_comments;
create policy comments_insert_own on public.novel_comments for insert to authenticated with check(auth.uid()=user_id and status='pending');
drop policy if exists comments_delete_own_pending on public.novel_comments;
create policy comments_delete_own_pending on public.novel_comments for delete to authenticated using(auth.uid()=user_id and status='pending');
drop policy if exists submissions_own_read on public.character_submissions;
create policy submissions_own_read on public.character_submissions for select to authenticated using(auth.uid()=user_id);
drop policy if exists characters_own_read on public.characters;
create policy characters_own_read on public.characters for select to authenticated using(auth.uid()=user_id and visible_to_user=true);

drop policy if exists char_source_insert_own on storage.objects;
create policy char_source_insert_own on storage.objects for insert to authenticated with check(bucket_id='sinjira-character-sources' and (storage.foldername(name))[1]=auth.uid()::text);
drop policy if exists char_source_select_own on storage.objects;
create policy char_source_select_own on storage.objects for select to authenticated using(bucket_id='sinjira-character-sources' and (storage.foldername(name))[1]=auth.uid()::text);
drop policy if exists char_source_delete_own on storage.objects;
create policy char_source_delete_own on storage.objects for delete to authenticated using(bucket_id='sinjira-character-sources' and (storage.foldername(name))[1]=auth.uid()::text);

create index if not exists novel_comments_status_idx on public.novel_comments(novel_id,status,created_at desc);
create index if not exists character_submissions_user_idx on public.character_submissions(user_id,created_at desc);
create index if not exists characters_user_idx on public.characters(user_id,updated_at desc);

alter table public.characters add column if not exists canon_status text not null default 'PROVISOIRE';
alter table public.characters add column if not exists canon_version text not null default 'v1.0';
alter table public.characters drop constraint if exists characters_canon_status_check;
alter table public.characters add constraint characters_canon_status_check
check(canon_status in('PROVISOIRE','CANON','SECRET_AUTEUR','A_ARBITRER'));
