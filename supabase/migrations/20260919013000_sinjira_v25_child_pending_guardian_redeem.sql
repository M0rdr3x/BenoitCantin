-- SINJIRA™ V25 — rétablissement fail-closed de supervision pour child_pending.
-- Après révocation de tous les liens tuteur valides, un compte 11–12 passe en child_pending.
-- L'interface Relations propose alors un nouveau code parental : le RPC doit accepter exactement
-- cet état pending, sans ouvrir l'ajout implicite de tuteurs aux comptes déjà supervisés.

create or replace function public.redeem_guardian_signup_invite(p_code text)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,auth
as $$
declare
  uid uuid:=auth.uid();
  v_code text:=upper(trim(coalesce(p_code,'')));
  band text;
  inv public.guardian_signup_invites%rowtype;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  -- Sérialise toutes les consommations de code pour un même compte. Sans ce verrou,
  -- deux invitations de tuteurs différents pourraient lire child_pending en parallèle
  -- puis créer deux liens verified avant que la bande d'âge ne soit recalculée.
  perform 1
  from public.account_safety_profiles s
  where s.user_id=uid
  for update;
  if not found then raise exception 'YOUTH_ACCOUNT_REQUIRED'; end if;

  band:=public.sinjira_age_band(uid);

  -- V25 : child_pending est désormais une bande de premier ordre.
  -- youth reste accepté uniquement pour compatibilité avec l'ancien contrat; un lien
  -- vérifié non révoqué le fera échouer immédiatement comme déjà supervisé.
  if band not in ('child_pending','youth_pending','youth') then
    raise exception 'YOUTH_ACCOUNT_REQUIRED';
  end if;

  if band='youth' and exists(
    select 1
    from public.guardian_links g
    where g.minor_user_id=uid
      and g.status='verified'
      and g.revoked_at is null
  ) then
    raise exception 'GUARDIAN_ALREADY_VERIFIED';
  end if;

  if v_code !~ '^YOUTH-[A-Z0-9]{10}$' then
    raise exception 'INVALID_GUARDIAN_CODE_FORMAT';
  end if;

  select * into inv
  from public.guardian_signup_invites
  where invite_code=v_code
    and used_at is null
    and expires_at>now()
  for update;

  if inv.id is null then raise exception 'INVALID_OR_EXPIRED_GUARDIAN_CODE'; end if;
  if inv.guardian_user_id=uid then raise exception 'SELF_GUARDIAN_FORBIDDEN'; end if;
  if public.sinjira_age_band(inv.guardian_user_id)<>'adult' then
    raise exception 'ADULT_GUARDIAN_REQUIRED';
  end if;

  update public.guardian_signup_invites
  set used_at=now(),minor_user_id=uid
  where id=inv.id;

  -- sync_guardian_signup_invite_link réactive/crée guardian_links en verified,
  -- remet revoked_at à null et la bande est recalculée immédiatement.
  return jsonb_build_object(
    'ok',true,
    'status','verified',
    'minor_user_id',uid,
    'age_band',public.sinjira_age_band(uid)
  );
end;
$$;

revoke all on function public.redeem_guardian_signup_invite(text) from public,anon;
grant execute on function public.redeem_guardian_signup_invite(text) to authenticated;

comment on function public.redeem_guardian_signup_invite(text) is
  'V25: rétablissement sérialisé par compte via verrou account_safety_profiles; consomme un code parental à usage unique uniquement depuis un état pending admissible, sans ajout concurrent implicite de tuteur.';
