-- CANDIDATE ONLY / REVIEW REQUIRED / NOT A MIGRATION
-- Changes do not run against production. Preserve the existing function body,
-- ACL and signatures while requiring a live auth.sessions row for privileged
-- device-trust and connection-challenge operations. Requires an isolated
-- database test and reconciliation of the production migration ledger.
-- Existing source: current production pg_get_functiondef(), 2026-10-31.
--
-- No new GRANT, REVOKE, policy changes, tables or privileges.
-- Do NOT deploy without comparing future V25 migrations (#713 / #714).
BEGIN;

-- Original SQL source: pg_get_functiondef() on current production, reviewed 2026-10-31.
-- Signature: p_challenge_id uuid, p_device_key text, p_decision text
CREATE OR REPLACE FUNCTION sinjira_security_internal.security_resolve_connection_challenge(p_challenge_id uuid, p_device_key text, p_decision text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'private', 'auth'
AS $function$
declare
  v_user uuid := auth.uid();
  v_session uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_device public.security_devices;
  v_request_device public.security_devices;
  v_ch public.security_connection_challenges;
  v_status text;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  if p_decision not in ('approved','denied') then raise exception 'INVALID_DECISION'; end if;
  if v_session is null then raise exception 'CURRENT_TRUSTED_DEVICE_REQUIRED' using errcode='42501'; end if;

  -- Obligation de session active : le JWT peut survivre à une déconnexion.
  -- Le garde doit précéder toute décision ou mutation d'appareil/challenge.
  if v_session is null or not exists (
    select 1
    from auth.sessions as live_session
    where live_session.id = v_session
      and live_session.user_id = v_user
      and (live_session.not_after is null or live_session.not_after > now())
  ) then
    raise exception 'ACTIVE_SESSION_REQUIRED' using errcode='42501';
  end if;

  perform private.security_require_aal2_if_available(v_user);

  select * into v_device
  from public.security_devices
  where user_id=v_user
    and device_key=p_device_key
    and is_trusted
    and revoked_at is null
    and last_session_id=v_session;
  if not found then
    raise exception 'CURRENT_TRUSTED_DEVICE_REQUIRED' using errcode='42501';
  end if;

  select * into v_ch
  from public.security_connection_challenges
  where id=p_challenge_id and user_id=v_user
  for update;
  if not found then raise exception 'CHALLENGE_NOT_FOUND'; end if;

  if v_ch.status<>'pending' or v_ch.expires_at<=now() then
    update public.security_connection_challenges
       set status='expired'
     where id=v_ch.id and status='pending';
    raise exception 'CHALLENGE_EXPIRED';
  end if;

  if v_ch.request_device_id is null then
    raise exception 'CHALLENGE_REQUEST_DEVICE_MISSING';
  end if;

  if v_device.id=v_ch.request_device_id then
    raise exception 'TRUSTED_OTHER_DEVICE_REQUIRED' using errcode='42501';
  end if;

  select * into v_request_device
  from public.security_devices
  where id=v_ch.request_device_id and user_id=v_user
  for update;
  if not found then raise exception 'REQUEST_DEVICE_NOT_FOUND'; end if;

  v_status:=p_decision;

  if v_status='approved' then
    if v_request_device.revoked_at is not null then
      raise exception 'REQUEST_DEVICE_REVOKED' using errcode='42501';
    end if;
    update public.security_devices
       set is_trusted=true,
           is_primary=false,
           last_seen_at=greatest(last_seen_at,now())
     where id=v_request_device.id;
  else
    update public.security_devices
       set revoked_at=coalesce(revoked_at,now()),
           is_trusted=false,
           is_primary=false
     where id=v_request_device.id;
  end if;

  update public.security_connection_challenges
     set status=v_status,
         resolved_at=now(),
         resolved_device_id=v_device.id
   where id=v_ch.id
  returning * into v_ch;

  update public.security_connection_events
     set outcome=v_status,
         event_type=case when v_status='approved' then 'approved' else 'denied' end
   where id=v_ch.connection_event_id;

  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(
    v_user,
    v_device.id,
    'connection_'||v_status,
    case when v_status='approved'
      then 'Connexion inhabituelle approuvée depuis un autre appareil fiable et courant.'
      else 'Connexion inhabituelle refusée depuis un autre appareil fiable et courant; l’appareil demandeur a été révoqué.'
    end,
    case when v_status='approved' then 'info' else 'critical' end
  );

  return to_jsonb(v_ch);
end;
$function$;

-- Original SQL source: pg_get_functiondef() on current production, reviewed 2026-10-31.
-- Signature: p_device_id uuid, p_trusted boolean, p_primary boolean
CREATE OR REPLACE FUNCTION sinjira_security_internal.security_set_device_trust(p_device_id uuid, p_trusted boolean, p_primary boolean DEFAULT false)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'auth', 'private'
AS $function$
declare
  v_user uuid := auth.uid();
  v_session uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_row public.security_devices;
  v_has_other_trusted boolean := false;
  v_recent_approved boolean := false;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  -- Obligation de session active : le JWT peut survivre à une déconnexion.
  -- Le garde doit précéder toute décision ou mutation d'appareil/challenge.
  if v_session is null or not exists (
    select 1
    from auth.sessions as live_session
    where live_session.id = v_session
      and live_session.user_id = v_user
      and (live_session.not_after is null or live_session.not_after > now())
  ) then
    raise exception 'ACTIVE_SESSION_REQUIRED' using errcode='42501';
  end if;

  perform private.security_require_aal2_if_available(v_user);

  if p_trusted and coalesce(auth.jwt()->>'aal','aal1') <> 'aal2' then
    raise exception 'AAL2_REQUIRED' using errcode='42501';
  end if;
  if p_primary and not p_trusted then
    raise exception 'PRIMARY_DEVICE_MUST_BE_TRUSTED' using errcode='22023';
  end if;

  select * into v_row
  from public.security_devices
  where id=p_device_id and user_id=v_user and revoked_at is null
  for update;
  if not found then raise exception 'DEVICE_NOT_FOUND'; end if;

  if p_trusted and not v_row.is_trusted then
    if v_session is null or v_row.last_session_id is distinct from v_session then
      raise exception 'CURRENT_DEVICE_REQUIRED' using errcode='42501';
    end if;

    select exists(
      select 1 from public.security_devices d
      where d.user_id=v_user
        and d.id<>v_row.id
        and d.is_trusted
        and d.revoked_at is null
    ) into v_has_other_trusted;

    if v_has_other_trusted then
      select exists(
        select 1
        from public.security_connection_challenges c
        join public.security_devices resolver
          on resolver.id=c.resolved_device_id
         and resolver.user_id=v_user
         and resolver.id<>v_row.id
         and resolver.is_trusted
         and resolver.revoked_at is null
        where c.user_id=v_user
          and c.request_device_id=v_row.id
          and c.status='approved'
          and c.resolved_at is not null
          and c.resolved_at>now()-interval '30 minutes'
      ) into v_recent_approved;

      if not v_recent_approved then
        raise exception 'TRUST_CONFIRMATION_REQUIRED' using errcode='42501';
      end if;
    end if;
  end if;

  if p_primary then
    update public.security_devices
       set is_primary=false
     where user_id=v_user and id<>p_device_id;
  end if;

  update public.security_devices
     set is_trusted=p_trusted,
         is_primary=(p_trusted and p_primary)
   where id=p_device_id
   returning * into v_row;

  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(
    v_user,
    v_row.id,
    'device_trust_changed',
    case when p_trusted then 'Appareil marqué comme fiable.' else 'Confiance retirée à un appareil.' end,
    'warning'
  );

  return jsonb_build_object(
    'id',v_row.id,
    'display_name',v_row.display_name,
    'device_type',v_row.device_type,
    'platform',v_row.platform,
    'is_trusted',v_row.is_trusted,
    'is_primary',v_row.is_primary,
    'first_seen_at',v_row.first_seen_at,
    'last_seen_at',v_row.last_seen_at,
    'last_country_code',v_row.last_country_code,
    'last_region_code',v_row.last_region_code,
    'revoked_at',v_row.revoked_at,
    'is_current',(v_session is not null and v_row.last_session_id=v_session)
  );
end;
$function$;

COMMIT;
