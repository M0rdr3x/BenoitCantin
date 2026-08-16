-- SINJIRA™ V24.4.12 — autorisation parentale 12–13 ans et pont metadata V22/V24

create table if not exists public.guardian_signup_invites(
 id uuid primary key default gen_random_uuid(),
 guardian_user_id uuid not null references auth.users(id) on delete cascade,
 invite_code text not null unique,
 consented_at timestamptz not null default now(),
 expires_at timestamptz not null default (now()+interval '7 days'),
 used_at timestamptz,
 minor_user_id uuid references auth.users(id) on delete set null,
 created_at timestamptz not null default now()
);
create index if not exists guardian_signup_invites_guardian_idx on public.guardian_signup_invites(guardian_user_id,created_at desc);
alter table public.guardian_signup_invites enable row level security;
drop policy if exists guardian_signup_invites_own on public.guardian_signup_invites;
create policy guardian_signup_invites_own on public.guardian_signup_invites for select to authenticated using((select auth.uid())=guardian_user_id);
revoke all on public.guardian_signup_invites from anon;
grant select on public.guardian_signup_invites to authenticated;

create or replace function public.create_guardian_signup_invite()
returns text language plpgsql security definer set search_path=public as $$
declare v_code text;
begin
 if auth.uid() is null then raise exception 'AUTH_REQUIRED'; end if;
 if public.sinjira_age_band(auth.uid()) <> 'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;
 if not public.sinjira_mfa_access_allowed(auth.uid()) then raise exception 'MFA_REQUIRED'; end if;
 delete from public.guardian_signup_invites where guardian_user_id=auth.uid() and used_at is null and expires_at<now();
 v_code:='YOUTH-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,10));
 insert into public.guardian_signup_invites(guardian_user_id,invite_code) values(auth.uid(),v_code);
 return v_code;
end;
$$;
revoke all on function public.create_guardian_signup_invite() from public,anon;
grant execute on function public.create_guardian_signup_invite() to authenticated;

create or replace function public.handle_new_sinjira_user()
returns trigger language plpgsql security definer set search_path=public as $$
declare
 c boolean:=coalesce((new.raw_user_meta_data->>'initial_contributor_opt_in')::boolean,false);
 f boolean:=coalesce((new.raw_user_meta_data->>'initial_share_free_text')::boolean,false);
 dob date; sx text; raw_dob text; raw_sex text; years integer;
 guardian_code text:=upper(trim(coalesce(new.raw_user_meta_data->>'guardian_code','')));
 inv public.guardian_signup_invites%rowtype;
begin
 raw_dob:=coalesce(nullif(new.raw_user_meta_data->>'birth_date',''),nullif(new.raw_user_meta_data->>'date_of_birth',''));
 begin dob:=raw_dob::date; exception when others then dob:=null; end;
 if dob is null then raise exception 'BIRTH_DATE_REQUIRED'; end if;
 if dob>current_date then raise exception 'INVALID_BIRTH_DATE'; end if;
 years:=extract(year from age(current_date,dob))::integer;
 if years<12 then raise exception 'SINJIRA_MINIMUM_AGE_12'; end if;
 if years>120 then raise exception 'INVALID_BIRTH_DATE'; end if;
 raw_sex:=trim(coalesce(new.raw_user_meta_data->>'gender',new.raw_user_meta_data->>'sex',''));
 sx:=case lower(raw_sex) when 'femme' then 'female' when 'female' then 'female' when 'homme' then 'male' when 'male' then 'male' else null end;
 if sx is null then raise exception 'SEX_REQUIRED_FEMALE_OR_MALE'; end if;
 if years<14 then
  if guardian_code='' then raise exception 'GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14'; end if;
  select * into inv from public.guardian_signup_invites where invite_code=guardian_code and used_at is null and expires_at>now() for update;
  if inv.id is null then raise exception 'INVALID_OR_EXPIRED_GUARDIAN_CODE'; end if;
  if public.sinjira_age_band(inv.guardian_user_id)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;
 elsif guardian_code<>'' then
  select * into inv from public.guardian_signup_invites where invite_code=guardian_code and used_at is null and expires_at>now() for update;
  if inv.id is null then raise exception 'INVALID_OR_EXPIRED_GUARDIAN_CODE'; end if;
  if public.sinjira_age_band(inv.guardian_user_id)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;
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
 values(new.id,'memorialize','peaceful',true,false) on conflict(user_id) do nothing;
 if inv.id is not null and years<18 then
  insert into public.guardian_links(minor_user_id,guardian_user_id,status,guardian_role,can_view_contact_metadata,consented_at)
  values(new.id,inv.guardian_user_id,'verified','parent',true,inv.consented_at) on conflict do nothing;
  update public.guardian_signup_invites set used_at=now(),minor_user_id=new.id where id=inv.id;
 end if;
 return new;
end;
$$;
revoke all on function public.handle_new_sinjira_user() from public,anon,authenticated;
