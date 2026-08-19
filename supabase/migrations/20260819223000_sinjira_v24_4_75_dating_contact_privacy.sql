-- SINJIRA™ V24.4.75 — confidentialité des coordonnées dans Rencontres.
-- Empêche de contourner l'anonymat avant le dévoilement mutuel avec un courriel,
-- téléphone, URL, domaine, @identifiant ou identifiant social explicite.

create or replace function private.dating_contains_contact_info(p_text text)
returns boolean
language plpgsql
immutable
set search_path=pg_catalog
as $$
declare
  v text:=lower(coalesce(p_text,''));
  m text[];
begin
  if btrim(v)='' then return false; end if;
  if v ~ '[[:alnum:]._%+\-]+@[[:alnum:].\-]+\.[[:alpha:]]{2,}' then return true; end if;
  if v ~ '(https?://|www\.)' then return true; end if;
  if v ~ '(^|[^[:alnum:]_])@[[:alnum:]_.\-]{2,}' then return true; end if;
  if v ~ '(^|[^[:alnum:]_])([[:alnum:]\-]+\.)+(com|ca|net|org|io|me|fr|co|app|gg|social|chat|dev|tv|info|xyz)([^[:alnum:]_]|$)' then return true; end if;
  if v ~ '(instagram|insta|snapchat|snap|tiktok|telegram|discord|whatsapp|facebook|messenger)[[:space:]]*[:=][[:space:]]*[[:alnum:]_.\-]{3,}' then return true; end if;
  for m in select regexp_matches(v,'(\+?[0-9][0-9 ()\.\-]{5,}[0-9])','g') loop
    if char_length(regexp_replace(m[1],'[^0-9]','','g'))>=7 then return true; end if;
  end loop;
  return false;
end;
$$;

create or replace function private.dating_array_contains_contact_info(p_values text[])
returns boolean
language sql
immutable
set search_path=pg_catalog,private
as $$
  select exists(
    select 1 from unnest(coalesce(p_values,'{}'::text[])) v
    where private.dating_contains_contact_info(v)
  );
$$;

revoke all on function private.dating_contains_contact_info(text), private.dating_array_contains_contact_info(text[]) from public,anon,authenticated;
grant execute on function private.dating_contains_contact_info(text), private.dating_array_contains_contact_info(text[]) to service_role;

create or replace function private.dating_profile_contact_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
begin
  if private.dating_contains_contact_info(new.region)
     or private.dating_contains_contact_info(new.intro)
     or private.dating_array_contains_contact_info(new.values_tags)
     or private.dating_array_contains_contact_info(new.interests_tags)
     or private.dating_array_contains_contact_info(new.lifestyle_tags)
     or private.dating_array_contains_contact_info(new.communication_tags)
     or private.dating_array_contains_contact_info(new.goals_tags)
     or private.dating_array_contains_contact_info(new.registry_traits) then
    raise exception 'DATING_CONTACT_INFO_FORBIDDEN';
  end if;
  return new;
end;
$$;

create or replace function private.dating_preferences_contact_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
begin
  if private.dating_contains_contact_info(new.partner_description)
     or private.dating_contains_contact_info(new.dealbreakers)
     or private.dating_array_contains_contact_info(new.wanted_values)
     or private.dating_array_contains_contact_info(new.wanted_interests)
     or private.dating_array_contains_contact_info(new.wanted_lifestyle)
     or private.dating_array_contains_contact_info(new.wanted_communication)
     or private.dating_array_contains_contact_info(new.wanted_goals) then
    raise exception 'DATING_CONTACT_INFO_FORBIDDEN';
  end if;
  return new;
end;
$$;

revoke all on function private.dating_profile_contact_guard(), private.dating_preferences_contact_guard() from public,anon,authenticated;

-- Nettoyage défensif AVANT l'installation des triggers, afin de pouvoir désactiver
-- proprement un ancien profil qui contiendrait déjà des coordonnées.
update public.dating_profiles p
set enabled=false,serious_intent_confirmed=false,single_confirmed_at=null,updated_at=now()
where private.dating_contains_contact_info(p.region)
   or private.dating_contains_contact_info(p.intro)
   or private.dating_array_contains_contact_info(p.values_tags)
   or private.dating_array_contains_contact_info(p.interests_tags)
   or private.dating_array_contains_contact_info(p.lifestyle_tags)
   or private.dating_array_contains_contact_info(p.communication_tags)
   or private.dating_array_contains_contact_info(p.goals_tags)
   or private.dating_array_contains_contact_info(p.registry_traits)
   or exists(
     select 1 from public.dating_preferences d
     where d.user_id=p.user_id
       and (
         private.dating_contains_contact_info(d.partner_description)
         or private.dating_contains_contact_info(d.dealbreakers)
         or private.dating_array_contains_contact_info(d.wanted_values)
         or private.dating_array_contains_contact_info(d.wanted_interests)
         or private.dating_array_contains_contact_info(d.wanted_lifestyle)
         or private.dating_array_contains_contact_info(d.wanted_communication)
         or private.dating_array_contains_contact_info(d.wanted_goals)
       )
   );

drop trigger if exists dating_profile_contact_guard on public.dating_profiles;
create trigger dating_profile_contact_guard
before insert or update on public.dating_profiles
for each row execute function private.dating_profile_contact_guard();

drop trigger if exists dating_preferences_contact_guard on public.dating_preferences;
create trigger dating_preferences_contact_guard
before insert or update on public.dating_preferences
for each row execute function private.dating_preferences_contact_guard();

create or replace function private.dating_is_eligible(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $$
select coalesce(
  private.dating_age(p_user_id)>=18
  and s.legacy_status='active'
  and s.relationship_data_opt_in is true
  and s.relationship_status='single'
  and p.enabled is true
  and p.serious_intent_confirmed is true
  and p.single_confirmed_at is not null
  and p.single_confirmed_at>=now()-interval '90 days'
  and p.gender_identity is not null
  and btrim(p.intro)<>''
  and not private.dating_contains_contact_info(p.region)
  and not private.dating_contains_contact_info(p.intro)
  and not private.dating_array_contains_contact_info(p.values_tags)
  and not private.dating_array_contains_contact_info(p.interests_tags)
  and not private.dating_array_contains_contact_info(p.lifestyle_tags)
  and not private.dating_array_contains_contact_info(p.communication_tags)
  and not private.dating_array_contains_contact_info(p.goals_tags)
  and not private.dating_array_contains_contact_info(p.registry_traits)
  and exists(
    select 1 from public.dating_preferences d
    where d.user_id=p_user_id
      and cardinality(d.seeking_genders)>0
      and not private.dating_contains_contact_info(d.partner_description)
      and not private.dating_contains_contact_info(d.dealbreakers)
      and not private.dating_array_contains_contact_info(d.wanted_values)
      and not private.dating_array_contains_contact_info(d.wanted_interests)
      and not private.dating_array_contains_contact_info(d.wanted_lifestyle)
      and not private.dating_array_contains_contact_info(d.wanted_communication)
      and not private.dating_array_contains_contact_info(d.wanted_goals)
  ),false)
from public.account_safety_profiles s
join public.dating_profiles p on p.user_id=s.user_id
where s.user_id=p_user_id;
$$;

revoke all on function private.dating_is_eligible(uuid) from public,anon,authenticated;
grant execute on function private.dating_is_eligible(uuid) to service_role;

create or replace function public.dating_connections_overview()
returns table(
  connection_id uuid,status text,direction text,blind_alias text,intro text,region text,
  my_message_count integer,their_message_count integer,photo_unlock_available boolean,
  my_photo_consent boolean,their_photo_consent boolean,identity_revealed boolean,
  revealed_name text,revealed_avatar_path text,created_at timestamptz
)
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $$
with me as (
  select p.id,p.user_id from public.dating_profiles p where p.user_id=auth.uid()
), c as (
  select x.*,m.id me_id,
    case when x.profile_a_id=m.id then x.profile_b_id else x.profile_a_id end other_id,
    case when x.requested_by_profile_id=m.id then 'outgoing' else 'incoming' end dir,
    m.user_id me_user_id
  from public.dating_connections x
  join me m on m.id in(x.profile_a_id,x.profile_b_id)
), counts as (
  select c.*,
    (select count(*)::int from public.dating_messages dm where dm.connection_id=c.id and dm.sender_profile_id=c.me_id) my_count,
    (select count(*)::int from public.dating_messages dm where dm.connection_id=c.id and dm.sender_profile_id=c.other_id) their_count
  from c
), ready as (
  select counts.*,
    case when profile_a_id=me_id then coalesce(a_photo_consent,false) else coalesce(b_photo_consent,false) end my_consent,
    case when profile_a_id=me_id then coalesce(b_photo_consent,false) else coalesce(a_photo_consent,false) end their_consent
  from counts
)
select
  r.id,r.status,r.dir,
  'Profil '||upper(substr(replace(o.id::text,'-',''),1,6)),
  case when private.dating_contains_contact_info(o.intro) then '' else o.intro end,
  case when private.dating_contains_contact_info(o.region) then '' else o.region end,
  r.my_count,r.their_count,
  (r.status='accepted' and private.dating_is_eligible(r.me_user_id) and private.dating_is_eligible(o.user_id) and r.my_count>=10 and r.their_count>=10),
  r.my_consent,r.their_consent,
  (r.status='accepted' and private.dating_is_eligible(r.me_user_id) and private.dating_is_eligible(o.user_id) and r.my_count>=10 and r.their_count>=10 and r.my_consent and r.their_consent),
  case when r.status='accepted' and private.dating_is_eligible(r.me_user_id) and private.dating_is_eligible(o.user_id) and r.my_count>=10 and r.their_count>=10 and r.my_consent and r.their_consent then coalesce(sp.pseudo,sp.display_name,'Membre SINJIRA™') end,
  case when r.status='accepted' and private.dating_is_eligible(r.me_user_id) and private.dating_is_eligible(o.user_id) and r.my_count>=10 and r.their_count>=10 and r.my_consent and r.their_consent then sp.avatar_path end,
  r.created_at
from ready r
join public.dating_profiles o on o.id=r.other_id
left join public.social_profiles sp on sp.user_id=o.user_id
order by r.created_at desc;
$$;

revoke all on function public.dating_connections_overview() from public,anon;
grant execute on function public.dating_connections_overview() to authenticated;

create or replace function public.dating_send_message(p_connection_id uuid,p_body text)
returns uuid
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_me uuid;
  v_other uuid;
  v_other_user uuid;
  v_id uuid;
  v_a uuid;
  v_b uuid;
  v_a_consent boolean;
  v_b_consent boolean;
  v_my_count integer;
  v_their_count integer;
  v_revealed boolean:=false;
  v_recent integer;
  v_body text:=btrim(coalesce(p_body,''));
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if char_length(v_body) not between 1 and 2000 then raise exception 'INVALID_MESSAGE'; end if;

  select id into v_me from public.dating_profiles where user_id=v_user;
  select c.profile_a_id,c.profile_b_id,c.a_photo_consent,c.b_photo_consent,
         case when c.profile_a_id=v_me then c.profile_b_id else c.profile_a_id end
    into v_a,v_b,v_a_consent,v_b_consent,v_other
  from public.dating_connections c
  where c.id=p_connection_id and c.status='accepted' and v_me in(c.profile_a_id,c.profile_b_id);

  if v_other is null then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;
  select user_id into v_other_user from public.dating_profiles where id=v_other;

  if not private.dating_is_eligible(v_user) or not private.dating_is_eligible(v_other_user) then
    raise exception 'DATING_NOT_ELIGIBLE';
  end if;
  if exists(
    select 1 from public.social_blocks b
    where (b.blocker_user_id=v_user and b.blocked_user_id=v_other_user)
       or (b.blocker_user_id=v_other_user and b.blocked_user_id=v_user)
  ) then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;

  select count(*)::int into v_my_count
  from public.dating_messages dm where dm.connection_id=p_connection_id and dm.sender_profile_id=v_me;
  select count(*)::int into v_their_count
  from public.dating_messages dm where dm.connection_id=p_connection_id and dm.sender_profile_id=v_other;

  v_revealed := v_my_count>=10 and v_their_count>=10 and coalesce(v_a_consent,false) and coalesce(v_b_consent,false);
  if not v_revealed and private.dating_contains_contact_info(v_body) then
    raise exception 'DATING_CONTACT_INFO_FORBIDDEN_BEFORE_REVEAL';
  end if;

  if exists(
    select 1 from public.dating_messages dm
    where dm.connection_id=p_connection_id and dm.sender_profile_id=v_me and dm.created_at>now()-interval '2 seconds'
  ) then raise exception 'DATING_RATE_LIMIT'; end if;

  select count(*)::int into v_recent
  from public.dating_messages dm
  where dm.connection_id=p_connection_id and dm.sender_profile_id=v_me and dm.created_at>now()-interval '1 hour';
  if v_recent>=120 then raise exception 'DATING_RATE_LIMIT'; end if;

  insert into public.dating_messages(connection_id,sender_profile_id,body)
  values(p_connection_id,v_me,v_body)
  returning id into v_id;
  return v_id;
end;
$$;

revoke all on function public.dating_send_message(uuid,text) from public,anon;
grant execute on function public.dating_send_message(uuid,text) to authenticated;

create or replace function private.dating_close_on_social_block()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_blocker_profile uuid;
  v_blocked_profile uuid;
begin
  select id into v_blocker_profile from public.dating_profiles where user_id=new.blocker_user_id;
  select id into v_blocked_profile from public.dating_profiles where user_id=new.blocked_user_id;
  if v_blocker_profile is null or v_blocked_profile is null then return new; end if;

  update public.dating_connections
  set status='closed',closed_at=coalesce(closed_at,now()),a_photo_consent=false,b_photo_consent=false
  where status in('pending','accepted')
    and ((profile_a_id=v_blocker_profile and profile_b_id=v_blocked_profile)
      or (profile_a_id=v_blocked_profile and profile_b_id=v_blocker_profile));
  return new;
end;
$$;

revoke all on function private.dating_close_on_social_block() from public,anon,authenticated;

drop trigger if exists dating_social_block_guard on public.social_blocks;
create trigger dating_social_block_guard
after insert on public.social_blocks
for each row execute function private.dating_close_on_social_block();

comment on function private.dating_contains_contact_info(text) is 'Détecte coordonnées directes utilisées pour contourner l’anonymat Rencontres.';
comment on function public.dating_send_message(uuid,text) is 'Bloque coordonnées directes avant le dévoilement 10+10 + double consentement et applique un anti-spam serveur.';
comment on trigger dating_profile_contact_guard on public.dating_profiles is 'Empêche coordonnées directes dans les données de profil Rencontres.';
comment on trigger dating_preferences_contact_guard on public.dating_preferences is 'Empêche coordonnées directes dans les préférences Rencontres.';
