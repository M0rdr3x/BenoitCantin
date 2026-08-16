-- SINJIRA™ V24.4.17 — cohérence de version du moteur Fracture
-- Corrige une dérive historique : le moteur actif était 24.4.6 mais fracture_engine_start
-- persistait encore 24.4.1 et l'état brut annonçait 24.4.0.

alter table public.fracture_parties
  alter column engine_version set default '24.4.6';

create or replace function public.fracture_engine_start(p_party_code text)
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
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

  update public.fracture_parties
  set engine_version='24.4.6',engine_status='playing',engine_started_at=now(),updated_at=now()
  where id=p.id;
  perform public._fracture_event(p.id,1,'game_started','La partie commence.',jsonb_build_object('mode',p.play_mode,'humans',p.human_player_count,'seats',p.effective_player_count));
  perform public._fracture_start_round(p.id,1,false);
  return public.fracture_engine_get_state(p_party_code);
end $$;
revoke all on function public.fracture_engine_start(text) from public,anon;
grant execute on function public.fracture_engine_start(text) to authenticated,service_role;

create or replace function public.fracture_engine_get_state(p_party_code text)
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  base jsonb;
  cleaned_reports jsonb;
  my_seat integer;
  canonical_engine_version text;
begin
  base:=public._fracture_engine_get_state_raw(p_party_code);

  select coalesce(p.engine_version,'24.4.6')
    into canonical_engine_version
  from public.fracture_parties p
  where upper(p.party_code)=upper(trim(p_party_code))
  limit 1;

  base:=jsonb_set(
    base,
    '{engine_version}',
    to_jsonb(coalesce(canonical_engine_version,'24.4.6')),
    true
  );

  my_seat:=nullif(base->>'my_seat','')::integer;
  select coalesce(jsonb_agg(
    case when nullif(r->>'seat','')::integer=my_seat then r else r-'suspect' end
  ),'[]'::jsonb)
  into cleaned_reports
  from jsonb_array_elements(coalesce(base->'reports','[]'::jsonb)) r;
  return jsonb_set(base,'{reports}',cleaned_reports,true);
end $$;
revoke all on function public.fracture_engine_get_state(text) from public,anon;
grant execute on function public.fracture_engine_get_state(text) to authenticated,service_role;

-- Répare uniquement les parties encore actives : l'historique terminé reste intact.
update public.fracture_parties
set engine_version='24.4.6',updated_at=now()
where engine_status in ('lobby','playing','final_vote')
  and engine_version is distinct from '24.4.6';

create or replace function public.fracture_engine_health()
returns jsonb
language sql
stable
set search_path=public
as $$
  select jsonb_build_object(
    'ok',
      to_regclass('public.fracture_engine_games') is not null and
      to_regclass('public.fracture_engine_seats') is not null and
      to_regclass('public.fracture_engine_cards') is not null and
      to_regclass('public.fracture_engine_actions') is not null and
      to_regclass('public.fracture_engine_rounds') is not null and
      to_regclass('public.fracture_engine_votes') is not null and
      to_regclass('public.fracture_engine_events') is not null and
      to_regprocedure('public.create_fracture_party(integer,integer,integer)') is not null and
      to_regprocedure('public.join_fracture_party(text,integer)') is not null and
      to_regprocedure('public.fracture_engine_get_state(text)') is not null and
      to_regprocedure('public.fracture_engine_start(text)') is not null and
      to_regprocedure('public.fracture_engine_submit_keep(text,bigint[])') is not null and
      to_regprocedure('public.fracture_engine_pick(text,bigint)') is not null and
      to_regprocedure('public.fracture_engine_submit_report(text,text,integer,bigint)') is not null and
      to_regprocedure('public.fracture_engine_submit_accusation(text,integer[])') is not null and
      not exists(
        select 1 from public.fracture_parties
        where engine_status in ('lobby','playing','final_vote')
          and engine_version is distinct from '24.4.6'
      ),
    'engine_version','24.4.6',
    'version_consistent',not exists(
      select 1 from public.fracture_parties
      where engine_status in ('lobby','playing','final_vote')
        and engine_version is distinct from '24.4.6'
    ),
    'active_version_mismatches',(
      select count(*) from public.fracture_parties
      where engine_status in ('lobby','playing','final_vote')
        and engine_version is distinct from '24.4.6'
    ),
    'tables',jsonb_build_object(
      'games',to_regclass('public.fracture_engine_games') is not null,
      'seats',to_regclass('public.fracture_engine_seats') is not null,
      'cards',to_regclass('public.fracture_engine_cards') is not null,
      'actions',to_regclass('public.fracture_engine_actions') is not null,
      'rounds',to_regclass('public.fracture_engine_rounds') is not null,
      'votes',to_regclass('public.fracture_engine_votes') is not null,
      'events',to_regclass('public.fracture_engine_events') is not null
    ),
    'functions',jsonb_build_object(
      'create_party',to_regprocedure('public.create_fracture_party(integer,integer,integer)') is not null,
      'join_party',to_regprocedure('public.join_fracture_party(text,integer)') is not null,
      'get_state',to_regprocedure('public.fracture_engine_get_state(text)') is not null,
      'start',to_regprocedure('public.fracture_engine_start(text)') is not null,
      'submit_keep',to_regprocedure('public.fracture_engine_submit_keep(text,bigint[])') is not null,
      'pick',to_regprocedure('public.fracture_engine_pick(text,bigint)') is not null,
      'submit_report',to_regprocedure('public.fracture_engine_submit_report(text,text,integer,bigint)') is not null,
      'submit_accusation',to_regprocedure('public.fracture_engine_submit_accusation(text,integer[])') is not null
    )
  );
$$;
revoke all on function public.fracture_engine_health() from public,anon;
grant execute on function public.fracture_engine_health() to authenticated,service_role;
