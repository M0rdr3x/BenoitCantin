-- SINJIRA™ Fracture V24.4.1 — correctifs du moteur Web

create or replace function public.get_sinjira_server_version()
returns text language sql stable security definer set search_path=public as $$ select '24.4.1'::text; $$;
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;

create or replace function public.fracture_engine_health()
returns jsonb language sql stable security definer set search_path=public as $$
  select jsonb_build_object(
    'ok',true,
    'engine_version','24.4.1',
    'tables',jsonb_build_object(
      'games',to_regclass('public.fracture_engine_games') is not null,
      'seats',to_regclass('public.fracture_engine_seats') is not null,
      'cards',to_regclass('public.fracture_engine_cards') is not null,
      'actions',to_regclass('public.fracture_engine_actions') is not null,
      'rounds',to_regclass('public.fracture_engine_rounds') is not null,
      'votes',to_regclass('public.fracture_engine_votes') is not null
    )
  );
$$;
revoke all on function public.fracture_engine_health() from public,anon;
grant execute on function public.fracture_engine_health() to authenticated,service_role;

create or replace function public.fracture_engine_start(p_party_code text)
returns jsonb language plpgsql security definer set search_path=public,auth as $$
declare
  uid uuid:=auth.uid(); p public.fracture_parties%rowtype; agents integer;
  member_count integer; firstseat integer;
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

  firstseat:=case when p.play_mode='duo' then coalesce(p.duo_first_player_seat,1) else 1 end;
  insert into public.fracture_engine_games(party_id,phase,round_no,first_seat)
  values(p.id,'lobby',0,firstseat);

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

  update public.fracture_parties set engine_version='24.4.1',engine_status='playing',engine_started_at=now(),updated_at=now() where id=p.id;
  perform public._fracture_event(p.id,1,'game_started','La partie commence.',jsonb_build_object('mode',p.play_mode,'humans',p.human_player_count,'seats',p.effective_player_count));
  perform public._fracture_start_round(p.id,1,false);
  return public.fracture_engine_get_state(p_party_code);
end $$;
revoke all on function public.fracture_engine_start(text) from public,anon;
grant execute on function public.fracture_engine_start(text) to authenticated;

create or replace function public._fracture_resolve_final_vote(p_party uuid)
returns void language plpgsql security definer set search_path=public as $$
declare
  g public.fracture_engine_games%rowtype;
  p public.fracture_parties%rowtype;
  agents integer; expected integer; accused integer[];
  rb integer; nb integer; totalr integer; totaln integer; nextfirst integer;
begin
  select * into g from public.fracture_engine_games where party_id=p_party for update;
  select * into p from public.fracture_parties where id=p_party;
  if g.phase<>'final_vote' then return; end if;
  agents:=public.fracture_agents_for_seats(p.effective_player_count);
  expected:=p.human_player_count;
  if (select count(*) from public.fracture_engine_votes where party_id=p_party)<expected then return; end if;

  with vote_counts as (
    select s.seat_number,
      coalesce((select count(*) from public.fracture_engine_votes v cross join lateral unnest(v.accused_seats) as u(seat) where v.party_id=p_party and u.seat=s.seat_number),0) votes,
      coalesce((select count(*) from public.fracture_engine_actions x where x.party_id=p_party and x.suspect_seat=s.seat_number),0) suspicions
    from public.fracture_engine_seats s where s.party_id=p_party
  ), ranked as (
    select seat_number from vote_counts order by votes desc,suspicions desc,gen_random_uuid() limit agents
  )
  select coalesce(array_agg(seat_number),'{}'::integer[]) into accused from ranked;

  select coalesce(sum(case when identity='network' then 5 else 0 end),0),
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

  nextfirst:=case when g.first_seat>=p.effective_player_count then 1 else g.first_seat+1 end;
  update public.fracture_engine_games set first_seat=nextfirst,tiebreak_active=true where party_id=p_party;
  update public.fracture_parties set engine_status='playing',updated_at=now() where id=p_party;
  perform public._fracture_start_round(p_party,p.round_count+1,true);
end $$;
revoke all on function public._fracture_resolve_final_vote(uuid) from public,anon,authenticated;
