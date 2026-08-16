-- SINJIRA™ V24.3.1 — réparation propriétaire + contrôle d'accès Fracture
-- Cumulatif et idempotent après V24 / V24.1.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Réparation explicite et réutilisable du compte propriétaire AbyssTime.
-- Le frontend peut appeler cette RPC uniquement depuis le compte propriétaire.
-- ---------------------------------------------------------------------------
create or replace function public.ensure_sinjira_owner_character()
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  v_user uuid;
  v_submission uuid;
  v_character uuid;
  v_social_character uuid;
  v_parallel_character uuid;
  v_caller uuid:=auth.uid();
begin
  select u.id into v_user
  from auth.users u
  where lower(coalesce(u.email,''))='kingtyrano@gmail.com'
  limit 1;

  if v_user is null then
    return jsonb_build_object('ok',false,'code','OWNER_ACCOUNT_NOT_FOUND');
  end if;

  if v_caller is not null and v_caller<>v_user then
    raise exception 'OWNER_ONLY';
  end if;

  insert into public.internal_admin_users(user_id)
  values(v_user)
  on conflict(user_id) do nothing;

  insert into public.profiles(user_id,pseudo,display_name)
  values(v_user,'AbyssTime','Benoit Cantin')
  on conflict(user_id) do update set
    pseudo='AbyssTime',display_name='Benoit Cantin',updated_at=now();

  if to_regclass('public.character_social_profiles') is not null then
    select csp.character_id into v_social_character
    from public.character_social_profiles csp
    where csp.user_id=v_user
    limit 1;
  end if;

  if to_regclass('public.parallel_character_state') is not null then
    select pcs.character_id into v_parallel_character
    from public.parallel_character_state pcs
    where pcs.user_id=v_user
    limit 1;
  end if;

  v_character:=coalesce(v_social_character,v_parallel_character);

  if v_character is null then
    select c.id into v_character
    from public.characters c
    where c.user_id=v_user
    order by
      case when lower(coalesce(c.public_name,''))='abysstime' then 0 else 1 end,
      case when c.status in('assigned','published','approved','future') then 0 else 1 end,
      c.updated_at desc
    limit 1;
  end if;

  select s.id into v_submission
  from public.character_submissions s
  where s.user_id=v_user
  order by s.created_at desc
  limit 1;

  if v_character is null then
    insert into public.characters(
      submission_id,user_id,public_name,public_description,portrait_path,status,
      novel_id,novel_note,bible,ai_generated,visible_to_user,canon_status,canon_version
    ) values(
      v_submission,v_user,'AbyssTime','Personnage officiel associé au compte de Benoit Cantin.',
      '/assets/media/characters/abysstime.webp','assigned',null,
      'SINJIRA — Livre II (titre à confirmer)',
      jsonb_build_object(
        'owner','Benoit Cantin',
        'account','AbyssTime',
        'placement','SINJIRA — Livre II (titre à confirmer)',
        'source','Synchronisation propriétaire V24.3.1',
        'notes','Compléter la Bible narrative depuis l’administration SINJIRA™.'
      ),false,true,'PROVISOIRE','v1.0'
    ) returning id into v_character;
  else
    if v_submission is not null then
      update public.characters
      set submission_id=null,updated_at=now()
      where user_id=v_user and id<>v_character and submission_id=v_submission;
    end if;

    update public.characters
    set submission_id=null,status='archived',visible_to_user=false,updated_at=now()
    where user_id=v_user and id<>v_character;

    update public.characters
    set submission_id=coalesce(v_submission,submission_id),
        public_name='AbyssTime',
        public_description=coalesce(nullif(public_description,''),'Personnage officiel associé au compte de Benoit Cantin.'),
        portrait_path='/assets/media/characters/abysstime.webp',
        status='assigned',
        novel_id=null,
        novel_note='SINJIRA — Livre II (titre à confirmer)',
        visible_to_user=true,
        canon_status=coalesce(canon_status,'PROVISOIRE'),
        updated_at=now()
    where id=v_character;
  end if;

  if v_submission is not null then
    update public.character_submissions
    set status=case when id=v_submission then 'assigned' else 'archived' end,
        updated_at=now()
    where user_id=v_user;
  end if;

  if to_regclass('public.character_social_profiles') is not null then
    insert into public.character_social_profiles(
      character_id,user_id,public_name,public_description,portrait_path,status,updated_at
    )
    select c.id,c.user_id,c.public_name,c.public_description,c.portrait_path,c.status,now()
    from public.characters c
    where c.id=v_character
    on conflict(character_id) do update set
      user_id=excluded.user_id,
      public_name=excluded.public_name,
      public_description=excluded.public_description,
      portrait_path=excluded.portrait_path,
      status=excluded.status,
      updated_at=now();
  end if;

  if to_regclass('public.parallel_character_state') is not null then
    update public.parallel_character_state
    set character_id=v_character,user_id=v_user,updated_at=now()
    where user_id=v_user;

    if not found then
      insert into public.parallel_character_state(character_id,user_id,private_summary,state)
      values(v_character,v_user,'Chronique propriétaire prête à être initialisée.','{}'::jsonb)
      on conflict(character_id) do update set user_id=excluded.user_id,updated_at=now();
    end if;
  end if;

  if to_regclass('public.project_access') is not null and to_regclass('public.projects') is not null then
    insert into public.project_access(user_id,project_id,access_level,granted_by,source)
    select v_user,p.id,'tester',v_user,'migration'
    from public.projects p
    on conflict(user_id,project_id) do update set
      access_level='tester',granted_by=v_user,source='migration',expires_at=null,updated_at=now();
  end if;

  if to_regclass('public.user_entitlements') is not null and to_regclass('public.products') is not null then
    insert into public.user_entitlements(user_id,product_id,source)
    select v_user,p.id,'owner' from public.products p
    on conflict(user_id,product_id) do nothing;
  end if;

  if to_regclass('public.reader_library') is not null and to_regclass('public.novels') is not null then
    insert into public.reader_library(user_id,novel_id,last_opened_at)
    select v_user,n.id,now() from public.novels n
    on conflict(user_id,novel_id) do update set last_opened_at=greatest(public.reader_library.last_opened_at,excluded.last_opened_at);
  end if;

  return jsonb_build_object(
    'ok',true,
    'owner_user_id',v_user,
    'character_id',v_character,
    'submission_id',v_submission,
    'public_name','AbyssTime',
    'visible_to_user',true,
    'status','assigned',
    'unlimited_tokens',true,
    'all_content',true
  );
end;
$$;

revoke all on function public.ensure_sinjira_owner_character() from public,anon;
grant execute on function public.ensure_sinjira_owner_character() to authenticated,service_role;

select public.ensure_sinjira_owner_character();

-- ---------------------------------------------------------------------------
-- FRACTURE ONLINE — la licence est vérifiée côté serveur pour CHAQUE joueur.
-- Le propriétaire passe automatiquement grâce à has_sinjira_product().
-- ---------------------------------------------------------------------------
create or replace function public.create_fracture_party(
  p_human_player_count integer,
  p_round_count integer default 10,
  p_duo_first_player_seat integer default 1
)
returns table(
  party_id uuid,party_code text,seat_number integer,human_player_count integer,
  effective_player_count integer,play_mode text,round_count integer
)
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  uid uuid:=auth.uid();
  v_party_id uuid;
  v_party_code text;
  v_effective integer;
  v_mode text;
  v_rounds integer;
  v_project uuid;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.has_sinjira_product('fracture-du-reseau-mere',uid) then
    raise exception 'FRACTURE_ENTITLEMENT_REQUIRED';
  end if;
  if p_human_player_count not between 1 and 20 then raise exception 'INVALID_PLAYER_COUNT'; end if;

  v_effective:=case when p_human_player_count<=2 then 3 else p_human_player_count end;
  v_mode:=case when p_human_player_count=1 then 'solo' when p_human_player_count=2 then 'duo' else 'multiplayer' end;
  v_rounds:=case when p_human_player_count>=13 and p_round_count=6 then 6 else 10 end;

  loop
    v_party_code:='FRM-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,6));
    exit when not exists(select 1 from public.fracture_parties fp where fp.party_code=v_party_code);
  end loop;

  insert into public.fracture_parties(
    party_code,owner_user_id,human_player_count,effective_player_count,
    play_mode,round_count,duo_first_player_seat
  ) values(
    v_party_code,uid,p_human_player_count,v_effective,v_mode,v_rounds,
    case when v_mode='duo' then greatest(1,least(2,coalesce(p_duo_first_player_seat,1))) else null end
  ) returning id into v_party_id;

  insert into public.fracture_party_members(party_id,user_id,seat_number)
  values(v_party_id,uid,1);

  select pr.id into v_project from public.projects pr where pr.slug='fracture-du-reseau-mere' limit 1;

  insert into public.game_sessions(
    user_id,project_id,game_slug,title,status,player_count,human_player_count,
    effective_player_count,play_mode,party_code
  ) values(
    uid,v_project,'fracture-du-reseau-mere','Partie '||v_party_code||' - Fracture du Réseau-Mère',
    'in_progress',p_human_player_count,p_human_player_count,v_effective,v_mode,v_party_code
  ) on conflict do nothing;

  return query select v_party_id,v_party_code,1,p_human_player_count,v_effective,v_mode,v_rounds;
end;
$$;
revoke all on function public.create_fracture_party(integer,integer,integer) from public,anon;
grant execute on function public.create_fracture_party(integer,integer,integer) to authenticated;

create or replace function public.join_fracture_party(p_party_code text,p_seat_number integer default null)
returns table(
  party_id uuid,party_code text,seat_number integer,human_player_count integer,
  effective_player_count integer,play_mode text,round_count integer
)
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  uid uuid:=auth.uid();
  v_party public.fracture_parties%rowtype;
  v_seat integer;
  v_existing integer;
  v_project uuid;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.has_sinjira_product('fracture-du-reseau-mere',uid) then
    raise exception 'FRACTURE_ENTITLEMENT_REQUIRED';
  end if;

  select fp.* into v_party
  from public.fracture_parties fp
  where upper(fp.party_code)=upper(trim(p_party_code)) and fp.status='in_progress'
  limit 1;

  if v_party.id is null then raise exception 'PARTY_NOT_FOUND'; end if;

  select m.seat_number into v_existing
  from public.fracture_party_members m
  where m.party_id=v_party.id and m.user_id=uid;

  if v_existing is not null then
    return query select v_party.id,v_party.party_code,v_existing,v_party.human_player_count,v_party.effective_player_count,v_party.play_mode,v_party.round_count;
    return;
  end if;

  if v_party.human_player_count=1 then raise exception 'SOLO_PARTY_CANNOT_BE_JOINED'; end if;

  if p_seat_number is not null then
    if p_seat_number<1 or p_seat_number>v_party.human_player_count then raise exception 'INVALID_SEAT'; end if;
    if exists(select 1 from public.fracture_party_members m where m.party_id=v_party.id and m.seat_number=p_seat_number) then raise exception 'SEAT_ALREADY_TAKEN'; end if;
    v_seat:=p_seat_number;
  else
    select gs into v_seat
    from generate_series(1,v_party.human_player_count) gs
    where not exists(select 1 from public.fracture_party_members m where m.party_id=v_party.id and m.seat_number=gs)
    order by gs limit 1;
    if v_seat is null then raise exception 'PARTY_FULL'; end if;
  end if;

  insert into public.fracture_party_members(party_id,user_id,seat_number)
  values(v_party.id,uid,v_seat);

  select pr.id into v_project from public.projects pr where pr.slug='fracture-du-reseau-mere' limit 1;

  insert into public.game_sessions(
    user_id,project_id,game_slug,title,status,player_count,human_player_count,
    effective_player_count,play_mode,party_code
  ) values(
    uid,v_project,'fracture-du-reseau-mere','Partie '||v_party.party_code||' - Fracture du Réseau-Mère',
    'in_progress',v_party.human_player_count,v_party.human_player_count,v_party.effective_player_count,
    v_party.play_mode,v_party.party_code
  ) on conflict do nothing;

  return query select v_party.id,v_party.party_code,v_seat,v_party.human_player_count,v_party.effective_player_count,v_party.play_mode,v_party.round_count;
end;
$$;
revoke all on function public.join_fracture_party(text,integer) from public,anon;
grant execute on function public.join_fracture_party(text,integer) to authenticated;

select
  public.is_sinjira_owner(u.id) as owner_ok,
  public.has_sinjira_product('fracture-du-reseau-mere',u.id) as fracture_unlocked,
  (select c.public_name from public.characters c where c.user_id=u.id order by c.updated_at desc limit 1) as character_name,
  (select c.status from public.characters c where c.user_id=u.id order by c.updated_at desc limit 1) as character_status
from auth.users u
where lower(coalesce(u.email,''))='kingtyrano@gmail.com';
