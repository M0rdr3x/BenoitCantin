-- SINJIRA / Fracture du Réseau-Mère V9
-- Parties en ligne 1 à 20 joueurs, fiches privées par compte, seule la fin de partie est transmissible.

alter table public.game_sessions add column if not exists human_player_count integer;
alter table public.game_sessions add column if not exists effective_player_count integer;
alter table public.game_sessions add column if not exists play_mode text;
alter table public.game_sessions add column if not exists party_code text;

alter table public.game_sessions drop constraint if exists game_sessions_human_player_count_check;
alter table public.game_sessions add constraint game_sessions_human_player_count_check
  check (human_player_count is null or human_player_count between 1 and 20);

alter table public.game_sessions drop constraint if exists game_sessions_effective_player_count_check;
alter table public.game_sessions add constraint game_sessions_effective_player_count_check
  check (effective_player_count is null or effective_player_count between 3 and 20);

alter table public.game_sessions drop constraint if exists game_sessions_play_mode_check;
alter table public.game_sessions add constraint game_sessions_play_mode_check
  check (play_mode is null or play_mode in ('solo','duo','multiplayer'));

create table if not exists public.fracture_parties (
  id uuid primary key default gen_random_uuid(),
  party_code text not null unique,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  human_player_count integer not null check (human_player_count between 1 and 20),
  effective_player_count integer not null check (effective_player_count between 3 and 20),
  play_mode text not null check (play_mode in ('solo','duo','multiplayer')),
  round_count integer not null default 10 check (round_count in (6,10)),
  duo_first_player_seat integer check (duo_first_player_seat is null or duo_first_player_seat in (1,2)),
  status text not null default 'in_progress' check (status in ('in_progress','finished','archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.fracture_party_members (
  party_id uuid not null references public.fracture_parties(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  seat_number integer not null check (seat_number between 1 and 20),
  joined_at timestamptz not null default now(),
  primary key(party_id,user_id),
  unique(party_id,seat_number)
);

create table if not exists public.fracture_player_documents (
  id uuid primary key default gen_random_uuid(),
  party_id uuid not null references public.fracture_parties(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  document_key text not null,
  document_type text not null check (document_type in ('player','invisible3','solo')),
  seat_number integer not null check (seat_number between 1 and 20),
  fields jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(party_id,user_id,document_key)
);

create table if not exists public.fracture_endgame_reports (
  id uuid primary key default gen_random_uuid(),
  party_id uuid not null unique references public.fracture_parties(id) on delete cascade,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  fields jsonb not null default '{}'::jsonb,
  submitted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.internal_gameplay_contributions add column if not exists source_party_id uuid references public.fracture_parties(id) on delete set null;
alter table public.internal_gameplay_contributions add column if not exists source_kind text;
create unique index if not exists fracture_contribution_party_unique
  on public.internal_gameplay_contributions(source_party_id)
  where source_party_id is not null and source_kind='fracture_endgame';

create index if not exists fracture_members_user_idx on public.fracture_party_members(user_id);
create index if not exists fracture_docs_user_idx on public.fracture_player_documents(user_id);
create index if not exists fracture_docs_party_idx on public.fracture_player_documents(party_id);

drop trigger if exists fracture_parties_updated_at on public.fracture_parties;
create trigger fracture_parties_updated_at before update on public.fracture_parties for each row execute function public.set_updated_at();
drop trigger if exists fracture_documents_updated_at on public.fracture_player_documents;
create trigger fracture_documents_updated_at before update on public.fracture_player_documents for each row execute function public.set_updated_at();
drop trigger if exists fracture_endgame_updated_at on public.fracture_endgame_reports;
create trigger fracture_endgame_updated_at before update on public.fracture_endgame_reports for each row execute function public.set_updated_at();

create or replace function public.is_fracture_party_member(p_party_id uuid,p_user_id uuid default auth.uid())
returns boolean language sql stable security definer set search_path=public as $$
select exists(select 1 from public.fracture_party_members m where m.party_id=p_party_id and m.user_id=p_user_id);
$$;
revoke all on function public.is_fracture_party_member(uuid,uuid) from public;
grant execute on function public.is_fracture_party_member(uuid,uuid) to authenticated,service_role;

create or replace function public.fracture_agents_for_seats(p_seats integer)
returns integer language sql immutable as $$
select case p_seats
 when 3 then 1 when 4 then 1 when 5 then 2 when 6 then 2 when 7 then 2
 when 8 then 3 when 9 then 3 when 10 then 3 when 11 then 4 when 12 then 4
 when 13 then 4 when 14 then 5 when 15 then 5 when 16 then 5 when 17 then 6
 when 18 then 6 when 19 then 6 when 20 then 7 else null end;
$$;
grant execute on function public.fracture_agents_for_seats(integer) to authenticated,service_role;

create or replace function public.create_fracture_party(
  p_human_player_count integer,
  p_round_count integer default 10,
  p_duo_first_player_seat integer default 1
)
returns table(party_id uuid,party_code text,seat_number integer,human_player_count integer,effective_player_count integer,play_mode text,round_count integer)
language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid(); pid uuid; code text; eff integer; mode text; rounds integer; project_uuid uuid;
begin
  if uid is null then raise exception 'Connexion requise.'; end if;
  if p_human_player_count not between 1 and 20 then raise exception 'Nombre de joueurs invalide.'; end if;
  eff:=case when p_human_player_count<=2 then 3 else p_human_player_count end;
  mode:=case when p_human_player_count=1 then 'solo' when p_human_player_count=2 then 'duo' else 'multiplayer' end;
  rounds:=case when p_human_player_count>=13 and p_round_count=6 then 6 else 10 end;
  loop
    code:='FRM-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,6));
    exit when not exists(select 1 from public.fracture_parties where fracture_parties.party_code=code);
  end loop;
  insert into public.fracture_parties(party_code,owner_user_id,human_player_count,effective_player_count,play_mode,round_count,duo_first_player_seat)
  values(code,uid,p_human_player_count,eff,mode,rounds,case when mode='duo' then greatest(1,least(2,coalesce(p_duo_first_player_seat,1))) else null end)
  returning id into pid;
  insert into public.fracture_party_members(party_id,user_id,seat_number) values(pid,uid,1);
  select id into project_uuid from public.projects where slug='fracture-du-reseau-mere' limit 1;
  insert into public.game_sessions(user_id,project_id,game_slug,title,status,player_count,human_player_count,effective_player_count,play_mode,party_code)
  values(uid,project_uuid,'fracture-du-reseau-mere','Partie '||code||' - Fracture du Réseau-Mère','in_progress',p_human_player_count,p_human_player_count,eff,mode,code)
  on conflict (user_id,game_slug,party_code) where party_code is not null do update set
    player_count=excluded.player_count,human_player_count=excluded.human_player_count,effective_player_count=excluded.effective_player_count,play_mode=excluded.play_mode,updated_at=now();
  return query select pid,code,1,p_human_player_count,eff,mode,rounds;
end $$;
revoke all on function public.create_fracture_party(integer,integer,integer) from public;
grant execute on function public.create_fracture_party(integer,integer,integer) to authenticated;

create or replace function public.join_fracture_party(p_party_code text,p_seat_number integer default null)
returns table(party_id uuid,party_code text,seat_number integer,human_player_count integer,effective_player_count integer,play_mode text,round_count integer)
language plpgsql security definer set search_path=public as $$
declare uid uuid:=auth.uid(); p public.fracture_parties%rowtype; seat integer; existing integer; project_uuid uuid;
begin
  if uid is null then raise exception 'Connexion requise.'; end if;
  select * into p from public.fracture_parties where upper(fracture_parties.party_code)=upper(trim(p_party_code)) and status='in_progress' limit 1;
  if p.id is null then raise exception 'Partie introuvable ou terminée.'; end if;
  select m.seat_number into existing from public.fracture_party_members m where m.party_id=p.id and m.user_id=uid;
  if existing is not null then return query select p.id,p.party_code,existing,p.human_player_count,p.effective_player_count,p.play_mode,p.round_count; return; end if;
  if p.human_player_count=1 then raise exception 'Une partie Solo ne peut pas être rejointe.'; end if;
  if p_seat_number is not null then
    if p_seat_number<1 or p_seat_number>p.human_player_count then raise exception 'Siège humain invalide.'; end if;
    if exists(select 1 from public.fracture_party_members m where m.party_id=p.id and m.seat_number=p_seat_number) then raise exception 'Ce siège est déjà occupé.'; end if;
    seat:=p_seat_number;
  else
    select gs into seat from generate_series(1,p.human_player_count) gs where not exists(select 1 from public.fracture_party_members m where m.party_id=p.id and m.seat_number=gs) order by gs limit 1;
    if seat is null then raise exception 'Tous les sièges humains sont occupés.'; end if;
  end if;
  insert into public.fracture_party_members(party_id,user_id,seat_number) values(p.id,uid,seat);
  select id into project_uuid from public.projects where slug='fracture-du-reseau-mere' limit 1;
  insert into public.game_sessions(user_id,project_id,game_slug,title,status,player_count,human_player_count,effective_player_count,play_mode,party_code)
  values(uid,project_uuid,'fracture-du-reseau-mere','Partie '||p.party_code||' - Fracture du Réseau-Mère','in_progress',p.human_player_count,p.human_player_count,p.effective_player_count,p.play_mode,p.party_code)
  on conflict (user_id,game_slug,party_code) where party_code is not null do update set updated_at=now();
  return query select p.id,p.party_code,seat,p.human_player_count,p.effective_player_count,p.play_mode,p.round_count;
end $$;
revoke all on function public.join_fracture_party(text,integer) from public;
grant execute on function public.join_fracture_party(text,integer) to authenticated;

alter table public.fracture_parties enable row level security;
alter table public.fracture_party_members enable row level security;
alter table public.fracture_player_documents enable row level security;
alter table public.fracture_endgame_reports enable row level security;

drop policy if exists "fracture parties members read" on public.fracture_parties;
create policy "fracture parties members read" on public.fracture_parties for select to authenticated
using(owner_user_id=auth.uid() or public.is_fracture_party_member(id,auth.uid()));

drop policy if exists "fracture members party read" on public.fracture_party_members;
create policy "fracture members party read" on public.fracture_party_members for select to authenticated
using(user_id=auth.uid() or public.is_fracture_party_member(party_id,auth.uid()));

drop policy if exists "fracture docs own read" on public.fracture_player_documents;
create policy "fracture docs own read" on public.fracture_player_documents for select to authenticated using(user_id=auth.uid());
drop policy if exists "fracture docs own insert" on public.fracture_player_documents;
create policy "fracture docs own insert" on public.fracture_player_documents for insert to authenticated
with check(user_id=auth.uid() and public.is_fracture_party_member(party_id,auth.uid()));
drop policy if exists "fracture docs own update" on public.fracture_player_documents;
create policy "fracture docs own update" on public.fracture_player_documents for update to authenticated
using(user_id=auth.uid()) with check(user_id=auth.uid());
drop policy if exists "fracture docs own delete" on public.fracture_player_documents;
create policy "fracture docs own delete" on public.fracture_player_documents for delete to authenticated using(user_id=auth.uid());

drop policy if exists "fracture endgame members read" on public.fracture_endgame_reports;
create policy "fracture endgame members read" on public.fracture_endgame_reports for select to authenticated
using(public.is_fracture_party_member(party_id,auth.uid()));
drop policy if exists "fracture endgame owner insert" on public.fracture_endgame_reports;
create policy "fracture endgame owner insert" on public.fracture_endgame_reports for insert to authenticated
with check(owner_user_id=auth.uid() and exists(select 1 from public.fracture_parties p where p.id=party_id and p.owner_user_id=auth.uid()));
drop policy if exists "fracture endgame owner update" on public.fracture_endgame_reports;
create policy "fracture endgame owner update" on public.fracture_endgame_reports for update to authenticated
using(owner_user_id=auth.uid()) with check(owner_user_id=auth.uid());

update public.projects set
  description='Jeu de cartes SINJIRA de déduction, bluff et majorité pour 1 à 20 joueurs. L’espace en ligne sauvegarde les fiches privées dans le compte de chaque joueur; seule la Feuille de fin de partie peut être transmise à SINJIRA.',
  play_path='/projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html',
  status='active',
  updated_at=now()
where slug='fracture-du-reseau-mere';

update public.documents d set status='archived',updated_at=now()
from public.projects p
where d.project_id=p.id and p.slug='fracture-du-reseau-mere'
  and d.title in ('Fiche joueur officielle - interactive','Préparation dynamique des joueurs','Feuille de fin de partie officielle - interactive');

insert into public.documents(project_id,title,description,document_type,version,status,access_level,external_url,mime_type,sort_order,approved_at)
select p.id,'Règles officielles en ligne','Règles complètes 1 à 20 joueurs issues du manuel officiel Fracture du Réseau-Mère.','Règles','9.0','approved','public','/projets/sinjira/jeux/fracture-du-reseau-mere/regles.html','text/html',5,now()
from public.projects p where p.slug='fracture-du-reseau-mere'
and not exists(select 1 from public.documents d where d.project_id=p.id and d.title='Règles officielles en ligne' and d.status='approved');

insert into public.documents(project_id,title,description,document_type,version,status,access_level,external_url,mime_type,sort_order,approved_at)
select p.id,'Espace joueur en ligne','Création et jonction de parties 1 à 20 joueurs avec fiches privées sauvegardées au compte utilisateur.','Outil web','9.0','approved','account','/projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html','text/html',10,now()
from public.projects p where p.slug='fracture-du-reseau-mere'
and not exists(select 1 from public.documents d where d.project_id=p.id and d.title='Espace joueur en ligne' and d.status='approved');

insert into public.documents(project_id,title,description,document_type,version,status,access_level,external_url,mime_type,sort_order,approved_at)
select p.id,'Feuille de fin de partie en ligne','Seul document de Fracture du Réseau-Mère pouvant être transmis à SINJIRA pour l’équilibrage.','Fin de partie','9.0','approved','account','/projets/sinjira/jeux/fracture-du-reseau-mere/fin-de-partie.html','text/html',20,now()
from public.projects p where p.slug='fracture-du-reseau-mere'
and not exists(select 1 from public.documents d where d.project_id=p.id and d.title='Feuille de fin de partie en ligne' and d.status='approved');
