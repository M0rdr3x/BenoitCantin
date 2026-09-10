-- SINJIRA™ V25 — durcissement du rebind de session des appareils fiables
-- L’HUMAIN AVANT TOUT : une device_key est un identifiant de possession côté client,
-- jamais une preuve suffisante pour transporter la confiance vers une autre session.

begin;

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
  v_rebound_trust boolean := false;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  if p_device_key is null or char_length(p_device_key) not between 16 and 128 then
    raise exception 'INVALID_DEVICE_KEY' using errcode='22023';
  end if;

  -- Verrouiller la ligne empêche qu'un changement de confiance concurrent soit conservé
  -- pendant qu'une nouvelle session réassocie la même clé appareil.
  select * into v_row
  from public.security_devices
  where user_id=v_user and device_key=p_device_key
  for update;

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
    -- Une clé déjà connue peut identifier la même installation, mais elle ne prouve pas
    -- que la nouvelle session est encore autorisée à hériter du statut fiable. Dès que
    -- le session_id change (ou n'est plus disponible), on retire la confiance avant le
    -- rebind. La restauration devra repasser par security_set_device_trust et ses gardes
    -- AAL2 / approbation par un autre appareil fiable lorsqu'elles s'appliquent.
    v_rebound_trust := (v_row.is_trusted or v_row.is_primary)
      and (v_session is null or v_row.last_session_id is distinct from v_session);

    update public.security_devices
       set display_name=left(coalesce(nullif(trim(p_display_name),''),display_name),120),
           device_type=case when p_device_type in ('browser','ios','android','tablet','other') then p_device_type else device_type end,
           platform=left(coalesce(p_platform,platform),120),
           last_seen_at=now(),
           is_trusted=case when v_rebound_trust then false else is_trusted end,
           is_primary=case when v_rebound_trust then false else is_primary end,
           last_session_id=v_session
     where id=v_row.id
     returning * into v_row;

    if v_rebound_trust then
      insert into public.security_events(user_id,device_id,event_type,summary,severity)
      values(
        v_user,
        v_row.id,
        'device_trust_session_rebind',
        'Confiance appareil retirée automatiquement après changement de session authentifiée.',
        'warning'
      );
    end if;
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

-- Conserver la frontière V24.5.10 : l'implémentation privilégiée reste interne et
-- le wrapper public SECURITY INVOKER existant demeure la seule surface publique.
revoke all on function sinjira_security_internal.security_register_device(text,text,text,text) from public, anon;
grant execute on function sinjira_security_internal.security_register_device(text,text,text,text) to authenticated, service_role;

comment on function sinjira_security_internal.security_register_device(text,text,text,text) is
  'Enregistre/reassocie un appareil sans jamais transférer sa confiance entre sessions; un changement de session réinitialise trusted/primary avant rebind.';

commit;
