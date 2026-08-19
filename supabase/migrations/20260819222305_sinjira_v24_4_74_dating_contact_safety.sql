create or replace function public.dating_close_connection(p_connection_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_user uuid:=auth.uid();
  v_me uuid;
  v_other_user uuid;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  select id into v_me from public.dating_profiles where user_id=v_user;
  if v_me is null then raise exception 'DATING_PROFILE_REQUIRED'; end if;

  select op.user_id into v_other_user
  from public.dating_connections c
  join public.dating_profiles op on op.id=case when c.profile_a_id=v_me then c.profile_b_id else c.profile_a_id end
  where c.id=p_connection_id
    and v_me in(c.profile_a_id,c.profile_b_id)
    and c.status in ('pending','accepted');

  if v_other_user is null then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;

  update public.dating_connections
  set status='closed',closed_at=now(),a_photo_consent=false,b_photo_consent=false
  where id=p_connection_id;

  insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path)
  values(v_other_user,'dating','Discussion de compatibilité terminée','Cette discussion de rencontres a été fermée.','dating_connection',p_connection_id,'/compte/rencontres.html');

  return jsonb_build_object('ok',true,'status','closed');
end;
$$;

create or replace function public.dating_block_connection(p_connection_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_user uuid:=auth.uid();
  v_me uuid;
  v_other_user uuid;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  select id into v_me from public.dating_profiles where user_id=v_user;
  if v_me is null then raise exception 'DATING_PROFILE_REQUIRED'; end if;

  select op.user_id into v_other_user
  from public.dating_connections c
  join public.dating_profiles op on op.id=case when c.profile_a_id=v_me then c.profile_b_id else c.profile_a_id end
  where c.id=p_connection_id
    and v_me in(c.profile_a_id,c.profile_b_id);

  if v_other_user is null then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;

  insert into public.social_blocks(blocker_user_id,blocked_user_id)
  values(v_user,v_other_user)
  on conflict (blocker_user_id,blocked_user_id) do nothing;

  update public.dating_connections
  set status='closed',closed_at=now(),a_photo_consent=false,b_photo_consent=false
  where id=p_connection_id;

  return jsonb_build_object('ok',true,'blocked',true,'status','closed');
end;
$$;

revoke all on function public.dating_close_connection(uuid), public.dating_block_connection(uuid) from public,anon;
grant execute on function public.dating_close_connection(uuid), public.dating_block_connection(uuid) to authenticated;
