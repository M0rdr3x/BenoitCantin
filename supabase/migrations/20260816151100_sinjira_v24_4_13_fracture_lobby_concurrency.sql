-- SINJIRA™ V24.4.13 — concurrence du lobby Fracture
-- Copie conforme de la migration déjà appliquée en production.

create or replace function public.create_fracture_party(
  p_human_player_count integer,p_round_count integer default 10,p_duo_first_player_seat integer default 1
)
returns table(party_id uuid,party_code text,seat_number integer,human_player_count integer,effective_player_count integer,play_mode text,round_count integer)
language plpgsql security definer set search_path=public,auth as $$
declare uid uuid:=auth.uid(); pid uuid; code text; eff integer; mode text; rounds integer; project_uuid uuid; attempt integer:=0;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.has_sinjira_product('fracture-du-reseau-mere',uid) then raise exception 'FRACTURE_ACCESS_REQUIRED'; end if;
  if p_human_player_count not between 1 and 20 then raise exception 'INVALID_PLAYER_COUNT'; end if;
  eff:=case when p_human_player_count<=2 then 3 else p_human_player_count end;
  mode:=case when p_human_player_count=1 then 'solo' when p_human_player_count=2 then 'duo' else 'multiplayer' end;
  rounds:=case when p_human_player_count>=13 and p_round_count=6 then 6 else 10 end;
  loop
    attempt:=attempt+1;
    if attempt>20 then raise exception 'PARTY_CODE_GENERATION_FAILED'; end if;
    code:='FRM-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,6));
    begin
      insert into public.fracture_parties(party_code,owner_user_id,human_player_count,effective_player_count,play_mode,round_count,duo_first_player_seat,engine_version,engine_status)
      values(code,uid,p_human_player_count,eff,mode,rounds,case when mode='duo' then greatest(1,least(2,coalesce(p_duo_first_player_seat,1))) else null end,'24.4.6','lobby') returning id into pid;
      exit;
    exception when unique_violation then null;
    end;
  end loop;
  insert into public.fracture_party_members(party_id,user_id,seat_number) values(pid,uid,1);
  select id into project_uuid from public.projects where slug='fracture-du-reseau-mere' limit 1;
  insert into public.game_sessions(user_id,project_id,game_slug,title,status,player_count,human_player_count,effective_player_count,play_mode,party_code)
  values(uid,project_uuid,'fracture-du-reseau-mere','Partie '||code||' - Fracture du Réseau-Mère','in_progress',p_human_player_count,p_human_player_count,eff,mode,code) on conflict do nothing;
  return query select pid,code,1,p_human_player_count,eff,mode,rounds;
end; $$;
revoke all on function public.create_fracture_party(integer,integer,integer) from public,anon;
grant execute on function public.create_fracture_party(integer,integer,integer) to authenticated;

create or replace function public.join_fracture_party(p_party_code text,p_seat_number integer default null)
returns table(party_id uuid,party_code text,seat_number integer,human_player_count integer,effective_player_count integer,play_mode text,round_count integer)
language plpgsql security definer set search_path=public,auth as $$
declare uid uuid:=auth.uid(); p public.fracture_parties%rowtype; seat integer; existing integer; project_uuid uuid;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.has_sinjira_product('fracture-du-reseau-mere',uid) then raise exception 'FRACTURE_ACCESS_REQUIRED'; end if;
  select fp.* into p from public.fracture_parties fp where upper(fp.party_code)=upper(trim(p_party_code)) and fp.status='in_progress' for update;
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
end; $$;
revoke all on function public.join_fracture_party(text,integer) from public,anon;
grant execute on function public.join_fracture_party(text,integer) to authenticated;
