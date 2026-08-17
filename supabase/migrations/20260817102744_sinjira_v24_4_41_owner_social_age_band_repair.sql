-- SINJIRA™ V24.4.41 — répare l'accès social du compte propriétaire sans inventer une date de naissance.
-- Le propriétaire est un compte adulte d'administration explicitement verrouillé par courriel côté serveur.
-- Tous les autres comptes continuent d'utiliser account_safety_profiles comme source canonique d'âge.

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
    when age(current_date,s.date_of_birth)<interval '12 years' then 'under12'
    when age(current_date,s.date_of_birth)<interval '18 years' then
      case
        when exists(
          select 1
          from public.guardian_links g
          where g.minor_user_id=s.user_id
            and g.status='verified'
        ) then 'youth'
        else 'youth_pending'
      end
    else 'adult'
  end
  from (select p_user_id user_id) x
  left join public.account_safety_profiles s on s.user_id=x.user_id;
$$;

revoke all on function public.sinjira_age_band(uuid) from public,anon;
grant execute on function public.sinjira_age_band(uuid) to authenticated,service_role;

create or replace function public.sinjira_owner_social_health()
returns jsonb
language plpgsql
stable
security definer
set search_path=public,auth
as $$
declare
  v_user uuid;
  v_band text;
  v_rules boolean:=false;
  v_suspended boolean:=false;
  v_profile boolean:=false;
  v_character uuid;
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED';
  end if;

  select u.id into v_user
  from auth.users u
  where lower(coalesce(u.email,''))='kingtyrano@gmail.com'
  limit 1;

  if v_user is null then
    return jsonb_build_object(
      'ok',false,
      'health_version','24.4.41',
      'owner_found',false
    );
  end if;

  v_band:=public.sinjira_age_band(v_user);
  v_rules:=public.has_accepted_community_rules(v_user);
  v_suspended:=public.social_is_suspended(v_user);

  select c.character_id into v_character
  from public.character_social_profiles c
  where c.user_id=v_user
    and lower(coalesce(c.status,''))<>'archived'
  order by c.updated_at desc nulls last
  limit 1;
  v_profile:=v_character is not null;

  return jsonb_build_object(
    'ok',v_band='adult' and v_rules and not v_suspended and v_profile,
    'health_version','24.4.41',
    'owner_found',true,
    'effective_age_band',v_band,
    'rules_accepted',v_rules,
    'suspended',v_suspended,
    'social_profile',v_profile,
    'character_id',v_character
  );
end;
$$;

revoke all on function public.sinjira_owner_social_health() from public,anon,authenticated;
grant execute on function public.sinjira_owner_social_health() to service_role;
