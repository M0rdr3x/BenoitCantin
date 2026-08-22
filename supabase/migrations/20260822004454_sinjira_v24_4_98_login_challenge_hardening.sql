-- SINJIRA™ V24.4.98 — durcissement des confirmations de connexion et du risque de voyage impossible
-- Une connexion suspecte ne peut pas s'auto-approuver en faisant simplement confiance au même appareil.

begin;

create or replace function public.security_resolve_connection_challenge(
  p_challenge_id uuid,
  p_device_key text,
  p_decision text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_user uuid := auth.uid();
  v_device public.security_devices;
  v_request_device public.security_devices;
  v_ch public.security_connection_challenges;
  v_status text;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  if p_decision not in ('approved','denied') then raise exception 'INVALID_DECISION'; end if;

  perform private.security_require_aal2_if_available(v_user);

  select * into v_device
  from public.security_devices
  where user_id=v_user
    and device_key=p_device_key
    and is_trusted
    and revoked_at is null;
  if not found then raise exception 'TRUSTED_DEVICE_REQUIRED' using errcode='42501'; end if;

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
      then 'Connexion inhabituelle approuvée depuis un autre appareil fiable.'
      else 'Connexion inhabituelle refusée depuis un autre appareil fiable; l’appareil demandeur a été révoqué.'
    end,
    case when v_status='approved' then 'info' else 'critical' end
  );

  return to_jsonb(v_ch);
end;
$$;

revoke all on function public.security_resolve_connection_challenge(uuid,text,text) from public, anon;
grant execute on function public.security_resolve_connection_challenge(uuid,text,text) to authenticated;

create or replace function public.security_resolve_connection_challenge_mfa(
  p_challenge_id uuid,
  p_device_key text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_user uuid := auth.uid();
  v_device public.security_devices;
  v_ch public.security_connection_challenges;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  if coalesce(auth.jwt()->>'aal','aal1') <> 'aal2' then
    raise exception 'AAL2_REQUIRED' using errcode='42501';
  end if;

  select * into v_device
  from public.security_devices
  where user_id=v_user
    and device_key=p_device_key
    and revoked_at is null
  for update;
  if not found then raise exception 'REQUEST_DEVICE_NOT_FOUND'; end if;

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

  if v_ch.request_device_id is distinct from v_device.id then
    raise exception 'CHALLENGE_DEVICE_MISMATCH' using errcode='42501';
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

revoke all on function public.security_resolve_connection_challenge_mfa(uuid,text) from public, anon;
grant execute on function public.security_resolve_connection_challenge_mfa(uuid,text) to authenticated;

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
set search_path = pg_catalog, public
as $$
declare
  v_device public.security_devices;
  v_new boolean:=false;
  v_score integer:=0;
  v_reasons text[]:='{}'::text[];
  v_previous public.security_connection_events;
  v_travel_match boolean:=false;
  v_event public.security_connection_events;
  v_outcome text:='allow';
  v_challenge public.security_connection_challenges;
  v_settings public.security_user_settings;
  v_country text:=case when p_country_code ~ '^[A-Za-z]{2}$' then upper(p_country_code) else null end;
  v_sensitive boolean:=coalesce(p_action,'') in ('registry','ai_private','recovery','passkeys','posthumous','security_change');
  v_notify boolean:=false;
  v_had_trusted_device boolean:=false;
  v_rapid_country_change boolean:=false;
  v_force_challenge boolean:=false;
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED' using errcode='42501';
  end if;
  if p_user_id is null or p_device_key is null or char_length(p_device_key) not between 16 and 128 then
    raise exception 'INVALID_CONTEXT';
  end if;

  insert into public.security_user_settings(user_id) values(p_user_id) on conflict(user_id) do nothing;
  select * into v_settings from public.security_user_settings where user_id=p_user_id;

  select exists(
    select 1 from public.security_devices
    where user_id=p_user_id and is_trusted and revoked_at is null
  ) into v_had_trusted_device;

  select * into v_device from public.security_devices where user_id=p_user_id and device_key=p_device_key;

  if not found then
    v_new:=true;
    insert into public.security_devices(user_id,device_key,display_name,device_type,platform,last_country_code,last_region_code)
    values(
      p_user_id,p_device_key,left(coalesce(nullif(trim(p_display_name),''),'Appareil SINJIRA'),120),
      case when p_device_type in ('browser','ios','android','tablet','other') then p_device_type else 'other' end,
      left(coalesce(p_platform,''),120),v_country,left(p_region_code,80)
    ) returning * into v_device;
    v_score:=v_score+35;
    v_reasons:=array_append(v_reasons,'new_device');
    v_notify:=v_settings.notify_new_device;
    if v_had_trusted_device then
      v_force_challenge:=true;
      v_reasons:=array_append(v_reasons,'trusted_device_already_exists');
    end if;
  else
    update public.security_devices set
      last_seen_at=now(),
      last_country_code=coalesce(v_country,last_country_code),
      last_region_code=coalesce(left(p_region_code,80),last_region_code),
      platform=left(coalesce(p_platform,platform),120)
    where id=v_device.id returning * into v_device;
  end if;

  if v_device.revoked_at is not null then
    v_score:=100;
    v_reasons:=array_append(v_reasons,'revoked_device');
    v_outcome:='block';
  else
    if not v_device.is_trusted then
      v_score:=v_score+15;
      v_reasons:=array_append(v_reasons,'untrusted_device');
    else
      v_score:=greatest(0,v_score-20);
    end if;

    if v_country is not null then
      select * into v_previous from public.security_connection_events
      where user_id=p_user_id and country_code is not null and outcome in ('allow','approved')
      order by occurred_at desc limit 1;

      if found and v_previous.country_code<>v_country then
        v_score:=v_score+15;
        v_reasons:=array_append(v_reasons,'country_changed');
        if v_previous.occurred_at>now()-interval '2 hours' then
          v_score:=v_score+25;
          v_reasons:=array_append(v_reasons,'rapid_country_change');
          v_rapid_country_change:=true;
        end if;
      end if;

      select exists(
        select 1
        from public.security_travel_plans t, unnest(t.destinations) d
        where t.user_id=p_user_id
          and t.status='active'
          and now() between t.starts_at and t.ends_at
          and upper(trim(d))=v_country
      ) into v_travel_match;

      if v_travel_match then
        v_score:=greatest(0,v_score-25);
        v_reasons:=array_append(v_reasons,'travel_plan_match');
      elsif v_rapid_country_change then
        v_force_challenge:=true;
      end if;
    end if;

    if v_sensitive and v_score>0 then
      v_score:=least(100,v_score+10);
      v_reasons:=array_append(v_reasons,'sensitive_action');
    end if;

    if v_score>=60 or v_force_challenge then v_outcome:='challenge'; end if;
  end if;

  insert into public.security_connection_events(
    user_id,device_id,event_type,country_code,region_code,client_type,platform,
    action_name,risk_score,risk_reasons,outcome
  ) values(
    p_user_id,v_device.id,case when v_sensitive then 'sensitive_access' else 'login_context' end,
    v_country,left(p_region_code,80),left(coalesce(p_device_type,''),80),left(coalesce(p_platform,''),120),
    left(coalesce(p_action,'session'),80),v_score,v_reasons,v_outcome
  ) returning * into v_event;

  if v_outcome='challenge' then
    insert into public.security_connection_challenges(user_id,connection_event_id,request_device_id,display_code)
    values(p_user_id,v_event.id,v_device.id,10+floor(random()*90)::int)
    returning * into v_challenge;
    v_notify:=true;
  end if;
  if v_outcome='block' then v_notify:=true; end if;

  if v_notify and (v_settings.notify_high_risk or v_new) then
    insert into public.user_notifications(
      user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path
    ) values(
      p_user_id,'security_connection',
      case when v_outcome='block' then 'Connexion bloquée' else 'Connexion à vérifier' end,
      case when v_outcome='block'
        then 'SINJIRA a refusé un appareil révoqué.'
        else 'Une connexion inhabituelle demande votre confirmation.'
      end,
      'security_connection_event',v_event.id,'/compte/securite.html'
    );
  end if;

  return jsonb_build_object(
    'outcome',v_outcome,
    'risk_score',v_score,
    'risk_reasons',to_jsonb(v_reasons),
    'device_id',v_device.id,
    'new_device',v_new,
    'travel_match',v_travel_match,
    'requires_step_up',(v_sensitive and v_settings.sensitive_step_up),
    'challenge_id',v_challenge.id,
    'display_code',v_challenge.display_code,
    'mfa_or_other_trusted_device_required',(v_outcome='challenge')
  );
end;
$$;

revoke all on function public.security_evaluate_context(uuid,text,text,text,text,text,text,text) from public, anon, authenticated;
grant execute on function public.security_evaluate_context(uuid,text,text,text,text,text,text,text) to service_role;

commit;
