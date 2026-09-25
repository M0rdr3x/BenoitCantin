-- SINJIRA™ V25 — AAL2 obligatoire pour créer une autorisation parentale.
-- Un code parental peut créer/rétablir un lien de supervision d'un mineur.
-- Ce geste sensible exige donc une session adulte élevée à AAL2, indépendamment
-- du réglage MFA global, tout en conservant les gardes historiques supplémentaires.
--
-- Compatibilité : les codes historiques à 10 caractères restent valides jusqu'à
-- leur expiration; les nouveaux codes générés utilisent 16 caractères hexadécimaux.

alter table public.guardian_signup_invites
  drop constraint if exists guardian_signup_invites_code_format_check;

alter table public.guardian_signup_invites
  add constraint guardian_signup_invites_code_format_check
  check (invite_code ~ '^YOUTH-[A-Z0-9]{10}([A-Z0-9]{6})?returns text
language plpgsql
security definer
set search_path=pg_catalog,public,auth
as $$
declare
  uid uuid:=auth.uid();
  v_code text;
  v_uuid_hex text;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if public.sinjira_age_band(uid) <> 'adult' then
    raise exception 'ADULT_GUARDIAN_REQUIRED';
  end if;

  -- Frontière V25 : une session AAL1 ne peut jamais émettre un code
  -- capable de créer/rétablir une supervision d'enfant.
  if coalesce(auth.jwt()->>'aal','aal1') <> 'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;

  -- Conserver les politiques historiques plus strictes lorsqu'elles sont activées
  -- (ex. configuration MFA/ligne mobile du déploiement).
  if not public.sinjira_mfa_access_allowed(uid) then
    raise exception 'MFA_REQUIRED';
  end if;

  -- Un nouveau code invalide tous les anciens codes non consommés de ce tuteur.
  delete from public.guardian_signup_invites
  where guardian_user_id=uid
    and used_at is null;

  loop
    -- UUID v4 contient des nibbles réservés (version/variant). Pour obtenir
    -- 16 chiffres hexadécimaux réellement aléatoires, on exclut ces positions
    -- au lieu de tronquer naïvement les 16 premiers caractères.
    v_uuid_hex:=replace(gen_random_uuid()::text,'-','');
    v_code:='YOUTH-'||upper(
      substr(v_uuid_hex,1,12)
      ||substr(v_uuid_hex,14,3)
      ||substr(v_uuid_hex,18,1)
    );
    exit when not exists(
      select 1
      from public.guardian_signup_invites
      where invite_code=v_code
    );
  end loop;

  insert into public.guardian_signup_invites(guardian_user_id,invite_code)
  values(uid,v_code);

  return v_code;
end;
$$;

revoke all on function public.create_guardian_signup_invite()
from public,anon;
grant execute on function public.create_guardian_signup_invite()
to authenticated;

comment on function public.create_guardian_signup_invite() is
  'V25: émission code parental à usage unique de 16 caractères réservée à un adulte en session AAL2; les anciens codes 10 caractères restent consommables jusqu à expiration.';
);

create or replace function public.create_guardian_signup_invite()
returns text
language plpgsql
security definer
set search_path=pg_catalog,public,auth
as $$
declare
  uid uuid:=auth.uid();
  v_code text;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if public.sinjira_age_band(uid) <> 'adult' then
    raise exception 'ADULT_GUARDIAN_REQUIRED';
  end if;

  -- Frontière V25 : une session AAL1 ne peut jamais émettre un code
  -- capable de créer/rétablir une supervision d'enfant.
  if coalesce(auth.jwt()->>'aal','aal1') <> 'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;

  -- Conserver les politiques historiques plus strictes lorsqu'elles sont activées
  -- (ex. configuration MFA/ligne mobile du déploiement).
  if not public.sinjira_mfa_access_allowed(uid) then
    raise exception 'MFA_REQUIRED';
  end if;

  -- Un nouveau code invalide tous les anciens codes non consommés de ce tuteur.
  delete from public.guardian_signup_invites
  where guardian_user_id=uid
    and used_at is null;

  loop
    v_code:='YOUTH-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,10));
    exit when not exists(
      select 1
      from public.guardian_signup_invites
      where invite_code=v_code
    );
  end loop;

  insert into public.guardian_signup_invites(guardian_user_id,invite_code)
  values(uid,v_code);

  return v_code;
end;
$$;

revoke all on function public.create_guardian_signup_invite()
from public,anon;
grant execute on function public.create_guardian_signup_invite()
to authenticated;

comment on function public.create_guardian_signup_invite() is
  'V25: émission code parental à usage unique réservée à un adulte en session AAL2; conserve les gardes MFA historiques additionnelles.';
