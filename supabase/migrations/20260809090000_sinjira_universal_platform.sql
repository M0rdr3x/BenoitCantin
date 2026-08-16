-- SINJIRA — plateforme universelle de comptes, projets, documents protégés et playtests
-- Exécuter après 20260808_sinjira_players.sql. Idempotent.

create extension if not exists pgcrypto;

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  type text not null default 'game' check (type in ('game','experience','tool','other')),
  status text not null default 'development' check (status in ('draft','development','testing','active','archived')),
  visibility text not null default 'account' check (visibility in ('public','account','restricted')),
  description text,
  cover_url text,
  public_path text,
  play_path text,
  allow_tester_requests boolean not null default true,
  sort_order integer not null default 100,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.projects(slug,name,type,status,visibility,description,cover_url,public_path,play_path,allow_tester_requests,sort_order)
values
('fracture-du-reseau-mere','Fracture du Réseau-Mère','game','active','account',
 'Jeu SINJIRA avec fiche joueur web, sauvegardes, rapports et programme de contribution.',
 '/assets/media/sinjira-fracture-du-reseau-mere-officiel.webp',
 '/projets/sinjira/jeux/fracture-du-reseau-mere/index.html',
 '/projets/sinjira/jeux/fracture-du-reseau-mere/fiche-web.html',true,10),
('reseau-mere-resistance','Réseau-Mère : Résistance','game','development','account',
 'Second jeu officiel de SINJIRA. Son espace joueur accueillera les documents et outils approuvés au fil du développement.',
 '/assets/media/sinjira-reseau-mere-resistance-officiel.webp',
 '/projets/sinjira/jeux/reseau-mere-resistance/index.html',null,true,20)
on conflict (slug) do update set
name=excluded.name,type=excluded.type,status=excluded.status,visibility=excluded.visibility,
description=excluded.description,cover_url=excluded.cover_url,public_path=excluded.public_path,
play_path=excluded.play_path,allow_tester_requests=excluded.allow_tester_requests,sort_order=excluded.sort_order;

create table if not exists public.project_access (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  access_level text not null default 'player' check (access_level in ('player','tester')),
  granted_by uuid references auth.users(id) on delete set null,
  source text not null default 'manual' check (source in ('manual','request','playtest','migration')),
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id,project_id)
);

create table if not exists public.access_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  requested_level text not null default 'tester' check (requested_level in ('player','tester')),
  message text,
  status text not null default 'pending' check (status in ('pending','approved','refused','cancelled')),
  reviewed_by uuid references auth.users(id) on delete set null,
  reviewed_at timestamptz,
  review_note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists access_requests_one_pending_idx
on public.access_requests(user_id,project_id,requested_level) where status='pending';

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  title text not null,
  description text,
  document_type text not null default 'document',
  version text not null default '1.0',
  status text not null default 'draft' check (status in ('draft','review','approved','archived')),
  access_level text not null default 'account' check (access_level in ('public','account','player','tester','admin')),
  storage_bucket text,
  storage_path text,
  external_url text,
  mime_type text,
  file_size_bytes bigint,
  sort_order integer not null default 100,
  created_by uuid references auth.users(id) on delete set null,
  approved_by uuid references auth.users(id) on delete set null,
  approved_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (storage_path is not null or external_url is not null)
);

insert into public.documents(project_id,title,description,document_type,version,status,access_level,external_url,mime_type,sort_order)
select p.id,'Fiche joueur officielle — PDF remplissable',
'Fiche officielle de Fracture du Réseau-Mère utilisable dans le lecteur PDF du site.',
'Fiche joueur','1.0','approved','account',
'/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Fracture_du_Reseau_Mere_Fiche_Joueur_Web.pdf',
'application/pdf',10
from public.projects p
where p.slug='fracture-du-reseau-mere'
and not exists(select 1 from public.documents d where d.project_id=p.id and d.title='Fiche joueur officielle — PDF remplissable');

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('sinjira-private-documents','sinjira-private-documents',false,52428800,
array['application/pdf','application/zip','image/png','image/jpeg','image/webp','text/plain'])
on conflict(id) do update set public=false;

create table if not exists public.playtests (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  title text not null,
  description text,
  status text not null default 'draft' check (status in ('draft','open','active','closed','archived')),
  required_access text not null default 'tester' check (required_access in ('account','player','tester')),
  starts_at timestamptz,
  ends_at timestamptz,
  max_participants integer check (max_participants is null or max_participants>0),
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.playtest_participants (
  playtest_id uuid not null references public.playtests(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'applied' check (status in ('invited','applied','approved','refused','completed','withdrawn')),
  application_message text,
  reviewed_by uuid references auth.users(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key(playtest_id,user_id)
);

create table if not exists public.extensions (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  title text not null,
  description text,
  status text not null default 'idea' check (status in ('idea','research','design','testing','approved','released','archived')),
  is_public boolean not null default false,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.game_sessions add column if not exists project_id uuid references public.projects(id) on delete set null;
update public.game_sessions s set project_id=p.id from public.projects p where s.project_id is null and p.slug=s.game_slug;


create or replace function public.sinjira_set_session_project()
returns trigger
language plpgsql
security invoker
set search_path=public
as $$
begin
  if new.project_id is null and new.game_slug is not null then
    select id into new.project_id from public.projects where slug=new.game_slug limit 1;
  end if;
  return new;
end;
$$;

drop trigger if exists sinjira_game_session_project on public.game_sessions;
create trigger sinjira_game_session_project
before insert or update of game_slug,project_id on public.game_sessions
for each row execute function public.sinjira_set_session_project();

create index if not exists game_sessions_project_idx on public.game_sessions(project_id);
create index if not exists project_access_user_idx on public.project_access(user_id);
create index if not exists project_access_project_idx on public.project_access(project_id);
create index if not exists access_requests_user_idx on public.access_requests(user_id);
create index if not exists documents_project_idx on public.documents(project_id);
create index if not exists playtests_project_idx on public.playtests(project_id);
create index if not exists playtest_participants_user_idx on public.playtest_participants(user_id);

do $$
declare t text;
begin
  foreach t in array array['projects','project_access','access_requests','documents','playtests','playtest_participants','extensions']
  loop
    execute format('drop trigger if exists %I_updated_at on public.%I',t,t);
    execute format('create trigger %I_updated_at before update on public.%I for each row execute function public.set_updated_at()',t,t);
  end loop;
end $$;

create or replace function public.is_sinjira_admin(p_user_id uuid default auth.uid())
returns boolean language sql stable security definer set search_path=public as $$
select exists(select 1 from public.internal_admin_users a where a.user_id=p_user_id);
$$;
revoke all on function public.is_sinjira_admin(uuid) from public;
grant execute on function public.is_sinjira_admin(uuid) to anon,authenticated,service_role;

create or replace function public.project_access_rank(p_project_id uuid,p_user_id uuid default auth.uid())
returns integer language sql stable security definer set search_path=public as $$
select case
 when public.is_sinjira_admin(p_user_id) then 100
 when exists(select 1 from public.project_access pa where pa.project_id=p_project_id and pa.user_id=p_user_id and (pa.expires_at is null or pa.expires_at>now()) and pa.access_level='tester') then 30
 when exists(select 1 from public.project_access pa where pa.project_id=p_project_id and pa.user_id=p_user_id and (pa.expires_at is null or pa.expires_at>now()) and pa.access_level='player') then 20
 when p_user_id is not null and exists(select 1 from public.projects p where p.id=p_project_id and p.visibility in ('public','account')) then 10
 when exists(select 1 from public.projects p where p.id=p_project_id and p.visibility='public') then 1
 else 0 end;
$$;
revoke all on function public.project_access_rank(uuid,uuid) from public;
grant execute on function public.project_access_rank(uuid,uuid) to anon,authenticated,service_role;

create or replace function public.document_access_rank(p_level text)
returns integer language sql immutable as $$
select case p_level when 'public' then 1 when 'account' then 10 when 'player' then 20 when 'tester' then 30 when 'admin' then 100 else 999 end;
$$;
grant execute on function public.document_access_rank(text) to anon,authenticated,service_role;

alter table public.projects enable row level security;
alter table public.project_access enable row level security;
alter table public.access_requests enable row level security;
alter table public.documents enable row level security;
alter table public.playtests enable row level security;
alter table public.playtest_participants enable row level security;
alter table public.extensions enable row level security;

drop policy if exists "projects readable when accessible" on public.projects;
create policy "projects readable when accessible" on public.projects for select to anon,authenticated
using(status<>'draft' and (visibility='public' or (visibility='account' and (select auth.uid()) is not null) or public.project_access_rank(id,(select auth.uid()))>=20));

drop policy if exists "access own select" on public.project_access;
create policy "access own select" on public.project_access for select to authenticated using((select auth.uid())=user_id);

drop policy if exists "requests own select" on public.access_requests;
create policy "requests own select" on public.access_requests for select to authenticated using((select auth.uid())=user_id);
drop policy if exists "requests own insert" on public.access_requests;
create policy "requests own insert" on public.access_requests for insert to authenticated
with check((select auth.uid())=user_id and status='pending');

drop policy if exists "approved documents visible by access" on public.documents;
create policy "approved documents visible by access" on public.documents for select to anon,authenticated
using(status='approved' and public.project_access_rank(project_id,(select auth.uid()))>=public.document_access_rank(access_level));

drop policy if exists "playtests readable" on public.playtests;
create policy "playtests readable" on public.playtests for select to authenticated
using(
  status in ('open','active')
  and public.project_access_rank(project_id,(select auth.uid())) >= 10
);

drop policy if exists "participants own select" on public.playtest_participants;
create policy "participants own select" on public.playtest_participants for select to authenticated using((select auth.uid())=user_id);
drop policy if exists "participants own apply" on public.playtest_participants;
create policy "participants own apply" on public.playtest_participants for insert to authenticated
with check((select auth.uid())=user_id and status='applied');

drop policy if exists "extensions public read" on public.extensions;
create policy "extensions public read" on public.extensions for select to anon,authenticated
using(is_public=true and status in ('approved','released'));

-- Le bucket privé n'a volontairement aucune policy de lecture directe.
-- Les téléchargements passent par get-document-url, qui renvoie une URL signée temporaire.
