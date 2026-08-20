-- SINJIRA V24.4.79 — centre de sécurité communautaire.
-- Les preuves de modération sont reconstruites côté serveur; le navigateur ne fournit plus de snapshot d'identité.

create or replace function public.social_report_content(
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
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.has_accepted_community_rules(v_user) then raise exception 'RULES_REQUIRED'; end if;
  if coalesce(p_network,'') not in ('real','character') then raise exception 'SOCIAL_REPORT_NETWORK_INVALID'; end if;
  if coalesce(p_target_type,'') not in ('post','comment','message','profile') then raise exception 'SOCIAL_REPORT_TARGET_INVALID'; end if;
  if coalesce(p_reason,'') not in ('harassment','sexual_content','pressure','scam','hate','threats','impersonation','spam','other') then
    raise exception 'SOCIAL_REPORT_REASON_INVALID';
  end if;
  if v_details is not null and char_length(v_details)>1200 then raise exception 'SOCIAL_REPORT_DETAILS_TOO_LONG'; end if;

  if (
    select count(*) from public.social_reports r
    where r.reporter_user_id=v_user and r.created_at>now()-interval '1 hour'
  )>=10 then raise exception 'SOCIAL_REPORT_RATE_LIMIT'; end if;

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
  end if;

  if v_author is null then raise exception 'SOCIAL_REPORT_TARGET_UNAVAILABLE'; end if;
  if v_author=v_user then raise exception 'SOCIAL_REPORT_SELF_FORBIDDEN'; end if;
  if not public.sinjira_can_social_interact(v_user,v_author) then raise exception 'SOCIAL_REPORT_TARGET_UNAVAILABLE'; end if;
  if public.social_is_blocked(v_user,v_author) then raise exception 'SOCIAL_REPORT_TARGET_UNAVAILABLE'; end if;

  if exists(
    select 1 from public.social_reports r
    where r.reporter_user_id=v_user
      and r.network=p_network
      and r.target_type=p_target_type
      and r.target_id=p_target_id
      and r.status='open'
  ) then raise exception 'SOCIAL_REPORT_ALREADY_OPEN'; end if;

  insert into public.social_reports(reporter_user_id,network,target_type,target_id,reason,snapshot)
  values(
    v_user,p_network,p_target_type,p_target_id,p_reason,
    jsonb_strip_nulls(jsonb_build_object(
      'source','community',
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

  return jsonb_build_object('ok',true,'report_id',v_report_id,'blocked',coalesce(p_block,false));
end;
$$;

create or replace function public.social_my_blocks()
returns table(blocked_user_id uuid,display_label text,blocked_at timestamptz)
language sql
stable
security definer
set search_path=pg_catalog,public
as $$
  select b.blocked_user_id,
         coalesce(sp.pseudo,sp.display_name,'Membre SINJIRA™')::text,
         b.created_at
  from public.social_blocks b
  left join public.social_profiles sp on sp.user_id=b.blocked_user_id
  where b.blocker_user_id=auth.uid()
  order by b.created_at desc;
$$;

create or replace function public.social_unblock_user(p_blocked_user_id uuid)
returns boolean
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare v_user uuid:=auth.uid(); v_count integer;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  delete from public.social_blocks
  where blocker_user_id=v_user and blocked_user_id=p_blocked_user_id;
  get diagnostics v_count=row_count;
  return v_count>0;
end;
$$;

create or replace function public.social_my_reports(p_limit integer default 20)
returns table(report_id uuid,source text,target_type text,reason text,status text,created_at timestamptz,reviewed_at timestamptz)
language sql
stable
security definer
set search_path=pg_catalog,public
as $$
  select r.id,
         coalesce(nullif(r.snapshot->>'source',''),r.network)::text,
         r.target_type,
         r.reason,
         r.status,
         r.created_at,
         r.reviewed_at
  from public.social_reports r
  where r.reporter_user_id=auth.uid()
  order by r.created_at desc
  limit greatest(1,least(coalesce(p_limit,20),50));
$$;

revoke all on function public.social_report_content(text,text,uuid,text,text,boolean), public.social_my_blocks(), public.social_unblock_user(uuid), public.social_my_reports(integer) from public,anon;
grant execute on function public.social_report_content(text,text,uuid,text,text,boolean), public.social_my_blocks(), public.social_unblock_user(uuid), public.social_my_reports(integer) to authenticated;

comment on function public.social_report_content(text,text,uuid,text,text,boolean) is
'Crée un signalement social avec cible et preuve résolues côté serveur, détails bornés, anti-spam et blocage facultatif.';
comment on function public.social_my_blocks() is
'Liste uniquement les comptes bloqués par auth.uid() avec un libellé minimal destiné à la gestion de ses propres blocages.';