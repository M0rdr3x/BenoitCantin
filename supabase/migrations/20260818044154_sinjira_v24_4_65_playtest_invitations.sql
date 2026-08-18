create or replace function public.invite_sinjira_playtest_participant(
  p_playtest_id uuid,
  p_target_user_id uuid
) returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_admin uuid := auth.uid();
  v_status text;
  v_existing_status text;
  v_birth_date date;
  v_legacy_status text;
  v_age integer;
begin
  if v_admin is null then
    return jsonb_build_object('ok',false,'code','AUTH_REQUIRED');
  end if;
  if not exists (select 1 from public.internal_admin_users a where a.user_id=v_admin) then
    return jsonb_build_object('ok',false,'code','ADMIN_REQUIRED');
  end if;
  if p_target_user_id is null or p_playtest_id is null then
    return jsonb_build_object('ok',false,'code','INVALID_ARGUMENT');
  end if;

  select p.status into v_status
  from public.playtests p
  where p.id=p_playtest_id;
  if not found then
    return jsonb_build_object('ok',false,'code','PLAYTEST_NOT_FOUND');
  end if;
  if v_status not in ('open','active') then
    return jsonb_build_object('ok',false,'code','PLAYTEST_NOT_INVITABLE');
  end if;

  select s.date_of_birth,s.legacy_status
    into v_birth_date,v_legacy_status
  from public.account_safety_profiles s
  where s.user_id=p_target_user_id;
  if not found or v_birth_date is null then
    return jsonb_build_object('ok',false,'code','SAFETY_PROFILE_REQUIRED');
  end if;
  if coalesce(v_legacy_status,'active') <> 'active' then
    return jsonb_build_object('ok',false,'code','ACCOUNT_INACTIVE');
  end if;

  v_age := extract(year from age(current_date,v_birth_date))::integer;
  if v_age < 12 then
    return jsonb_build_object('ok',false,'code','AGE_INELIGIBLE');
  end if;
  if v_age < 18 and not exists (
    select 1 from public.guardian_links g
    where g.minor_user_id=p_target_user_id
      and g.status='verified'
      and g.revoked_at is null
  ) then
    return jsonb_build_object('ok',false,'code','GUARDIAN_REQUIRED');
  end if;

  select pp.status into v_existing_status
  from public.playtest_participants pp
  where pp.playtest_id=p_playtest_id and pp.user_id=p_target_user_id
  for update;

  if found then
    if v_existing_status='invited' then
      return jsonb_build_object('ok',true,'code','ALREADY_INVITED');
    end if;
    if v_existing_status not in ('refused','withdrawn') then
      return jsonb_build_object('ok',false,'code','PARTICIPATION_EXISTS','status',v_existing_status);
    end if;
    update public.playtest_participants
      set status='invited',reviewed_by=v_admin,reviewed_at=now(),updated_at=now()
    where playtest_id=p_playtest_id and user_id=p_target_user_id;
  else
    insert into public.playtest_participants(
      playtest_id,user_id,status,application_message,reviewed_by,reviewed_at
    ) values (
      p_playtest_id,p_target_user_id,'invited',null,v_admin,now()
    );
  end if;

  return jsonb_build_object('ok',true,'code','INVITED');
end;
$$;

revoke all on function public.invite_sinjira_playtest_participant(uuid,uuid) from public, anon, authenticated;
grant execute on function public.invite_sinjira_playtest_participant(uuid,uuid) to authenticated, service_role;

create or replace function public.accept_sinjira_playtest_invitation(
  p_playtest_id uuid
) returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_user uuid := auth.uid();
  v_admin uuid;
  v_project_id uuid;
  v_playtest_status text;
  v_birth_date date;
  v_legacy_status text;
  v_age integer;
begin
  if v_user is null then
    return jsonb_build_object('ok',false,'code','AUTH_REQUIRED');
  end if;

  select pp.reviewed_by,p.project_id,p.status
    into v_admin,v_project_id,v_playtest_status
  from public.playtest_participants pp
  join public.playtests p on p.id=pp.playtest_id
  where pp.playtest_id=p_playtest_id
    and pp.user_id=v_user
    and pp.status='invited'
  for update of pp;
  if not found then
    return jsonb_build_object('ok',false,'code','INVITATION_NOT_FOUND');
  end if;
  if v_playtest_status not in ('open','active') then
    return jsonb_build_object('ok',false,'code','PLAYTEST_CLOSED');
  end if;

  select s.date_of_birth,s.legacy_status
    into v_birth_date,v_legacy_status
  from public.account_safety_profiles s
  where s.user_id=v_user;
  if not found or v_birth_date is null then
    return jsonb_build_object('ok',false,'code','SAFETY_PROFILE_REQUIRED');
  end if;
  if coalesce(v_legacy_status,'active') <> 'active' then
    return jsonb_build_object('ok',false,'code','ACCOUNT_INACTIVE');
  end if;

  v_age := extract(year from age(current_date,v_birth_date))::integer;
  if v_age < 12 then
    return jsonb_build_object('ok',false,'code','AGE_INELIGIBLE');
  end if;
  if v_age < 18 and not exists (
    select 1 from public.guardian_links g
    where g.minor_user_id=v_user
      and g.status='verified'
      and g.revoked_at is null
  ) then
    return jsonb_build_object('ok',false,'code','GUARDIAN_REQUIRED');
  end if;

  update public.playtest_participants
    set status='approved',reviewed_at=coalesce(reviewed_at,now()),updated_at=now()
  where playtest_id=p_playtest_id and user_id=v_user and status='invited';

  insert into public.project_access(
    user_id,project_id,access_level,granted_by,source,expires_at
  ) values (
    v_user,v_project_id,'tester',v_admin,'playtest_invite',null
  )
  on conflict (user_id,project_id) do update
    set access_level='tester',
        granted_by=excluded.granted_by,
        source=excluded.source,
        expires_at=null,
        updated_at=now();

  return jsonb_build_object('ok',true,'code','ACCEPTED');
end;
$$;

revoke all on function public.accept_sinjira_playtest_invitation(uuid) from public, anon, authenticated;
grant execute on function public.accept_sinjira_playtest_invitation(uuid) to authenticated, service_role;
