-- CANDIDAT STAGING / REVUE SQL UNIQUEMENT.
-- Ne PAS exécuter en production : ce script se termine par ROLLBACK.
-- Sources : définitions actives pg_get_functiondef, lues sans données.
-- Aucun changement de grant sur les huit RPC existantes.
BEGIN;

CREATE OR REPLACE FUNCTION private.security_require_current_auth_session(p_user uuid)
RETURNS void
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path TO 'pg_catalog'
AS $session_guard$
DECLARE
  v_session uuid;
BEGIN
  IF p_user IS NULL OR p_user IS DISTINCT FROM auth.uid() THEN
    RAISE EXCEPTION 'AUTH_SESSION_INVALID' USING ERRCODE='42501';
  END IF;

  -- Le session_id provient du JWT validé par Supabase, pas d'un
  -- paramètre arbitraire de l'API.
  BEGIN
    v_session := NULLIF(auth.jwt()->>'session_id','')::uuid;
  EXCEPTION WHEN invalid_text_representation THEN
    RAISE EXCEPTION 'AUTH_SESSION_INVALID' USING ERRCODE='42501';
  END;

  IF v_session IS NULL OR NOT EXISTS(
    SELECT 1 FROM auth.sessions s
    WHERE s.id = v_session
      AND s.user_id = p_user
      AND (s.not_after IS NULL OR s.not_after > now())
  ) THEN
    RAISE EXCEPTION 'AUTH_SESSION_INVALID' USING ERRCODE='42501';
  END IF;
END;
$session_guard$;

REVOKE ALL ON FUNCTION private.security_require_current_auth_session(uuid)
FROM PUBLIC, anon, authenticated;

-- Contrat original conservé : security_after_password_recovery
CREATE OR REPLACE FUNCTION sinjira_security_internal.security_after_password_recovery(p_device_key text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'private'
AS $function$
declare
  v_user uuid := auth.uid();
  v_current uuid;
  v_revoked integer := 0;
  v_push_disabled integer := 0;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_current_auth_session(v_user);
  perform private.security_require_aal2_if_available(v_user);

  select id into v_current
  from public.security_devices
  where user_id=v_user and device_key=p_device_key and revoked_at is null;

  update public.security_devices
     set revoked_at=now(), is_trusted=false, is_primary=false, updated_at=now()
   where user_id=v_user
     and revoked_at is null
     and (v_current is null or id<>v_current);
  get diagnostics v_revoked=row_count;

  if v_current is not null then
    update public.security_devices
       set is_trusted=false, is_primary=false, last_seen_at=now(), updated_at=now()
     where id=v_current and user_id=v_user and revoked_at is null;
  end if;

  update public.security_push_endpoints
     set enabled=false, updated_at=now()
   where user_id=v_user and enabled;
  get diagnostics v_push_disabled=row_count;

  update public.security_connection_challenges
     set status='expired'
   where user_id=v_user and status='pending';

  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(v_user,v_current,'password_recovery_completed',
    'Récupération du mot de passe terminée; les anciens appareils ont été révoqués, les notifications push désactivées et la confiance de l’appareil courant doit être réaccordée.',
    'critical');

  insert into public.user_notifications(user_id,notification_type,title,body,action_path)
  values(v_user,'security_recovery','Récupération du compte terminée',
    'Le mot de passe a été modifié. Les anciennes sessions seront fermées et les appareils doivent être vérifiés de nouveau.',
    '/compte/securite.html');

  return jsonb_build_object('ok',true,'revoked_devices',v_revoked,'disabled_push_endpoints',v_push_disabled,'current_device_id',v_current,'current_device_trusted',false);
end;
$function$

-- Contrat original conservé : security_compromise_account
CREATE OR REPLACE FUNCTION sinjira_security_internal.security_compromise_account(p_current_device_key text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'private'
AS $function$
declare
  v_user uuid := auth.uid(); v_current uuid; v_revoked integer;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_current_auth_session(v_user);
  perform private.security_require_aal2_if_available(v_user);
  select id into v_current from public.security_devices where user_id=v_user and device_key=p_current_device_key and revoked_at is null;
  update public.security_devices set revoked_at=now(),is_trusted=false,is_primary=false
    where user_id=v_user and revoked_at is null and (v_current is null or id<>v_current);
  get diagnostics v_revoked=row_count;
  update public.security_connection_challenges set status='expired' where user_id=v_user and status='pending';
  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(v_user,v_current,'account_emergency','Parcours compte compromis déclenché; les autres appareils SINJIRA ont été révoqués.','critical');
  insert into public.user_notifications(user_id,notification_type,title,body,action_path)
  values(v_user,'security_emergency','Mesures de sécurité appliquées','Les autres appareils enregistrés ont été révoqués. Vérifiez vos moyens d’authentification.','/compte/securite.html');
  return jsonb_build_object('ok',true,'revoked_devices',v_revoked,'current_device_id',v_current);
end;
$function$

-- Contrat original conservé : security_report_lost_device
CREATE OR REPLACE FUNCTION sinjira_security_internal.security_report_lost_device(p_device_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'private'
AS $function$
declare
  v_user uuid := auth.uid();
  v_row public.security_devices;
  v_push_disabled integer := 0;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_current_auth_session(v_user);
  perform private.security_require_aal2_if_available(v_user);

  select * into v_row
  from public.security_devices
  where id=p_device_id and user_id=v_user and revoked_at is null
  for update;
  if not found then raise exception 'DEVICE_NOT_FOUND'; end if;

  update public.security_devices
     set revoked_at=now(), is_trusted=false, is_primary=false, updated_at=now()
   where id=v_row.id and user_id=v_user;

  update public.security_push_endpoints
     set enabled=false, updated_at=now()
   where user_id=v_user and device_id=v_row.id and enabled;
  get diagnostics v_push_disabled=row_count;

  update public.security_connection_challenges
     set status='expired'
   where user_id=v_user and request_device_id=v_row.id and status='pending';

  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(v_user,v_row.id,'device_reported_lost',
    'Appareil déclaré perdu; confiance révoquée et notifications push désactivées pour cet appareil.',
    'critical');

  insert into public.user_notifications(user_id,notification_type,title,body,action_path)
  values(v_user,'security_lost_device','Appareil déclaré perdu',
    'L’appareil a été révoqué dans SINJIRA. Pour invalider aussi toutes les autres sessions, utilisez Déconnecter les autres appareils ou Compte compromis.',
    '/compte/securite.html');

  return jsonb_build_object('ok',true,'device_id',v_row.id,'disabled_push_endpoints',v_push_disabled,'session_revocation_required',true);
end;
$function$

-- Contrat original conservé : security_resolve_connection_challenge
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
  perform private.security_require_current_auth_session(v_user);
  if p_decision not in ('approved','denied') then raise exception 'INVALID_DECISION'; end if;
  if v_session is null then raise exception 'CURRENT_TRUSTED_DEVICE_REQUIRED' using errcode='42501'; end if;

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
$function$

-- Contrat original conservé : security_resolve_connection_challenge_mfa
CREATE OR REPLACE FUNCTION sinjira_security_internal.security_resolve_connection_challenge_mfa(p_challenge_id uuid, p_device_key text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'private', 'auth'
AS $function$
declare
  v_user uuid := auth.uid();
  v_session uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_device public.security_devices;
  v_ch public.security_connection_challenges;
  v_action text;
  v_has_other_trusted boolean := false;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_current_auth_session(v_user);
  if coalesce(auth.jwt()->>'aal','aal1') <> 'aal2' then
    raise exception 'AAL2_REQUIRED' using errcode='42501';
  end if;
  if v_session is null then raise exception 'CURRENT_DEVICE_REQUIRED' using errcode='42501'; end if;

  select * into v_device
  from public.security_devices
  where user_id=v_user
    and device_key=p_device_key
    and revoked_at is null
    and last_session_id=v_session
  for update;
  if not found then raise exception 'CURRENT_DEVICE_REQUIRED' using errcode='42501'; end if;

  select c.* into v_ch
  from public.security_connection_challenges c
  where c.id=p_challenge_id and c.user_id=v_user
  for update;
  if not found then raise exception 'CHALLENGE_NOT_FOUND'; end if;

  select e.action_name into v_action
  from public.security_connection_events e
  where e.id=v_ch.connection_event_id;
  if not found then raise exception 'CHALLENGE_EVENT_NOT_FOUND'; end if;

  if v_ch.status<>'pending' or v_ch.expires_at<=now() then
    update public.security_connection_challenges
       set status='expired'
     where id=v_ch.id and status='pending';
    raise exception 'CHALLENGE_EXPIRED';
  end if;

  if v_ch.request_device_id is distinct from v_device.id then
    raise exception 'CHALLENGE_DEVICE_MISMATCH' using errcode='42501';
  end if;

  if v_action='conscience_vault' then
    select exists(
      select 1
      from public.security_devices d
      where d.user_id=v_user
        and d.id<>v_device.id
        and d.is_trusted
        and d.revoked_at is null
    ) into v_has_other_trusted;

    if v_has_other_trusted then
      raise exception 'TRUSTED_OTHER_DEVICE_REQUIRED' using errcode='42501';
    end if;
  end if;

  update public.security_devices
     set is_trusted=true,
         is_primary=false,
         last_seen_at=greatest(last_seen_at,now())
   where id=v_device.id;

  update public.security_connection_challenges
     set status='approved',
         resolved_at=now(),
         resolved_device_id=v_device.id
   where id=v_ch.id
  returning * into v_ch;

  update public.security_connection_events
     set outcome='approved',event_type='approved'
   where id=v_ch.connection_event_id;

  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(v_user,v_device.id,'connection_approved_mfa','Connexion inhabituelle approuvée après une vérification MFA AAL2.','info');

  return to_jsonb(v_ch);
end;
$function$

-- Contrat original conservé : security_revoke_device
CREATE OR REPLACE FUNCTION sinjira_security_internal.security_revoke_device(p_device_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'auth', 'private'
AS $function$
declare
  v_user uuid := auth.uid();
  v_session uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_row public.security_devices;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_current_auth_session(v_user);
  perform private.security_require_aal2_if_available(v_user);

  update public.security_devices
     set revoked_at=now(),is_trusted=false,is_primary=false
   where id=p_device_id and user_id=v_user and revoked_at is null
   returning * into v_row;
  if not found then raise exception 'DEVICE_NOT_FOUND'; end if;

  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(v_user,v_row.id,'device_revoked','Appareil révoqué par le propriétaire du compte.','critical');

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
$function$

-- Contrat original conservé : security_set_device_trust
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
  perform private.security_require_current_auth_session(v_user);
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
$function$

-- Contrat original conservé : security_update_settings
CREATE OR REPLACE FUNCTION sinjira_security_internal.security_update_settings(p_remember_usual_region boolean DEFAULT NULL::boolean, p_sensitive_step_up boolean DEFAULT NULL::boolean, p_notify_new_device boolean DEFAULT NULL::boolean, p_notify_high_risk boolean DEFAULT NULL::boolean, p_notify_security_changes boolean DEFAULT NULL::boolean)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'public', 'private'
AS $function$
declare
  v_user uuid := auth.uid();
  v_old public.security_user_settings;
  v_row public.security_user_settings;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_current_auth_session(v_user);
  insert into public.security_user_settings(user_id) values (v_user)
  on conflict (user_id) do nothing;
  select * into v_old from public.security_user_settings where user_id=v_user for update;
  if p_sensitive_step_up is false and v_old.sensitive_step_up is true then
    perform private.security_require_aal2_if_available(v_user);
  end if;
  update public.security_user_settings set
    remember_usual_region=coalesce(p_remember_usual_region,remember_usual_region),
    sensitive_step_up=coalesce(p_sensitive_step_up,sensitive_step_up),
    notify_new_device=coalesce(p_notify_new_device,notify_new_device),
    notify_high_risk=coalesce(p_notify_high_risk,notify_high_risk),
    notify_security_changes=coalesce(p_notify_security_changes,notify_security_changes)
  where user_id=v_user returning * into v_row;
  insert into public.security_events(user_id,event_type,summary,severity)
  values(v_user,'settings_updated','Préférences du Centre de sécurité mises à jour.','info');
  return to_jsonb(v_row);
end;
$function$

-- Candidat inerte : toute exécution de test annule ses modifications.
ROLLBACK;
