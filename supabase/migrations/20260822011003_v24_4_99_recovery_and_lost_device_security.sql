create or replace function public.security_after_password_recovery(p_device_key text default null)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public','private'
as $$
declare
  v_user uuid := auth.uid();
  v_current uuid;
  v_revoked integer := 0;
  v_push_disabled integer := 0;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_aal2_if_available(v_user);

  select id into v_current
  from public.security_devices
  where user_id=v_user and device_key=p_device_key and revoked_at is null;

  update public.security_devices
     set revoked_at=now(), is_trusted=false, is_primary=false, updated_at=now()
   where user_id=v_user
     and revoked_at is null
     and (v_current is null or id<>v_current);
  get diagnostics v_revoked=row_count;

  if v_current is not null then
    update public.security_devices
       set is_trusted=false, is_primary=false, last_seen_at=now(), updated_at=now()
     where id=v_current and user_id=v_user and revoked_at is null;
  end if;

  update public.security_push_endpoints
     set enabled=false, updated_at=now()
   where user_id=v_user and enabled;
  get diagnostics v_push_disabled=row_count;

  update public.security_connection_challenges
     set status='expired'
   where user_id=v_user and status='pending';

  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(v_user,v_current,'password_recovery_completed',
    'Récupération du mot de passe terminée; les anciens appareils ont été révoqués, les notifications push désactivées et la confiance de l’appareil courant doit être réaccordée.',
    'critical');

  insert into public.user_notifications(user_id,notification_type,title,body,action_path)
  values(v_user,'security_recovery','Récupération du compte terminée',
    'Le mot de passe a été modifié. Les anciennes sessions seront fermées et les appareils doivent être vérifiés de nouveau.',
    '/compte/securite.html');

  return jsonb_build_object('ok',true,'revoked_devices',v_revoked,'disabled_push_endpoints',v_push_disabled,'current_device_id',v_current,'current_device_trusted',false);
end;
$$;

revoke all on function public.security_after_password_recovery(text) from public, anon;
grant execute on function public.security_after_password_recovery(text) to authenticated;

create or replace function public.security_report_lost_device(p_device_id uuid)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public','private'
as $$
declare
  v_user uuid := auth.uid();
  v_row public.security_devices;
  v_push_disabled integer := 0;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.security_require_aal2_if_available(v_user);

  select * into v_row
  from public.security_devices
  where id=p_device_id and user_id=v_user and revoked_at is null
  for update;
  if not found then raise exception 'DEVICE_NOT_FOUND'; end if;

  update public.security_devices
     set revoked_at=now(), is_trusted=false, is_primary=false, updated_at=now()
   where id=v_row.id and user_id=v_user;

  update public.security_push_endpoints
     set enabled=false, updated_at=now()
   where user_id=v_user and device_id=v_row.id and enabled;
  get diagnostics v_push_disabled=row_count;

  update public.security_connection_challenges
     set status='expired'
   where user_id=v_user and request_device_id=v_row.id and status='pending';

  insert into public.security_events(user_id,device_id,event_type,summary,severity)
  values(v_user,v_row.id,'device_reported_lost',
    'Appareil déclaré perdu; confiance révoquée et notifications push désactivées pour cet appareil.',
    'critical');

  insert into public.user_notifications(user_id,notification_type,title,body,action_path)
  values(v_user,'security_lost_device','Appareil déclaré perdu',
    'L’appareil a été révoqué dans SINJIRA. Pour invalider aussi toutes les autres sessions, utilisez Déconnecter les autres appareils ou Compte compromis.',
    '/compte/securite.html');

  return jsonb_build_object('ok',true,'device_id',v_row.id,'disabled_push_endpoints',v_push_disabled,'session_revocation_required',true);
end;
$$;

revoke all on function public.security_report_lost_device(uuid) from public, anon;
grant execute on function public.security_report_lost_device(uuid) to authenticated;
