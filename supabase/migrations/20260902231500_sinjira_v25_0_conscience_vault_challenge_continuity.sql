-- SINJIRA™ V25.0 — continuité du challenge pour le Registre personnel
-- Un appareil devenu « connu » après un premier essai ne doit jamais contourner
-- une confirmation encore pending, expirée ou récemment refusée.

begin;

create or replace function public.service_conscience_evaluate_access(
  p_user_id uuid,
  p_device_key text,
  p_display_name text,
  p_device_type text,
  p_platform text,
  p_country_code text default null,
  p_region_code text default null
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

  -- Le périmètre est fixé côté serveur. Le client ne peut jamais choisir un scope
  -- moins sensible puis réutiliser cette décision pour le Registre personnel.
  v_result := public.security_evaluate_context(
    p_user_id,
    p_device_key,
    p_display_name,
    p_device_type,
    p_platform,
    v_country,
    left(p_region_code,80),
    'conscience_vault'
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
    and revoked_at is null;
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

  -- Premier appareil du compte ou appareil déjà fiable : aucune confirmation
  -- additionnelle n'est imposée au-delà d'AAL2 et du moteur de risque.
  if not v_has_other_trusted or coalesce(v_device.is_trusted,false) then
    return v_result || jsonb_build_object(
      'trusted_device_confirmation',
      case when coalesce(v_device.is_trusted,false) then 'trusted_device' else 'not_required' end
    );
  end if;

  select * into v_challenge
  from public.security_connection_challenges c
  where c.user_id=p_user_id
    and c.request_device_id=v_device.id
  order by c.created_at desc
  limit 1;

  if found then
    -- Une approbation depuis un appareil fiable confirme ce device tant qu'il n'est
    -- pas révoqué; elle ne le transforme pas silencieusement en appareil principal.
    if v_challenge.status='approved' then
      return v_result || jsonb_build_object(
        'trusted_device_confirmation','approved',
        'challenge_id',v_challenge.id
      );
    end if;

    -- Un refus explicite ne doit pas générer immédiatement une nouvelle demande :
    -- fenêtre anti-fatigue de 30 minutes.
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

    -- Réutilise le même challenge pendant sa fenêtre; un simple retry ne peut
    -- donc plus convertir un challenge en allow.
    if v_challenge.status='pending' and v_challenge.expires_at>v_now then
      return v_result || jsonb_build_object(
        'outcome','challenge',
        'risk_score',greatest(v_score,50),
        'risk_band','high',
        'risk_reasons',coalesce(v_result->'risk_reasons','[]'::jsonb) || jsonb_build_array('trusted_device_confirmation_required'),
        'challenge_id',v_challenge.id,
        'display_code',v_challenge.display_code,
        'mfa_or_other_trusted_device_required',true,
        'trusted_device_confirmation','pending'
      );
    end if;

    if v_challenge.status='pending' and v_challenge.expires_at<=v_now then
      update public.security_connection_challenges
         set status='expired'
       where id=v_challenge.id and status='pending';
    end if;
  end if;

  -- Aucun challenge approuvé utilisable : réémet une confirmation contrôlée.
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
    user_id,connection_event_id,request_device_id,display_code
  ) values(
    p_user_id,v_event_id,v_device.id,10+floor(random()*90)::int
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
    'mfa_or_other_trusted_device_required',true,
    'trusted_device_confirmation','reissued'
  );
end;
$$;

revoke all on function public.service_conscience_evaluate_access(uuid,text,text,text,text,text,text)
from public, anon, authenticated;
grant execute on function public.service_conscience_evaluate_access(uuid,text,text,text,text,text,text)
to service_role;

comment on function public.service_conscience_evaluate_access(uuid,text,text,text,text,text,text) is
  'Serveur seulement. Enveloppe security_evaluate_context pour conscience_vault et maintient la confirmation appareil fiable entre les retries, avec anti-fatigue après refus.';

commit;