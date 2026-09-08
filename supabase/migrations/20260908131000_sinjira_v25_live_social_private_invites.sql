-- SINJIRA V25 — invitations privées du module « En direct ».
-- Donnée durable minimale : invitation, état, expiration. Aucune présence persistée.

create table if not exists private.social_live_room_invites (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references public.social_live_rooms(id) on delete cascade,
  inviter_user_id uuid not null references auth.users(id) on delete cascade,
  invitee_user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'pending'
    check (status in ('pending','accepted','declined','revoked','expired')),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default (now()+interval '7 days'),
  responded_at timestamptz,
  check (inviter_user_id<>invitee_user_id),
  check (expires_at>created_at),
  check (
    (status='pending' and responded_at is null)
    or (status<>'pending' and responded_at is not null)
  )
);

create unique index if not exists social_live_room_invites_one_pending_idx
  on private.social_live_room_invites(room_id,invitee_user_id)
  where status='pending';
create index if not exists social_live_room_invites_invitee_pending_idx
  on private.social_live_room_invites(invitee_user_id,status,expires_at);
create index if not exists social_live_room_invites_inviter_created_idx
  on private.social_live_room_invites(inviter_user_id,created_at desc);

alter table private.social_live_room_invites enable row level security;
revoke all on table private.social_live_room_invites from public,anon,authenticated;
grant all on table private.social_live_room_invites to service_role;

-- Création : propriétaire uniquement, salon privé, même cohorte et interaction permise.
create or replace function sinjira_social_user_internal.social_live_invite_create(
  p_room_id uuid,
  p_invitee_user_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_room public.social_live_rooms%rowtype;
  v_invite_id uuid;
  v_expires_at timestamptz;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if p_invitee_user_id is null or p_invitee_user_id=v_user then
    raise exception 'SOCIAL_LIVE_INVITEE_UNAVAILABLE';
  end if;
  if not public.has_accepted_community_rules(v_user) then raise exception 'RULES_REQUIRED'; end if;
  if public.social_is_suspended(v_user) then raise exception 'SOCIAL_SUSPENDED'; end if;

  select * into v_room
  from public.social_live_rooms r
  where r.id=p_room_id
    and r.owner_user_id=v_user
    and r.visibility='private'
    and not r.is_archived;
  if v_room.id is null then raise exception 'SOCIAL_LIVE_ROOM_UNAVAILABLE'; end if;
  if v_room.audience<>public.sinjira_age_band(v_user) then
    raise exception 'SOCIAL_LIVE_ROOM_UNAVAILABLE';
  end if;

  if public.sinjira_age_band(p_invitee_user_id)<>v_room.audience
     or not public.sinjira_can_social_interact(v_user,p_invitee_user_id)
     or public.social_is_blocked(v_user,p_invitee_user_id) then
    raise exception 'SOCIAL_LIVE_INVITEE_UNAVAILABLE';
  end if;

  if exists(
    select 1 from public.social_live_room_members m
    where m.room_id=p_room_id and m.user_id=p_invitee_user_id
  ) then
    raise exception 'SOCIAL_LIVE_ALREADY_MEMBER';
  end if;

  perform pg_advisory_xact_lock(hashtextextended('sinjira-live-invite:'||v_user::text,0));

  update private.social_live_room_invites i
  set status='expired',responded_at=now()
  where i.inviter_user_id=v_user
    and i.status='pending'
    and i.expires_at<=now();

  if (
    select count(*) from private.social_live_room_invites i
    where i.inviter_user_id=v_user and i.created_at>now()-interval '1 hour'
  )>=20 then
    raise exception 'SOCIAL_LIVE_INVITE_RATE_LIMIT';
  end if;

  if (
    select count(*) from private.social_live_room_invites i
    where i.inviter_user_id=v_user and i.status='pending' and i.expires_at>now()
  )>=50 then
    raise exception 'SOCIAL_LIVE_INVITE_PENDING_LIMIT';
  end if;

  if exists(
    select 1 from private.social_live_room_invites i
    where i.room_id=p_room_id and i.invitee_user_id=p_invitee_user_id and i.status='pending'
  ) then
    raise exception 'SOCIAL_LIVE_INVITE_ALREADY_PENDING';
  end if;

  insert into private.social_live_room_invites(room_id,inviter_user_id,invitee_user_id)
  values(p_room_id,v_user,p_invitee_user_id)
  returning id,expires_at into v_invite_id,v_expires_at;

  return jsonb_build_object(
    'ok',true,
    'invite_id',v_invite_id,
    'room_id',p_room_id,
    'expires_at',v_expires_at
  );
end;
$$;

-- Liste minimale des invitations reçues. Aucun UUID d'inviteur n'est retourné.
create or replace function sinjira_social_user_internal.social_live_my_invites(
  p_limit integer default 20
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_rows jsonb;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.has_accepted_community_rules(v_user) then raise exception 'RULES_REQUIRED'; end if;

  update private.social_live_room_invites i
  set status='expired',responded_at=now()
  where i.invitee_user_id=v_user
    and i.status='pending'
    and i.expires_at<=now();

  select coalesce(jsonb_agg(to_jsonb(x) order by x.created_at desc),'[]'::jsonb)
  into v_rows
  from (
    select
      i.id as invite_id,
      r.id as room_id,
      r.slug as room_slug,
      r.name as room_name,
      coalesce(sp.pseudo,sp.display_name,'Membre SINJIRA™')::text as inviter_label,
      i.created_at,
      i.expires_at
    from private.social_live_room_invites i
    join public.social_live_rooms r on r.id=i.room_id
    left join public.social_profiles sp on sp.user_id=i.inviter_user_id
    where i.invitee_user_id=v_user
      and i.status='pending'
      and i.expires_at>now()
      and r.visibility='private'
      and not r.is_archived
      and r.audience=public.sinjira_age_band(v_user)
      and public.sinjira_can_social_interact(v_user,i.inviter_user_id)
      and not public.social_is_blocked(v_user,i.inviter_user_id)
    order by i.created_at desc
    limit greatest(1,least(coalesce(p_limit,20),50))
  ) x;

  return jsonb_build_object('ok',true,'invites',v_rows);
end;
$$;

-- Acceptation/refus par l'invité seulement. L'acceptation crée l'adhésion privée
-- côté serveur et réutilise le trigger anti-raid des adhésions.
create or replace function sinjira_social_user_internal.social_live_invite_respond(
  p_invite_id uuid,
  p_accept boolean
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_invite private.social_live_room_invites%rowtype;
  v_room public.social_live_rooms%rowtype;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;

  select * into v_invite
  from private.social_live_room_invites i
  where i.id=p_invite_id and i.invitee_user_id=v_user
  for update;
  if v_invite.id is null or v_invite.status<>'pending' then
    raise exception 'SOCIAL_LIVE_INVITE_UNAVAILABLE';
  end if;

  if v_invite.expires_at<=now() then
    update private.social_live_room_invites
    set status='expired',responded_at=now()
    where id=v_invite.id;
    return jsonb_build_object('ok',false,'status','expired');
  end if;

  select * into v_room from public.social_live_rooms where id=v_invite.room_id;
  if v_room.id is null
     or v_room.visibility<>'private'
     or v_room.is_archived
     or v_room.owner_user_id<>v_invite.inviter_user_id then
    update private.social_live_room_invites
    set status='revoked',responded_at=now()
    where id=v_invite.id;
    return jsonb_build_object('ok',false,'status','unavailable');
  end if;

  if not public.has_accepted_community_rules(v_user) then raise exception 'RULES_REQUIRED'; end if;
  if public.social_is_suspended(v_user) then raise exception 'SOCIAL_SUSPENDED'; end if;
  if v_room.audience<>public.sinjira_age_band(v_user)
     or not public.sinjira_can_social_interact(v_user,v_invite.inviter_user_id)
     or public.social_is_blocked(v_user,v_invite.inviter_user_id) then
    raise exception 'SOCIAL_LIVE_INVITE_UNAVAILABLE';
  end if;

  if coalesce(p_accept,false) then
    if not exists(
      select 1 from public.social_live_room_members m
      where m.room_id=v_invite.room_id and m.user_id=v_user
    ) then
      insert into public.social_live_room_members(room_id,user_id,role)
      values(v_invite.room_id,v_user,'member');
    end if;

    update private.social_live_room_invites
    set status='accepted',responded_at=now()
    where id=v_invite.id;
    return jsonb_build_object('ok',true,'status','accepted','room_id',v_invite.room_id);
  end if;

  update private.social_live_room_invites
  set status='declined',responded_at=now()
  where id=v_invite.id;
  return jsonb_build_object('ok',true,'status','declined');
end;
$$;

-- Révocation par le propriétaire du salon seulement.
create or replace function sinjira_social_user_internal.social_live_invite_revoke(
  p_invite_id uuid
)
returns boolean
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_count integer;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;

  update private.social_live_room_invites i
  set status='revoked',responded_at=now()
  where i.id=p_invite_id
    and i.inviter_user_id=v_user
    and i.status='pending'
    and exists(
      select 1 from public.social_live_rooms r
      where r.id=i.room_id and r.owner_user_id=v_user
    );
  get diagnostics v_count=row_count;
  return v_count>0;
end;
$$;

revoke all on function sinjira_social_user_internal.social_live_invite_create(uuid,uuid) from public,anon;
revoke all on function sinjira_social_user_internal.social_live_my_invites(integer) from public,anon;
revoke all on function sinjira_social_user_internal.social_live_invite_respond(uuid,boolean) from public,anon;
revoke all on function sinjira_social_user_internal.social_live_invite_revoke(uuid) from public,anon;
grant execute on function sinjira_social_user_internal.social_live_invite_create(uuid,uuid) to authenticated,service_role;
grant execute on function sinjira_social_user_internal.social_live_my_invites(integer) to authenticated,service_role;
grant execute on function sinjira_social_user_internal.social_live_invite_respond(uuid,boolean) to authenticated,service_role;
grant execute on function sinjira_social_user_internal.social_live_invite_revoke(uuid) to authenticated,service_role;

-- API publique : wrappers non privilégiés uniquement.
create or replace function public.social_live_invite_create(p_room_id uuid,p_invitee_user_id uuid)
returns jsonb language sql security invoker set search_path=''
as $$ select sinjira_social_user_internal.social_live_invite_create(p_room_id,p_invitee_user_id); $$;

create or replace function public.social_live_my_invites(p_limit integer default 20)
returns jsonb language sql security invoker set search_path=''
as $$ select sinjira_social_user_internal.social_live_my_invites(p_limit); $$;

create or replace function public.social_live_invite_respond(p_invite_id uuid,p_accept boolean)
returns jsonb language sql security invoker set search_path=''
as $$ select sinjira_social_user_internal.social_live_invite_respond(p_invite_id,p_accept); $$;

create or replace function public.social_live_invite_revoke(p_invite_id uuid)
returns boolean language sql security invoker set search_path=''
as $$ select sinjira_social_user_internal.social_live_invite_revoke(p_invite_id); $$;

revoke all on function public.social_live_invite_create(uuid,uuid) from public,anon;
revoke all on function public.social_live_my_invites(integer) from public,anon;
revoke all on function public.social_live_invite_respond(uuid,boolean) from public,anon;
revoke all on function public.social_live_invite_revoke(uuid) from public,anon;
grant execute on function public.social_live_invite_create(uuid,uuid) to authenticated,service_role;
grant execute on function public.social_live_my_invites(integer) to authenticated,service_role;
grant execute on function public.social_live_invite_respond(uuid,boolean) to authenticated,service_role;
grant execute on function public.social_live_invite_revoke(uuid) to authenticated,service_role;

comment on table private.social_live_room_invites is
'Invitations privées En direct : état et expiration seulement. Aucun annuaire public et aucune présence persistée.';
comment on function public.social_live_invite_create(uuid,uuid) is
'Wrapper SECURITY INVOKER : crée une invitation privée propriétaire-only avec cohorte/blocage et anti-raid côté serveur.';
comment on function public.social_live_my_invites(integer) is
'Wrapper SECURITY INVOKER : retourne uniquement les invitations du compte courant, avec libellé public minimal de l invitant.';
comment on function public.social_live_invite_respond(uuid,boolean) is
'Wrapper SECURITY INVOKER : accepte ou refuse sa propre invitation; une acceptation crée l adhésion privée côté serveur.';
