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
