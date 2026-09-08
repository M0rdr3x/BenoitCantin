-- SINJIRA V25 — modération et signalement du module « En direct ».
-- L'HUMAIN AVANT TOUT. Les preuves de signalement sont résolues côté serveur.

-- Le registre de signalements existant accepte désormais le réseau live.
alter table public.social_reports
  drop constraint if exists social_reports_network_check;
alter table public.social_reports
  add constraint social_reports_network_check
  check (network in ('real','character','live'));

-- Les décisions humaines existantes peuvent cibler le réseau live.
alter table private.moderation_decisions
  drop constraint if exists moderation_decisions_network_check;
alter table private.moderation_decisions
  add constraint moderation_decisions_network_check
  check (network in ('real','character','dating','account','live'));

-- Étend l'implémentation privilégiée existante. Le wrapper public reste
-- SECURITY INVOKER via la frontière V24.5.15.
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
  if not public.has_accepted_community_rules(v_user) then raise exception 'RULES_REQUIRED'; end if;
  if coalesce(p_network,'') not in ('real','character','live') then
    raise exception 'SOCIAL_REPORT_NETWORK_INVALID';
  end if;
  if coalesce(p_target_type,'') not in ('post','comment','message','profile') then
    raise exception 'SOCIAL_REPORT_TARGET_INVALID';
  end if;
  if p_network='live' and p_target_type<>'message' then
    raise exception 'SOCIAL_REPORT_TARGET_INVALID';
  end if;
  if coalesce(p_reason,'') not in ('harassment','sexual_content','pressure','scam','hate','threats','impersonation','spam','other') then
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
      'snapshot_source','server'
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

-- Le wrapper API demeure non privilégié et ne fait que déléguer à l'implémentation interne.
create or replace function public.social_report_content(
  p_network text,
  p_target_type text,
  p_target_id uuid,
  p_reason text,
  p_details text default null,
  p_block boolean default false
)
returns jsonb
language sql
security invoker
set search_path=''
as $$
  select sinjira_social_user_internal.social_report_content(
    p_network,p_target_type,p_target_id,p_reason,p_details,p_block
  );
$$;

revoke all on function public.social_report_content(text,text,uuid,text,text,boolean)
  from public,anon;
grant execute on function public.social_report_content(text,text,uuid,text,text,boolean)
  to authenticated,service_role;

-- Un masquage humain devient effectif pour tous les lecteurs du message live.
drop policy if exists social_live_messages_read on public.social_live_messages;
create policy social_live_messages_read on public.social_live_messages
for select to authenticated
using (
  public.moderation_content_visible('live','message',id)
  and exists(select 1 from public.social_live_rooms r where r.id=social_live_messages.room_id)
  and (
    user_id=(select auth.uid())
    or (
      public.sinjira_can_social_interact((select auth.uid()),user_id)
      and not public.social_is_blocked((select auth.uid()),user_id)
    )
  )
);

comment on function public.social_report_content(text,text,uuid,text,text,boolean) is
'Wrapper SECURITY INVOKER du signalement social. Le réseau live accepte uniquement les messages dont le reporter est membre du salon; preuve reconstruite côté serveur.';
