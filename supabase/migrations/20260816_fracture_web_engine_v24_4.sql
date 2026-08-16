-- SINJIRA™ V24.4 — Fracture du Réseau-Mère, moteur Web 100 % numérique
-- Le serveur est l'autorité pour les identités, cartes, tours, scores et bots.
-- Solo : sièges 2 et 3 automatisés. Duo : siège 3 automatisé.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- VERSION SERVEUR
-- ---------------------------------------------------------------------------
create or replace function public.get_sinjira_server_version()
returns text
language sql
stable
security definer
set search_path=public
as $$ select '24.4.0'::text; $$;
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;

-- ---------------------------------------------------------------------------
-- ÉTAT DU MOTEUR
-- ---------------------------------------------------------------------------
alter table public.fracture_parties add column if not exists engine_version text;
alter table public.fracture_parties add column if not exists engine_status text not null default 'lobby';
alter table public.fracture_parties add column if not exists engine_started_at timestamptz;
alter table public.fracture_parties add column if not exists engine_finished_at timestamptz;
alter table public.fracture_parties drop constraint if exists fracture_parties_engine_status_check;
alter table public.fracture_parties add constraint fracture_parties_engine_status_check
  check (engine_status in ('lobby','playing','final_vote','finished'));

create table if not exists public.fracture_engine_games (
  party_id uuid primary key references public.fracture_parties(id) on delete cascade,
  phase text not null default 'lobby' check (phase in ('lobby','choose_keep','pick','report','final_vote','finished')),
  round_no integer not null default 0,
  first_seat integer,
  turn_seat integer,
  pick_pass integer not null default 0 check (pick_pass between 0 and 2),
  resistance_score integer not null default 0,
  network_score integer not null default 0,
  resistance_rounds integer not null default 0,
  network_rounds integer not null default 0,
  resistance_bonus integer not null default 0,
  network_bonus integer not null default 0,
  final_accused integer[] not null default '{}',
  winner text check (winner is null or winner in ('resistance','network')),
  tiebreak_active boolean not null default false,
  state_version bigint not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.fracture_engine_seats (
  party_id uuid not null references public.fracture_parties(id) on delete cascade,
  seat_number integer not null check (seat_number between 1 and 20),
  seat_kind text not null check (seat_kind in ('human','bot')),
  user_id uuid references auth.users(id) on delete set null,
  identity text not null check (identity in ('resistance','network')),
  proof_used boolean not null default false,
  created_at timestamptz not null default now(),
  primary key(party_id,seat_number)
);
create unique index if not exists fracture_engine_seats_user_unique
  on public.fracture_engine_seats(party_id,user_id) where user_id is not null;

create table if not exists public.fracture_engine_cards (
  card_id bigserial primary key,
  party_id uuid not null references public.fracture_parties(id) on delete cascade,
  round_no integer not null,
  serial_no integer not null,
  faction text not null check (faction in ('R','RM')),
  points integer not null check (points between 1 and 3),
  location text not null default 'deck' check (location in ('deck','hand','center','discard','picked','resolved')),
  dealt_seat integer,
  selected_seat integer,
  selected_pass integer,
  public_position integer,
  created_at timestamptz not null default now(),
  unique(party_id,round_no,serial_no)
);
create index if not exists fracture_engine_cards_party_round_idx on public.fracture_engine_cards(party_id,round_no,location);

create table if not exists public.fracture_engine_actions (
  party_id uuid not null references public.fracture_parties(id) on delete cascade,
  round_no integer not null,
  seat_number integer not null,
  kept_card_ids bigint[] not null default '{}',
  picked_card_ids bigint[] not null default '{}',
  report text check (report is null or report in ('R','RM','EQ')),
  proof_card_id bigint,
  suspect_seat integer,
  updated_at timestamptz not null default now(),
  primary key(party_id,round_no,seat_number)
);

create table if not exists public.fracture_engine_rounds (
  party_id uuid not null references public.fracture_parties(id) on delete cascade,
  round_no integer not null,
  resistance_points integer not null,
  network_points integer not null,
  winner text not null check (winner in ('resistance','network','tie')),
  is_tiebreak boolean not null default false,
  resolved_at timestamptz not null default now(),
  primary key(party_id,round_no)
);

create table if not exists public.fracture_engine_votes (
  party_id uuid not null references public.fracture_parties(id) on delete cascade,
  seat_number integer not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  accused_seats integer[] not null,
  submitted_at timestamptz not null default now(),
  primary key(party_id,seat_number)
);

create table if not exists public.fracture_engine_events (
  id bigserial primary key,
  party_id uuid not null references public.fracture_parties(id) on delete cascade,
  round_no integer,
  event_type text not null,
  message text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists fracture_engine_events_party_idx on public.fracture_engine_events(party_id,id desc);

-- Les secrets du moteur ne sont jamais lisibles directement depuis le navigateur.
alter table public.fracture_engine_games enable row level security;
alter table public.fracture_engine_seats enable row level security;
alter table public.fracture_engine_cards enable row level security;
alter table public.fracture_engine_actions enable row level security;
alter table public.fracture_engine_rounds enable row level security;
alter table public.fracture_engine_votes enable row level security;
alter table public.fracture_engine_events enable row level security;
revoke all on public.fracture_engine_games,public.fracture_engine_seats,public.fracture_engine_cards,
  public.fracture_engine_actions,public.fracture_engine_rounds,public.fracture_engine_votes,public.fracture_engine_events
  from anon,authenticated;

-- ---------------------------------------------------------------------------
-- OUTILS INTERNES
-- ---------------------------------------------------------------------------
create or replace function public._fracture_party_id(p_code text)
returns uuid language sql stable security definer set search_path=public as $$
  select id from public.fracture_parties where upper(party_code)=upper(trim(p_code)) limit 1;
$$;
revoke all on function public._fracture_party_id(text) from public,anon,authenticated;

create or replace function public._fracture_member_seat(p_party uuid,p_user uuid)
returns integer language sql stable security definer set search_path=public as $$
  select seat_number from public.fracture_party_members where party_id=p_party and user_id=p_user limit 1;
$$;
revoke all on function public._fracture_member_seat(uuid,uuid) from public,anon,authenticated;

create or replace function public._fracture_event(p_party uuid,p_round integer,p_type text,p_message text,p_details jsonb default '{}'::jsonb)
returns void language plpgsql security definer set search_path=public as $$
begin
  insert into public.fracture_engine_events(party_id,round_no,event_type,message,details)
  values(p_party,p_round,p_type,p_message,coalesce(p_details,'{}'::jsonb));
end $$;
revoke all on function public._fracture_event(uuid,integer,text,text,jsonb) from public,anon,authenticated;

create or replace function public._fracture_start_round(p_party uuid,p_round integer,p_tiebreak boolean default false)
returns void language plpgsql security definer set search_path=public as $$
declare
  eff integer;
  bot record;
  keep_ids bigint[];
begin
  select effective_player_count into eff from public.fracture_parties where id=p_party;
  if eff is null then raise exception 'PARTY_NOT_FOUND'; end if;

  delete from public.fracture_engine_cards where party_id=p_party and round_no=p_round;
  delete from public.fracture_engine_actions where party_id=p_party and round_no=p_round;

  insert into public.fracture_engine_actions(party_id,round_no,seat_number)
  select p_party,p_round,seat_number from public.fracture_engine_seats where party_id=p_party order by seat_number;

  insert into public.fracture_engine_cards(party_id,round_no,serial_no,faction,points)
  select p_party,p_round,row_number() over ()::integer,faction,points
  from (
    select 'R'::text faction,1 points from generate_series(1,30)
    union all select 'R',2 from generate_series(1,12)
    union all select 'R',3 from generate_series(1,3)
    union all select 'RM',1 from generate_series(1,30)
    union all select 'RM',2 from generate_series(1,12)
    union all select 'RM',3 from generate_series(1,3)
  ) d;

  with shuffled as (
    select card_id,row_number() over(order by gen_random_uuid()) rn
    from public.fracture_engine_cards
    where party_id=p_party and round_no=p_round and location='deck'
  )
  update public.fracture_engine_cards c
  set location='hand',dealt_seat=((s.rn-1)/3)+1
  from shuffled s
  where c.card_id=s.card_id and s.rn<=eff*3;

  -- Les bots choisissent immédiatement 2 cartes à conserver. Ils connaissent seulement
  -- leur propre identité et leurs propres cartes, jamais les identités adverses.
  for bot in
    select seat_number,identity from public.fracture_engine_seats
    where party_id=p_party and seat_kind='bot' order by seat_number
  loop
    select (array_agg(card_id order by
      case when (bot.identity='resistance' and faction='R') or (bot.identity='network' and faction='RM') then points else -points end desc,
      gen_random_uuid()))[1:2]
    into keep_ids
    from public.fracture_engine_cards
    where party_id=p_party and round_no=p_round and location='hand' and dealt_seat=bot.seat_number;

    update public.fracture_engine_actions
    set kept_card_ids=coalesce(keep_ids,'{}'::bigint[]),updated_at=now()
    where party_id=p_party and round_no=p_round and seat_number=bot.seat_number;

    update public.fracture_engine_cards
    set location=case when card_id=any(coalesce(keep_ids,'{}'::bigint[])) then 'center' else 'discard' end
    where party_id=p_party and round_no=p_round and dealt_seat=bot.seat_number and location='hand';
  end loop;

  update public.fracture_engine_games
  set phase='choose_keep',round_no=p_round,pick_pass=0,turn_seat=null,tiebreak_active=p_tiebreak,
      state_version=state_version+1,updated_at=now()
  where party_id=p_party;

  perform public._fracture_event(p_party,p_round,'round_started',
    case when p_tiebreak then 'Ronde de départage démarrée.' else 'Ronde '||p_round||' démarrée.' end,
    jsonb_build_object('tiebreak',p_tiebreak));
end $$;
revoke all on function public._fracture_start_round(uuid,integer,boolean) from public,anon,authenticated;

create or replace function public._fracture_prepare_center(p_party uuid)
returns void language plpgsql security definer set search_path=public as $$
declare
  g public.fracture_engine_games%rowtype;
  eff integer;
begin
  select * into g from public.fracture_engine_games where party_id=p_party for update;
  select effective_player_count into eff from public.fracture_parties where id=p_party;
  if exists(
    select 1 from public.fracture_engine_actions
    where party_id=p_party and round_no=g.round_no and cardinality(kept_card_ids)<>2
  ) then return; end if;

  -- N cartes d'interférence système parmi les cartes non distribuées.
  with chosen as (
    select card_id from public.fracture_engine_cards
    where party_id=p_party and round_no=g.round_no and location='deck'
    order by gen_random_uuid() limit eff
  )
  update public.fracture_engine_cards c set location='center'
  from chosen x where c.card_id=x.card_id;

  -- Position publique aléatoire : les valeurs restent secrètes.
  with ord as (
    select card_id,row_number() over(order by gen_random_uuid())::integer pos
    from public.fracture_engine_cards
    where party_id=p_party and round_no=g.round_no and location='center'
  )
  update public.fracture_engine_cards c set public_position=o.pos
  from ord o where c.card_id=o.card_id;

  update public.fracture_engine_games
  set phase='pick',pick_pass=1,turn_seat=first_seat,state_version=state_version+1,updated_at=now()
  where party_id=p_party;
  perform public._fracture_event(p_party,g.round_no,'center_ready','Le paquet central est prêt.','{}');
end $$;
revoke all on function public._fracture_prepare_center(uuid) from public,anon,authenticated;

create or replace function public._fracture_auto_reports(p_party uuid)
returns void language plpgsql security definer set search_path=public as $$
declare
  g public.fracture_engine_games%rowtype;
  b record;
  rpts integer; npts integer; actual text; claim text; suspect integer; proof bigint;
begin
  select * into g from public.fracture_engine_games where party_id=p_party;
  for b in select * from public.fracture_engine_seats where party_id=p_party and seat_kind='bot' order by seat_number loop
    select coalesce(sum(points) filter(where faction='R'),0),coalesce(sum(points) filter(where faction='RM'),0)
      into rpts,npts
    from public.fracture_engine_cards
    where party_id=p_party and round_no=g.round_no and selected_seat=b.seat_number and location='picked';
    actual:=case when rpts>npts then 'R' when npts>rpts then 'RM' else 'EQ' end;
    -- Comportement tactique sans API IA : un bot Résistance est plus souvent sincère,
    -- un bot Réseau-Mère bluffe davantage. Il n'utilise jamais l'identité des autres sièges.
    if b.identity='resistance' then
      claim:=case when random()<0.78 then actual else (array['R','RM','EQ'])[1+floor(random()*3)::int] end;
    else
      claim:=case when random()<0.42 then actual when actual<>'R' then 'R' else 'EQ' end;
    end if;
    select seat_number into suspect from public.fracture_engine_seats
      where party_id=p_party and seat_number<>b.seat_number order by gen_random_uuid() limit 1;
    proof:=null;
    if not b.proof_used and random()<0.14 then
      select card_id into proof from public.fracture_engine_cards
      where party_id=p_party and round_no=g.round_no and selected_seat=b.seat_number and location='picked'
      order by gen_random_uuid() limit 1;
      update public.fracture_engine_seats set proof_used=true where party_id=p_party and seat_number=b.seat_number;
    end if;
    update public.fracture_engine_actions
    set report=claim,proof_card_id=proof,suspect_seat=suspect,updated_at=now()
    where party_id=p_party and round_no=g.round_no and seat_number=b.seat_number;
  end loop;
end $$;
revoke all on function public._fracture_auto_reports(uuid) from public,anon,authenticated;

create or replace function public._fracture_advance_turn(p_party uuid)
returns void language plpgsql security definer set search_path=public as $$
declare
  g public.fracture_engine_games%rowtype;
  eff integer;
  kind text;
  card bigint;
  nextseat integer;
begin
  loop
    select * into g from public.fracture_engine_games where party_id=p_party for update;
    exit when g.phase<>'pick';
    select effective_player_count into eff from public.fracture_parties where id=p_party;
    select seat_kind into kind from public.fracture_engine_seats where party_id=p_party and seat_number=g.turn_seat;
    if kind='human' then exit; end if;

    select card_id into card from public.fracture_engine_cards
      where party_id=p_party and round_no=g.round_no and location='center'
      order by gen_random_uuid() limit 1;
    if card is null then raise exception 'CENTER_EMPTY'; end if;

    update public.fracture_engine_cards
      set location='picked',selected_seat=g.turn_seat,selected_pass=g.pick_pass
      where card_id=card;
    update public.fracture_engine_actions
      set picked_card_ids=array_append(picked_card_ids,card),updated_at=now()
      where party_id=p_party and round_no=g.round_no and seat_number=g.turn_seat;

    nextseat:=case when g.turn_seat>=eff then 1 else g.turn_seat+1 end;
    if nextseat=g.first_seat then
      if g.pick_pass=1 then
        update public.fracture_engine_games set pick_pass=2,turn_seat=g.first_seat,state_version=state_version+1,updated_at=now() where party_id=p_party;
      else
        update public.fracture_engine_games set phase='report',pick_pass=0,turn_seat=null,state_version=state_version+1,updated_at=now() where party_id=p_party;
        perform public._fracture_auto_reports(p_party);
        exit;
      end if;
    else
      update public.fracture_engine_games set turn_seat=nextseat,state_version=state_version+1,updated_at=now() where party_id=p_party;
    end if;
  end loop;
end $$;
revoke all on function public._fracture_advance_turn(uuid) from public,anon,authenticated;

create or replace function public._fracture_finish_game(p_party uuid,p_winner text)
returns void language plpgsql security definer set search_path=public as $$
declare code text;
begin
  select party_code into code from public.fracture_parties where id=p_party;
  update public.fracture_engine_games set phase='finished',winner=p_winner,turn_seat=null,state_version=state_version+1,updated_at=now() where party_id=p_party;
  update public.fracture_parties set engine_status='finished',status='finished',engine_finished_at=now(),updated_at=now() where id=p_party;
  update public.game_sessions set status='finished',updated_at=now() where party_code=code and game_slug='fracture-du-reseau-mere';
  perform public._fracture_event(p_party,null,'game_finished',case when p_winner='resistance' then 'La Résistance remporte la partie.' else 'Le Réseau-Mère remporte la partie.' end,jsonb_build_object('winner',p_winner));
end $$;
revoke all on function public._fracture_finish_game(uuid,text) from public,anon,authenticated;

create or replace function public._fracture_resolve_round(p_party uuid)
returns void language plpgsql security definer set search_path=public as $$
declare
  g public.fracture_engine_games%rowtype;
  p public.fracture_parties%rowtype;
  rpts integer; npts integer; rw text; nextfirst integer;
  totalr integer; totaln integer;
begin
  select * into g from public.fracture_engine_games where party_id=p_party for update;
  select * into p from public.fracture_parties where id=p_party;
  if g.phase<>'report' then return; end if;
  if exists(select 1 from public.fracture_engine_actions where party_id=p_party and round_no=g.round_no and report is null) then return; end if;

  select coalesce(sum(points) filter(where faction='R'),0),coalesce(sum(points) filter(where faction='RM'),0)
    into rpts,npts
  from public.fracture_engine_cards
  where party_id=p_party and round_no=g.round_no and location='picked';
  rw:=case when rpts>npts then 'resistance' when npts>rpts then 'network' else 'tie' end;

  insert into public.fracture_engine_rounds(party_id,round_no,resistance_points,network_points,winner,is_tiebreak)
  values(p_party,g.round_no,rpts,npts,rw,g.tiebreak_active)
  on conflict(party_id,round_no) do update set resistance_points=excluded.resistance_points,network_points=excluded.network_points,winner=excluded.winner,is_tiebreak=excluded.is_tiebreak,resolved_at=now();

  update public.fracture_engine_cards set location='resolved' where party_id=p_party and round_no=g.round_no and location='picked';
  update public.fracture_engine_games set
    resistance_score=resistance_score+rpts,
    network_score=network_score+npts,
    resistance_rounds=resistance_rounds+case when rw='resistance' then 1 else 0 end,
    network_rounds=network_rounds+case when rw='network' then 1 else 0 end,
    state_version=state_version+1,updated_at=now()
  where party_id=p_party;
  perform public._fracture_event(p_party,g.round_no,'round_resolved','Résultat de ronde : Résistance '||rpts||' — Réseau-Mère '||npts||'.',jsonb_build_object('resistance',rpts,'network',npts,'winner',rw));

  nextfirst:=case when g.first_seat>=p.effective_player_count then 1 else g.first_seat+1 end;

  if g.tiebreak_active then
    if rw='resistance' then perform public._fracture_finish_game(p_party,'resistance'); return;
    elsif rw='network' then perform public._fracture_finish_game(p_party,'network'); return;
    else
      update public.fracture_engine_games set first_seat=nextfirst where party_id=p_party;
      perform public._fracture_start_round(p_party,g.round_no+1,true);
      return;
    end if;
  end if;

  if g.round_no < p.round_count then
    update public.fracture_engine_games set first_seat=nextfirst where party_id=p_party;
    perform public._fracture_start_round(p_party,g.round_no+1,false);
    return;
  end if;

  update public.fracture_engine_games set phase='final_vote',turn_seat=null,state_version=state_version+1,updated_at=now() where party_id=p_party;
  update public.fracture_parties set engine_status='final_vote',updated_at=now() where id=p_party;
  perform public._fracture_event(p_party,g.round_no,'final_vote','Les accusations finales sont ouvertes.','{}');
end $$;
revoke all on function public._fracture_resolve_round(uuid) from public,anon,authenticated;

create or replace function public._fracture_resolve_final_vote(p_party uuid)
returns void language plpgsql security definer set search_path=public as $$
declare
  g public.fracture_engine_games%rowtype;
  p public.fracture_parties%rowtype;
  agents integer;
  expected integer;
  accused integer[];
  rb integer; nb integer;
  totalr integer; totaln integer;
  nextfirst integer;
begin
  select * into g from public.fracture_engine_games where party_id=p_party for update;
  select * into p from public.fracture_parties where id=p_party;
  if g.phase<>'final_vote' then return; end if;
  agents:=public.fracture_agents_for_seats(p.effective_player_count);
  expected:=p.human_player_count;
  if (select count(*) from public.fracture_engine_votes where party_id=p_party) < expected then return; end if;

  with vote_counts as (
    select s.seat_number,
      coalesce((select count(*) from public.fracture_engine_votes v,unnest(v.accused_seats) a where v.party_id=p_party and a=s.seat_number),0) votes,
      coalesce((select count(*) from public.fracture_engine_actions x where x.party_id=p_party and x.suspect_seat=s.seat_number),0) suspicions
    from public.fracture_engine_seats s where s.party_id=p_party
  ), ranked as (
    select seat_number from vote_counts order by votes desc,suspicions desc,gen_random_uuid() limit agents
  )
  select coalesce(array_agg(seat_number),'{}'::integer[]) into accused from ranked;

  select
    coalesce(sum(case when identity='network' then 5 else 0 end),0),
    coalesce(sum(case when identity='resistance' then 5 else 0 end),0)
  into rb,nb
  from public.fracture_engine_seats where party_id=p_party and seat_number=any(accused);

  update public.fracture_engine_games set resistance_bonus=rb,network_bonus=nb,final_accused=accused,state_version=state_version+1,updated_at=now() where party_id=p_party;
  select resistance_score+rb,network_score+nb into totalr,totaln from public.fracture_engine_games where party_id=p_party;

  if totalr>totaln then perform public._fracture_finish_game(p_party,'resistance'); return;
  elsif totaln>totalr then perform public._fracture_finish_game(p_party,'network'); return;
  elsif g.resistance_rounds>g.network_rounds then perform public._fracture_finish_game(p_party,'resistance'); return;
  elsif g.network_rounds>g.resistance_rounds then perform public._fracture_finish_game(p_party,'network'); return;
  end if;

  -- Égalité persistante : ronde(s) de départage sans nouveau bonus d'accusation.
  nextfirst:=case when g.first_seat>=p.effective_player_count then 1 else g.first_seat+1 end;
  update public.fracture_engine_games set first_seat=nextfirst,tiebreak_active=true where party_id=p_party;
  update public.fracture_parties set engine_status='playing',updated_at=now() where id=p_party;
  perform public._fracture_start_round(p_party,p.round_count+1,true);
end $$;
revoke all on function public._fracture_resolve_final_vote(uuid) from public,anon,authenticated;

-- ---------------------------------------------------------------------------
-- RPC PUBLIQUES DU MOTEUR
-- ---------------------------------------------------------------------------
create or replace function public.fracture_engine_start(p_party_code text)
returns jsonb language plpgsql security definer set search_path=public,auth as $$
declare
  uid uuid:=auth.uid(); p public.fracture_parties%rowtype; agents integer;
  member_count integer;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select * into p from public.fracture_parties where upper(party_code)=upper(trim(p_party_code)) for update;
  if p.id is null then raise exception 'PARTY_NOT_FOUND'; end if;
  if p.owner_user_id<>uid then raise exception 'OWNER_ONLY'; end if;
  if not public.has_sinjira_product('fracture-du-reseau-mere',uid) then raise exception 'FRACTURE_ACCESS_REQUIRED'; end if;
  if p.engine_status<>'lobby' then return public.fracture_engine_get_state(p_party_code); end if;
  select count(*) into member_count from public.fracture_party_members where party_id=p.id;
  if member_count<>p.human_player_count then raise exception 'WAITING_FOR_PLAYERS'; end if;

  delete from public.fracture_engine_votes where party_id=p.id;
  delete from public.fracture_engine_events where party_id=p.id;
  delete from public.fracture_engine_rounds where party_id=p.id;
  delete from public.fracture_engine_actions where party_id=p.id;
  delete from public.fracture_engine_cards where party_id=p.id;
  delete from public.fracture_engine_seats where party_id=p.id;
  delete from public.fracture_engine_games where party_id=p.id;

  insert into public.fracture_engine_games(party_id,phase,round_no,first_seat)
  values(p.id,'lobby',0,1);

  insert into public.fracture_engine_seats(party_id,seat_number,seat_kind,user_id,identity)
  select p.id,gs,
    case when gs<=p.human_player_count then 'human' else 'bot' end,
    case when gs<=p.human_player_count then (select m.user_id from public.fracture_party_members m where m.party_id=p.id and m.seat_number=gs) else null end,
    'resistance'
  from generate_series(1,p.effective_player_count) gs;

  agents:=public.fracture_agents_for_seats(p.effective_player_count);
  update public.fracture_engine_seats set identity='network'
  where party_id=p.id and seat_number in (
    select seat_number from public.fracture_engine_seats where party_id=p.id order by gen_random_uuid() limit agents
  );

  update public.fracture_parties set engine_version='24.4.0',engine_status='playing',engine_started_at=now(),updated_at=now() where id=p.id;
  perform public._fracture_event(p.id,1,'game_started','La partie commence.',jsonb_build_object('mode',p.play_mode,'humans',p.human_player_count,'seats',p.effective_player_count));
  perform public._fracture_start_round(p.id,1,false);
  return public.fracture_engine_get_state(p_party_code);
end $$;
revoke all on function public.fracture_engine_start(text) from public,anon;
grant execute on function public.fracture_engine_start(text) to authenticated;

create or replace function public.fracture_engine_submit_keep(p_party_code text,p_card_ids bigint[])
returns jsonb language plpgsql security definer set search_path=public,auth as $$
declare uid uuid:=auth.uid(); pid uuid; seat integer; g public.fracture_engine_games%rowtype; valid_count integer;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  pid:=public._fracture_party_id(p_party_code); seat:=public._fracture_member_seat(pid,uid);
  if seat is null then raise exception 'NOT_A_MEMBER'; end if;
  select * into g from public.fracture_engine_games where party_id=pid for update;
  if g.phase<>'choose_keep' then raise exception 'WRONG_PHASE'; end if;
  if cardinality(p_card_ids)<>2 or p_card_ids[1]=p_card_ids[2] then raise exception 'CHOOSE_EXACTLY_TWO'; end if;
  select count(*) into valid_count from public.fracture_engine_cards where party_id=pid and round_no=g.round_no and location='hand' and dealt_seat=seat and card_id=any(p_card_ids);
  if valid_count<>2 then raise exception 'INVALID_CARDS'; end if;
  if cardinality((select kept_card_ids from public.fracture_engine_actions where party_id=pid and round_no=g.round_no and seat_number=seat))=2 then raise exception 'ALREADY_SUBMITTED'; end if;

  update public.fracture_engine_actions set kept_card_ids=p_card_ids,updated_at=now() where party_id=pid and round_no=g.round_no and seat_number=seat;
  update public.fracture_engine_cards set location=case when card_id=any(p_card_ids) then 'center' else 'discard' end where party_id=pid and round_no=g.round_no and dealt_seat=seat and location='hand';
  update public.fracture_engine_games set state_version=state_version+1,updated_at=now() where party_id=pid;
  perform public._fracture_prepare_center(pid);
  perform public._fracture_advance_turn(pid);
  return public.fracture_engine_get_state(p_party_code);
end $$;
revoke all on function public.fracture_engine_submit_keep(text,bigint[]) from public,anon;
grant execute on function public.fracture_engine_submit_keep(text,bigint[]) to authenticated;

create or replace function public.fracture_engine_pick(p_party_code text,p_card_id bigint)
returns jsonb language plpgsql security definer set search_path=public,auth as $$
declare uid uuid:=auth.uid(); pid uuid; seat integer; g public.fracture_engine_games%rowtype; eff integer; nextseat integer;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  pid:=public._fracture_party_id(p_party_code); seat:=public._fracture_member_seat(pid,uid);
  if seat is null then raise exception 'NOT_A_MEMBER'; end if;
  select * into g from public.fracture_engine_games where party_id=pid for update;
  if g.phase<>'pick' or g.turn_seat<>seat then raise exception 'NOT_YOUR_TURN'; end if;
  if not exists(select 1 from public.fracture_engine_cards where card_id=p_card_id and party_id=pid and round_no=g.round_no and location='center') then raise exception 'CARD_NOT_AVAILABLE'; end if;
  update public.fracture_engine_cards set location='picked',selected_seat=seat,selected_pass=g.pick_pass where card_id=p_card_id;
  update public.fracture_engine_actions set picked_card_ids=array_append(picked_card_ids,p_card_id),updated_at=now() where party_id=pid and round_no=g.round_no and seat_number=seat;
  select effective_player_count into eff from public.fracture_parties where id=pid;
  nextseat:=case when seat>=eff then 1 else seat+1 end;
  if nextseat=g.first_seat then
    if g.pick_pass=1 then update public.fracture_engine_games set pick_pass=2,turn_seat=g.first_seat,state_version=state_version+1,updated_at=now() where party_id=pid;
    else update public.fracture_engine_games set phase='report',pick_pass=0,turn_seat=null,state_version=state_version+1,updated_at=now() where party_id=pid; perform public._fracture_auto_reports(pid); end if;
  else
    update public.fracture_engine_games set turn_seat=nextseat,state_version=state_version+1,updated_at=now() where party_id=pid;
  end if;
  perform public._fracture_advance_turn(pid);
  return public.fracture_engine_get_state(p_party_code);
end $$;
revoke all on function public.fracture_engine_pick(text,bigint) from public,anon;
grant execute on function public.fracture_engine_pick(text,bigint) to authenticated;

create or replace function public.fracture_engine_submit_report(p_party_code text,p_report text,p_suspect_seat integer,p_proof_card_id bigint default null)
returns jsonb language plpgsql security definer set search_path=public,auth as $$
declare uid uuid:=auth.uid(); pid uuid; seat integer; g public.fracture_engine_games%rowtype; proof_used boolean; c record;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  pid:=public._fracture_party_id(p_party_code); seat:=public._fracture_member_seat(pid,uid);
  if seat is null then raise exception 'NOT_A_MEMBER'; end if;
  select * into g from public.fracture_engine_games where party_id=pid for update;
  if g.phase<>'report' then raise exception 'WRONG_PHASE'; end if;
  if upper(coalesce(p_report,'')) not in ('R','RM','EQ') then raise exception 'INVALID_REPORT'; end if;
  if p_suspect_seat is null or p_suspect_seat=seat or not exists(select 1 from public.fracture_engine_seats where party_id=pid and seat_number=p_suspect_seat) then raise exception 'INVALID_SUSPECT'; end if;
  if (select report from public.fracture_engine_actions where party_id=pid and round_no=g.round_no and seat_number=seat) is not null then raise exception 'ALREADY_SUBMITTED'; end if;
  if p_proof_card_id is not null then
    select proof_used into proof_used from public.fracture_engine_seats where party_id=pid and seat_number=seat;
    if proof_used then raise exception 'PROOF_ALREADY_USED'; end if;
    select card_id,faction,points into c from public.fracture_engine_cards where card_id=p_proof_card_id and party_id=pid and round_no=g.round_no and selected_seat=seat and location='picked';
    if c.card_id is null then raise exception 'INVALID_PROOF'; end if;
    update public.fracture_engine_seats set proof_used=true where party_id=pid and seat_number=seat;
    perform public._fracture_event(pid,g.round_no,'proof','Joueur '||seat||' révèle une Preuve : '||c.faction||' +'||c.points||'.',jsonb_build_object('seat',seat,'faction',c.faction,'points',c.points));
  end if;
  update public.fracture_engine_actions set report=upper(p_report),suspect_seat=p_suspect_seat,proof_card_id=p_proof_card_id,updated_at=now() where party_id=pid and round_no=g.round_no and seat_number=seat;
  perform public._fracture_event(pid,g.round_no,'report','Joueur '||seat||' annonce '||upper(p_report)||'.',jsonb_build_object('seat',seat,'report',upper(p_report),'suspect',p_suspect_seat));
  update public.fracture_engine_games set state_version=state_version+1,updated_at=now() where party_id=pid;
  perform public._fracture_resolve_round(pid);
  return public.fracture_engine_get_state(p_party_code);
end $$;
revoke all on function public.fracture_engine_submit_report(text,text,integer,bigint) from public,anon;
grant execute on function public.fracture_engine_submit_report(text,text,integer,bigint) to authenticated;

create or replace function public.fracture_engine_submit_accusation(p_party_code text,p_accused_seats integer[])
returns jsonb language plpgsql security definer set search_path=public,auth as $$
declare uid uuid:=auth.uid(); pid uuid; seat integer; g public.fracture_engine_games%rowtype; p public.fracture_parties%rowtype; agents integer; x integer;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  pid:=public._fracture_party_id(p_party_code); seat:=public._fracture_member_seat(pid,uid);
  if seat is null then raise exception 'NOT_A_MEMBER'; end if;
  select * into g from public.fracture_engine_games where party_id=pid for update;
  select * into p from public.fracture_parties where id=pid;
  if g.phase<>'final_vote' then raise exception 'WRONG_PHASE'; end if;
  agents:=public.fracture_agents_for_seats(p.effective_player_count);
  if cardinality(p_accused_seats)<>agents then raise exception 'INVALID_ACCUSATION_COUNT'; end if;
  if (select count(distinct v) from unnest(p_accused_seats) v)<>agents then raise exception 'ACCUSATIONS_MUST_BE_DISTINCT'; end if;
  foreach x in array p_accused_seats loop
    if x=seat or not exists(select 1 from public.fracture_engine_seats where party_id=pid and seat_number=x) then raise exception 'INVALID_ACCUSED_SEAT'; end if;
  end loop;
  insert into public.fracture_engine_votes(party_id,seat_number,user_id,accused_seats)
  values(pid,seat,uid,p_accused_seats)
  on conflict(party_id,seat_number) do update set accused_seats=excluded.accused_seats,submitted_at=now();
  update public.fracture_engine_games set state_version=state_version+1,updated_at=now() where party_id=pid;
  perform public._fracture_resolve_final_vote(pid);
  return public.fracture_engine_get_state(p_party_code);
end $$;
revoke all on function public.fracture_engine_submit_accusation(text,integer[]) from public,anon;
grant execute on function public.fracture_engine_submit_accusation(text,integer[]) to authenticated;

create or replace function public.fracture_engine_get_state(p_party_code text)
returns jsonb language plpgsql security definer set search_path=public,auth as $$
declare
  uid uuid:=auth.uid(); p public.fracture_parties%rowtype; g public.fracture_engine_games%rowtype; seat integer;
  me public.fracture_engine_seats%rowtype; agents integer; member_count integer;
  hand jsonb:='[]'::jsonb; center jsonb:='[]'::jsonb; picks jsonb:='[]'::jsonb;
  seats jsonb:='[]'::jsonb; reports jsonb:='[]'::jsonb; rounds jsonb:='[]'::jsonb; events jsonb:='[]'::jsonb;
  voted boolean:=false;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select * into p from public.fracture_parties where upper(party_code)=upper(trim(p_party_code));
  if p.id is null then raise exception 'PARTY_NOT_FOUND'; end if;
  seat:=public._fracture_member_seat(p.id,uid);
  if seat is null then raise exception 'NOT_A_MEMBER'; end if;
  select count(*) into member_count from public.fracture_party_members where party_id=p.id;
  select * into g from public.fracture_engine_games where party_id=p.id;
  agents:=public.fracture_agents_for_seats(p.effective_player_count);

  if g.party_id is null then
    return jsonb_build_object(
      'ok',true,'engine_version','24.4.0','engine_status','lobby','phase','lobby','party_code',p.party_code,
      'owner',p.owner_user_id=uid,'my_seat',seat,'human_player_count',p.human_player_count,'effective_player_count',p.effective_player_count,
      'round_count',p.round_count,'member_count',member_count,'ready_to_start',member_count=p.human_player_count,'agents',agents,
      'members',(select coalesce(jsonb_agg(jsonb_build_object('seat',m.seat_number,'name',coalesce(pr.pseudo,pr.display_name,'Joueur '||m.seat_number)) order by m.seat_number),'[]'::jsonb)
                 from public.fracture_party_members m left join public.profiles pr on pr.user_id=m.user_id where m.party_id=p.id)
    );
  end if;

  select * into me from public.fracture_engine_seats where party_id=p.id and seat_number=seat;
  select coalesce(jsonb_agg(jsonb_build_object(
    'seat',s.seat_number,'kind',s.seat_kind,'name',case when s.seat_kind='bot' then 'Moteur '||s.seat_number else coalesce(pr.pseudo,pr.display_name,'Joueur '||s.seat_number) end,
    'identity',case when g.phase='finished' or s.seat_number=seat then s.identity else null end,
    'proof_used',case when s.seat_number=seat then s.proof_used else null end
  ) order by s.seat_number),'[]'::jsonb) into seats
  from public.fracture_engine_seats s left join public.profiles pr on pr.user_id=s.user_id where s.party_id=p.id;

  if g.phase='choose_keep' then
    select coalesce(jsonb_agg(jsonb_build_object('id',card_id,'faction',faction,'points',points) order by card_id),'[]'::jsonb) into hand
    from public.fracture_engine_cards where party_id=p.id and round_no=g.round_no and location='hand' and dealt_seat=seat;
  end if;
  if g.phase='pick' then
    select coalesce(jsonb_agg(jsonb_build_object('id',card_id,'position',public_position) order by public_position),'[]'::jsonb) into center
    from public.fracture_engine_cards where party_id=p.id and round_no=g.round_no and location='center';
  end if;
  select coalesce(jsonb_agg(jsonb_build_object('id',card_id,'faction',faction,'points',points,'pass',selected_pass) order by selected_pass),'[]'::jsonb) into picks
  from public.fracture_engine_cards where party_id=p.id and round_no=g.round_no and selected_seat=seat and location in ('picked','resolved');

  select coalesce(jsonb_agg(jsonb_build_object(
    'seat',a.seat_number,'report',a.report,'suspect',a.suspect_seat,
    'proof',case when a.proof_card_id is null then null else (select jsonb_build_object('faction',c.faction,'points',c.points) from public.fracture_engine_cards c where c.card_id=a.proof_card_id) end
  ) order by a.seat_number),'[]'::jsonb) into reports
  from public.fracture_engine_actions a where a.party_id=p.id and a.round_no=g.round_no and a.report is not null;

  select coalesce(jsonb_agg(jsonb_build_object('round',r.round_no,'R',r.resistance_points,'RM',r.network_points,'winner',r.winner,'tiebreak',r.is_tiebreak) order by r.round_no),'[]'::jsonb) into rounds
  from public.fracture_engine_rounds r where r.party_id=p.id;
  select coalesce(jsonb_agg(jsonb_build_object('id',e.id,'round',e.round_no,'type',e.event_type,'message',e.message,'at',e.created_at) order by e.id desc),'[]'::jsonb) into events
  from (select * from public.fracture_engine_events where party_id=p.id order by id desc limit 40) e;
  select exists(select 1 from public.fracture_engine_votes where party_id=p.id and seat_number=seat) into voted;

  return jsonb_build_object(
    'ok',true,'engine_version','24.4.0','engine_status',p.engine_status,'phase',g.phase,'party_code',p.party_code,
    'owner',p.owner_user_id=uid,'my_seat',seat,'my_identity',me.identity,'my_proof_used',me.proof_used,
    'human_player_count',p.human_player_count,'effective_player_count',p.effective_player_count,'round_count',p.round_count,'agents',agents,
    'round',g.round_no,'first_seat',g.first_seat,'turn_seat',g.turn_seat,'pick_pass',g.pick_pass,'state_version',g.state_version,
    'score',jsonb_build_object('R',g.resistance_score,'RM',g.network_score,'R_rounds',g.resistance_rounds,'RM_rounds',g.network_rounds,'R_bonus',g.resistance_bonus,'RM_bonus',g.network_bonus),
    'winner',g.winner,'final_accused',g.final_accused,'tiebreak',g.tiebreak_active,'voted',voted,
    'hand',hand,'center',center,'my_picks',picks,'seats',seats,'reports',reports,'rounds',rounds,'events',events,
    'keep_submitted',(select cardinality(kept_card_ids)=2 from public.fracture_engine_actions where party_id=p.id and round_no=g.round_no and seat_number=seat),
    'report_submitted',(select report is not null from public.fracture_engine_actions where party_id=p.id and round_no=g.round_no and seat_number=seat)
  );
end $$;
revoke all on function public.fracture_engine_get_state(text) from public,anon;
grant execute on function public.fracture_engine_get_state(text) to authenticated;

-- ---------------------------------------------------------------------------
-- CRÉATION / JONCTION : contrôle de licence côté serveur et blocage après départ
-- ---------------------------------------------------------------------------
create or replace function public.create_fracture_party(p_human_player_count integer,p_round_count integer default 10,p_duo_first_player_seat integer default 1)
returns table(party_id uuid,party_code text,seat_number integer,human_player_count integer,effective_player_count integer,play_mode text,round_count integer)
language plpgsql security definer set search_path=public,auth as $$
declare uid uuid:=auth.uid(); pid uuid; code text; eff integer; mode text; rounds integer; project_uuid uuid;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.has_sinjira_product('fracture-du-reseau-mere',uid) then raise exception 'FRACTURE_ACCESS_REQUIRED'; end if;
  if p_human_player_count not between 1 and 20 then raise exception 'INVALID_PLAYER_COUNT'; end if;
  eff:=case when p_human_player_count<=2 then 3 else p_human_player_count end;
  mode:=case when p_human_player_count=1 then 'solo' when p_human_player_count=2 then 'duo' else 'multiplayer' end;
  rounds:=case when p_human_player_count>=13 and p_round_count=6 then 6 else 10 end;
  loop code:='FRM-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,6)); exit when not exists(select 1 from public.fracture_parties fp where fp.party_code=code); end loop;
  insert into public.fracture_parties(party_code,owner_user_id,human_player_count,effective_player_count,play_mode,round_count,duo_first_player_seat,engine_version,engine_status)
  values(code,uid,p_human_player_count,eff,mode,rounds,case when mode='duo' then greatest(1,least(2,coalesce(p_duo_first_player_seat,1))) else null end,'24.4.0','lobby') returning id into pid;
  insert into public.fracture_party_members(party_id,user_id,seat_number) values(pid,uid,1);
  select id into project_uuid from public.projects where slug='fracture-du-reseau-mere' limit 1;
  insert into public.game_sessions(user_id,project_id,game_slug,title,status,player_count,human_player_count,effective_player_count,play_mode,party_code)
  values(uid,project_uuid,'fracture-du-reseau-mere','Partie '||code||' - Fracture du Réseau-Mère','in_progress',p_human_player_count,p_human_player_count,eff,mode,code) on conflict do nothing;
  return query select pid,code,1,p_human_player_count,eff,mode,rounds;
end $$;
revoke all on function public.create_fracture_party(integer,integer,integer) from public,anon;
grant execute on function public.create_fracture_party(integer,integer,integer) to authenticated;

create or replace function public.join_fracture_party(p_party_code text,p_seat_number integer default null)
returns table(party_id uuid,party_code text,seat_number integer,human_player_count integer,effective_player_count integer,play_mode text,round_count integer)
language plpgsql security definer set search_path=public,auth as $$
declare uid uuid:=auth.uid(); p public.fracture_parties%rowtype; seat integer; existing integer; project_uuid uuid;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.has_sinjira_product('fracture-du-reseau-mere',uid) then raise exception 'FRACTURE_ACCESS_REQUIRED'; end if;
  select fp.* into p from public.fracture_parties fp where upper(fp.party_code)=upper(trim(p_party_code)) and fp.status='in_progress' limit 1;
  if p.id is null then raise exception 'PARTY_NOT_FOUND'; end if;
  if coalesce(p.engine_status,'lobby')<>'lobby' then raise exception 'GAME_ALREADY_STARTED'; end if;
  select m.seat_number into existing from public.fracture_party_members m where m.party_id=p.id and m.user_id=uid;
  if existing is not null then return query select p.id,p.party_code,existing,p.human_player_count,p.effective_player_count,p.play_mode,p.round_count; return; end if;
  if p.human_player_count=1 then raise exception 'SOLO_CANNOT_BE_JOINED'; end if;
  if p_seat_number is not null then
    if p_seat_number<1 or p_seat_number>p.human_player_count then raise exception 'INVALID_HUMAN_SEAT'; end if;
    if exists(select 1 from public.fracture_party_members m where m.party_id=p.id and m.seat_number=p_seat_number) then raise exception 'SEAT_TAKEN'; end if;
    seat:=p_seat_number;
  else
    select gs into seat from generate_series(1,p.human_player_count) gs where not exists(select 1 from public.fracture_party_members m where m.party_id=p.id and m.seat_number=gs) order by gs limit 1;
    if seat is null then raise exception 'PARTY_FULL'; end if;
  end if;
  insert into public.fracture_party_members(party_id,user_id,seat_number) values(p.id,uid,seat);
  select id into project_uuid from public.projects where slug='fracture-du-reseau-mere' limit 1;
  insert into public.game_sessions(user_id,project_id,game_slug,title,status,player_count,human_player_count,effective_player_count,play_mode,party_code)
  values(uid,project_uuid,'fracture-du-reseau-mere','Partie '||p.party_code||' - Fracture du Réseau-Mère','in_progress',p.human_player_count,p.human_player_count,p.effective_player_count,p.play_mode,p.party_code) on conflict do nothing;
  return query select p.id,p.party_code,seat,p.human_player_count,p.effective_player_count,p.play_mode,p.round_count;
end $$;
revoke all on function public.join_fracture_party(text,integer) from public,anon;
grant execute on function public.join_fracture_party(text,integer) to authenticated;

-- Métadonnées produit/projet.
update public.projects set name='Fracture du Réseau-Mère',status='active',play_path='/projets/sinjira/jeux/fracture-du-reseau-mere/jouer.html',updated_at=now() where slug='fracture-du-reseau-mere';
update public.products set name='Fracture du Réseau-Mère — accès en ligne' where slug='fracture-du-reseau-mere';
