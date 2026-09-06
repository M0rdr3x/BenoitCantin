-- SINJIRA™ V25.0 — durcissement de la continuité des challenges appareil
-- L’HUMAIN AVANT TOUT : une clé d’appareil connue ne suffit jamais à approuver
-- une demande sensible. L’approbateur doit être l’appareil fiable de la session
-- courante et, pour le Coffre, un autre appareil fiable est obligatoire lorsqu’il existe.

begin;

create or replace function sinjira_security_internal.security_resolve_connection_challenge(
  p_challenge_id uuid,
  p_device_key text,
  p_decision text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
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

  perform private.security_require_aal2_if_available(v_user);

  -- Une clé copiée depuis un autre appareil ne prouve pas que cet appareil est celui
  -- de la session courante. Le last_session_id lie l’approbation au contexte authentifié.
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
$$;

create or replace function sinjira_security_internal.security_resolve_connection_challenge_mfa(
  p_challenge_id uuid,
  p_device_key text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
declare
  v_user uuid := auth.uid();
  v_session uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_device public.security_devices;
  v_ch public.security_connection_challenges;
  v_action text;
  v_has_other_trusted boolean := false;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  if coalesce(auth.jwt()->>'aal','aal1') <> 'aal2' then
    raise exception 'AAL2_REQUIRED' using errcode='42501';
  end if;
  if v_session is null then raise exception 'CURRENT_DEVICE_REQUIRED' using errcode='42501'; end if;

  -- Même avec AAL2, la clé fournie doit désigner l’appareil de la session courante.
  select * into v_device
  from public.security_devices
  where user_id=v_user
    and device_key=p_device_key
    and revoked_at is null
    and last_session_id=v_session
  for update;
  if not found then raise exception 'CURRENT_DEVICE_REQUIRED' using errcode='42501'; end if;

  select c.*, e.action_name into v_ch, v_action
  from public.security_connection_challenges c
  join public.security_connection_events e on e.id=c.connection_event_id
  where c.id=p_challenge_id and c.user_id=v_user
  for update of c;
  if not found then raise exception 'CHALLENGE_NOT_FOUND'; end if;

  if v_ch.status<>'pending' or v_ch.expires_at<=now() then
    update public.security_connection_challenges
       set status='expired'
     where id=v_ch.id and status='pending';
    raise exception 'CHALLENGE_EXPIRED';
  end if;

  if v_ch.request_device_id is distinct from v_device.id then
    raise exception 'CHALLENGE_DEVICE_MISMATCH' using errcode='42501';
  end if;

  -- Le Coffre possède une règle plus forte que le challenge générique : dès qu’un
  -- autre appareil fiable existe, AAL2 sur l’appareil demandeur ne peut pas remplacer
  -- l’approbation de cet autre appareil. Cela ferme l’ancienne auto-approbation MFA.
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
$$;

-- Reprend le contrat V25 de confiance appareil et verrouille explicitement le fait
-- qu’une approbation fraîche doit provenir d’un autre appareil que la cible.
create or replace function sinjira_security_internal.security_set_device_trust(
  p_device_id uuid,
  p_trusted boolean,
  p_primary boolean default false
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, auth, private
as $$
declare
  v_user uuid := auth.uid();
  v_session uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_row public.security_devices;
  v_has_other_trusted boolean := false;
  v_recent_approved boolean := false;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
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
$$;

-- Les implémentations privilégiées restent hors du schéma API public. Les wrappers
-- public SECURITY INVOKER créés en V24.5.10 demeurent l’unique surface PostgREST.
revoke all on function sinjira_security_internal.security_resolve_connection_challenge(uuid,text,text) from public, anon;
revoke all on function sinjira_security_internal.security_resolve_connection_challenge_mfa(uuid,text) from public, anon;
revoke all on function sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean) from public, anon;
grant execute on function sinjira_security_internal.security_resolve_connection_challenge(uuid,text,text) to authenticated, service_role;
grant execute on function sinjira_security_internal.security_resolve_connection_challenge_mfa(uuid,text) to authenticated, service_role;
grant execute on function sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean) to authenticated, service_role;

comment on function sinjira_security_internal.security_resolve_connection_challenge(uuid,text,text) is
  'V25: résolution depuis un autre appareil fiable, non révoqué et lié à la session authentifiée courante.';
comment on function sinjira_security_internal.security_resolve_connection_challenge_mfa(uuid,text) is
  'V25: MFA AAL2 reste disponible pour les challenges génériques, mais ne peut auto-approuver un challenge conscience_vault lorsqu’un autre appareil fiable existe.';
comment on function sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean) is
  'V25: augmenter la confiance exige AAL2, appareil cible courant et, lorsqu’une confiance existe déjà, une approbation fraîche provenant explicitement d’un autre appareil fiable.';

commit;
