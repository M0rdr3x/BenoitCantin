-- SINJIRA™ V25.0 — liaison fail-closed des challenges à la session demandeuse
-- L’HUMAIN AVANT TOUT : une approbation d’appareil est une preuve éphémère,
-- attachée à la session qui l’a demandée. Elle ne transporte jamais la confiance
-- vers une nouvelle session, même si la même device_key est réutilisée.

begin;

alter table public.security_connection_challenges
  add column if not exists request_session_id uuid references auth.sessions(id) on delete set null;

create index if not exists security_connection_challenges_request_session_idx
  on public.security_connection_challenges(user_id, request_device_id, request_session_id, created_at desc);

comment on column public.security_connection_challenges.request_session_id is
  'Session authentifiée ayant demandé le challenge. NULL reste permis pour l’historique mais ne peut jamais élever la confiance.';

create or replace function private.security_rebind_service_session(
  p_user_id uuid,
  p_device_key text,
  p_session_id uuid
)
returns boolean
language plpgsql
security definer
set search_path = pg_catalog, public, auth, private
as $$
declare
  v_device public.security_devices;
  v_session_valid boolean := false;
  v_changed boolean := false;
  v_trust_dropped boolean := false;
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED' using errcode='42501';
  end if;
  if p_user_id is null
     or p_session_id is null
     or p_device_key is null
     or char_length(p_device_key) not between 16 and 128 then
    raise exception 'INVALID_SESSION_CONTEXT' using errcode='22023';
  end if;

  select exists(
    select 1
    from auth.sessions s
    where s.id=p_session_id
      and s.user_id=p_user_id
      and (s.not_after is null or s.not_after>now())
  ) into v_session_valid;

  if not v_session_valid then
    raise exception 'USER_SESSION_INVALID' using errcode='42501';
  end if;

  select * into v_device
  from public.security_devices
  where user_id=p_user_id and device_key=p_device_key
  for update;

  if found then
    v_changed := v_device.last_session_id is distinct from p_session_id;
    v_trust_dropped := v_changed and (v_device.is_trusted or v_device.is_primary);

    if v_changed then
      update public.security_devices
         set last_session_id=p_session_id,
             is_trusted=false,
             is_primary=false
       where id=v_device.id;

      update public.security_connection_challenges
         set status='expired'
       where user_id=p_user_id
         and request_device_id=v_device.id
         and status='pending'
         and request_session_id is distinct from p_session_id;

      if v_trust_dropped then
        insert into public.security_events(user_id,device_id,event_type,summary,severity)
        values(
          p_user_id,
          v_device.id,
          'device_session_rebind_trust_reset',
          'La confiance de cet appareil a été retirée après un changement de session vérifié côté serveur.',
          'warning'
        );
      end if;
    end if;
  end if;

  return v_changed;
end;
$$;

revoke all on function private.security_rebind_service_session(uuid,text,uuid) from public, anon, authenticated;
grant execute on function private.security_rebind_service_session(uuid,text,uuid) to service_role;

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

    select d.last_session_id into v_bound_session
    from public.security_devices d
    where d.id=old.request_device_id
      and d.user_id=old.user_id
      and d.revoked_at is null;

    if not found or v_bound_session is distinct from old.request_session_id then
      raise exception 'CHALLENGE_SESSION_MISMATCH' using errcode='42501';
    end if;
  end if;

  return new;
end;
$$;

revoke all on function private.security_challenge_request_session_guard() from public, anon, authenticated;
grant execute on function private.security_challenge_request_session_guard() to service_role;

drop trigger if exists security_connection_challenge_session_guard on public.security_connection_challenges;
create trigger security_connection_challenge_session_guard
before update on public.security_connection_challenges
for each row execute function private.security_challenge_request_session_guard();

create or replace function public.service_security_evaluate_context_session(
  p_user_id uuid,
  p_device_key text,
  p_display_name text,
  p_device_type text,
  p_platform text,
  p_country_code text default null,
  p_region_code text default null,
  p_action text default 'session',
  p_session_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
declare
  v_result jsonb;
  v_device_id uuid;
  v_challenge_id uuid;
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED' using errcode='42501';
  end if;

  perform private.security_rebind_service_session(p_user_id,p_device_key,p_session_id);

  v_result := public.security_evaluate_context(
    p_user_id,
    p_device_key,
    p_display_name,
    p_device_type,
    p_platform,
    p_country_code,
    p_region_code,
    p_action
  );

  v_device_id := nullif(v_result->>'device_id','')::uuid;
  if v_device_id is null then
    raise exception 'SECURITY_DEVICE_BINDING_FAILED' using errcode='42501';
  end if;

  update public.security_devices
     set last_session_id=p_session_id
   where id=v_device_id
     and user_id=p_user_id
     and device_key=p_device_key;
  if not found then
    raise exception 'SECURITY_DEVICE_BINDING_FAILED' using errcode='42501';
  end if;

  v_challenge_id := nullif(v_result->>'challenge_id','')::uuid;
  if v_challenge_id is not null then
    update public.security_connection_challenges
       set request_session_id=p_session_id
     where id=v_challenge_id
       and user_id=p_user_id
       and request_device_id=v_device_id
       and status='pending';
    if not found then
      raise exception 'SECURITY_CHALLENGE_BINDING_FAILED' using errcode='42501';
    end if;
  elsif v_result->>'outcome'='challenge' then
    raise exception 'SECURITY_CHALLENGE_BINDING_FAILED' using errcode='42501';
  end if;

  return v_result;
end;
$$;

revoke all on function public.service_security_evaluate_context_session(uuid,text,text,text,text,text,text,text,uuid)
from public, anon, authenticated;
grant execute on function public.service_security_evaluate_context_session(uuid,text,text,text,text,text,text,text,uuid)
to service_role;

create or replace function public.service_conscience_evaluate_access_session(
  p_user_id uuid,
  p_device_key text,
  p_display_name text,
  p_device_type text,
  p_platform text,
  p_country_code text default null,
  p_region_code text default null,
  p_session_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
declare
  v_result jsonb;
  v_device public.security_devices;
  v_challenge public.security_connection_challenges;
  v_event_id uuid;
  v_has_other_trusted boolean := false;
  v_score integer := 0;
  v_now timestamptz := now();
  v_country text := case
    when p_country_code ~ '^[A-Za-z]{2}$' then upper(p_country_code)
    else null
  end;
begin
  perform private.conscience_vault_require_service_role();

  -- L'identité de session provient du JWT utilisateur déjà validé par l'Edge Function.
  -- Le wrapper générique vérifie cette session dans auth.sessions avant tout calcul de risque.
  v_result := public.service_security_evaluate_context_session(
    p_user_id,
    p_device_key,
    p_display_name,
    p_device_type,
    p_platform,
    v_country,
    left(p_region_code,80),
    'conscience_vault',
    p_session_id
  );

  if v_result->>'risk_model_version' is distinct from 'v25.0'
     or coalesce((v_result->>'mandatory_step_up')::boolean,false) is not true
     or coalesce((v_result->>'requires_step_up')::boolean,false) is not true then
    raise exception 'VAULT_SECURITY_DECISION_INVALID' using errcode='42501';
  end if;

  v_score := coalesce((v_result->>'risk_score')::integer,0);

  -- Les décisions déjà bloquées/challengées par le moteur V25 restent prioritaires.
  if v_result->>'outcome' in ('block','challenge') then
    return v_result || jsonb_build_object('trusted_device_confirmation','risk_engine');
  end if;
  if v_result->>'outcome' not in ('allow','approved') then
    raise exception 'VAULT_SECURITY_DECISION_INVALID' using errcode='42501';
  end if;

  select * into v_device
  from public.security_devices
  where id = nullif(v_result->>'device_id','')::uuid
    and user_id = p_user_id
    and revoked_at is null
    and last_session_id = p_session_id;
  if not found then
    raise exception 'VAULT_DEVICE_INVALID' using errcode='42501';
  end if;

  select exists(
    select 1
    from public.security_devices d
    where d.user_id=p_user_id
      and d.id<>v_device.id
      and d.is_trusted
      and d.revoked_at is null
  ) into v_has_other_trusted;

  if not v_has_other_trusted or coalesce(v_device.is_trusted,false) then
    return v_result || jsonb_build_object(
      'trusted_device_confirmation',
      case when coalesce(v_device.is_trusted,false) then 'trusted_device' else 'not_required' end
    );
  end if;

  -- Une approbation n'est réutilisable que dans la session demandeuse exacte.
  select c.* into v_challenge
  from public.security_connection_challenges c
  join public.security_connection_events e
    on e.id=c.connection_event_id
   and e.user_id=p_user_id
   and e.action_name='conscience_vault'
  where c.user_id=p_user_id
    and c.request_device_id=v_device.id
    and c.request_session_id=p_session_id
  order by c.created_at desc
  limit 1;

  if found then
    if v_challenge.status='approved'
       and coalesce(v_challenge.resolved_at,v_challenge.created_at) > v_now-interval '30 minutes'
       and exists(
         select 1
         from public.security_devices resolver
         where resolver.id=v_challenge.resolved_device_id
           and resolver.user_id=p_user_id
           and resolver.id<>v_device.id
           and resolver.is_trusted
           and resolver.revoked_at is null
       ) then
      return v_result || jsonb_build_object(
        'trusted_device_confirmation','approved_recently',
        'challenge_id',v_challenge.id
      );
    end if;

    if v_challenge.status='denied'
       and coalesce(v_challenge.resolved_at,v_challenge.created_at) > v_now-interval '30 minutes' then
      return v_result || jsonb_build_object(
        'outcome','block',
        'risk_score',greatest(v_score,75),
        'risk_band','critical',
        'risk_reasons',coalesce(v_result->'risk_reasons','[]'::jsonb) || jsonb_build_array('recent_trusted_device_denial'),
        'challenge_id',v_challenge.id,
        'display_code',null,
        'trusted_device_confirmation','denied_recently'
      );
    end if;

    if v_challenge.status='pending' and v_challenge.expires_at>v_now then
      return v_result || jsonb_build_object(
        'outcome','challenge',
        'risk_score',greatest(v_score,50),
        'risk_band','high',
        'risk_reasons',coalesce(v_result->'risk_reasons','[]'::jsonb) || jsonb_build_array('trusted_device_confirmation_required'),
        'challenge_id',v_challenge.id,
        'display_code',v_challenge.display_code,
        'other_trusted_device_required',true,
        'trusted_device_confirmation','pending'
      );
    end if;

    if v_challenge.status='pending' and v_challenge.expires_at<=v_now then
      update public.security_connection_challenges
         set status='expired'
       where id=v_challenge.id and status='pending';
    end if;
  end if;

  insert into public.security_connection_events(
    user_id,device_id,event_type,country_code,region_code,client_type,platform,
    action_name,risk_score,risk_reasons,outcome,risk_model_version
  ) values(
    p_user_id,
    v_device.id,
    'challenge',
    v_country,
    left(p_region_code,80),
    left(coalesce(p_device_type,''),80),
    left(coalesce(p_platform,''),120),
    'conscience_vault',
    greatest(v_score,50),
    array['trusted_device_confirmation_required']::text[],
    'challenge',
    'v25.0'
  ) returning id into v_event_id;

  insert into public.security_connection_challenges(
    user_id,connection_event_id,request_device_id,request_session_id,display_code
  ) values(
    p_user_id,v_event_id,v_device.id,p_session_id,10+floor(random()*90)::int
  ) returning * into v_challenge;

  insert into public.user_notifications(
    user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path
  ) values(
    p_user_id,
    'security_connection',
    'Connexion à confirmer',
    'Une connexion inhabituelle demande une vérification renforcée depuis un appareil fiable.',
    'security_connection_challenge',
    v_challenge.id,
    '/compte/securite.html'
  );

  return v_result || jsonb_build_object(
    'outcome','challenge',
    'risk_score',greatest(v_score,50),
    'risk_band','high',
    'risk_reasons',coalesce(v_result->'risk_reasons','[]'::jsonb) || jsonb_build_array('trusted_device_confirmation_required'),
    'challenge_id',v_challenge.id,
    'display_code',v_challenge.display_code,
    'other_trusted_device_required',true,
    'trusted_device_confirmation','reissued'
  );
end;
$$;

revoke all on function public.service_conscience_evaluate_access_session(uuid,text,text,text,text,text,text,uuid)
from public, anon, authenticated;
grant execute on function public.service_conscience_evaluate_access_session(uuid,text,text,text,text,text,text,uuid)
to service_role;

-- L'ancien service sans identité de session est retiré de la surface exécutable.
revoke execute on function public.service_conscience_evaluate_access(uuid,text,text,text,text,text,text)
from service_role;

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
          and c.request_session_id=v_session
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

revoke all on function sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean) from public, anon;
grant execute on function sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean) to authenticated, service_role;

comment on function public.service_security_evaluate_context_session(uuid,text,text,text,text,text,text,text,uuid) is
  'Service-only. Vérifie auth.sessions, réassocie l’appareil sans transporter sa confiance et lie tout challenge à la session demandeuse.';
comment on function public.service_conscience_evaluate_access_session(uuid,text,text,text,text,text,text,uuid) is
  'Service-only. Accès Registre V25 avec challenge strictement lié à la session JWT utilisateur vérifiée par l’Edge Function.';
comment on function sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean) is
  'V25: toute élévation de confiance exige AAL2 et, lorsqu’un autre appareil fiable existe, un challenge récent approuvé pour la session demandeuse exacte.';

commit;
