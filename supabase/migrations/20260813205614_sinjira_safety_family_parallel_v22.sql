-- SINJIRA V22 — sécurité des comptes, séparation adultes/jeunes, famille privée et héritage narratif

-- 1) Métadonnées de sécurité privées. Aucun numéro brut n'est dupliqué dans public.* : le facteur téléphone reste dans Supabase Auth.
alter table public.account_safety_profiles
  add column if not exists phone_validation_status text not null default 'unverified',
  add column if not exists phone_line_type text,
  add column if not exists phone_factor_verified_at timestamptz,
  add column if not exists public_birthday_opt_in boolean not null default false;

create table if not exists public.sinjira_security_settings(
  singleton_id integer primary key default 1 check(singleton_id=1),
  require_phone_mfa boolean not null default false,
  require_mobile_line boolean not null default true,
  youth_requires_guardian boolean not null default true,
  updated_at timestamptz not null default now()
);
insert into public.sinjira_security_settings(singleton_id) values(1) on conflict(singleton_id) do nothing;
alter table public.sinjira_security_settings enable row level security;

create or replace function public.sinjira_phone_factor_verified(p_user_id uuid default auth.uid())
returns boolean language sql stable security definer set search_path=public,auth as $$
  select exists(
    select 1 from auth.mfa_factors f
    where f.user_id=p_user_id and f.factor_type::text='phone' and f.status::text='verified'
  );
$$;
revoke all on function public.sinjira_phone_factor_verified(uuid) from public,anon;
grant execute on function public.sinjira_phone_factor_verified(uuid) to authenticated,service_role;

create or replace function public.sinjira_mfa_access_allowed(p_user_id uuid default auth.uid())
returns boolean language plpgsql stable security definer set search_path=public,auth as $$
declare cfg public.sinjira_security_settings%rowtype; line_ok boolean;
begin
  select * into cfg from public.sinjira_security_settings where singleton_id=1;
  if coalesce(cfg.require_phone_mfa,false)=false then return true; end if;
  if p_user_id is null or p_user_id<>auth.uid() then return false; end if;
  if coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then return false; end if;
  if not public.sinjira_phone_factor_verified(p_user_id) then return false; end if;
  if coalesce(cfg.require_mobile_line,true)=false then return true; end if;
  select (s.phone_validation_status='approved' and s.phone_line_type='mobile') into line_ok
  from public.account_safety_profiles s where s.user_id=p_user_id;
  return coalesce(line_ok,false);
end $$;
revoke all on function public.sinjira_mfa_access_allowed(uuid) from public,anon;
grant execute on function public.sinjira_mfa_access_allowed(uuid) to authenticated,service_role;

-- 2) Le profil privé et les directives d'héritage restent accessibles uniquement au propriétaire,
-- avec AAL2 automatiquement lorsque l'option MFA obligatoire sera activée.
drop policy if exists safety_own on public.account_safety_profiles;
create policy safety_own on public.account_safety_profiles for all to authenticated
using(auth.uid()=user_id and public.sinjira_mfa_access_allowed(auth.uid()))
with check(auth.uid()=user_id and public.sinjira_mfa_access_allowed(auth.uid()));

drop policy if exists legacy_own on public.legacy_directives;
create policy legacy_own on public.legacy_directives for all to authenticated
using(auth.uid()=user_id and public.sinjira_mfa_access_allowed(auth.uid()))
with check(auth.uid()=user_id and public.sinjira_mfa_access_allowed(auth.uid()));

-- 3) Liens familiaux volontaires entre comptes adultes. Aucun nom de tiers non inscrit n'est requis.
alter table public.private_family_links
  add column if not exists owner_consented_at timestamptz,
  add column if not exists related_consented_at timestamptz,
  add column if not exists ended_by_user_id uuid references auth.users(id) on delete set null;

create table if not exists public.family_link_invites(
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  invite_code text not null unique,
  expires_at timestamptz not null default (now()+interval '7 days'),
  used_at timestamptz,
  created_at timestamptz not null default now()
);
alter table public.family_link_invites enable row level security;
drop policy if exists family_invites_own on public.family_link_invites;
create policy family_invites_own on public.family_link_invites for all to authenticated
using(owner_user_id=auth.uid() and public.sinjira_mfa_access_allowed(auth.uid()))
with check(owner_user_id=auth.uid() and public.sinjira_mfa_access_allowed(auth.uid()));

create table if not exists public.family_relationship_events(
  id uuid primary key default gen_random_uuid(),
  family_link_id uuid references public.private_family_links(id) on delete cascade,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  related_user_id uuid references auth.users(id) on delete cascade,
  event_type text not null check(event_type in ('relationship_started','married','separated','divorced','child_born','bereavement','reconciled','other')),
  event_date date not null,
  mirror_to_fiction boolean not null default false,
  private_note text,
  created_at timestamptz not null default now()
);
alter table public.family_relationship_events enable row level security;
drop policy if exists family_events_parties_read on public.family_relationship_events;
create policy family_events_parties_read on public.family_relationship_events for select to authenticated
using((owner_user_id=auth.uid() or related_user_id=auth.uid()) and public.sinjira_mfa_access_allowed(auth.uid()));
drop policy if exists family_events_owner_insert on public.family_relationship_events;
create policy family_events_owner_insert on public.family_relationship_events for insert to authenticated
with check(owner_user_id=auth.uid() and public.sinjira_mfa_access_allowed(auth.uid()));
drop policy if exists family_events_owner_update on public.family_relationship_events;
create policy family_events_owner_update on public.family_relationship_events for update to authenticated
using(owner_user_id=auth.uid() and public.sinjira_mfa_access_allowed(auth.uid()))
with check(owner_user_id=auth.uid() and public.sinjira_mfa_access_allowed(auth.uid()));

-- Les deux comptes liés peuvent voir le lien. Les modifications restent limitées au créateur; le second compte accepte via RPC.
drop policy if exists family_own on public.private_family_links;
drop policy if exists family_parties_read on public.private_family_links;
create policy family_parties_read on public.private_family_links for select to authenticated
using((owner_user_id=auth.uid() or related_user_id=auth.uid()) and public.sinjira_mfa_access_allowed(auth.uid()));
drop policy if exists family_owner_write on public.private_family_links;
create policy family_owner_write on public.private_family_links for all to authenticated
using(owner_user_id=auth.uid() and public.sinjira_mfa_access_allowed(auth.uid()))
with check(owner_user_id=auth.uid() and public.sinjira_mfa_access_allowed(auth.uid()));

create or replace function public.create_family_link_invite()
returns text language plpgsql security definer set search_path=public as $$
declare code text;
begin
  if auth.uid() is null then raise exception 'Connexion requise.'; end if;
  if public.sinjira_age_band(auth.uid())<>'adult' then raise exception 'Les liens familiaux de compte sont gérés par un compte adulte.'; end if;
  if not public.sinjira_mfa_access_allowed(auth.uid()) then raise exception 'Authentification renforcée requise.'; end if;
  code:=upper(substr(replace(gen_random_uuid()::text,'-',''),1,10));
  insert into public.family_link_invites(owner_user_id,invite_code) values(auth.uid(),code);
  return code;
end $$;
revoke all on function public.create_family_link_invite() from public,anon;
grant execute on function public.create_family_link_invite() to authenticated;

create or replace function public.redeem_family_link_invite(p_code text,p_relationship_type text,p_started_on date default null,p_mirror_to_fiction boolean default false)
returns uuid language plpgsql security definer set search_path=public as $$
declare inv public.family_link_invites%rowtype; lid uuid; rel text:=lower(trim(p_relationship_type));
begin
  if auth.uid() is null then raise exception 'Connexion requise.'; end if;
  if public.sinjira_age_band(auth.uid())<>'adult' then raise exception 'Les liens familiaux de compte sont gérés par un compte adulte.'; end if;
  if rel not in ('partner','spouse','sibling','parent','adult_child','family') then raise exception 'Type de lien non permis.'; end if;
  select * into inv from public.family_link_invites where invite_code=upper(trim(p_code)) and used_at is null and expires_at>now() for update;
  if inv.id is null then raise exception 'Code expiré ou invalide.'; end if;
  if inv.owner_user_id=auth.uid() then raise exception 'Vous ne pouvez pas relier votre compte à lui-même.'; end if;
  if public.sinjira_age_band(inv.owner_user_id)<>'adult' then raise exception 'Le compte source doit être adulte.'; end if;
  insert into public.private_family_links(owner_user_id,related_user_id,relationship_type,status,started_on,mirror_to_fiction,owner_consented_at,related_consented_at)
  values(inv.owner_user_id,auth.uid(),rel,'active',p_started_on,p_mirror_to_fiction,inv.created_at,now()) returning id into lid;
  update public.family_link_invites set used_at=now() where id=inv.id;
  return lid;
end $$;
revoke all on function public.redeem_family_link_invite(text,text,date,boolean) from public,anon;
grant execute on function public.redeem_family_link_invite(text,text,date,boolean) to authenticated;

-- 4) Protection des mineurs 12-17 : aucune interaction sociale adulte/jeune.
-- Un compte jeune n'accède aux fonctions sociales qu'avec un lien parent/tuteur vérifié.
create or replace function public.sinjira_can_social_interact(p_a uuid,p_b uuid)
returns boolean language sql stable security definer set search_path=public as $$
  select case
    when p_a is null or p_b is null then false
    when p_a=p_b then true
    when public.sinjira_age_band(p_a)='adult' and public.sinjira_age_band(p_b)='adult' then true
    when public.sinjira_age_band(p_a)='youth' and public.sinjira_age_band(p_b)='youth' then true
    else false end;
$$;

create or replace function public.sinjira_content_allowed(p_user_id uuid,p_body text)
returns boolean language plpgsql stable security definer set search_path=public as $$
declare band text:=public.sinjira_age_band(p_user_id); t text:=lower(coalesce(p_body,''));
begin
  if t ~ '(onlyfans|fansly|manyvids|justfor\.fans|loyalfans|chaturbate|myfreecams|sexcam|webcam adulte|vente de nudes|nudes for sale|escort service|service d.escolte)' then return false; end if;
  if band='youth' and t ~ '(\bnsfw\b|\b18\+\b|\bporn\b|\bporno\b|pornhub|xvideos|xnxx|redtube|sexting|nude|nudité sexuelle|contenu sexuel|rencontre sexuelle|sugar daddy|sugar baby)' then return false; end if;
  return band in ('adult','youth');
end $$;

-- 5) Supervision parentale : le parent voit AVEC QUI le jeune communique, pas automatiquement le contenu des messages.
create or replace function public.guardian_minor_contact_summary(p_minor_user_id uuid)
returns table(network text,peer_user_id uuid,peer_pseudo text,last_interaction timestamptz,message_count bigint)
language plpgsql stable security definer set search_path=public as $$
begin
  if auth.uid() is null then raise exception 'Connexion requise.'; end if;
  if not exists(select 1 from public.guardian_links g where g.minor_user_id=p_minor_user_id and g.guardian_user_id=auth.uid() and g.status='verified') then
    raise exception 'Supervision parentale non autorisée.';
  end if;
  return query
  with msg as (
    select 'compte'::text network,
           case when m.sender_user_id=p_minor_user_id then m.recipient_user_id else m.sender_user_id end peer,
           m.created_at
    from public.social_real_messages m
    where m.sender_user_id=p_minor_user_id or m.recipient_user_id=p_minor_user_id
    union all
    select 'personnage'::text,
           case when m.sender_user_id=p_minor_user_id then m.recipient_user_id else m.sender_user_id end,
           m.created_at
    from public.social_character_messages m
    where m.sender_user_id=p_minor_user_id or m.recipient_user_id=p_minor_user_id
  )
  select msg.network,msg.peer,coalesce(sp.pseudo,sp.display_name,'Membre SINJIRA'),max(msg.created_at),count(*)
  from msg left join public.social_profiles sp on sp.user_id=msg.peer
  group by msg.network,msg.peer,sp.pseudo,sp.display_name
  order by max(msg.created_at) desc;
end $$;
revoke all on function public.guardian_minor_contact_summary(uuid) from public,anon;
grant execute on function public.guardian_minor_contact_summary(uuid) to authenticated;

-- 6) Les nouvelles écritures sociales respectent aussi la politique MFA lorsqu'elle sera activée.
drop policy if exists real_posts_insert on public.social_real_posts;
create policy real_posts_insert on public.social_real_posts for insert to authenticated with check(
  auth.uid()=user_id and public.sinjira_mfa_access_allowed(auth.uid()) and public.sinjira_age_band(auth.uid()) in ('adult','youth') and public.sinjira_content_allowed(auth.uid(),body) and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid())
);
drop policy if exists char_posts_insert on public.social_character_posts;
create policy char_posts_insert on public.social_character_posts for insert to authenticated with check(
  auth.uid()=user_id and public.sinjira_mfa_access_allowed(auth.uid()) and public.sinjira_age_band(auth.uid()) in ('adult','youth') and public.sinjira_content_allowed(auth.uid(),body) and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and exists(select 1 from public.character_social_profiles c where c.character_id=social_character_posts.character_id and c.user_id=auth.uid())
);
drop policy if exists real_messages_insert on public.social_real_messages;
create policy real_messages_insert on public.social_real_messages for insert to authenticated with check(
  auth.uid()=sender_user_id and public.sinjira_mfa_access_allowed(auth.uid()) and public.sinjira_can_social_interact(sender_user_id,recipient_user_id) and public.sinjira_content_allowed(sender_user_id,body) and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and not public.social_is_blocked(sender_user_id,recipient_user_id)
);
drop policy if exists char_messages_insert on public.social_character_messages;
create policy char_messages_insert on public.social_character_messages for insert to authenticated with check(
  auth.uid()=sender_user_id and public.sinjira_mfa_access_allowed(auth.uid()) and public.sinjira_can_social_interact(sender_user_id,recipient_user_id) and public.sinjira_content_allowed(sender_user_id,body) and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and not public.social_is_blocked(sender_user_id,recipient_user_id) and exists(select 1 from public.character_social_profiles c where c.character_id=social_character_messages.sender_character_id and c.user_id=auth.uid()) and exists(select 1 from public.character_social_profiles c where c.character_id=social_character_messages.recipient_character_id and c.user_id=social_character_messages.recipient_user_id)
);

-- 7) Index utiles.
create index if not exists family_events_owner_date_idx on public.family_relationship_events(owner_user_id,event_date desc);
create index if not exists family_links_related_idx on public.private_family_links(related_user_id,status);
create index if not exists guardian_verified_idx on public.guardian_links(minor_user_id,guardian_user_id,status);
