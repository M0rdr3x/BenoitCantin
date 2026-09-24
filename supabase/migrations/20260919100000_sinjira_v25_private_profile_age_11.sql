-- SINJIRA™ V25 — compatibilité Profil privé avec le minimum d'âge actuel 11+.
-- Forward-only : ne modifie aucune migration historique déjà inscrite au ledger.
-- Les 11–13 ans restent conditionnés à un lien parent/tuteur vérifié et non révoqué, en lecture comme en écriture.

create or replace function sinjira_profile_internal.private_profile_get()
returns jsonb
language plpgsql
stable
security definer
set search_path to 'pg_catalog','public'
as $$
declare
  v_uid uuid:=auth.uid();
  p public.private_profiles%rowtype;
  s public.account_safety_profiles%rowtype;
  v_birth date;
  v_age integer;
  v_gender text;
  v_relationship text;
begin
  if v_uid is null then raise exception 'AUTH_REQUIRED'; end if;

  if to_regprocedure('sinjira_rls_internal.sinjira_mfa_access_allowed(uuid)') is not null
     and not sinjira_rls_internal.sinjira_mfa_access_allowed(v_uid) then
    raise exception 'MFA_REQUIRED';
  end if;

  select * into p from public.private_profiles where user_id=v_uid;
  select * into s from public.account_safety_profiles where user_id=v_uid;

  v_birth:=coalesce(p.birth_date,s.date_of_birth);

  if v_birth is not null then
    if v_birth>current_date then
      raise exception 'INVALID_BIRTH_DATE';
    end if;

    v_age:=extract(year from age(current_date,v_birth))::integer;

    if v_age<11 then
      raise exception 'SINJIRA_MINIMUM_AGE_11';
    end if;

    if v_age>120 then
      raise exception 'INVALID_BIRTH_DATE';
    end if;

    if v_age<14
       and not exists(
         select 1
         from public.guardian_links g
         where g.minor_user_id=v_uid
           and g.status='verified'
           and g.revoked_at is null
       ) then
      raise exception 'GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14';
    end if;
  end if;

  v_gender:=coalesce(
    p.gender,
    case s.sex when 'female' then 'woman' when 'male' then 'man' else null end
  );
  v_relationship:=coalesce(
    nullif(p.relationship_status,'not_set'),
    nullif(s.relationship_status,'not_set'),
    nullif(s.relationship_status,'not_specified'),
    'not_set'
  );

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

revoke all on function sinjira_profile_internal.private_profile_get()
from public,anon;
grant execute on function sinjira_profile_internal.private_profile_get()
to authenticated,service_role;

comment on function sinjira_profile_internal.private_profile_get() is
  'V25: lecture self-only du coffre privé sous MFA; minimum 11 ans et tuteur actif requis avant 14 ans.';

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
  v_uid uuid:=auth.uid();
  s public.account_safety_profiles%rowtype;
  v_effective_birth date;
  v_age integer;
  v_relationship text;
  v_gender text;
  v_languages text[]:='{}'::text[];
  v_residence_country text:=nullif(btrim(coalesce(p_residence_country,'')),'');
  v_birth_changed boolean:=false;
  v_relationship_changed boolean:=false;
begin
  if v_uid is null then raise exception 'AUTH_REQUIRED'; end if;

  if to_regprocedure('sinjira_rls_internal.sinjira_mfa_access_allowed(uuid)') is not null
     and not sinjira_rls_internal.sinjira_mfa_access_allowed(v_uid) then
    raise exception 'MFA_REQUIRED';
  end if;

  v_gender:=nullif(btrim(coalesce(p_gender,'')),'');
  if v_gender is not null
     and v_gender not in ('woman','man','non_binary','other','prefer_not_to_say') then
    raise exception 'INVALID_GENDER';
  end if;

  v_relationship:=coalesce(
    nullif(btrim(coalesce(p_relationship_status,'')),''),
    'not_set'
  );
  if v_relationship not in (
    'not_set','single','partnered','engaged','married',
    'separated','divorced','widowed'
  ) then
    raise exception 'INVALID_RELATIONSHIP_STATUS';
  end if;

  if p_relationship_since is not null
     and p_relationship_since>current_date then
    raise exception 'INVALID_RELATIONSHIP_DATE';
  end if;

  v_languages:=array(
    select x
    from (
      select btrim(v) x,min(ord) first_ord
      from unnest(coalesce(p_languages,'{}'::text[])) with ordinality u(v,ord)
      where btrim(v)<>''
      group by btrim(v)
      order by min(ord)
      limit 12
    ) q
    order by first_ord
  );

  if exists(
    select 1
    from unnest(v_languages) x
    where char_length(x)>40
  ) then
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

  select *
  into s
  from public.account_safety_profiles
  where user_id=v_uid
  for update;

  v_effective_birth:=coalesce(p_birth_date,s.date_of_birth);

  -- Une date de naissance déjà enregistrée dans le profil sécurité est une frontière
  -- de protection. Un compte mineur peut corriger sa date vers un état au moins aussi
  -- protecteur, mais ne peut pas se vieillir lui-même pour sortir de Junior/tuteur/youth.
  if s.user_id is not null
     and s.date_of_birth is not null
     and extract(year from age(current_date,s.date_of_birth))::integer < 18
     and v_effective_birth is not null
     and v_effective_birth < s.date_of_birth then
    raise exception 'BIRTH_DATE_PROTECTION_BOUNDARY_REQUIRES_REVIEW';
  end if;

  if v_effective_birth is not null then
    if v_effective_birth>current_date then
      raise exception 'INVALID_BIRTH_DATE';
    end if;

    v_age:=extract(year from age(current_date,v_effective_birth))::integer;

    if v_age<11 then
      raise exception 'SINJIRA_MINIMUM_AGE_11';
    end if;

    if v_age>120 then
      raise exception 'INVALID_BIRTH_DATE';
    end if;

    if v_age<18
       and lower(coalesce(v_residence_country,'')) not in ('canada','ca','can') then
      raise exception 'YOUTH_JURISDICTION_NOT_ENABLED';
    end if;

    if v_age<14
       and not exists(
         select 1
         from public.guardian_links g
         where g.minor_user_id=v_uid
           and g.status='verified'
           and g.revoked_at is null
       ) then
      raise exception 'GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14';
    end if;
  end if;

  if s.user_id is not null then
    v_birth_changed:=s.date_of_birth is distinct from v_effective_birth;
    v_relationship_changed:=s.relationship_status is distinct from v_relationship;

    update public.account_safety_profiles
    set date_of_birth=v_effective_birth,
        relationship_status=v_relationship,
        relationship_status_updated_at=case
          when v_relationship_changed then now()
          else relationship_status_updated_at
        end,
        updated_at=now()
    where user_id=v_uid;
  elsif v_effective_birth is not null then
    insert into public.account_safety_profiles(
      user_id,date_of_birth,relationship_status,relationship_status_updated_at
    )
    values(
      v_uid,
      v_effective_birth,
      v_relationship,
      case when v_relationship<>'not_set' then now() else null end
    );
    v_birth_changed:=true;
    v_relationship_changed:=v_relationship<>'not_set';
  end if;

  insert into public.private_profiles(
    user_id,birth_date,gender,languages,
    residence_city,residence_region,residence_country,
    origin_city,origin_region,origin_country,
    relationship_status,relationship_since,relationship_partner_label,
    created_at,updated_at
  )
  values(
    v_uid,v_effective_birth,v_gender,v_languages,
    nullif(btrim(coalesce(p_residence_city,'')),''),
    nullif(btrim(coalesce(p_residence_region,'')),''),
    v_residence_country,
    nullif(btrim(coalesce(p_origin_city,'')),''),
    nullif(btrim(coalesce(p_origin_region,'')),''),
    nullif(btrim(coalesce(p_origin_country,'')),''),
    v_relationship,
    p_relationship_since,
    nullif(btrim(coalesce(p_relationship_partner_label,'')),''),
    now(),now()
  )
  on conflict(user_id) do update
  set birth_date=excluded.birth_date,
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

revoke all on function sinjira_profile_internal.private_profile_save(
  date,text,text[],text,text,text,text,text,text,text,date,text
) from public,anon;
grant execute on function sinjira_profile_internal.private_profile_save(
  date,text,text[],text,text,text,text,text,text,text,date,text
) to authenticated,service_role;

comment on function sinjira_profile_internal.private_profile_save(
  date,text,text[],text,text,text,text,text,text,text,date,text
) is
  'V25: profil privé modifiable à partir de 11 ans; tuteur actif requis avant 14 ans; un mineur ne peut pas augmenter son âge déclaré sans revue séparée; accès direct à private_profiles toujours fermé.';
