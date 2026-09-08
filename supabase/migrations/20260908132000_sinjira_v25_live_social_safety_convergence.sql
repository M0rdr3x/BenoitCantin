-- SINJIRA V25 — convergence sécurité « En direct ».
-- Restaure intégralement les garanties V24.4.82 lors de l'extension du signalement à live.
-- Ajoute aussi le garde anti-exploitation aux messages live, surface inexistante en V24.4.82.

create or replace function sinjira_social_user_internal.social_report_content(
  p_network text,
  p_target_type text,
  p_target_id uuid,
  p_reason text,
  p_details text default null,
  p_block boolean default false
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_author uuid;
  v_body text;
  v_created_at timestamptz;
  v_parent_id uuid;
  v_details text:=nullif(btrim(coalesce(p_details,'')),'');
  v_report_id uuid;
  v_source text:='community';
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;

  -- Invariant V24.4.82 : signaler un danger doit rester possible même avant
  -- la réacceptation des règles communautaires.
  if coalesce(p_network,'') not in ('real','character','live') then
    raise exception 'SOCIAL_REPORT_NETWORK_INVALID';
  end if;
  if coalesce(p_target_type,'') not in ('post','comment','message','profile') then
    raise exception 'SOCIAL_REPORT_TARGET_INVALID';
  end if;
  if p_network='live' and p_target_type<>'message' then
    raise exception 'SOCIAL_REPORT_TARGET_INVALID';
  end if;
  if not private.sinjira_report_reason_allowed(p_reason) then
    raise exception 'SOCIAL_REPORT_REASON_INVALID';
  end if;
  if v_details is not null and char_length(v_details)>1200 then
    raise exception 'SOCIAL_REPORT_DETAILS_TOO_LONG';
  end if;

  perform pg_advisory_xact_lock(hashtextextended('sinjira-social-report:'||v_user::text,0));
  if (
    select count(*) from public.social_reports r
    where r.reporter_user_id=v_user and r.created_at>now()-interval '1 hour'
  )>=10 then
    raise exception 'SOCIAL_REPORT_RATE_LIMIT';
  end if;

  if p_network='real' and p_target_type='post' then
    select p.user_id,p.body,p.created_at into v_author,v_body,v_created_at
    from public.social_real_posts p where p.id=p_target_id;
  elsif p_network='real' and p_target_type='comment' then
    select c.user_id,c.body,c.created_at,c.post_id into v_author,v_body,v_created_at,v_parent_id
    from public.social_real_comments c where c.id=p_target_id;
  elsif p_network='real' and p_target_type='message' then
    select m.sender_user_id,m.body,m.created_at into v_author,v_body,v_created_at
    from public.social_real_messages m
    where m.id=p_target_id and v_user in(m.sender_user_id,m.recipient_user_id);
  elsif p_network='real' and p_target_type='profile' then
    select sp.user_id,coalesce(sp.pseudo,sp.display_name,'Membre SINJIRA™'),sp.updated_at
    into v_author,v_body,v_created_at
    from public.social_profiles sp where sp.user_id=p_target_id;
  elsif p_network='character' and p_target_type='post' then
    select p.user_id,p.body,p.created_at into v_author,v_body,v_created_at
    from public.social_character_posts p where p.id=p_target_id;
  elsif p_network='character' and p_target_type='comment' then
    select c.user_id,c.body,c.created_at,c.post_id into v_author,v_body,v_created_at,v_parent_id
    from public.social_character_comments c where c.id=p_target_id;
  elsif p_network='character' and p_target_type='message' then
    select m.sender_user_id,m.body,m.created_at into v_author,v_body,v_created_at
    from public.social_character_messages m
    where m.id=p_target_id and v_user in(m.sender_user_id,m.recipient_user_id);
  elsif p_network='character' and p_target_type='profile' then
    select cp.user_id,coalesce(cp.public_name,'Personnage SINJIRA™'),cp.updated_at
    into v_author,v_body,v_created_at
    from public.character_social_profiles cp where cp.character_id=p_target_id;
  elsif p_network='live' and p_target_type='message' then
    v_source:='live';
    select m.user_id,m.body,m.created_at,m.room_id
    into v_author,v_body,v_created_at,v_parent_id
    from public.social_live_messages m
    where m.id=p_target_id
      and exists(
        select 1 from public.social_live_room_members rm
        where rm.room_id=m.room_id and rm.user_id=v_user
      );
  end if;

  if v_author is null then raise exception 'SOCIAL_REPORT_TARGET_UNAVAILABLE'; end if;
  if v_author=v_user then raise exception 'SOCIAL_REPORT_SELF_FORBIDDEN'; end if;
  if not public.sinjira_can_social_interact(v_user,v_author) then
    raise exception 'SOCIAL_REPORT_TARGET_UNAVAILABLE';
  end if;
  if public.social_is_blocked(v_user,v_author) then
    raise exception 'SOCIAL_REPORT_TARGET_UNAVAILABLE';
  end if;

  if exists(
    select 1 from public.social_reports r
    where r.reporter_user_id=v_user
      and r.network=p_network
      and r.target_type=p_target_type
      and r.target_id=p_target_id
      and r.status='open'
  ) then
    raise exception 'SOCIAL_REPORT_ALREADY_OPEN';
  end if;

  insert into public.social_reports(reporter_user_id,network,target_type,target_id,reason,snapshot)
  values(
    v_user,p_network,p_target_type,p_target_id,p_reason,
    jsonb_strip_nulls(jsonb_build_object(
      'source',v_source,
      'body',left(coalesce(v_body,''),3000),
      'details',v_details,
      'content_created_at',v_created_at,
      'parent_id',v_parent_id,
      'identity_data_included',false,
      'snapshot_source','server',
      'priority_safety',p_reason in (
        'minor_safety','grooming','sexual_exploitation','human_trafficking',
        'paid_sexual_content','drugs_or_illicit_sales','off_platform_minor_contact'
      )
    ))
  ) returning id into v_report_id;

  if coalesce(p_block,false) then
    insert into public.social_blocks(blocker_user_id,blocked_user_id)
    values(v_user,v_author)
    on conflict (blocker_user_id,blocked_user_id) do nothing;
  end if;

  return jsonb_build_object(
    'ok',true,
    'report_id',v_report_id,
    'blocked',coalesce(p_block,false)
  );
end;
$$;

revoke all on function sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)
  from public,anon;
grant execute on function sinjira_social_user_internal.social_report_content(text,text,uuid,text,text,boolean)
  to authenticated,service_role;

-- Garde contenu dédié à la nouvelle surface live. Il réutilise le moteur
-- V24.4.82 sans persister de donnée supplémentaire.
create or replace function private.sinjira_live_message_content_policy_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_code text;
begin
  v_code:=private.sinjira_content_policy_code(new.body,new.user_id,null,'message');
  if v_code is not null then
    raise exception 'SINJIRA_CONTENT_POLICY_%',v_code using errcode='P0001';
  end if;
  return new;
end;
$$;

revoke all on function private.sinjira_live_message_content_policy_guard()
  from public,anon,authenticated;
grant execute on function private.sinjira_live_message_content_policy_guard() to service_role;

drop trigger if exists sinjira_content_policy_guard on public.social_live_messages;
create trigger sinjira_content_policy_guard
before insert on public.social_live_messages
for each row execute function private.sinjira_live_message_content_policy_guard();

-- La table d'invitations est server-only stricte : les fonctions SECURITY DEFINER
-- internes en sont propriétaires/mandataires; aucun CRUD direct service_role n'est requis.
revoke all on table private.social_live_room_invites from service_role;

comment on function private.sinjira_live_message_content_policy_guard() is
'Garde de contenu V24.4.82 appliqué aux messages En direct; aucune télémétrie additionnelle.';
