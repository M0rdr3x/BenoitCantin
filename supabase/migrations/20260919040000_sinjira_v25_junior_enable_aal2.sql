-- SINJIRA™ V25 — step-up parental pour activer la Communauté Junior.
-- L'activation augmente les capacités sociales d'un compte 11–12 ans et exige AAL2.
-- La désactivation reste volontairement possible en AAL1 afin de préserver une voie
-- fail-safe immédiate de retrait d'accès.

create or replace function public.guardian_set_junior_community(
  p_child_user_id uuid,
  p_enabled boolean
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  uid uuid:=auth.uid();
  v_enabled boolean:=coalesce(p_enabled,false);
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  -- Sérialise activation/révocation sur le lien de supervision lui-même.
  -- Une révocation concurrente ne peut donc pas passer entre le contrôle
  -- d'autorité et l'écriture du consentement Junior.
  perform 1
  from public.guardian_links g
  where g.guardian_user_id=uid
    and g.minor_user_id=p_child_user_id
    and g.status='verified'
    and g.revoked_at is null
  for update;

  if not found then
    raise exception 'GUARDIAN_ACCESS_REQUIRED';
  end if;

  if public.sinjira_age_band(p_child_user_id)<>'child' then
    raise exception 'JUNIOR_COMMUNITY_11_12_ONLY';
  end if;

  -- L'activation est un consentement parental qui augmente les capacités sociales.
  -- Le retrait reste disponible sans step-up pour être fail-safe.
  if v_enabled and coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;

  insert into public.junior_community_guardian_consents(
    minor_user_id,guardian_user_id,consented_at,revoked_at
  )
  values(
    p_child_user_id,uid,now(),case when v_enabled then null else now() end
  )
  on conflict(minor_user_id,guardian_user_id)
  do update set
    consented_at=case
      when v_enabled then now()
      else public.junior_community_guardian_consents.consented_at
    end,
    revoked_at=case when v_enabled then null else now() end;

  return jsonb_build_object('ok',true,'enabled',v_enabled);
end;
$$;

revoke all on function public.guardian_set_junior_community(uuid,boolean)
from public,anon;
grant execute on function public.guardian_set_junior_community(uuid,boolean)
to authenticated;

comment on function public.guardian_set_junior_community(uuid,boolean) is
  'V25: activation Junior exige lien tuteur actif verrouillé transactionnellement + enfant 11–12 + session AAL2; désactivation reste fail-safe en AAL1.';
