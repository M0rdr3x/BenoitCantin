-- SINJIRA™ V25 — comptes enfants supervisés 11–12 ans.
-- Objectifs :
--  * permettre la création d'un compte dès 11 ans uniquement avec un parent/tuteur adulte vérifié;
--  * conserver la validation serveur comme autorité de l'âge;
--  * maintenir les comptes 11–12 hors des fonctions sociales jusqu'à 13 ans;
--  * conserver la porte de juridiction jeunesse canadienne pour les 11–17 ans.

create or replace function public.enforce_sinjira_account_safety_age()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
declare years integer;
begin
  if new.date_of_birth is null then raise exception 'BIRTH_DATE_REQUIRED'; end if;
  if new.date_of_birth>current_date then raise exception 'INVALID_BIRTH_DATE'; end if;
  years:=extract(year from age(current_date,new.date_of_birth))::integer;
  if years<11 then raise exception 'SINJIRA_MINIMUM_AGE_11'; end if;
  if years>120 then raise exception 'INVALID_BIRTH_DATE'; end if;
  if new.sex is not null and new.sex not in ('female','male') then raise exception 'SEX_REQUIRED_FEMALE_OR_MALE'; end if;
  return new;
end;
$$;
revoke all on function public.enforce_sinjira_account_safety_age() from public,anon,authenticated;

-- Privacy-by-default dès la première consommation/réactivation d'un code parental V25.
-- Le trigger historique sync_guardian_signup_invite_link_trigger appelle cette fonction :
-- sa logique doit donc être sûre avant que handle_new_sinjira_user ou child_pending ne
-- consomme une invitation, sans attendre une migration de minimisation ultérieure.
create or replace function public.sync_guardian_signup_invite_link()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $guardian_sync$
begin
  if new.used_at is not null and new.minor_user_id is not null then
    insert into public.guardian_links(
      minor_user_id,guardian_user_id,status,guardian_role,
      can_view_contact_metadata,consented_at,revoked_at
    )
    values(
      new.minor_user_id,new.guardian_user_id,'verified','parent',
      false,new.consented_at,null
    )
    on conflict(minor_user_id,guardian_user_id) do update
      set status='verified',
          guardian_role='parent',
          can_view_contact_metadata=false,
          consented_at=excluded.consented_at,
          revoked_at=null,
          updated_at=now();
  end if;
  return new;
end;
$guardian_sync$;
revoke all on function public.sync_guardian_signup_invite_link()
from public,anon,authenticated;

comment on function public.sync_guardian_signup_invite_link() is
  'V25 privacy-by-default: toute création ou réactivation de supervision via invitation remet can_view_contact_metadata à false.';

-- guardian_code est une capacité à usage unique. Elle est retirée des métadonnées Auth
-- dès la même migration qui ouvre l'inscription enfant, sans fenêtre de conservation.
create or replace function private.sinjira_strip_guardian_signup_secret()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,auth
as $guardian_secret$
begin
  if coalesce(new.raw_user_meta_data,'{}'::jsonb) ? 'guardian_code' then
    update auth.users
    set raw_user_meta_data=coalesce(raw_user_meta_data,'{}'::jsonb)-'guardian_code'
    where id=new.id;
  end if;
  return new;
end;
$guardian_secret$;

revoke all on function private.sinjira_strip_guardian_signup_secret()
from public,anon,authenticated;

drop trigger if exists zz_sinjira_strip_guardian_signup_secret
on auth.users;

create trigger zz_sinjira_strip_guardian_signup_secret
after insert on auth.users
for each row
when (coalesce(new.raw_user_meta_data,'{}'::jsonb) ? 'guardian_code')
execute function private.sinjira_strip_guardian_signup_secret();

-- Nettoyage des comptes déjà créés avant cette frontière V25.
update auth.users
set raw_user_meta_data=coalesce(raw_user_meta_data,'{}'::jsonb)-'guardian_code'
where coalesce(raw_user_meta_data,'{}'::jsonb) ? 'guardian_code';

comment on function private.sinjira_strip_guardian_signup_secret() is
  'V25 initial: guardian_code est retiré des métadonnées Auth après création; les secrets historiques résiduels sont aussi purgés.';

-- 11–12 ans : bande `child`, volontairement exclue des autorisations sociales existantes.
-- À 13 ans, la bande est recalculée automatiquement depuis la date de naissance et devient `youth`
-- lorsque le lien de supervision est toujours vérifié.
create or replace function public.sinjira_age_band(p_user_id uuid default auth.uid())
returns text
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when exists(
      select 1
      from auth.users u
      where u.id=p_user_id
        and lower(coalesce(u.email,''))='kingtyrano@gmail.com'
    ) then 'adult'
    when s.user_id is null or s.date_of_birth is null or s.date_of_birth>current_date then 'unverified'
    when s.legacy_status='memorialized' then 'memorial'
    when age(current_date,s.date_of_birth)<interval '11 years' then 'under11'
    when age(current_date,s.date_of_birth)<interval '13 years' then
      case
        when exists(
          select 1 from public.guardian_links g
          where g.minor_user_id=s.user_id and g.status='verified' and g.revoked_at is null
        ) then 'child'
        else 'child_pending'
      end
    when age(current_date,s.date_of_birth)<interval '18 years' then
      case
        when exists(
          select 1 from public.guardian_links g
          where g.minor_user_id=s.user_id and g.status='verified' and g.revoked_at is null
        ) then 'youth'
        else 'youth_pending'
      end
    else 'adult'
  end
  from (select p_user_id user_id) x
  left join public.account_safety_profiles s on s.user_id=x.user_id;
$$;
revoke all on function public.sinjira_age_band(uuid) from public,anon,authenticated;
grant execute on function public.sinjira_age_band(uuid) to service_role;

revoke all on function public.sinjira_my_age_band() from public,anon,authenticated;
grant execute on function public.sinjira_my_age_band() to anon,authenticated,service_role;

-- Un parent peut superviser un compte enfant ou jeunesse lié et vérifié.
create or replace function public.sinjira_parent_can_supervise(p_parent uuid,p_child uuid)
returns boolean
language sql
stable
security definer
set search_path=public
as $$
  select public.sinjira_age_band(p_parent)='adult'
    and public.sinjira_age_band(p_child) in ('child','youth')
    and exists(
      select 1 from public.guardian_links g
      where g.guardian_user_id=p_parent
        and g.minor_user_id=p_child
        and g.status='verified'
        and g.revoked_at is null
    );
$$;
revoke all on function public.sinjira_parent_can_supervise(uuid,uuid) from public,anon,authenticated;
grant execute on function public.sinjira_parent_can_supervise(uuid,uuid) to service_role;

-- La supervision historique reste privée au compte concerné après sa majorité.
-- L'ancien tuteur ne conserve aucune visibilité une fois la bande devenue adult.
create or replace function public.sinjira_can_read_guardian_link(p_link_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public
as $guardian_visibility$
  select coalesce((
    select case
      when auth.uid()=g.minor_user_id then true
      when auth.uid()=g.guardian_user_id
        then public.sinjira_age_band(g.minor_user_id) in (
          'child','child_pending','youth','youth_pending'
        )
      else false
    end
    from public.guardian_links g
    where g.id=p_link_id
  ),false);
$guardian_visibility$;

revoke all on function public.sinjira_can_read_guardian_link(uuid)
from public,anon,authenticated;
grant execute on function public.sinjira_can_read_guardian_link(uuid)
to authenticated;

drop policy if exists guardian_read_parties on public.guardian_links;
drop policy if exists guardian_read_parties_age_bounded on public.guardian_links;

create policy guardian_read_parties_age_bounded
on public.guardian_links
for select
to authenticated
using (public.sinjira_can_read_guardian_link(id));

-- Les codes parentaux deviennent une capacité d'accès dès l'ouverture du parcours 11 ans.
-- Leur émission et leur relecture exigent donc AAL2 dès cette migration, sans fenêtre AAL1.
create or replace function public.create_guardian_signup_invite()
returns text
language plpgsql
security definer
set search_path=pg_catalog,public,auth
as $guardian_invite$
declare
  uid uuid:=auth.uid();
  v_code text;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if public.sinjira_age_band(uid)<>'adult' then
    raise exception 'ADULT_GUARDIAN_REQUIRED';
  end if;
  if coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;
  if not public.sinjira_mfa_access_allowed(uid) then
    raise exception 'MFA_REQUIRED';
  end if;

  delete from public.guardian_signup_invites
  where guardian_user_id=uid
    and used_at is null;

  loop
    v_code:='YOUTH-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,10));
    exit when not exists(
      select 1 from public.guardian_signup_invites where invite_code=v_code
    );
  end loop;

  insert into public.guardian_signup_invites(guardian_user_id,invite_code)
  values(uid,v_code);

  return v_code;
end;
$guardian_invite$;

revoke all on function public.create_guardian_signup_invite()
from public,anon;
grant execute on function public.create_guardian_signup_invite()
to authenticated;

drop policy if exists guardian_signup_invites_own
on public.guardian_signup_invites;
drop policy if exists guardian_signup_invites_own_aal2
on public.guardian_signup_invites;

create policy guardian_signup_invites_own_aal2
on public.guardian_signup_invites
for select
to authenticated
using (
  (select auth.uid())=guardian_user_id
  and coalesce(auth.jwt()->>'aal','aal1')='aal2'
  and (
    minor_user_id is null
    or exists(
      select 1
      from public.guardian_links g
      where g.guardian_user_id=(select auth.uid())
        and g.minor_user_id=guardian_signup_invites.minor_user_id
    )
  )
);

revoke all on table public.guardian_signup_invites from anon;
grant select on table public.guardian_signup_invites to authenticated;

-- La révocation par le tuteur est sensible et exige AAL2.
-- Le mineur lié garde une voie de sortie immédiate, sans dépendre du second facteur du tuteur.
create or replace function public.revoke_guardian_link(p_link_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,auth
as $guardian_revoke$
declare
  uid uuid:=auth.uid();
  r public.guardian_links%rowtype;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  select * into r
  from public.guardian_links
  where id=p_link_id
  for update;

  if r.id is null then raise exception 'GUARDIAN_LINK_NOT_FOUND'; end if;
  if uid not in (r.guardian_user_id,r.minor_user_id) then
    raise exception 'GUARDIAN_LINK_FORBIDDEN';
  end if;

  if r.status='revoked' or r.revoked_at is not null then
    return jsonb_build_object('ok',true,'status','revoked','link_id',r.id);
  end if;

  if uid=r.guardian_user_id
     and coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;

  update public.guardian_links
  set status='revoked',
      revoked_at=now(),
      updated_at=now()
  where id=r.id;

  return jsonb_build_object('ok',true,'status','revoked','link_id',r.id);
end;
$guardian_revoke$;

revoke all on function public.revoke_guardian_link(uuid)
from public,anon;
grant execute on function public.revoke_guardian_link(uuid)
to authenticated;

-- Défense en profondeur : tout lien actif créé ou réactivé repart sans permission
-- de métadonnées. Les permissions historiques implicites sont retirées immédiatement.
alter table public.guardian_links
  alter column can_view_contact_metadata set default false;

create or replace function private.sinjira_guardian_contact_metadata_default_off()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $guardian_metadata$
begin
  if new.status='verified' and new.revoked_at is null then
    new.can_view_contact_metadata:=false;
  end if;
  return new;
end;
$guardian_metadata$;

revoke all on function private.sinjira_guardian_contact_metadata_default_off()
from public,anon,authenticated;

drop trigger if exists guardian_contact_metadata_default_off
on public.guardian_links;

create trigger guardian_contact_metadata_default_off
before insert or update of status,revoked_at
on public.guardian_links
for each row
execute function private.sinjira_guardian_contact_metadata_default_off();

update public.guardian_links
set can_view_contact_metadata=false,
    updated_at=now()
where status='verified'
  and revoked_at is null
  and can_view_contact_metadata is true;

comment on function public.create_guardian_signup_invite() is
  'V25 initial: code parental réservé à un adulte AAL2; anciens codes ouverts invalidés.';
comment on function public.sinjira_can_read_guardian_link(uuid) is
  'V25 initial: le compte concerné garde son historique; le tuteur ne voit le lien que tant que le compte est mineur.';
comment on policy guardian_read_parties_age_bounded
on public.guardian_links is
  'V25 initial: visibilité tuteur automatiquement coupée au passage à adult.';
comment on policy guardian_signup_invites_own_aal2
on public.guardian_signup_invites is
  'V25 initial: AAL2 self-only; invitation consommée lisible uniquement tant que le guardian_link reste visible.';
comment on function public.revoke_guardian_link(uuid) is
  'V25 initial: tuteur AAL2 pour révoquer; mineur lié peut sortir immédiatement.';
comment on function private.sinjira_guardian_contact_metadata_default_off() is
  'V25 initial privacy-by-default: création/réactivation de guardian_link remet la permission de métadonnées à false.';

create or replace function public.handle_new_sinjira_user()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
declare
  c boolean:=coalesce((new.raw_user_meta_data->>'initial_contributor_opt_in')::boolean,false);
  f boolean:=coalesce((new.raw_user_meta_data->>'initial_share_free_text')::boolean,false);
  dob date;
  sx text;
  raw_dob text;
  raw_sex text;
  years integer;
  guardian_code text:=upper(trim(coalesce(new.raw_user_meta_data->>'guardian_code','')));
  residence_country text:=lower(trim(coalesce(new.raw_user_meta_data->>'residence_country','')));
  inv public.guardian_signup_invites%rowtype;
begin
  raw_dob:=coalesce(nullif(new.raw_user_meta_data->>'birth_date',''),nullif(new.raw_user_meta_data->>'date_of_birth',''));
  begin dob:=raw_dob::date; exception when others then dob:=null; end;
  if dob is null then raise exception 'BIRTH_DATE_REQUIRED'; end if;
  if dob>current_date then raise exception 'INVALID_BIRTH_DATE'; end if;
  years:=extract(year from age(current_date,dob))::integer;
  if years<11 then raise exception 'SINJIRA_MINIMUM_AGE_11'; end if;
  if years>120 then raise exception 'INVALID_BIRTH_DATE'; end if;

  -- Le lancement jeunesse reste limité au Canada jusqu'à validation spécifique d'autres juridictions.
  if years<18 and residence_country not in ('canada','ca','can') then
    raise exception 'YOUTH_JURISDICTION_NOT_ENABLED';
  end if;

  raw_sex:=trim(coalesce(new.raw_user_meta_data->>'gender',new.raw_user_meta_data->>'sex',''));
  sx:=case lower(raw_sex)
    when 'femme' then 'female' when 'female' then 'female'
    when 'homme' then 'male' when 'male' then 'male'
    else null end;
  if sx is null then raise exception 'SEX_REQUIRED_FEMALE_OR_MALE'; end if;

  -- 11, 12 et 13 ans : aucun compte sans autorisation parentale/tuteur vérifiée.
  if years<14 then
    if guardian_code='' then raise exception 'GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14'; end if;
    select * into inv from public.guardian_signup_invites
      where invite_code=guardian_code and used_at is null and expires_at>now()
      for update;
    if inv.id is null then raise exception 'INVALID_OR_EXPIRED_GUARDIAN_CODE'; end if;
    if public.sinjira_age_band(inv.guardian_user_id)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;
  elsif guardian_code<>'' then
    select * into inv from public.guardian_signup_invites
      where invite_code=guardian_code and used_at is null and expires_at>now()
      for update;
    if inv.id is null then raise exception 'INVALID_OR_EXPIRED_GUARDIAN_CODE'; end if;
    if public.sinjira_age_band(inv.guardian_user_id)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;
  end if;

  -- Les comptes enfants 11–12 ans ne participent jamais au Programme Contributeur.
  if years<13 then
    c:=false;
    f:=false;
  end if;

  insert into public.profiles(user_id,pseudo,display_name)
    values(new.id,coalesce(nullif(new.raw_user_meta_data->>'pseudo',''),'Joueur SINJIRA'),nullif(new.raw_user_meta_data->>'display_name',''))
    on conflict(user_id) do update set pseudo=excluded.pseudo,display_name=excluded.display_name,updated_at=now();

  insert into public.research_consents(user_id,participate,share_free_text,consent_version,consented_at)
    values(new.id,c,c and f,'sinjira-gameplay-v2',case when c then now() else null end)
    on conflict(user_id) do nothing;

  insert into public.account_safety_profiles(user_id,date_of_birth,sex,birthday_greeting_opt_in,real_life_to_fiction_opt_in,relationship_data_opt_in,relationship_status,legacy_status)
    values(new.id,dob,sx,true,false,false,'not_specified','active')
    on conflict(user_id) do update set date_of_birth=excluded.date_of_birth,sex=excluded.sex,updated_at=now();

  insert into public.account_legacy_preferences(user_id,account_after_death,final_story_tone,memorial_public_opt_in,transfer_private_story_to_family)
    values(new.id,'memorialize','peaceful',true,false)
    on conflict(user_id) do nothing;

  if inv.id is not null and years<18 then
    insert into public.guardian_links(minor_user_id,guardian_user_id,status,guardian_role,can_view_contact_metadata,consented_at)
      values(new.id,inv.guardian_user_id,'verified','parent',false,inv.consented_at)
      on conflict do nothing;
    update public.guardian_signup_invites
      set used_at=now(),minor_user_id=new.id
      where id=inv.id;
  end if;

  return new;
end;
$$;
revoke all on function public.handle_new_sinjira_user() from public,anon,authenticated;
