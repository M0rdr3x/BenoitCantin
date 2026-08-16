-- SINJIRA™ V24.4.6 — durcissement du moteur Fracture
-- Objectifs : rendre l'accusation finale immuable après soumission et exposer un marqueur serveur précis.

create or replace function public.get_sinjira_server_version()
returns text
language sql
stable
security definer
set search_path=public
as $$ select '24.4.6'::text; $$;
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;

create or replace function public.fracture_engine_health()
returns jsonb
language sql
stable
security definer
set search_path=public
as $$
  select jsonb_build_object(
    'ok',true,
    'engine_version','24.4.6',
    'tables',jsonb_build_object(
      'games',to_regclass('public.fracture_engine_games') is not null,
      'seats',to_regclass('public.fracture_engine_seats') is not null,
      'cards',to_regclass('public.fracture_engine_cards') is not null,
      'actions',to_regclass('public.fracture_engine_actions') is not null,
      'rounds',to_regclass('public.fracture_engine_rounds') is not null,
      'votes',to_regclass('public.fracture_engine_votes') is not null,
      'events',to_regclass('public.fracture_engine_events') is not null
    )
  );
$$;
revoke all on function public.fracture_engine_health() from public,anon;
grant execute on function public.fracture_engine_health() to authenticated,service_role;

-- Un vote final est une action définitive. L'ancienne fonction utilisait un UPSERT,
-- ce qui permettait à un client modifié de remplacer son vote tant que les autres
-- humains n'avaient pas encore soumis le leur. Le serveur refuse désormais toute
-- deuxième soumission pour le même siège.
create or replace function public.fracture_engine_submit_accusation(
  p_party_code text,
  p_accused_seats integer[]
)
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  uid uuid:=auth.uid();
  pid uuid;
  seat integer;
  g public.fracture_engine_games%rowtype;
  p public.fracture_parties%rowtype;
  agents integer;
  x integer;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  pid:=public._fracture_party_id(p_party_code);
  if pid is null then raise exception 'PARTY_NOT_FOUND'; end if;

  seat:=public._fracture_member_seat(pid,uid);
  if seat is null then raise exception 'NOT_A_MEMBER'; end if;

  select * into g
  from public.fracture_engine_games
  where party_id=pid
  for update;

  select * into p
  from public.fracture_parties
  where id=pid;

  if g.party_id is null then raise exception 'ENGINE_NOT_STARTED'; end if;
  if g.phase<>'final_vote' then raise exception 'WRONG_PHASE'; end if;

  if exists(
    select 1
    from public.fracture_engine_votes v
    where v.party_id=pid and v.seat_number=seat
  ) then
    raise exception 'ALREADY_SUBMITTED';
  end if;

  agents:=public.fracture_agents_for_seats(p.effective_player_count);
  if cardinality(p_accused_seats)<>agents then raise exception 'INVALID_ACCUSATION_COUNT'; end if;
  if (select count(distinct v) from unnest(p_accused_seats) v)<>agents then raise exception 'ACCUSATIONS_MUST_BE_DISTINCT'; end if;

  foreach x in array p_accused_seats loop
    if x=seat or not exists(
      select 1 from public.fracture_engine_seats s
      where s.party_id=pid and s.seat_number=x
    ) then
      raise exception 'INVALID_ACCUSED_SEAT';
    end if;
  end loop;

  insert into public.fracture_engine_votes(party_id,seat_number,user_id,accused_seats)
  values(pid,seat,uid,p_accused_seats);

  update public.fracture_engine_games
  set state_version=state_version+1,updated_at=now()
  where party_id=pid;

  perform public._fracture_resolve_final_vote(pid);
  return public.fracture_engine_get_state(p_party_code);
end;
$$;
revoke all on function public.fracture_engine_submit_accusation(text,integer[]) from public,anon;
grant execute on function public.fracture_engine_submit_accusation(text,integer[]) to authenticated;
