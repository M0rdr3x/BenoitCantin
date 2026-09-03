-- SINJIRA™ V25.0 — confidentialité device_key et confiance appareil
-- Principe : un identifiant d'appareil n'est jamais une donnée d'affichage.
-- Les anciennes clés ayant été lisibles par le client, la confiance existante est remise à zéro une fois.

begin;

-- La table contient un identifiant de possession interne. RLS ne suffit pas à masquer une colonne :
-- le navigateur passe désormais uniquement par security_list_devices().
revoke select on table public.security_devices from authenticated;

-- Remise à zéro volontaire de la confiance historique : les device_key ont déjà été exposés
-- par SELECT * et par certaines anciennes réponses RPC. Aucun ancien appareil ne conserve donc
-- un statut « fiable » sur la base d'un secret qui a pu être divulgué.
with reset_devices as (
  update public.security_devices
     set is_trusted=false,
         is_primary=false
   where is_trusted or is_primary
   returning user_id
)
insert into public.security_events(user_id,event_type,summary,severity)
select distinct user_id,
       'device_trust_reset_v25',
       'La confiance des appareils a été réinitialisée après un durcissement de la confidentialité des identifiants appareil.',
       'warning'
from reset_devices;

create or replace function sinjira_security_internal.security_list_devices(
  p_current_device_key text default null
)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, auth
as $$
declare
  v_user uuid := auth.uid();
  v_session uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_result jsonb;
begin
  if v_user is null then
    raise exception 'AUTH_REQUIRED' using errcode='42501';
  end if;
  if p_current_device_key is not null
     and char_length(p_current_device_key) not between 16 and 128 then
    raise exception 'INVALID_DEVICE_KEY' using errcode='22023';
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
    'id',d.id,
    'display_name',d.display_name,
    'device_type',d.device_type,
    'platform',d.platform,
    'is_trusted',d.is_trusted,
    'is_primary',d.is_primary,
    'first_seen_at',d.first_seen_at,
    'last_seen_at',d.last_seen_at,
    'last_country_code',d.last_country_code,
    'last_region_code',d.last_region_code,
    'revoked_at',d.revoked_at,
    'created_at',d.created_at,
    'updated_at',d.updated_at,
    'is_current',(
      p_current_device_key is not null
      and d.device_key=p_current_device_key
      and v_session is not null
      and d.last_session_id=v_session
    )
  ) order by d.last_seen_at desc),'[]'::jsonb)
  into v_result
  from public.security_devices d
  where d.user_id=v_user;

  return v_result;
end;
$$;
revoke all on function sinjira_security_internal.security_list_devices(text) from public, anon;
grant execute on function sinjira_security_internal.security_list_devices(text) to authenticated, service_role;

create or replace function public.security_list_devices(p_current_device_key text default null)
returns jsonb
language sql
security invoker
set search_path = ''
as $$
  select sinjira_security_internal.security_list_devices($1)
$$;
revoke all on function public.security_list_devices(text) from public, anon;
grant execute on function public.security_list_devices(text) to authenticated, service_role;

-- Réponse d'enregistrement assainie : jamais device_key ni last_session_id.
create or replace function sinjira_security_internal.security_register_device(
  p_device_key text,
  p_display_name text default 'Appareil SINJIRA',
  p_device_type text default 'browser',
  p_platform text default ''
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, auth
as $$
declare
  v_user uuid := auth.uid();
  v_session uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_row public.security_devices;
  v_new boolean := false;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  if p_device_key is null or char_length(p_device_key) not between 16 and 128 then
    raise exception 'INVALID_DEVICE_KEY' using errcode='22023';
  end if;

  select * into v_row
  from public.security_devices
  where user_id=v_user and device_key=p_device_key;

  if not found then
    v_new := true;
    insert into public.security_devices(user_id,device_key,display_name,device_type,platform,last_session_id)
    values(
      v_user,
      p_device_key,
      left(coalesce(nullif(trim(p_display_name),''),'Appareil SINJIRA'),120),
      case when p_device_type in ('browser','ios','android','tablet','other') then p_device_type else 'other' end,
      left(coalesce(p_platform,''),120),
      v_session
    )
    returning * into v_row;

    insert into public.security_events(user_id,device_id,event_type,summary,severity)
    values(v_user,v_row.id,'new_device','Nouvel appareil enregistré dans le Centre de sécurité.','warning');
  else
    update public.security_devices
       set display_name=left(coalesce(nullif(trim(p_display_name),''),display_name),120),
           device_type=case when p_device_type in ('browser','ios','android','tablet','other') then p_device_type else device_type end,
           platform=left(coalesce(p_platform,platform),120),
           last_seen_at=now(),
           last_session_id=v_session
     where id=v_row.id
     returning * into v_row;
  end if;

  insert into public.security_user_settings(user_id) values(v_user)
  on conflict(user_id) do nothing;

  return jsonb_build_object(
    'device',jsonb_build_object(
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
    ),
    'is_new',v_new,
    'revoked',v_row.revoked_at is not null
  );
end;
$$;

-- Un appareil ne peut devenir fiable que s'il s'agit de l'appareil de la session courante.
-- Le premier appareil fiable peut être amorcé avec AAL2. Dès qu'un autre appareil fiable existe,
-- une approbation récente depuis un autre appareil fiable est obligatoire.
-- Retirer une confiance demeure possible selon la protection historique afin de ne pas bloquer
-- une action défensive chez une personne qui n'a pas encore configuré de MFA.
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

  -- Accroître la confiance exige toujours AAL2 strict, même si aucune MFA n'était
  -- auparavant configurée. Retirer la confiance ne doit pas être rendu impossible.
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

-- Révoquer est une action défensive. On conserve donc le comportement historique :
-- si une MFA vérifiée existe elle impose AAL2; sinon la personne peut quand même retirer l'appareil.
create or replace function sinjira_security_internal.security_revoke_device(p_device_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, auth, private
as $$
declare
  v_user uuid := auth.uid();
  v_session uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_row public.security_devices;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
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
$$;

-- Les fonctions internes restent derrière les wrappers publics SECURITY INVOKER de V24.5.10.
revoke all on function sinjira_security_internal.security_register_device(text,text,text,text) from public, anon;
revoke all on function sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean) from public, anon;
revoke all on function sinjira_security_internal.security_revoke_device(uuid) from public, anon;
grant execute on function sinjira_security_internal.security_register_device(text,text,text,text) to authenticated, service_role;
grant execute on function sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean) to authenticated, service_role;
grant execute on function sinjira_security_internal.security_revoke_device(uuid) to authenticated, service_role;

comment on function public.security_list_devices(text) is
  'Liste assainie des appareils du compte. device_key et last_session_id ne sortent jamais vers le navigateur.';
comment on function sinjira_security_internal.security_set_device_trust(uuid,boolean,boolean) is
  'Confiance appareil: AAL2 strict pour augmenter la confiance; bootstrap du premier appareil seulement, puis approbation récente par un autre appareil fiable.';

commit;
