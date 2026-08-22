-- SINJIRA™ V24.4.98 — réglage du Bouclier de connexion
-- - un nouveau dispositif seul n'entraîne pas une confirmation impossible;
-- - le Mode Voyage ne réduit le risque que pour un pays explicitement prévu;
-- - l'option multi_country n'est jamais un joker mondial.

begin;

create or replace function public.security_evaluate_context(
  p_user_id uuid,p_device_key text,p_display_name text,p_device_type text,p_platform text,
  p_country_code text default null,p_region_code text default null,p_action text default 'session'
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_device public.security_devices; v_new boolean:=false; v_score integer:=0; v_reasons text[]:='{}'::text[];
  v_previous public.security_connection_events; v_travel_match boolean:=false; v_event public.security_connection_events;
  v_outcome text:='allow'; v_challenge public.security_connection_challenges; v_settings public.security_user_settings;
  v_country text:=case when p_country_code ~ '^[A-Za-z]{2}$' then upper(p_country_code) else null end;
  v_sensitive boolean:=coalesce(p_action,'') in ('registry','ai_private','recovery','passkeys','posthumous','security_change');
  v_notify boolean:=false;
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'SERVICE_ROLE_REQUIRED' using errcode='42501'; end if;
  if p_user_id is null or p_device_key is null or char_length(p_device_key) not between 16 and 128 then raise exception 'INVALID_CONTEXT'; end if;

  insert into public.security_user_settings(user_id) values(p_user_id) on conflict(user_id) do nothing;
  select * into v_settings from public.security_user_settings where user_id=p_user_id;
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
      end if;
    end if;

    if v_sensitive and v_score>0 then
      v_score:=least(100,v_score+10);
      v_reasons:=array_append(v_reasons,'sensitive_action');
    end if;

    -- 60 évite qu'un premier appareil entièrement nouveau (35+15=50)
    -- crée à lui seul une confirmation qu'aucun appareil fiable ne peut encore résoudre.
    if v_score>=60 then v_outcome:='challenge'; end if;
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
      case when v_outcome='block' then 'SINJIRA a refusé un appareil révoqué.' else 'Une connexion inhabituelle demande votre confirmation.' end,
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
    'display_code',v_challenge.display_code
  );
end;
$$;

revoke all on function public.security_evaluate_context(uuid,text,text,text,text,text,text,text)
from public, anon, authenticated;
grant execute on function public.security_evaluate_context(uuid,text,text,text,text,text,text,text)
to service_role;

commit;
