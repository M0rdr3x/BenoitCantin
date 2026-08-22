-- SINJIRA™ V24.4.98 — RPC du Centre de sécurité et moteur de risque contextuel
-- Les écritures sensibles passent par ces fonctions contrôlées.

begin;

create or replace function private.security_verified_mfa_exists(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path = pg_catalog, auth
as $$
  select exists (
    select 1 from auth.mfa_factors f
    where f.user_id = p_user_id and f.status::text = 'verified'
  );
$$;
revoke all on function private.security_verified_mfa_exists(uuid) from public, anon, authenticated;
grant execute on function private.security_verified_mfa_exists(uuid) to service_role;

create or replace function private.security_require_aal2_if_available(p_user_id uuid)
returns void
language plpgsql
stable
security definer
set search_path = pg_catalog, auth, private
as $$
begin
  if private.security_verified_mfa_exists(p_user_id)
     and coalesce(auth.jwt()->>'aal','aal1') <> 'aal2' then
    raise exception 'AAL2_REQUIRED' using errcode = '42501';
  end if;
end;
$$;
revoke all on function private.security_require_aal2_if_available(uuid) from public, anon, authenticated;
grant execute on function private.security_require_aal2_if_available(uuid) to authenticated, service_role;

create or replace function public.security_get_settings()
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_user uuid := auth.uid();
  v_row public.security_user_settings;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  insert into public.security_user_settings(user_id) values (v_user)
  on conflict (user_id) do nothing;
  select * into v_row from public.security_user_settings where user_id=v_user;
  return to_jsonb(v_row);
end;
$$;
revoke all on function public.security_get_settings() from public, anon;
grant execute on function public.security_get_settings() to authenticated;

create or replace function public.security_update_settings(
  p_remember_usual_region boolean default null,
  p_sensitive_step_up boolean default null,
  p_notify_new_device boolean default null,
  p_notify_high_risk boolean default null,
  p_notify_security_changes boolean default null
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_user uuid := auth.uid();
  v_old public.security_user_settings;
  v_row public.security_user_settings;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
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
$$;
revoke all on function public.security_update_settings(boolean,boolean,boolean,boolean,boolean) from public, anon;
grant execute on function public.security_update_settings(boolean,boolean,boolean,boolean,boolean) to authenticated;

create or replace function public.security_register_device(
  p_device_key text,
  p_display_name text default 'Appareil SINJIRA',
  p_device_type text default 'browser',
  p_platform text default ''
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_user uuid := auth.uid();
  v_session uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_row public.security_devices;
  v_new boolean := false;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  if p_device_key is null or char_length(p_device_key) not between 16 and 128 then raise exception 'INVALID_DEVICE_KEY'; end if;
  select * into v_row from public.security_devices where user_id=v_user and device_key=p_device_key;
  if not found then
    v_new := true;
    insert into public.security_devices(user_id,device_key,display_name,device_type,platform,last_session_id)
    values(v_user,p_device_key,left(coalesce(nullif(trim(p_display_name),''),'Appareil SINJIRA'),120),
      case when p_device_type in ('browser','ios','android','tablet','other') then p_device_type else 'other' end,
      left(coalesce(p_platform,''),120),v_session)
    returning * into v_row;
    insert into public.security_events(user_id,device_id,event_type,summary,severity)
    values(v_user,v_row.id,'new_device','Nouvel appareil enregistré dans le Centre de sécurité.','warning');
  else
    update public.security_devices set
      display_name=left(coalesce(nullif(trim(p_display_name),''),display_name),120),
      device_type=case when p_device_type in ('browser','ios','android','tablet','other') then p_device_type else device_type end,
      platform=left(coalesce(p_platform,platform),120),last_seen_at=now(),last_session_id=v_session
    where id=v_row.id returning * into v_row;
  end if;
  insert into public.security_user_settings(user_id) values(v_user) on conflict(user_id) do nothing;
  return jsonb_build_object('device',to_jsonb(v_row),'is_new',v_new,'revoked',v_row.revoked_at is not null);
end;
$$;
revoke all on function public.security_register_device(text,text,text,text) from public, anon;
grant execute on function public.security_register_device(text,text,text,text) to authenticated;

create or replace function public.security_set_device_trust(p_device_id uuid,p_trusted boolean,p_primary boolean default false)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_user uuid := auth.uid();
  v_row public.security_devices;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_aal2_if_available(v_user);
  select * into v_row from public.security_devices where id=p_device_id and user_id=v_user and revoked_at is null for update;
  if not found then raise exception 'DEVICE_NOT_FOUND'; end if;
  if p_primary then update public.security_devices set is_primary=false where user_id=v_user and id<>p_device_id; end if;
  update public.security_devices set is_trusted=p_trusted,is_primary=(p_trusted and p_primary)
  where id=p_device_id returning * into v_row;
  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(v_user,v_row.id,'device_trust_changed',case when p_trusted then 'Appareil marqué comme fiable.' else 'Confiance retirée à un appareil.' end,'warning');
  return to_jsonb(v_row);
end;
$$;
revoke all on function public.security_set_device_trust(uuid,boolean,boolean) from public, anon;
grant execute on function public.security_set_device_trust(uuid,boolean,boolean) to authenticated;

create or replace function public.security_revoke_device(p_device_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_user uuid := auth.uid();
  v_row public.security_devices;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_aal2_if_available(v_user);
  update public.security_devices set revoked_at=now(),is_trusted=false,is_primary=false
  where id=p_device_id and user_id=v_user and revoked_at is null returning * into v_row;
  if not found then raise exception 'DEVICE_NOT_FOUND'; end if;
  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(v_user,v_row.id,'device_revoked','Appareil révoqué par le propriétaire du compte.','critical');
  return to_jsonb(v_row);
end;
$$;
revoke all on function public.security_revoke_device(uuid) from public, anon;
grant execute on function public.security_revoke_device(uuid) to authenticated;

create or replace function public.security_create_travel_plan(
  p_starts_at timestamptz,p_ends_at timestamptz,p_destinations text[],p_multi_country boolean default false
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_user uuid := auth.uid();
  v_row public.security_travel_plans;
  v_dest text[];
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_aal2_if_available(v_user);
  if p_starts_at is null or p_ends_at is null or p_ends_at<=p_starts_at or p_ends_at>p_starts_at+interval '180 days' then raise exception 'INVALID_TRAVEL_PERIOD'; end if;
  select array_agg(left(trim(x),80)) into v_dest from unnest(coalesce(p_destinations,'{}'::text[])) x where trim(x)<>'';
  if cardinality(coalesce(v_dest,'{}'::text[])) not between 1 and 12 then raise exception 'INVALID_DESTINATIONS'; end if;
  insert into public.security_travel_plans(user_id,starts_at,ends_at,destinations,multi_country,delete_after)
  values(v_user,p_starts_at,p_ends_at,v_dest,coalesce(p_multi_country,false),p_ends_at+interval '7 days') returning * into v_row;
  insert into public.security_events(user_id,event_type,summary,severity)
  values(v_user,'travel_plan_created','Mode Voyage planifié. Les détails servent uniquement à la sécurité.','info');
  return to_jsonb(v_row);
end;
$$;
revoke all on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) from public, anon;
grant execute on function public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean) to authenticated;

create or replace function public.security_cancel_travel_plan(p_plan_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_user uuid := auth.uid(); v_row public.security_travel_plans;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_aal2_if_available(v_user);
  update public.security_travel_plans set status='cancelled',cancelled_at=now(),delete_after=least(delete_after,now()+interval '7 days')
  where id=p_plan_id and user_id=v_user and status='active' returning * into v_row;
  if not found then raise exception 'TRAVEL_PLAN_NOT_FOUND'; end if;
  insert into public.security_events(user_id,event_type,summary,severity) values(v_user,'travel_plan_cancelled','Mode Voyage annulé.','info');
  return to_jsonb(v_row);
end;
$$;
revoke all on function public.security_cancel_travel_plan(uuid) from public, anon;
grant execute on function public.security_cancel_travel_plan(uuid) to authenticated;

create or replace function public.security_list_sessions()
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, auth
as $$
declare
  v_user uuid := auth.uid();
  v_current uuid := nullif(auth.jwt()->>'session_id','')::uuid;
  v_result jsonb;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'id',s.id,'created_at',s.created_at,'updated_at',s.updated_at,'refreshed_at',s.refreshed_at,
    'not_after',s.not_after,'user_agent',coalesce(s.user_agent,''),'aal',s.aal::text,'is_current',(s.id=v_current)
  ) order by s.updated_at desc),'[]'::jsonb) into v_result
  from auth.sessions s where s.user_id=v_user and (s.not_after is null or s.not_after>now());
  return v_result;
end;
$$;
revoke all on function public.security_list_sessions() from public, anon;
grant execute on function public.security_list_sessions() to authenticated;

create or replace function public.security_sensitive_access_status(p_scope text default 'registry')
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public, auth, private
as $$
declare
  v_user uuid := auth.uid(); v_step boolean; v_has_mfa boolean; v_aal text;
begin
  if v_user is null then return jsonb_build_object('authenticated',false,'allowed',false,'reason','auth_required'); end if;
  select sensitive_step_up into v_step from public.security_user_settings where user_id=v_user;
  v_step := coalesce(v_step,true);
  v_has_mfa := private.security_verified_mfa_exists(v_user);
  v_aal := coalesce(auth.jwt()->>'aal','aal1');
  return jsonb_build_object(
    'authenticated',true,'scope',left(coalesce(p_scope,'sensitive'),80),'step_up_enabled',v_step,
    'has_verified_mfa',v_has_mfa,'current_aal',v_aal,
    'setup_required',(v_step and not v_has_mfa),'verification_required',(v_step and v_has_mfa and v_aal<>'aal2'),
    'allowed',(not v_step or (v_has_mfa and v_aal='aal2'))
  );
end;
$$;
revoke all on function public.security_sensitive_access_status(text) from public, anon;
grant execute on function public.security_sensitive_access_status(text) to authenticated;

create or replace function public.security_resolve_connection_challenge(p_challenge_id uuid,p_device_key text,p_decision text)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_user uuid := auth.uid(); v_device public.security_devices; v_ch public.security_connection_challenges; v_status text;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  if p_decision not in ('approved','denied') then raise exception 'INVALID_DECISION'; end if;
  select * into v_device from public.security_devices where user_id=v_user and device_key=p_device_key and is_trusted and revoked_at is null;
  if not found then raise exception 'TRUSTED_DEVICE_REQUIRED' using errcode='42501'; end if;
  select * into v_ch from public.security_connection_challenges where id=p_challenge_id and user_id=v_user for update;
  if not found then raise exception 'CHALLENGE_NOT_FOUND'; end if;
  if v_ch.status<>'pending' or v_ch.expires_at<=now() then
    update public.security_connection_challenges set status='expired' where id=v_ch.id and status='pending';
    raise exception 'CHALLENGE_EXPIRED';
  end if;
  v_status:=p_decision;
  update public.security_connection_challenges set status=v_status,resolved_at=now(),resolved_device_id=v_device.id where id=v_ch.id returning * into v_ch;
  update public.security_connection_events set outcome=v_status,event_type=case when v_status='approved' then 'approved' else 'denied' end
    where id=v_ch.connection_event_id;
  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(v_user,v_device.id,'connection_'||v_status,case when v_status='approved' then 'Connexion inhabituelle approuvée depuis un appareil fiable.' else 'Connexion inhabituelle refusée depuis un appareil fiable.' end,case when v_status='approved' then 'info' else 'critical' end);
  return to_jsonb(v_ch);
end;
$$;
revoke all on function public.security_resolve_connection_challenge(uuid,text,text) from public, anon;
grant execute on function public.security_resolve_connection_challenge(uuid,text,text) to authenticated;

create or replace function public.security_compromise_account(p_current_device_key text default null)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_user uuid := auth.uid(); v_current uuid; v_revoked integer;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
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
$$;
revoke all on function public.security_compromise_account(text) from public, anon;
grant execute on function public.security_compromise_account(text) to authenticated;

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
    values(p_user_id,p_device_key,left(coalesce(nullif(trim(p_display_name),''),'Appareil SINJIRA'),120),
      case when p_device_type in ('browser','ios','android','tablet','other') then p_device_type else 'other' end,
      left(coalesce(p_platform,''),120),v_country,left(p_region_code,80)) returning * into v_device;
    v_score:=v_score+35; v_reasons:=array_append(v_reasons,'new_device'); v_notify:=v_settings.notify_new_device;
  else
    update public.security_devices set last_seen_at=now(),last_country_code=coalesce(v_country,last_country_code),
      last_region_code=coalesce(left(p_region_code,80),last_region_code),platform=left(coalesce(p_platform,platform),120)
      where id=v_device.id returning * into v_device;
  end if;
  if v_device.revoked_at is not null then
    v_score:=100; v_reasons:=array_append(v_reasons,'revoked_device'); v_outcome:='block';
  else
    if not v_device.is_trusted then v_score:=v_score+15; v_reasons:=array_append(v_reasons,'untrusted_device'); else v_score:=greatest(0,v_score-20); end if;
    if v_country is not null then
      select * into v_previous from public.security_connection_events
      where user_id=p_user_id and country_code is not null and outcome in ('allow','approved')
      order by occurred_at desc limit 1;
      if found and v_previous.country_code<>v_country then
        v_score:=v_score+15; v_reasons:=array_append(v_reasons,'country_changed');
        if v_previous.occurred_at>now()-interval '2 hours' then v_score:=v_score+25; v_reasons:=array_append(v_reasons,'rapid_country_change'); end if;
      end if;
      select exists(select 1 from public.security_travel_plans t, unnest(t.destinations) d
        where t.user_id=p_user_id and t.status='active' and now() between t.starts_at and t.ends_at
          and (upper(trim(d))=v_country or t.multi_country)) into v_travel_match;
      if v_travel_match then v_score:=greatest(0,v_score-25); v_reasons:=array_append(v_reasons,'travel_plan_match'); end if;
    end if;
    if v_sensitive and v_score>0 then v_score:=least(100,v_score+10); v_reasons:=array_append(v_reasons,'sensitive_action'); end if;
    if v_score>=50 then v_outcome:='challenge'; end if;
  end if;
  insert into public.security_connection_events(user_id,device_id,event_type,country_code,region_code,client_type,platform,action_name,risk_score,risk_reasons,outcome)
  values(p_user_id,v_device.id,case when v_sensitive then 'sensitive_access' else 'login_context' end,v_country,left(p_region_code,80),
    left(coalesce(p_device_type,''),80),left(coalesce(p_platform,''),120),left(coalesce(p_action,'session'),80),v_score,v_reasons,v_outcome)
  returning * into v_event;
  if v_outcome='challenge' then
    insert into public.security_connection_challenges(user_id,connection_event_id,request_device_id,display_code)
    values(p_user_id,v_event.id,v_device.id,10+floor(random()*90)::int) returning * into v_challenge;
    v_notify:=true;
  end if;
  if v_outcome='block' then v_notify:=true; end if;
  if v_notify and (v_settings.notify_high_risk or v_new) then
    insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path)
    values(p_user_id,'security_connection',case when v_outcome='block' then 'Connexion bloquée' else 'Connexion à vérifier' end,
      case when v_outcome='block' then 'SINJIRA a refusé un appareil révoqué.' else 'Une connexion inhabituelle demande votre confirmation.' end,
      'security_connection_event',v_event.id,'/compte/securite.html');
  end if;
  return jsonb_build_object('outcome',v_outcome,'risk_score',v_score,'risk_reasons',to_jsonb(v_reasons),'device_id',v_device.id,
    'new_device',v_new,'travel_match',v_travel_match,'requires_step_up',(v_sensitive and v_settings.sensitive_step_up),
    'challenge_id',v_challenge.id,'display_code',v_challenge.display_code);
end;
$$;
revoke all on function public.security_evaluate_context(uuid,text,text,text,text,text,text,text) from public, anon, authenticated;
grant execute on function public.security_evaluate_context(uuid,text,text,text,text,text,text,text) to service_role;

create or replace function public.security_purge_expired_data()
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare a integer;b integer;c integer;d integer;
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'SERVICE_ROLE_REQUIRED' using errcode='42501'; end if;
  update public.security_travel_plans set status='expired' where status='active' and ends_at<now();
  delete from public.security_connection_events where retention_until<now(); get diagnostics a=row_count;
  delete from public.security_events where retention_until<now(); get diagnostics b=row_count;
  delete from public.security_connection_challenges where delete_after<now(); get diagnostics c=row_count;
  delete from public.security_travel_plans where delete_after<now(); get diagnostics d=row_count;
  delete from public.security_devices where revoked_at is not null and revoked_at<now()-interval '90 days';
  return jsonb_build_object('connection_events_deleted',a,'security_events_deleted',b,'challenges_deleted',c,'travel_plans_deleted',d);
end;
$$;
revoke all on function public.security_purge_expired_data() from public, anon, authenticated;
grant execute on function public.security_purge_expired_data() to service_role;

create or replace function public.sinjira_account_security_health()
returns jsonb
language sql
stable
security definer
set search_path = pg_catalog, public
as $$
select jsonb_build_object(
  'ok',to_regclass('public.security_devices') is not null and to_regclass('public.security_travel_plans') is not null
       and to_regprocedure('public.security_evaluate_context(uuid,text,text,text,text,text,text,text)') is not null,
  'security_version','24.4.98','stores_raw_ip',false,'stores_gps',false,
  'connection_event_retention_days',90,'travel_cleanup_delay_days',7,'security_event_retention_days',180
);
$$;
revoke all on function public.sinjira_account_security_health() from public, anon, authenticated;
grant execute on function public.sinjira_account_security_health() to service_role;

commit;
