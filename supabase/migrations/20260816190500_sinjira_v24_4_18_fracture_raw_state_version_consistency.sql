-- SINJIRA™ V24.4.18 — cohérence de version jusque dans l'état brut Fracture
-- Le helper brut n'est exposé qu'au service_role, mais il ne doit plus annoncer une
-- ancienne version si un service interne l'utilise directement.

create or replace function public._fracture_engine_get_state_raw(p_party_code text)
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  uid uuid:=auth.uid();
  p public.fracture_parties%rowtype;
  g public.fracture_engine_games%rowtype;
  seat integer;
  me public.fracture_engine_seats%rowtype;
  agents integer;
  member_count integer;
  hand jsonb:='[]'::jsonb;
  center jsonb:='[]'::jsonb;
  picks jsonb:='[]'::jsonb;
  seats jsonb:='[]'::jsonb;
  reports jsonb:='[]'::jsonb;
  rounds jsonb:='[]'::jsonb;
  events jsonb:='[]'::jsonb;
  voted boolean:=false;
  canonical_engine_version text;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  select * into p
  from public.fracture_parties
  where upper(party_code)=upper(trim(p_party_code));

  if p.id is null then raise exception 'PARTY_NOT_FOUND'; end if;
  canonical_engine_version:=coalesce(p.engine_version,'24.4.6');

  seat:=public._fracture_member_seat(p.id,uid);
  if seat is null then raise exception 'NOT_A_MEMBER'; end if;

  select count(*) into member_count
  from public.fracture_party_members
  where party_id=p.id;

  select * into g
  from public.fracture_engine_games
  where party_id=p.id;

  agents:=public.fracture_agents_for_seats(p.effective_player_count);

  if g.party_id is null then
    return jsonb_build_object(
      'ok',true,
      'engine_version',canonical_engine_version,
      'engine_status','lobby',
      'phase','lobby',
      'party_code',p.party_code,
      'owner',p.owner_user_id=uid,
      'my_seat',seat,
      'human_player_count',p.human_player_count,
      'effective_player_count',p.effective_player_count,
      'round_count',p.round_count,
      'member_count',member_count,
      'ready_to_start',member_count=p.human_player_count,
      'agents',agents,
      'members',(
        select coalesce(jsonb_agg(
          jsonb_build_object(
            'seat',m.seat_number,
            'name',coalesce(pr.pseudo,pr.display_name,'Joueur '||m.seat_number)
          ) order by m.seat_number
        ),'[]'::jsonb)
        from public.fracture_party_members m
        left join public.profiles pr on pr.user_id=m.user_id
        where m.party_id=p.id
      )
    );
  end if;

  select * into me
  from public.fracture_engine_seats
  where party_id=p.id and seat_number=seat;

  select coalesce(jsonb_agg(
    jsonb_build_object(
      'seat',s.seat_number,
      'kind',s.seat_kind,
      'name',case when s.seat_kind='bot' then 'Moteur '||s.seat_number else coalesce(pr.pseudo,pr.display_name,'Joueur '||s.seat_number) end,
      'identity',case when g.phase='finished' or s.seat_number=seat then s.identity else null end,
      'proof_used',case when s.seat_number=seat then s.proof_used else null end
    ) order by s.seat_number
  ),'[]'::jsonb)
  into seats
  from public.fracture_engine_seats s
  left join public.profiles pr on pr.user_id=s.user_id
  where s.party_id=p.id;

  if g.phase='choose_keep' then
    select coalesce(jsonb_agg(
      jsonb_build_object('id',card_id,'faction',faction,'points',points)
      order by card_id
    ),'[]'::jsonb)
    into hand
    from public.fracture_engine_cards
    where party_id=p.id and round_no=g.round_no and location='hand' and dealt_seat=seat;
  end if;

  if g.phase='pick' then
    select coalesce(jsonb_agg(
      jsonb_build_object('id',card_id,'position',public_position)
      order by public_position
    ),'[]'::jsonb)
    into center
    from public.fracture_engine_cards
    where party_id=p.id and round_no=g.round_no and location='center';
  end if;

  select coalesce(jsonb_agg(
    jsonb_build_object('id',card_id,'faction',faction,'points',points,'pass',selected_pass)
    order by selected_pass
  ),'[]'::jsonb)
  into picks
  from public.fracture_engine_cards
  where party_id=p.id and round_no=g.round_no and selected_seat=seat and location in ('picked','resolved');

  select coalesce(jsonb_agg(
    jsonb_build_object(
      'seat',a.seat_number,
      'report',a.report,
      'suspect',a.suspect_seat,
      'proof',case when a.proof_card_id is null then null else (
        select jsonb_build_object('faction',c.faction,'points',c.points)
        from public.fracture_engine_cards c
        where c.card_id=a.proof_card_id
      ) end
    ) order by a.seat_number
  ),'[]'::jsonb)
  into reports
  from public.fracture_engine_actions a
  where a.party_id=p.id and a.round_no=g.round_no and a.report is not null;

  select coalesce(jsonb_agg(
    jsonb_build_object(
      'round',r.round_no,
      'R',r.resistance_points,
      'RM',r.network_points,
      'winner',r.winner,
      'tiebreak',r.is_tiebreak
    ) order by r.round_no
  ),'[]'::jsonb)
  into rounds
  from public.fracture_engine_rounds r
  where r.party_id=p.id;

  select coalesce(jsonb_agg(
    jsonb_build_object(
      'id',e.id,
      'round',e.round_no,
      'type',e.event_type,
      'message',e.message,
      'at',e.created_at
    ) order by e.id desc
  ),'[]'::jsonb)
  into events
  from (
    select * from public.fracture_engine_events
    where party_id=p.id
    order by id desc
    limit 40
  ) e;

  select exists(
    select 1 from public.fracture_engine_votes
    where party_id=p.id and seat_number=seat
  ) into voted;

  return jsonb_build_object(
    'ok',true,
    'engine_version',canonical_engine_version,
    'engine_status',p.engine_status,
    'phase',g.phase,
    'party_code',p.party_code,
    'owner',p.owner_user_id=uid,
    'my_seat',seat,
    'my_identity',me.identity,
    'my_proof_used',me.proof_used,
    'human_player_count',p.human_player_count,
    'effective_player_count',p.effective_player_count,
    'round_count',p.round_count,
    'agents',agents,
    'round',g.round_no,
    'first_seat',g.first_seat,
    'turn_seat',g.turn_seat,
    'pick_pass',g.pick_pass,
    'state_version',g.state_version,
    'score',jsonb_build_object(
      'R',g.resistance_score,
      'RM',g.network_score,
      'R_rounds',g.resistance_rounds,
      'RM_rounds',g.network_rounds,
      'R_bonus',g.resistance_bonus,
      'RM_bonus',g.network_bonus
    ),
    'winner',g.winner,
    'final_accused',g.final_accused,
    'tiebreak',g.tiebreak_active,
    'voted',voted,
    'hand',hand,
    'center',center,
    'my_picks',picks,
    'seats',seats,
    'reports',reports,
    'rounds',rounds,
    'events',events,
    'keep_submitted',(
      select cardinality(kept_card_ids)=2
      from public.fracture_engine_actions
      where party_id=p.id and round_no=g.round_no and seat_number=seat
    ),
    'report_submitted',(
      select report is not null
      from public.fracture_engine_actions
      where party_id=p.id and round_no=g.round_no and seat_number=seat
    )
  );
end $$;

revoke all on function public._fracture_engine_get_state_raw(text) from public,anon,authenticated;
grant execute on function public._fracture_engine_get_state_raw(text) to service_role;
