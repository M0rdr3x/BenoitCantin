-- SINJIRA V25 — fondation « En direct » sécurisée.
-- L'HUMAIN AVANT TOUT. PROTÉGER SANS SURVEILLER.
-- Présence éphémère via Supabase Realtime Presence : aucune table de présence persistante.

create table if not exists public.social_live_rooms (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  slug text not null unique,
  name text not null,
  description text,
  visibility text not null default 'public' check (visibility in ('public','private')),
  audience text not null default public.sinjira_my_age_band() check (audience in ('adult','youth')),
  is_archived boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (slug ~ '^[a-z0-9][a-z0-9-]{2,47}$'),
  check (char_length(btrim(name)) between 1 and 80),
  check (description is null or char_length(description) <= 500)
);

create table if not exists public.social_live_room_members (
  room_id uuid not null references public.social_live_rooms(id) on delete cascade,
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  role text not null default 'member' check (role in ('owner','member')),
  joined_at timestamptz not null default now(),
  primary key (room_id,user_id)
);

create table if not exists public.social_live_messages (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references public.social_live_rooms(id) on delete cascade,
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  body text not null check (char_length(btrim(body)) between 1 and 2000),
  reply_to uuid references public.social_live_messages(id) on delete set null,
  created_at timestamptz not null default now()
);

create index if not exists social_live_rooms_owner_created_idx
  on public.social_live_rooms(owner_user_id,created_at desc);
create index if not exists social_live_rooms_audience_visibility_idx
  on public.social_live_rooms(audience,visibility,is_archived,created_at desc);
create index if not exists social_live_room_members_user_joined_idx
  on public.social_live_room_members(user_id,joined_at desc);
create index if not exists social_live_messages_room_created_idx
  on public.social_live_messages(room_id,created_at desc);
create index if not exists social_live_messages_user_created_idx
  on public.social_live_messages(user_id,created_at desc);
create index if not exists social_live_messages_reply_idx
  on public.social_live_messages(reply_to) where reply_to is not null;

alter table public.social_live_rooms enable row level security;
alter table public.social_live_room_members enable row level security;
alter table public.social_live_messages enable row level security;

revoke all on table public.social_live_rooms from public,anon,authenticated;
revoke all on table public.social_live_room_members from public,anon,authenticated;
revoke all on table public.social_live_messages from public,anon,authenticated;

grant select on public.social_live_rooms to authenticated;
grant insert(slug,name,description,visibility) on public.social_live_rooms to authenticated;
grant update(slug,name,description,visibility,is_archived) on public.social_live_rooms to authenticated;

grant select on public.social_live_room_members to authenticated;
grant insert(room_id) on public.social_live_room_members to authenticated;
grant delete on public.social_live_room_members to authenticated;

grant select on public.social_live_messages to authenticated;
grant insert(room_id,body,reply_to) on public.social_live_messages to authenticated;

grant all on table public.social_live_rooms,public.social_live_room_members,public.social_live_messages to service_role;

-- Création de salon : identité et cohorte viennent uniquement du serveur.
create or replace function public.social_live_room_insert_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_uid uuid:=auth.uid();
  v_band text;
begin
  if coalesce(auth.jwt()->>'role','')='service_role' then
    return new;
  end if;
  if v_uid is null or new.owner_user_id<>v_uid then
    raise exception 'SOCIAL_LIVE_OWNER_MISMATCH';
  end if;
  v_band:=public.sinjira_age_band(v_uid);
  if v_band not in ('adult','youth') or new.audience<>v_band then
    raise exception 'SOCIAL_LIVE_AUDIENCE_FORBIDDEN';
  end if;
  if not public.has_accepted_community_rules(v_uid) then
    raise exception 'RULES_REQUIRED';
  end if;
  if public.social_is_suspended(v_uid) then
    raise exception 'SOCIAL_SUSPENDED';
  end if;

  perform pg_advisory_xact_lock(hashtextextended('sinjira-live-room:'||v_uid::text,0));
  if (select count(*) from public.social_live_rooms r
      where r.owner_user_id=v_uid and r.created_at>now()-interval '1 hour')>=3 then
    raise exception 'SOCIAL_LIVE_ROOM_RATE_LIMIT';
  end if;
  return new;
end;
$$;

revoke all on function public.social_live_room_insert_guard() from public,anon,authenticated;
grant execute on function public.social_live_room_insert_guard() to service_role;

drop trigger if exists social_live_room_insert_guard_trigger on public.social_live_rooms;
create trigger social_live_room_insert_guard_trigger
before insert on public.social_live_rooms
for each row execute function public.social_live_room_insert_guard();

-- Le propriétaire devient membre automatiquement; aucun client ne peut s'attribuer le rôle owner.
create or replace function public.social_live_room_owner_membership()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
begin
  insert into public.social_live_room_members(room_id,user_id,role)
  values(new.id,new.owner_user_id,'owner')
  on conflict(room_id,user_id) do update set role='owner';
  return new;
end;
$$;

revoke all on function public.social_live_room_owner_membership() from public,anon,authenticated;
grant execute on function public.social_live_room_owner_membership() to service_role;

drop trigger if exists social_live_room_owner_membership_trigger on public.social_live_rooms;
create trigger social_live_room_owner_membership_trigger
after insert on public.social_live_rooms
for each row execute function public.social_live_room_owner_membership();

-- Limite des adhésions publiques par compte, sans IP ni géolocalisation.
create or replace function public.social_live_member_insert_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_uid uuid:=auth.uid();
begin
  if new.role='owner' then
    return new;
  end if;
  if coalesce(auth.jwt()->>'role','')='service_role' then
    return new;
  end if;
  if v_uid is null or new.user_id<>v_uid or new.role<>'member' then
    raise exception 'SOCIAL_LIVE_MEMBER_IDENTITY_FORBIDDEN';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('sinjira-live-join:'||v_uid::text,0));
  if (select count(*) from public.social_live_room_members m
      where m.user_id=v_uid and m.role='member' and m.joined_at>now()-interval '1 hour')>=20 then
    raise exception 'SOCIAL_LIVE_JOIN_RATE_LIMIT';
  end if;
  return new;
end;
$$;

revoke all on function public.social_live_member_insert_guard() from public,anon,authenticated;
grant execute on function public.social_live_member_insert_guard() to service_role;

drop trigger if exists social_live_member_insert_guard_trigger on public.social_live_room_members;
create trigger social_live_member_insert_guard_trigger
before insert on public.social_live_room_members
for each row execute function public.social_live_member_insert_guard();

-- Anti-spam / anti-rafale. Les limites sont attachées au compte, jamais à une IP.
create or replace function public.social_live_message_insert_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_uid uuid:=auth.uid();
  v_audience text;
  v_reply_user uuid;
begin
  new.body:=btrim(new.body);
  if coalesce(auth.jwt()->>'role','')='service_role' then
    return new;
  end if;
  if v_uid is null or new.user_id<>v_uid then
    raise exception 'SOCIAL_LIVE_AUTHOR_MISMATCH';
  end if;
  if not public.has_accepted_community_rules(v_uid) then
    raise exception 'RULES_REQUIRED';
  end if;
  if public.social_is_suspended(v_uid) then
    raise exception 'SOCIAL_SUSPENDED';
  end if;

  select r.audience into v_audience
  from public.social_live_rooms r
  where r.id=new.room_id and not r.is_archived;
  if v_audience is null or v_audience<>public.sinjira_age_band(v_uid) then
    raise exception 'SOCIAL_LIVE_ROOM_FORBIDDEN';
  end if;
  if not exists(select 1 from public.social_live_room_members m where m.room_id=new.room_id and m.user_id=v_uid) then
    raise exception 'SOCIAL_LIVE_MEMBERSHIP_REQUIRED';
  end if;

  if new.reply_to is not null then
    select m.user_id into v_reply_user
    from public.social_live_messages m
    where m.id=new.reply_to and m.room_id=new.room_id;
    if v_reply_user is null then
      raise exception 'SOCIAL_LIVE_REPLY_INVALID';
    end if;
    if public.social_is_blocked(v_uid,v_reply_user) then
      raise exception 'SOCIAL_LIVE_REPLY_BLOCKED';
    end if;
  end if;

  perform pg_advisory_xact_lock(hashtextextended('sinjira-live-message:'||v_uid::text,0));
  if (select count(*) from public.social_live_messages m
      where m.user_id=v_uid and m.created_at>now()-interval '10 seconds')>=8 then
    raise exception 'SOCIAL_LIVE_RATE_LIMIT_BURST';
  end if;
  if (select count(*) from public.social_live_messages m
      where m.user_id=v_uid and m.created_at>now()-interval '1 minute')>=40 then
    raise exception 'SOCIAL_LIVE_RATE_LIMIT_MINUTE';
  end if;
  if exists(select 1 from public.social_live_messages m
      where m.user_id=v_uid and m.room_id=new.room_id
        and m.created_at>now()-interval '8 seconds' and m.body=new.body) then
    raise exception 'SOCIAL_LIVE_DUPLICATE_MESSAGE';
  end if;
  return new;
end;
$$;

revoke all on function public.social_live_message_insert_guard() from public,anon,authenticated;
grant execute on function public.social_live_message_insert_guard() to service_role;

drop trigger if exists social_live_message_insert_guard_trigger on public.social_live_messages;
create trigger social_live_message_insert_guard_trigger
before insert on public.social_live_messages
for each row execute function public.social_live_message_insert_guard();

-- updated_at suit la convention existante du dépôt.
drop trigger if exists social_live_rooms_updated_at on public.social_live_rooms;
create trigger social_live_rooms_updated_at
before update on public.social_live_rooms
for each row execute function public.set_updated_at();

-- RLS salons : même cohorte seulement; les salons privés exigent une adhésion persistée.
drop policy if exists social_live_rooms_read on public.social_live_rooms;
create policy social_live_rooms_read on public.social_live_rooms
for select to authenticated
using (
  not is_archived
  and audience=public.sinjira_my_age_band()
  and public.has_accepted_community_rules((select auth.uid()))
  and not public.social_is_suspended((select auth.uid()))
  and (owner_user_id=(select auth.uid()) or not public.social_is_blocked((select auth.uid()),owner_user_id))
  and (
    visibility='public'
    or owner_user_id=(select auth.uid())
    or exists(
      select 1 from public.social_live_room_members m
      where m.room_id=social_live_rooms.id and m.user_id=(select auth.uid())
    )
  )
);

drop policy if exists social_live_rooms_insert on public.social_live_rooms;
create policy social_live_rooms_insert on public.social_live_rooms
for insert to authenticated
with check (
  owner_user_id=(select auth.uid())
  and audience=public.sinjira_my_age_band()
  and audience in ('adult','youth')
  and public.has_accepted_community_rules((select auth.uid()))
  and not public.social_is_suspended((select auth.uid()))
);

drop policy if exists social_live_rooms_update on public.social_live_rooms;
create policy social_live_rooms_update on public.social_live_rooms
for update to authenticated
using (owner_user_id=(select auth.uid()))
with check (
  owner_user_id=(select auth.uid())
  and audience=public.sinjira_my_age_band()
  and public.has_accepted_community_rules((select auth.uid()))
  and not public.social_is_suspended((select auth.uid()))
);

-- Les adhésions ne forment pas un annuaire durable : chacun ne lit que sa propre ligne.
drop policy if exists social_live_members_self_read on public.social_live_room_members;
create policy social_live_members_self_read on public.social_live_room_members
for select to authenticated
using (user_id=(select auth.uid()));

drop policy if exists social_live_members_public_join on public.social_live_room_members;
create policy social_live_members_public_join on public.social_live_room_members
for insert to authenticated
with check (
  user_id=(select auth.uid())
  and role='member'
  and public.has_accepted_community_rules((select auth.uid()))
  and not public.social_is_suspended((select auth.uid()))
  and exists(
    select 1 from public.social_live_rooms r
    where r.id=social_live_room_members.room_id
      and r.visibility='public'
      and not r.is_archived
      and r.audience=public.sinjira_my_age_band()
      and (r.owner_user_id=(select auth.uid()) or not public.social_is_blocked((select auth.uid()),r.owner_user_id))
  )
);

drop policy if exists social_live_members_self_leave on public.social_live_room_members;
create policy social_live_members_self_leave on public.social_live_room_members
for delete to authenticated
using (user_id=(select auth.uid()) and role='member');

-- Les messages restent lisibles via RLS; un blocage masque l'auteur immédiatement.
drop policy if exists social_live_messages_read on public.social_live_messages;
create policy social_live_messages_read on public.social_live_messages
for select to authenticated
using (
  exists(select 1 from public.social_live_rooms r where r.id=social_live_messages.room_id)
  and (
    user_id=(select auth.uid())
    or (
      public.sinjira_can_social_interact((select auth.uid()),user_id)
      and not public.social_is_blocked((select auth.uid()),user_id)
    )
  )
);

drop policy if exists social_live_messages_insert on public.social_live_messages;
create policy social_live_messages_insert on public.social_live_messages
for insert to authenticated
with check (
  user_id=(select auth.uid())
  and public.has_accepted_community_rules((select auth.uid()))
  and not public.social_is_suspended((select auth.uid()))
  and exists(
    select 1 from public.social_live_room_members m
    where m.room_id=social_live_messages.room_id and m.user_id=(select auth.uid())
  )
  and exists(select 1 from public.social_live_rooms r where r.id=social_live_messages.room_id)
);

-- Notification Realtime minimale : jamais le corps du message dans le Broadcast.
-- Le client reçoit l'identifiant puis relit la ligne via RLS.
create or replace function public.social_live_notify_message_insert()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,realtime
as $$
begin
  perform realtime.send(
    jsonb_build_object(
      'message_id',new.id,
      'room_id',new.room_id,
      'created_at',new.created_at
    ),
    'message_created',
    'sinjira-live:'||new.room_id::text,
    true
  );
  return null;
end;
$$;

revoke all on function public.social_live_notify_message_insert() from public,anon,authenticated;
grant execute on function public.social_live_notify_message_insert() to service_role;

drop trigger if exists social_live_message_notify_trigger on public.social_live_messages;
create trigger social_live_message_notify_trigger
after insert on public.social_live_messages
for each row execute function public.social_live_notify_message_insert();

-- Realtime Authorization. Les politiques RESTRICTIVE empêchent une politique générique future
-- de rendre le namespace sinjira-live:* public par accident.
drop policy if exists sinjira_live_realtime_read on realtime.messages;
create policy sinjira_live_realtime_read
on realtime.messages
for select to authenticated
using (
  realtime.messages.extension in ('broadcast','presence')
  and exists(
    select 1
    from public.social_live_room_members m
    join public.social_live_rooms r on r.id=m.room_id
    where m.user_id=(select auth.uid())
      and not r.is_archived
      and (r.owner_user_id=(select auth.uid()) or not public.social_is_blocked((select auth.uid()),r.owner_user_id))
      and ('sinjira-live:'||m.room_id::text)=(select realtime.topic())
  )
);

drop policy if exists sinjira_live_realtime_read_guard on realtime.messages;
create policy sinjira_live_realtime_read_guard
on realtime.messages as restrictive
for select to authenticated
using (
  (select realtime.topic()) not like 'sinjira-live:%'
  or (
    realtime.messages.extension in ('broadcast','presence')
    and exists(
      select 1
      from public.social_live_room_members m
      join public.social_live_rooms r on r.id=m.room_id
      where m.user_id=(select auth.uid())
        and not r.is_archived
        and (r.owner_user_id=(select auth.uid()) or not public.social_is_blocked((select auth.uid()),r.owner_user_id))
        and ('sinjira-live:'||m.room_id::text)=(select realtime.topic())
    )
  )
);

drop policy if exists sinjira_live_realtime_presence_write on realtime.messages;
create policy sinjira_live_realtime_presence_write
on realtime.messages
for insert to authenticated
with check (
  realtime.messages.extension='presence'
  and exists(
    select 1
    from public.social_live_room_members m
    join public.social_live_rooms r on r.id=m.room_id
    where m.user_id=(select auth.uid())
      and not r.is_archived
      and (r.owner_user_id=(select auth.uid()) or not public.social_is_blocked((select auth.uid()),r.owner_user_id))
      and ('sinjira-live:'||m.room_id::text)=(select realtime.topic())
  )
);

drop policy if exists sinjira_live_realtime_write_guard on realtime.messages;
create policy sinjira_live_realtime_write_guard
on realtime.messages as restrictive
for insert to authenticated
with check (
  (select realtime.topic()) not like 'sinjira-live:%'
  or (
    realtime.messages.extension='presence'
    and exists(
      select 1
      from public.social_live_room_members m
      join public.social_live_rooms r on r.id=m.room_id
      where m.user_id=(select auth.uid())
        and not r.is_archived
        and (r.owner_user_id=(select auth.uid()) or not public.social_is_blocked((select auth.uid()),r.owner_user_id))
        and ('sinjira-live:'||m.room_id::text)=(select realtime.topic())
    )
  )
);

comment on table public.social_live_rooms is
'Fondation En direct SINJIRA. Cohorte serveur adult/youth; salons public/private; aucune géolocalisation.';
comment on table public.social_live_room_members is
'Adhésions En direct. Pas un annuaire public; Presence Realtime reste éphémère.';
comment on table public.social_live_messages is
'Messages persistés En direct. Broadcast minimal puis relecture RLS; aucun payload client n est une source de vérité.';
