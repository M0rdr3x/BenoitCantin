-- SINJIRA V25 — codes de partage privés pour « En direct ».
-- Un code est une invitation bearer, volontairement partagée hors SINJIRA.
-- Le secret brut n'est jamais stocké : seul son SHA-256 est conservé.
-- Un code expire après 24 h et ne peut être utilisé qu'une seule fois.

create table if not exists private.social_live_room_share_codes (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references public.social_live_rooms(id) on delete cascade,
  creator_user_id uuid not null references auth.users(id) on delete cascade,
  code_hash text not null unique check (code_hash ~ '^[a-f0-9]{64}$'),
  status text not null default 'active'
    check (status in ('active','used','revoked','expired')),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default (now()+interval '24 hours'),
  closed_at timestamptz,
  check (expires_at>created_at),
  check (
    (status='active' and closed_at is null)
    or (status in ('used','revoked','expired') and closed_at is not null)
  )
);

create index if not exists social_live_room_share_codes_creator_idx
  on private.social_live_room_share_codes(creator_user_id,status,created_at desc);
create index if not exists social_live_room_share_codes_room_idx
  on private.social_live_room_share_codes(room_id,status,expires_at);

alter table private.social_live_room_share_codes enable row level security;
revoke all on table private.social_live_room_share_codes from public,anon,authenticated,service_role;

-- Création par le propriétaire d'un salon privé seulement. Le code brut est
-- retourné une fois; les lectures suivantes ne retournent jamais le secret.
create or replace function sinjira_social_user_internal.social_live_share_code_create(
  p_room_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private,extensions
as $$
declare
  v_user uuid:=auth.uid();
  v_room public.social_live_rooms%rowtype;
  v_raw text;
  v_hash text;
  v_code_id uuid;
  v_expires_at timestamptz;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
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

  perform pg_advisory_xact_lock(hashtextextended('sinjira-live-share-code:'||v_user::text,0));

  update private.social_live_room_share_codes c
  set status='expired',closed_at=now()
  where c.creator_user_id=v_user
    and c.status='active'
    and c.expires_at<=now();

  if (
    select count(*) from private.social_live_room_share_codes c
    where c.creator_user_id=v_user and c.created_at>now()-interval '1 hour'
  )>=10 then
    raise exception 'SOCIAL_LIVE_SHARE_CODE_RATE_LIMIT';
  end if;

  if (
    select count(*) from private.social_live_room_share_codes c
    where c.creator_user_id=v_user and c.status='active' and c.expires_at>now()
  )>=20 then
    raise exception 'SOCIAL_LIVE_SHARE_CODE_ACTIVE_LIMIT';
  end if;

  v_raw:=encode(gen_random_bytes(32),'hex');
  v_hash:=encode(digest(v_raw,'sha256'),'hex');

  insert into private.social_live_room_share_codes(
    room_id,creator_user_id,code_hash
  ) values (
    p_room_id,v_user,v_hash
  )
  returning id,expires_at into v_code_id,v_expires_at;

  return jsonb_build_object(
    'ok',true,
    'code_id',v_code_id,
    'code',v_raw,
    'display_once',true,
    'expires_at',v_expires_at
  );
end;
$$;

-- Liste self-only. Jamais de secret brut, de hash ou d'identité de la personne
-- ayant utilisé le code.
create or replace function sinjira_social_user_internal.social_live_share_code_list(
  p_room_id uuid default null,
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

  update private.social_live_room_share_codes c
  set status='expired',closed_at=now()
  where c.creator_user_id=v_user
    and c.status='active'
    and c.expires_at<=now();

  select coalesce(jsonb_agg(to_jsonb(x) order by x.created_at desc),'[]'::jsonb)
  into v_rows
  from (
    select
      c.id as code_id,
      r.id as room_id,
      r.slug as room_slug,
      r.name as room_name,
      c.status,
      c.created_at,
      c.expires_at,
      c.closed_at
    from private.social_live_room_share_codes c
    join public.social_live_rooms r on r.id=c.room_id
    where c.creator_user_id=v_user
      and (p_room_id is null or c.room_id=p_room_id)
    order by c.created_at desc
    limit greatest(1,least(coalesce(p_limit,20),50))
  ) x;

  return jsonb_build_object('ok',true,'codes',v_rows);
end;
$$;

-- Révocation self-only du propriétaire qui a créé le code.
create or replace function sinjira_social_user_internal.social_live_share_code_revoke(
  p_code_id uuid
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

  update private.social_live_room_share_codes c
  set status='revoked',closed_at=now()
  where c.id=p_code_id
    and c.creator_user_id=v_user
    and c.status='active';
  get diagnostics v_count=row_count;
  return v_count>0;
end;
$$;

-- Rachat : aucune recherche de profil et aucun identifiant de destinataire.
-- Le bearer code est verrouillé puis consommé atomiquement après toutes les
-- vérifications sociales. L'insertion d'adhésion réutilise le trigger anti-raid.
create or replace function sinjira_social_user_internal.social_live_share_code_redeem(
  p_code text
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private,extensions
as $$
declare
  v_user uuid:=auth.uid();
  v_raw text:=lower(btrim(coalesce(p_code,'')));
  v_hash text;
  v_code private.social_live_room_share_codes%rowtype;
  v_room public.social_live_rooms%rowtype;
  v_already_member boolean;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if v_raw !~ '^[a-f0-9]{64}$' then
    raise exception 'SOCIAL_LIVE_SHARE_CODE_UNAVAILABLE';
  end if;
  if not public.has_accepted_community_rules(v_user) then raise exception 'RULES_REQUIRED'; end if;
  if public.social_is_suspended(v_user) then raise exception 'SOCIAL_SUSPENDED'; end if;

  v_hash:=encode(digest(v_raw,'sha256'),'hex');
  perform pg_advisory_xact_lock(hashtextextended('sinjira-live-share-code-redeem:'||v_hash,0));

  select * into v_code
  from private.social_live_room_share_codes c
  where c.code_hash=v_hash
    and c.status='active'
    and c.expires_at>now()
  for update;
  if v_code.id is null then raise exception 'SOCIAL_LIVE_SHARE_CODE_UNAVAILABLE'; end if;
  if v_code.creator_user_id=v_user then raise exception 'SOCIAL_LIVE_SHARE_CODE_UNAVAILABLE'; end if;

  select * into v_room
  from public.social_live_rooms r
  where r.id=v_code.room_id
    and r.owner_user_id=v_code.creator_user_id
    and r.visibility='private'
    and not r.is_archived;
  if v_room.id is null then raise exception 'SOCIAL_LIVE_SHARE_CODE_UNAVAILABLE'; end if;

  if public.social_is_suspended(v_code.creator_user_id)
     or v_room.audience<>public.sinjira_age_band(v_user)
     or not public.sinjira_can_social_interact(v_user,v_code.creator_user_id)
     or public.social_is_blocked(v_user,v_code.creator_user_id) then
    raise exception 'SOCIAL_LIVE_SHARE_CODE_UNAVAILABLE';
  end if;

  select exists(
    select 1 from public.social_live_room_members m
    where m.room_id=v_room.id and m.user_id=v_user
  ) into v_already_member;

  if not v_already_member then
    insert into public.social_live_room_members(room_id,user_id,role)
    values(v_room.id,v_user,'member');

    -- Si une invitation directe existait déjà, la fermer évite qu'elle reste
    -- pendante après l'accès par code. Sinon, aucune nouvelle relation ciblée
    -- inviter→invité n'est créée.
    update private.social_live_room_invites i
    set status='accepted',responded_at=now()
    where i.room_id=v_room.id
      and i.invitee_user_id=v_user
      and i.status='pending';
  end if;

  update private.social_live_room_share_codes
  set status='used',closed_at=now()
  where id=v_code.id;

  return jsonb_build_object(
    'ok',true,
    'status',case when v_already_member then 'already_member' else 'joined' end,
    'room_id',v_room.id,
    'room_slug',v_room.slug
  );
end;
$$;

revoke all on function sinjira_social_user_internal.social_live_share_code_create(uuid) from public,anon;
revoke all on function sinjira_social_user_internal.social_live_share_code_list(uuid,integer) from public,anon;
revoke all on function sinjira_social_user_internal.social_live_share_code_revoke(uuid) from public,anon;
revoke all on function sinjira_social_user_internal.social_live_share_code_redeem(text) from public,anon;
grant execute on function sinjira_social_user_internal.social_live_share_code_create(uuid) to authenticated,service_role;
grant execute on function sinjira_social_user_internal.social_live_share_code_list(uuid,integer) to authenticated,service_role;
grant execute on function sinjira_social_user_internal.social_live_share_code_revoke(uuid) to authenticated,service_role;
grant execute on function sinjira_social_user_internal.social_live_share_code_redeem(text) to authenticated,service_role;

-- Frontière publique : wrappers SECURITY INVOKER seulement.
create or replace function public.social_live_share_code_create(p_room_id uuid)
returns jsonb language sql security invoker set search_path=''
as $$ select sinjira_social_user_internal.social_live_share_code_create(p_room_id); $$;

create or replace function public.social_live_share_code_list(p_room_id uuid default null,p_limit integer default 20)
returns jsonb language sql security invoker set search_path=''
as $$ select sinjira_social_user_internal.social_live_share_code_list(p_room_id,p_limit); $$;

create or replace function public.social_live_share_code_revoke(p_code_id uuid)
returns boolean language sql security invoker set search_path=''
as $$ select sinjira_social_user_internal.social_live_share_code_revoke(p_code_id); $$;

create or replace function public.social_live_share_code_redeem(p_code text)
returns jsonb language sql security invoker set search_path=''
as $$ select sinjira_social_user_internal.social_live_share_code_redeem(p_code); $$;

revoke all on function public.social_live_share_code_create(uuid) from public,anon;
revoke all on function public.social_live_share_code_list(uuid,integer) from public,anon;
revoke all on function public.social_live_share_code_revoke(uuid) from public,anon;
revoke all on function public.social_live_share_code_redeem(text) from public,anon;
grant execute on function public.social_live_share_code_create(uuid) to authenticated,service_role;
grant execute on function public.social_live_share_code_list(uuid,integer) to authenticated,service_role;
grant execute on function public.social_live_share_code_revoke(uuid) to authenticated,service_role;
grant execute on function public.social_live_share_code_redeem(text) to authenticated,service_role;

comment on table private.social_live_room_share_codes is
'Codes bearer privés En direct : SHA-256 seulement, 24 h, usage unique, aucun annuaire ni présence persistée; identité du rédempteur non stockée.';
comment on function public.social_live_share_code_create(uuid) is
'Crée un code d invitation En direct privé à usage unique; le secret brut est retourné une seule fois au propriétaire.';
comment on function public.social_live_share_code_list(uuid,integer) is
'Liste self-only les métadonnées de codes du propriétaire sans secret, hash ni identité du rédempteur.';
comment on function public.social_live_share_code_redeem(text) is
'Consomme un code bearer privé après revalidation cohorte, blocage, suspension et règles; aucun UUID utilisateur n est retourné ni persisté dans la table de codes.';
