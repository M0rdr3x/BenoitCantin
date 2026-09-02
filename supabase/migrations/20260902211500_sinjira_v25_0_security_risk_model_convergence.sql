-- SINJIRA™ V25.0 — convergence du moteur de risque de connexion
-- Principe : protéger sans surveiller. Le moteur reste déterministe, explicable et serveur.
-- Cette migration conserve les tables/RPC V24.4.98 existantes et remplace uniquement
-- le calcul de risque contextuel par le modèle V25 verrouillé.

begin;

-- Les événements historiques gardent leur provenance. Les autres producteurs éventuels
-- restent identifiés comme legacy; le moteur V25 écrit explicitement v25.0.
alter table public.security_connection_events
  add column if not exists risk_model_version text;

update public.security_connection_events
   set risk_model_version = 'v24.4.98'
 where risk_model_version is null;

alter table public.security_connection_events
  alter column risk_model_version set default 'legacy',
  alter column risk_model_version set not null;

comment on column public.security_connection_events.risk_model_version is
  'Version du modèle déterministe ayant produit le score. Aucun contenu intime n’est journalisé.';

-- Modèle V25 déterministe et testable.
-- Poids verrouillés :
--   +30 appareil inconnu
--   +20 région inattendue hors Mode Voyage
--   +30 voyage impossible
--   +20 plusieurs échecs récents
--   +25 récupération récente
--   +25 changement récent de facteur d’authentification
--   +20 action/ressource sensible
--   -20 appareil principal
--   -15 appareil fiable
--   -15 Mode Voyage correspondant
-- Score borné à 0..100.
create or replace function private.security_risk_score_v25(
  p_unknown_device boolean,
  p_unexpected_region boolean,
  p_impossible_travel boolean,
  p_recent_failures boolean,
  p_recent_recovery boolean,
  p_auth_factor_change boolean,
  p_sensitive_action boolean,
  p_primary_device boolean,
  p_trusted_device boolean,
  p_travel_match boolean
)
returns jsonb
language plpgsql
immutable
set search_path = pg_catalog, private
as $$
declare
  v_score integer := 0;
  v_reasons text[] := '{}'::text[];
  v_band text;
begin
  if coalesce(p_unknown_device,false) then
    v_score := v_score + 30;
    v_reasons := array_append(v_reasons,'unknown_device');
  end if;
  if coalesce(p_unexpected_region,false) then
    v_score := v_score + 20;
    v_reasons := array_append(v_reasons,'unexpected_region');
  end if;
  if coalesce(p_impossible_travel,false) then
    v_score := v_score + 30;
    v_reasons := array_append(v_reasons,'impossible_travel');
  end if;
  if coalesce(p_recent_failures,false) then
    v_score := v_score + 20;
    v_reasons := array_append(v_reasons,'recent_failures');
  end if;
  if coalesce(p_recent_recovery,false) then
    v_score := v_score + 25;
    v_reasons := array_append(v_reasons,'recent_recovery');
  end if;
  if coalesce(p_auth_factor_change,false) then
    v_score := v_score + 25;
    v_reasons := array_append(v_reasons,'auth_factor_change');
  end if;
  if coalesce(p_sensitive_action,false) then
    v_score := v_score + 20;
    v_reasons := array_append(v_reasons,'sensitive_action');
  end if;
  if coalesce(p_primary_device,false) then
    v_score := v_score - 20;
    v_reasons := array_append(v_reasons,'primary_device');
  end if;
  if coalesce(p_trusted_device,false) then
    v_score := v_score - 15;
    v_reasons := array_append(v_reasons,'trusted_device');
  end if;
  if coalesce(p_travel_match,false) then
    v_score := v_score - 15;
    v_reasons := array_append(v_reasons,'travel_match');
  end if;

  v_score := greatest(0,least(100,v_score));
  v_band := case
    when v_score <= 24 then 'low'
    when v_score <= 49 then 'medium'
    when v_score <= 74 then 'high'
    else 'critical'
  end;

  return jsonb_build_object(
    'score',v_score,
    'band',v_band,
    'reasons',to_jsonb(v_reasons),
    'model_version','v25.0'
  );
end;
$$;

revoke all on function private.security_risk_score_v25(boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean)
from public, anon, authenticated;
grant execute on function private.security_risk_score_v25(boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean)
to service_role;

-- Signature publique conservée pour ne pas casser l’Edge Function / les appels serveur existants.
create or replace function public.security_evaluate_context(
  p_user_id uuid,
  p_device_key text,
  p_display_name text,
  p_device_type text,
  p_platform text,
  p_country_code text default null,
  p_region_code text default null,
  p_action text default 'session'
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_device public.security_devices;
  v_previous public.security_connection_events;
  v_settings public.security_user_settings;
  v_event public.security_connection_events;
  v_challenge public.security_connection_challenges;

  v_country text := case when p_country_code ~ '^[A-Za-z]{2}$' then upper(p_country_code) else null end;
  v_action text := left(coalesce(nullif(trim(p_action),''),'session'),80);

  v_unknown_device boolean := false;
  v_had_trusted_device boolean := false;
  v_previous_found boolean := false;
  v_travel_match boolean := false;
  v_unexpected_region boolean := false;
  v_impossible_travel boolean := false;
  v_recent_failures boolean := false;
  v_recent_recovery boolean := false;
  v_auth_factor_change boolean := false;
  v_sensitive boolean := false;
  v_mandatory_step_up boolean := false;
  v_force_challenge boolean := false;
  v_notify boolean := false;

  v_risk jsonb;
  v_score integer := 0;
  v_band text := 'low';
  v_reasons text[] := '{}'::text[];
  v_outcome text := 'allow';
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED' using errcode='42501';
  end if;
  if p_user_id is null or p_device_key is null or char_length(p_device_key) not between 16 and 128 then
    raise exception 'INVALID_CONTEXT';
  end if;

  -- `registry` est conservé uniquement pour compatibilité avec les appels V24 existants.
  -- Les nouveaux périmètres du Registre personnel utilisent des noms explicites afin de
  -- ne pas le confondre avec le Registre narratif SINJIRA.
  v_sensitive := v_action in (
    'registry','ai_private','recovery','passkeys','posthumous','security_change',
    'conscience_vault','personal_registry','vault'
  );

  -- Ces zones ne peuvent jamais perdre le step-up à cause d’un appareil fiable,
  -- d’un Mode Voyage ou d’une préférence utilisateur.
  v_mandatory_step_up := v_action in (
    'ai_private','recovery','passkeys','posthumous','security_change',
    'conscience_vault','personal_registry','vault'
  );

  insert into public.security_user_settings(user_id)
  values(p_user_id)
  on conflict(user_id) do nothing;
  select * into v_settings
  from public.security_user_settings
  where user_id=p_user_id;

  select exists(
    select 1
    from public.security_devices
    where user_id=p_user_id and is_trusted and revoked_at is null
  ) into v_had_trusted_device;

  select * into v_device
  from public.security_devices
  where user_id=p_user_id and device_key=p_device_key;

  v_unknown_device := not found;

  if v_unknown_device then
    insert into public.security_devices(
      user_id,device_key,display_name,device_type,platform,last_country_code,last_region_code
    ) values(
      p_user_id,
      p_device_key,
      left(coalesce(nullif(trim(p_display_name),''),'Appareil SINJIRA'),120),
      case when p_device_type in ('browser','ios','android','tablet','other') then p_device_type else 'other' end,
      left(coalesce(p_platform,''),120),
      v_country,
      left(p_region_code,80)
    ) returning * into v_device;

    -- Garde existante conservée : si un appareil fiable existe déjà, un nouvel appareil
    -- doit être confirmé même si son score reste dans la bande moyenne.
    if v_had_trusted_device then
      v_force_challenge := true;
    end if;
  else
    update public.security_devices
       set last_seen_at=now(),
           last_country_code=coalesce(v_country,last_country_code),
           last_region_code=coalesce(left(p_region_code,80),last_region_code),
           platform=left(coalesce(p_platform,platform),120)
     where id=v_device.id
    returning * into v_device;
  end if;

  -- Appareil explicitement révoqué : interdiction dure indépendante des réductions de risque.
  if v_device.revoked_at is not null then
    v_score := 100;
    v_band := 'critical';
    v_reasons := array['revoked_device']::text[];
    v_outcome := 'block';
  else
    if v_country is not null then
      select * into v_previous
      from public.security_connection_events
      where user_id=p_user_id
        and country_code is not null
        and outcome in ('allow','approved')
      order by occurred_at desc
      limit 1;
      v_previous_found := found;

      select exists(
        select 1
        from public.security_travel_plans t,
             unnest(t.destinations) d
        where t.user_id=p_user_id
          and t.status='active'
          and now() between t.starts_at and t.ends_at
          and upper(trim(d))=v_country
      ) into v_travel_match;

      if v_previous_found then
        v_unexpected_region := v_previous.country_code <> v_country and not v_travel_match;
        v_impossible_travel := v_previous.country_code <> v_country
          and v_previous.occurred_at > now()-interval '2 hours';
      end if;
    end if;

    -- Un voyage planifié réduit le score mais ne neutralise jamais à lui seul
    -- un changement géographique physiquement impossible.
    if v_impossible_travel then
      v_force_challenge := true;
    end if;

    select count(*) >= 3 into v_recent_failures
    from public.security_connection_events
    where user_id=p_user_id
      and occurred_at >= now()-interval '30 minutes'
      and outcome in ('denied','block');

    select exists(
      select 1
      from public.security_events
      where user_id=p_user_id
        and event_type='password_recovery_completed'
        and created_at >= now()-interval '24 hours'
    ) into v_recent_recovery;

    -- Le dépôt journalise actuellement la récupération et les validations MFA, mais pas
    -- encore chaque mutation de facteur TOTP. Cette liste rend le signal actif dès qu’un
    -- producteur serveur écrit l’un de ces événements, sans inventer de donnée côté client.
    select exists(
      select 1
      from public.security_events
      where user_id=p_user_id
        and event_type in (
          'auth_factor_changed','mfa_factor_changed','mfa_factor_added','mfa_factor_removed',
          'passkey_added','passkey_removed','passkey_changed','recovery_factor_changed'
        )
        and created_at >= now()-interval '24 hours'
    ) into v_auth_factor_change;

    v_risk := private.security_risk_score_v25(
      v_unknown_device,
      v_unexpected_region,
      v_impossible_travel,
      v_recent_failures,
      v_recent_recovery,
      v_auth_factor_change,
      v_sensitive,
      coalesce(v_device.is_primary,false),
      coalesce(v_device.is_trusted,false),
      v_travel_match
    );

    v_score := (v_risk->>'score')::integer;
    v_band := v_risk->>'band';
    select coalesce(array_agg(value), '{}'::text[])
      into v_reasons
    from jsonb_array_elements_text(v_risk->'reasons');

    if v_score >= 75 and v_sensitive then
      v_outcome := 'block';
    elsif v_score >= 50 or v_force_challenge then
      v_outcome := 'challenge';
    else
      v_outcome := 'allow';
    end if;
  end if;

  insert into public.security_connection_events(
    user_id,device_id,event_type,country_code,region_code,client_type,platform,
    action_name,risk_score,risk_reasons,outcome,risk_model_version
  ) values(
    p_user_id,
    v_device.id,
    case when v_sensitive then 'sensitive_access' else 'login_context' end,
    v_country,
    left(p_region_code,80),
    left(coalesce(p_device_type,''),80),
    left(coalesce(p_platform,''),120),
    v_action,
    v_score,
    v_reasons,
    v_outcome,
    'v25.0'
  ) returning * into v_event;

  if v_outcome='challenge' then
    insert into public.security_connection_challenges(
      user_id,connection_event_id,request_device_id,display_code
    ) values(
      p_user_id,v_event.id,v_device.id,10+floor(random()*90)::int
    ) returning * into v_challenge;
  end if;

  v_notify :=
    (v_unknown_device and coalesce(v_settings.notify_new_device,true))
    or (v_score >= 25 and coalesce(v_settings.notify_high_risk,true))
    or v_outcome in ('challenge','block');

  if v_notify then
    insert into public.user_notifications(
      user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path
    ) values(
      p_user_id,
      'security_connection',
      case
        when v_outcome='block' then 'Connexion ou action bloquée'
        when v_outcome='challenge' then 'Connexion à confirmer'
        else 'Connexion inhabituelle détectée'
      end,
      case
        when v_outcome='block' then 'SINJIRA a bloqué une connexion ou une action présentant un risque critique. Vérifiez votre Centre de sécurité.'
        when v_outcome='challenge' then 'Une connexion inhabituelle demande une vérification renforcée.'
        else 'Une connexion inhabituelle a été détectée. Vérifiez-la dans votre Centre de sécurité si nécessaire.'
      end,
      'security_connection_event',
      v_event.id,
      '/compte/securite.html'
    );
  end if;

  return jsonb_build_object(
    'outcome',v_outcome,
    'risk_score',v_score,
    'risk_band',v_band,
    'risk_reasons',to_jsonb(v_reasons),
    'risk_model_version','v25.0',
    'device_id',v_device.id,
    'new_device',v_unknown_device,
    'travel_match',v_travel_match,
    'requires_step_up',(
      v_mandatory_step_up
      or (v_sensitive and coalesce(v_settings.sensitive_step_up,true))
      or v_score >= 50
    ),
    'mandatory_step_up',v_mandatory_step_up,
    'challenge_id',v_challenge.id,
    'display_code',v_challenge.display_code,
    'mfa_or_other_trusted_device_required',(v_outcome='challenge')
  );
end;
$$;

revoke all on function public.security_evaluate_context(uuid,text,text,text,text,text,text,text)
from public, anon, authenticated;
grant execute on function public.security_evaluate_context(uuid,text,text,text,text,text,text,text)
to service_role;

commit;
