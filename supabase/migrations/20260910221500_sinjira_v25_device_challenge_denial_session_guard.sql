-- SINJIRA™ V25.0 — convergence garde session lors d'un refus de challenge
-- L'HUMAIN AVANT TOUT : refuser un appareil reste atomique. La révocation de
-- l'appareil demandeur ne doit pas empêcher la garde de vérifier la session
-- à laquelle le challenge était lié.

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
  -- session -> NULL reste autorisé uniquement comme réduction de preuve
  -- (notamment via auth.sessions ON DELETE SET NULL). Un pending devient expiré.
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

  -- NULL -> session est permis uniquement pendant pending afin de lier
  -- atomiquement un challenge fraîchement créé au contexte serveur vérifié.
  if old.status <> 'pending'
     and new.request_session_id is distinct from old.request_session_id then
    raise exception 'CHALLENGE_SESSION_IMMUTABLE' using errcode='42501';
  end if;

  if old.status='pending' and new.status in ('approved','denied') then
    if old.request_session_id is null then
      raise exception 'CHALLENGE_SESSION_REQUIRED' using errcode='42501';
    end if;

    -- Ne pas filtrer revoked_at ici : sur le chemin denied, la fonction de
    -- résolution révoque volontairement l'appareil demandeur avant de résoudre
    -- le challenge dans la même transaction. La ligne doit néanmoins exister
    -- et conserver exactement la session demandeuse.
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
  'V25: résolution liée à la session demandeuse; le refus reste valide après révocation atomique de l’appareil, sans permettre le rejeu inter-session.';

commit;
