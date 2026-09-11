-- SINJIRA™ V25.0 — correction de la garde session lors d'un refus de challenge
-- L’HUMAIN AVANT TOUT : refuser une connexion peut révoquer l'appareil demandeur
-- avant de marquer le challenge comme denied. La vérification de session doit donc
-- rester valide même si revoked_at vient d'être posé dans la même transaction.

begin;

create or replace function private.security_challenge_request_session_guard()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_bound_session uuid;
begin
  -- Une liaison ne peut jamais être remplacée par une autre session.
  -- La seule réduction autorisée est session -> NULL (notamment via le FK
  -- ON DELETE SET NULL) : elle invalide la preuve et expire tout challenge pending.
  if old.request_session_id is not null
     and new.request_session_id is distinct from old.request_session_id then
    if new.request_session_id is null then
      if old.status='pending' then
        new.status := 'expired';
      end if;
      return new;
    end if;
    raise exception 'CHALLENGE_SESSION_IMMUTABLE' using errcode='42501';
  end if;

  -- L'enrichissement NULL -> session est permis uniquement pendant pending,
  -- afin de lier atomiquement le challenge créé par le moteur historique.
  if old.status <> 'pending'
     and new.request_session_id is distinct from old.request_session_id then
    raise exception 'CHALLENGE_SESSION_IMMUTABLE' using errcode='42501';
  end if;

  if old.status='pending' and new.status in ('approved','denied') then
    if old.request_session_id is null then
      raise exception 'CHALLENGE_SESSION_REQUIRED' using errcode='42501';
    end if;

    -- Ne pas filtrer revoked_at ici. Le chemin denied révoque volontairement
    -- l'appareil demandeur AVANT de faire passer le challenge à denied dans la
    -- même transaction. La preuve qui compte ici est la session liée, pas l'état
    -- de révocation. Le chemin approved refuse déjà explicitement un appareil
    -- préalablement révoqué avant cette transition de statut.
    select d.last_session_id into v_bound_session
    from public.security_devices d
    where d.id=old.request_device_id
      and d.user_id=old.user_id;

    if not found or v_bound_session is distinct from old.request_session_id then
      raise exception 'CHALLENGE_SESSION_MISMATCH' using errcode='42501';
    end if;
  end if;

  return new;
end;
$$;

revoke all on function private.security_challenge_request_session_guard() from public, anon, authenticated;
grant execute on function private.security_challenge_request_session_guard() to service_role;

comment on function private.security_challenge_request_session_guard() is
  'V25: la résolution exige la session demandeuse exacte; un refus peut révoquer l appareil avant le statut denied sans produire de faux mismatch.';

commit;
