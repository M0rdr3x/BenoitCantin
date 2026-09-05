-- SINJIRA V25 — Fondation privée « Mon IA »
-- L'humain avant tout : aucune mémoire conversationnelle, aucun profil psychologique caché,
-- aucun accès automatique au Registre personnel ou à Histoire de vie.

begin;

create table if not exists private.personal_ai_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  enabled boolean not null default false,
  display_name text,
  language_code text not null default 'fr-CA',
  runtime_status text not null default 'not_configured'
    check (runtime_status = 'not_configured'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (display_name is null or char_length(display_name) <= 80),
  check (char_length(language_code) between 2 and 16)
);

comment on table private.personal_ai_settings is
  'Réglages privés de Mon IA. V25 ne stocke aucune conversation ni mémoire IA et ne configure aucun fournisseur de modèle.';

create table if not exists private.personal_ai_source_permissions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  source_type text not null check (source_type in ('life_story','employment')),
  granted_at timestamptz not null default now(),
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, source_type)
);

comment on table private.personal_ai_source_permissions is
  'Consentements préparatoires explicites. Aucun RPC V25 ne lit les données Histoire de vie ou Emploi pour l IA; le Registre personnel est volontairement absent des sources autorisables.';

create table if not exists private.personal_ai_audit (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  action_name text not null check (action_name in ('settings_updated','source_granted','source_revoked','data_deleted')),
  source_type text,
  created_at timestamptz not null default now(),
  check (source_type is null or source_type in ('life_story','employment'))
);

comment on table private.personal_ai_audit is
  'Audit minimal Mon IA : action et type de source seulement. Aucun prompt, réponse, résumé, contenu intime, IP brute, GPS ou identifiant publicitaire.';

revoke all on table private.personal_ai_settings from public, anon, authenticated, service_role;
revoke all on table private.personal_ai_source_permissions from public, anon, authenticated, service_role;
revoke all on table private.personal_ai_audit from public, anon, authenticated, service_role;
revoke all on sequence private.personal_ai_audit_id_seq from public, anon, authenticated, service_role;

create or replace function private.personal_ai_require_service_role()
returns void
language plpgsql
stable
set search_path = pg_catalog, auth
as $$
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED' using errcode='42501';
  end if;
end;
$$;

revoke all on function private.personal_ai_require_service_role() from public, anon, authenticated;
grant execute on function private.personal_ai_require_service_role() to service_role;

create or replace function private.personal_ai_assert_access(
  p_aal text,
  p_risk_score integer,
  p_risk_outcome text,
  p_risk_model_version text
)
returns void
language plpgsql
stable
set search_path = pg_catalog
as $$
begin
  if p_aal is distinct from 'aal2' then
    raise exception 'PERSONAL_AI_AAL2_REQUIRED' using errcode='42501';
  end if;
  if p_risk_model_version is distinct from 'v25.0'
     or p_risk_score is null
     or p_risk_score < 0
     or p_risk_score > 100
     or p_risk_score >= 75
     or p_risk_outcome not in ('allow','approved') then
    raise exception 'PERSONAL_AI_RISK_REFUSED' using errcode='42501';
  end if;
end;
$$;

revoke all on function private.personal_ai_assert_access(text,integer,text,text) from public, anon, authenticated;
grant execute on function private.personal_ai_assert_access(text,integer,text,text) to service_role;

-- Enveloppe serveur : le client ne choisit jamais un périmètre moins sensible que ai_private.
-- Elle maintient aussi un challenge en attente entre les retries afin qu'un appareil
-- nouvellement « connu » ne contourne pas la confirmation d'un autre appareil fiable.
create or replace function public.service_personal_ai_evaluate_access(
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
  v_country text := case when p_country_code ~ '^[A-Za-z]{2}$' then upper(p_country_code) else null end;
begin
  perform private.personal_ai_require_service_role();

  v_result := public.security_evaluate_context(
    p_user_id,p_device_key,p_display_name,p_device_type,p_platform,
    v_country,left(p_region_code,80),'ai_private'
  );

  if v_result->>'risk_model_version' is distinct from 'v25.0'
     or coalesce((v_result->>'mandatory_step_up')::boolean,false) is not true
     or coalesce((v_result->>'requires_step_up')::boolean,false) is not true then
    raise exception 'PERSONAL_AI_SECURITY_DECISION_INVALID' using errcode='42501';
  end if;

  v_score := coalesce((v_result->>'risk_score')::integer,0);
  if v_result->>'outcome' in ('block','challenge') then
    return v_result || jsonb_build_object('trusted_device_confirmation','risk_engine');
  end if;
  if v_result->>'outcome' not in ('allow','approved') then
    raise exception 'PERSONAL_AI_SECURITY_DECISION_INVALID' using errcode='42501';
  end if;

  select * into v_device
  from public.security_devices
  where id=nullif(v_result->>'device_id','')::uuid
    and user_id=p_user_id
    and revoked_at is null;
  if not found then
    raise exception 'PERSONAL_AI_DEVICE_INVALID' using errcode='42501';
  end if;

  select exists(
    select 1 from public.security_devices d
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

  select c.* into v_challenge
  from public.security_connection_challenges c
  join public.security_connection_events e
    on e.id=c.connection_event_id
   and e.user_id=p_user_id
   and e.action_name='ai_private'
  where c.user_id=p_user_id
    and c.request_device_id=v_device.id
  order by c.created_at desc
  limit 1;

  if found then
    if v_challenge.status='approved'
       and coalesce(v_challenge.resolved_at,v_challenge.created_at) > v_now-interval '30 minutes'
       and exists(
         select 1 from public.security_devices resolver
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
    p_user_id,v_device.id,'challenge',v_country,left(p_region_code,80),
    left(coalesce(p_device_type,''),80),left(coalesce(p_platform,''),120),
    'ai_private',greatest(v_score,50),array['trusted_device_confirmation_required']::text[],
    'challenge','v25.0'
  ) returning id into v_event_id;

  insert into public.security_connection_challenges(
    user_id,connection_event_id,request_device_id,display_code
  ) values(p_user_id,v_event_id,v_device.id,10+floor(random()*90)::int)
  returning * into v_challenge;

  insert into public.user_notifications(
    user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path
  ) values(
    p_user_id,'security_connection','Connexion à confirmer',
    'Un accès à Mon IA demande une vérification renforcée depuis un appareil fiable.',
    'security_connection_challenge',v_challenge.id,'/compte/securite.html'
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

revoke all on function public.service_personal_ai_evaluate_access(uuid,text,text,text,text,text,text)
from public, anon, authenticated;
grant execute on function public.service_personal_ai_evaluate_access(uuid,text,text,text,text,text,text)
to service_role;

create or replace function public.service_personal_ai_get_state(
  p_user_id uuid,
  p_aal text,
  p_risk_score integer,
  p_risk_outcome text,
  p_risk_model_version text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
declare
  v_settings private.personal_ai_settings;
  v_permissions jsonb;
begin
  perform private.personal_ai_require_service_role();
  perform private.personal_ai_assert_access(p_aal,p_risk_score,p_risk_outcome,p_risk_model_version);

  insert into private.personal_ai_settings(user_id) values(p_user_id)
  on conflict(user_id) do nothing;
  select * into v_settings from private.personal_ai_settings where user_id=p_user_id;

  select coalesce(jsonb_agg(jsonb_build_object(
    'source_type',source_type,
    'granted',revoked_at is null,
    'granted_at',granted_at,
    'revoked_at',revoked_at
  ) order by source_type),'[]'::jsonb)
  into v_permissions
  from private.personal_ai_source_permissions
  where user_id=p_user_id;

  return jsonb_build_object(
    'settings',jsonb_build_object(
      'enabled',v_settings.enabled,
      'display_name',v_settings.display_name,
      'language_code',v_settings.language_code,
      'runtime_status',v_settings.runtime_status
    ),
    'source_permissions',v_permissions,
    'runtime',jsonb_build_object(
      'conversation_enabled',false,
      'memory_enabled',false,
      'source_retrieval_enabled',false,
      'provider_configured',false
    )
  );
end;
$$;

create or replace function public.service_personal_ai_update_settings(
  p_user_id uuid,
  p_enabled boolean,
  p_display_name text,
  p_language_code text,
  p_aal text,
  p_risk_score integer,
  p_risk_outcome text,
  p_risk_model_version text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
declare
  v_row private.personal_ai_settings;
  v_language text := left(coalesce(nullif(trim(p_language_code),''),'fr-CA'),16);
begin
  perform private.personal_ai_require_service_role();
  perform private.personal_ai_assert_access(p_aal,p_risk_score,p_risk_outcome,p_risk_model_version);
  if char_length(v_language)<2 then raise exception 'PERSONAL_AI_LANGUAGE_INVALID'; end if;

  insert into private.personal_ai_settings(user_id,enabled,display_name,language_code,updated_at)
  values(p_user_id,coalesce(p_enabled,false),nullif(left(trim(p_display_name),80),''),v_language,now())
  on conflict(user_id) do update set
    enabled=excluded.enabled,
    display_name=excluded.display_name,
    language_code=excluded.language_code,
    updated_at=now()
  returning * into v_row;

  insert into private.personal_ai_audit(user_id,action_name)
  values(p_user_id,'settings_updated');

  return jsonb_build_object(
    'enabled',v_row.enabled,
    'display_name',v_row.display_name,
    'language_code',v_row.language_code,
    'runtime_status',v_row.runtime_status
  );
end;
$$;

create or replace function public.service_personal_ai_set_source_permission(
  p_user_id uuid,
  p_source_type text,
  p_granted boolean,
  p_aal text,
  p_risk_score integer,
  p_risk_outcome text,
  p_risk_model_version text
)
returns boolean
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
declare
  v_source text := lower(trim(coalesce(p_source_type,'')));
begin
  perform private.personal_ai_require_service_role();
  perform private.personal_ai_assert_access(p_aal,p_risk_score,p_risk_outcome,p_risk_model_version);
  if v_source not in ('life_story','employment') then
    raise exception 'PERSONAL_AI_SOURCE_FORBIDDEN' using errcode='42501';
  end if;

  insert into private.personal_ai_source_permissions(user_id,source_type,granted_at,revoked_at,updated_at)
  values(p_user_id,v_source,now(),case when coalesce(p_granted,false) then null else now() end,now())
  on conflict(user_id,source_type) do update set
    granted_at=case when excluded.revoked_at is null then now() else private.personal_ai_source_permissions.granted_at end,
    revoked_at=excluded.revoked_at,
    updated_at=now();

  insert into private.personal_ai_audit(user_id,action_name,source_type)
  values(p_user_id,case when coalesce(p_granted,false) then 'source_granted' else 'source_revoked' end,v_source);

  return true;
end;
$$;

create or replace function public.service_personal_ai_delete_data(
  p_user_id uuid,
  p_aal text,
  p_risk_score integer,
  p_risk_outcome text,
  p_risk_model_version text
)
returns boolean
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
begin
  perform private.personal_ai_require_service_role();
  perform private.personal_ai_assert_access(p_aal,p_risk_score,p_risk_outcome,p_risk_model_version);

  delete from private.personal_ai_source_permissions where user_id=p_user_id;
  delete from private.personal_ai_settings where user_id=p_user_id;
  -- L'audit minimal est supprimé lui aussi : cette fondation n'impose pas de rétention produit.
  delete from private.personal_ai_audit where user_id=p_user_id;
  return true;
end;
$$;

revoke all on function public.service_personal_ai_get_state(uuid,text,integer,text,text) from public, anon, authenticated;
revoke all on function public.service_personal_ai_update_settings(uuid,boolean,text,text,text,integer,text,text) from public, anon, authenticated;
revoke all on function public.service_personal_ai_set_source_permission(uuid,text,boolean,text,integer,text,text) from public, anon, authenticated;
revoke all on function public.service_personal_ai_delete_data(uuid,text,integer,text,text) from public, anon, authenticated;

grant execute on function public.service_personal_ai_get_state(uuid,text,integer,text,text) to service_role;
grant execute on function public.service_personal_ai_update_settings(uuid,boolean,text,text,text,integer,text,text) to service_role;
grant execute on function public.service_personal_ai_set_source_permission(uuid,text,boolean,text,integer,text,text) to service_role;
grant execute on function public.service_personal_ai_delete_data(uuid,text,integer,text,text) to service_role;

comment on function public.service_personal_ai_get_state(uuid,text,integer,text,text) is
  'Serveur seulement. Retourne uniquement les réglages et consentements Mon IA, jamais le Registre personnel, Histoire de vie ou Emploi.';
comment on function public.service_personal_ai_set_source_permission(uuid,text,boolean,text,integer,text,text) is
  'Serveur seulement. Enregistre une intention explicite; V25 n expose aucun RPC de récupération de contenu source.';

commit;
