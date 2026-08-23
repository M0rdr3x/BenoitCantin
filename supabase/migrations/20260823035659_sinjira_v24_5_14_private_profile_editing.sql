-- Migration historique appliquée en production avant la convergence V24.5.23.
-- Son nom interne V24.5.14 est conservé immuable pour correspondre au ledger Supabase.

create table if not exists public.private_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  birth_date date,
  gender text,
  languages text[] not null default '{}'::text[],
  residence_city text,
  residence_region text,
  residence_country text,
  origin_city text,
  origin_region text,
  origin_country text,
  relationship_status text not null default 'not_set',
  relationship_since date,
  relationship_partner_label text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint private_profiles_gender_check check (gender is null or gender in ('woman','man','non_binary','other','prefer_not_to_say')),
  constraint private_profiles_relationship_status_check check (relationship_status in ('not_set','single','partnered','engaged','married','separated','divorced','widowed')),
  constraint private_profiles_birth_date_check check (birth_date is null or (birth_date <= current_date and birth_date >= current_date - interval '120 years')),
  constraint private_profiles_relationship_since_check check (relationship_since is null or relationship_since <= current_date),
  constraint private_profiles_languages_count_check check (cardinality(languages) <= 12),
  constraint private_profiles_residence_city_len check (residence_city is null or char_length(residence_city) <= 100),
  constraint private_profiles_residence_region_len check (residence_region is null or char_length(residence_region) <= 100),
  constraint private_profiles_residence_country_len check (residence_country is null or char_length(residence_country) <= 100),
  constraint private_profiles_origin_city_len check (origin_city is null or char_length(origin_city) <= 100),
  constraint private_profiles_origin_region_len check (origin_region is null or char_length(origin_region) <= 100),
  constraint private_profiles_origin_country_len check (origin_country is null or char_length(origin_country) <= 100),
  constraint private_profiles_partner_label_len check (relationship_partner_label is null or char_length(relationship_partner_label) <= 120)
);

alter table public.private_profiles enable row level security;
revoke all on table public.private_profiles from public, anon, authenticated;
grant all on table public.private_profiles to service_role;

drop policy if exists private_profiles_no_direct_client_access on public.private_profiles;
create policy private_profiles_no_direct_client_access
on public.private_profiles
as restrictive
for all
to anon, authenticated
using (false)
with check (false);

insert into public.private_profiles(user_id,birth_date,gender,relationship_status,created_at,updated_at)
select s.user_id,
       s.date_of_birth,
       case s.sex when 'female' then 'woman' when 'male' then 'man' else null end,
       case when s.relationship_status in ('not_set','single','partnered','engaged','married','separated','divorced','widowed') then s.relationship_status else 'not_set' end,
       now(),now()
from public.account_safety_profiles s
on conflict (user_id) do nothing;

create or replace function private.sinjira_birth_date_change_guard()
returns trigger
language plpgsql
security definer
set search_path to 'pg_catalog','public','private'
as $$
declare
  v_profile uuid;
  v_old_age integer;
  v_new_age integer;
begin
  if old.date_of_birth is not distinct from new.date_of_birth then
    return new;
  end if;

  v_old_age := extract(year from age(current_date,old.date_of_birth))::integer;
  v_new_age := extract(year from age(current_date,new.date_of_birth))::integer;

  select id into v_profile from public.dating_profiles where user_id=new.user_id;
  if v_profile is not null then
    update public.dating_profiles
    set enabled=false,
        serious_intent_confirmed=false,
        single_confirmed_at=null,
        updated_at=now()
    where id=v_profile;

    if (v_old_age < 18) is distinct from (v_new_age < 18) then
      update public.dating_connections
      set status='closed',
          closed_at=coalesce(closed_at,now()),
          a_photo_consent=false,
          b_photo_consent=false
      where status in ('pending','accepted')
        and v_profile in (profile_a_id,profile_b_id);

      update public.dating_meet_requests r
      set status='cancelled'
      from public.dating_connections c
      where r.connection_id=c.id
        and r.status='waiting'
        and v_profile in (c.profile_a_id,c.profile_b_id);
    end if;
  end if;

  return new;
end;
$$;

revoke all on function private.sinjira_birth_date_change_guard() from public, anon, authenticated;

drop trigger if exists sinjira_birth_date_change_guard on public.account_safety_profiles;
create trigger sinjira_birth_date_change_guard
after update of date_of_birth on public.account_safety_profiles
for each row
when (old.date_of_birth is distinct from new.date_of_birth)
execute function private.sinjira_birth_date_change_guard();

create schema if not exists sinjira_profile_internal;
revoke all on schema sinjira_profile_internal from public, anon;
grant usage on schema sinjira_profile_internal to authenticated, service_role;

create or replace function sinjira_profile_internal.private_profile_get()
returns jsonb
language plpgsql
stable
security definer
set search_path to 'pg_catalog','public'
as $$
declare
  v_uid uuid := auth.uid();
  p public.private_profiles%rowtype;
  s public.account_safety_profiles%rowtype;
  v_birth date;
  v_gender text;
  v_relationship text;
begin
  if v_uid is null then raise exception 'AUTH_REQUIRED'; end if;

  select * into p from public.private_profiles where user_id=v_uid;
  select * into s from public.account_safety_profiles where user_id=v_uid;

  v_birth := coalesce(p.birth_date,s.date_of_birth);
  v_gender := coalesce(p.gender,case s.sex when 'female' then 'woman' when 'male' then 'man' else null end);
  v_relationship := coalesce(nullif(p.relationship_status,'not_set'),nullif(s.relationship_status,'not_set'),'not_set');

  return jsonb_build_object(
    'birth_date',v_birth,
    'gender',v_gender,
    'languages',coalesce(to_jsonb(p.languages),'[]'::jsonb),
    'residence_city',p.residence_city,
    'residence_region',p.residence_region,
    'residence_country',p.residence_country,
    'origin_city',p.origin_city,
    'origin_region',p.origin_region,
    'origin_country',p.origin_country,
    'relationship_status',v_relationship,
    'relationship_since',p.relationship_since,
    'relationship_partner_label',p.relationship_partner_label,
    'has_safety_birth_date',(s.user_id is not null),
    'updated_at',p.updated_at
  );
end;
$$;

create or replace function sinjira_profile_internal.private_profile_save(
  p_birth_date date,
  p_gender text,
  p_languages text[],
  p_residence_city text,
  p_residence_region text,
  p_residence_country text,
  p_origin_city text,
  p_origin_region text,
  p_origin_country text,
  p_relationship_status text,
  p_relationship_since date,
  p_relationship_partner_label text
)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public'
as $$
declare
  v_uid uuid := auth.uid();
  s public.account_safety_profiles%rowtype;
  v_effective_birth date;
  v_relationship text;
  v_gender text;
  v_languages text[] := '{}'::text[];
  v_birth_changed boolean := false;
  v_relationship_changed boolean := false;
begin
  if v_uid is null then raise exception 'AUTH_REQUIRED'; end if;

  v_gender := nullif(btrim(coalesce(p_gender,'')),'');
  if v_gender is not null and v_gender not in ('woman','man','non_binary','other','prefer_not_to_say') then
    raise exception 'INVALID_GENDER';
  end if;

  v_relationship := coalesce(nullif(btrim(coalesce(p_relationship_status,'')),''),'not_set');
  if v_relationship not in ('not_set','single','partnered','engaged','married','separated','divorced','widowed') then
    raise exception 'INVALID_RELATIONSHIP_STATUS';
  end if;

  if p_relationship_since is not null and p_relationship_since>current_date then
    raise exception 'INVALID_RELATIONSHIP_DATE';
  end if;

  v_languages := array(
    select x
    from (
      select btrim(v) as x,min(ord) as first_ord
      from unnest(coalesce(p_languages,'{}'::text[])) with ordinality as u(v,ord)
      where btrim(v)<>''
      group by btrim(v)
      order by min(ord)
      limit 12
    ) q
    order by first_ord
  );
  if exists(select 1 from unnest(v_languages) x where char_length(x)>40) then
    raise exception 'LANGUAGE_VALUE_TOO_LONG';
  end if;

  if char_length(coalesce(p_residence_city,''))>100
     or char_length(coalesce(p_residence_region,''))>100
     or char_length(coalesce(p_residence_country,''))>100
     or char_length(coalesce(p_origin_city,''))>100
     or char_length(coalesce(p_origin_region,''))>100
     or char_length(coalesce(p_origin_country,''))>100
     or char_length(coalesce(p_relationship_partner_label,''))>120 then
    raise exception 'PROFILE_VALUE_TOO_LONG';
  end if;

  select * into s from public.account_safety_profiles where user_id=v_uid for update;

  if s.user_id is not null then
    v_effective_birth := coalesce(p_birth_date,s.date_of_birth);
    v_birth_changed := s.date_of_birth is distinct from v_effective_birth;
    v_relationship_changed := s.relationship_status is distinct from v_relationship;

    update public.account_safety_profiles
    set date_of_birth=v_effective_birth,
        relationship_status=v_relationship,
        relationship_status_updated_at=case when v_relationship_changed then now() else relationship_status_updated_at end,
        updated_at=now()
    where user_id=v_uid;
  else
    v_effective_birth := p_birth_date;
    if v_effective_birth is not null then
      if v_effective_birth>current_date then raise exception 'INVALID_BIRTH_DATE'; end if;
      if extract(year from age(current_date,v_effective_birth))::integer<13 then raise exception 'SINJIRA_MINIMUM_AGE_13'; end if;
      if extract(year from age(current_date,v_effective_birth))::integer>120 then raise exception 'INVALID_BIRTH_DATE'; end if;

      insert into public.account_safety_profiles(user_id,date_of_birth,relationship_status,relationship_status_updated_at)
      values(v_uid,v_effective_birth,v_relationship,case when v_relationship<>'not_set' then now() else null end);
      v_birth_changed := true;
      v_relationship_changed := v_relationship<>'not_set';
    end if;
  end if;

  insert into public.private_profiles(
    user_id,birth_date,gender,languages,
    residence_city,residence_region,residence_country,
    origin_city,origin_region,origin_country,
    relationship_status,relationship_since,relationship_partner_label,
    created_at,updated_at
  ) values (
    v_uid,v_effective_birth,v_gender,v_languages,
    nullif(btrim(coalesce(p_residence_city,'')),''),
    nullif(btrim(coalesce(p_residence_region,'')),''),
    nullif(btrim(coalesce(p_residence_country,'')),''),
    nullif(btrim(coalesce(p_origin_city,'')),''),
    nullif(btrim(coalesce(p_origin_region,'')),''),
    nullif(btrim(coalesce(p_origin_country,'')),''),
    v_relationship,p_relationship_since,
    nullif(btrim(coalesce(p_relationship_partner_label,'')),''),
    now(),now()
  )
  on conflict(user_id) do update set
    birth_date=excluded.birth_date,
    gender=excluded.gender,
    languages=excluded.languages,
    residence_city=excluded.residence_city,
    residence_region=excluded.residence_region,
    residence_country=excluded.residence_country,
    origin_city=excluded.origin_city,
    origin_region=excluded.origin_region,
    origin_country=excluded.origin_country,
    relationship_status=excluded.relationship_status,
    relationship_since=excluded.relationship_since,
    relationship_partner_label=excluded.relationship_partner_label,
    updated_at=now();

  return jsonb_build_object(
    'ok',true,
    'birth_date_changed',v_birth_changed,
    'relationship_status_changed',v_relationship_changed,
    'dating_reconfirmation_required',v_birth_changed
  );
end;
$$;

revoke all on function sinjira_profile_internal.private_profile_get() from public, anon;
grant execute on function sinjira_profile_internal.private_profile_get() to authenticated, service_role;
revoke all on function sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text) from public, anon;
grant execute on function sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text) to authenticated, service_role;

create or replace function public.private_profile_get()
returns jsonb
language sql
stable
security invoker
set search_path to ''
as $$select sinjira_profile_internal.private_profile_get()$$;

create or replace function public.private_profile_save(
  p_birth_date date,
  p_gender text,
  p_languages text[],
  p_residence_city text,
  p_residence_region text,
  p_residence_country text,
  p_origin_city text,
  p_origin_region text,
  p_origin_country text,
  p_relationship_status text,
  p_relationship_since date,
  p_relationship_partner_label text
)
returns jsonb
language sql
security invoker
set search_path to ''
as $$
select sinjira_profile_internal.private_profile_save(
  p_birth_date,p_gender,p_languages,
  p_residence_city,p_residence_region,p_residence_country,
  p_origin_city,p_origin_region,p_origin_country,
  p_relationship_status,p_relationship_since,p_relationship_partner_label
)
$$;

revoke all on function public.private_profile_get() from public, anon;
grant execute on function public.private_profile_get() to authenticated, service_role;
revoke all on function public.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text) from public, anon;
grant execute on function public.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text) to authenticated, service_role;
