-- SINJIRA™ V24.4.42 — permet le diagnostic interne SQL tout en gardant l'ACL service_role côté API.
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
  if auth.uid() is not null and coalesce(auth.jwt()->>'role','')<>'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED';
  end if;

  select u.id into v_user
  from auth.users u
  where lower(coalesce(u.email,''))='kingtyrano@gmail.com'
  limit 1;

  if v_user is null then
    return jsonb_build_object('ok',false,'health_version','24.4.42','owner_found',false);
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
    'health_version','24.4.42',
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
