-- SINJIRA™ V24.4.98 — rétention des appareils révoqués
-- Les appareils révoqués sont utiles brièvement pour l'explication d'un incident, pas indéfiniment.

begin;

create or replace function private.security_cleanup_expired()
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, private
as $$
declare
  v_expired_travel integer := 0;
  v_expired_challenges integer := 0;
  v_deleted_travel integer := 0;
  v_deleted_challenges integer := 0;
  v_deleted_connections integer := 0;
  v_deleted_events integer := 0;
  v_deleted_devices integer := 0;
begin
  update public.security_travel_plans
     set status = 'expired'
   where status = 'active'
     and ends_at <= now();
  get diagnostics v_expired_travel = row_count;

  update public.security_connection_challenges
     set status = 'expired'
   where status = 'pending'
     and expires_at <= now();
  get diagnostics v_expired_challenges = row_count;

  delete from public.security_connection_challenges
   where delete_after <= now();
  get diagnostics v_deleted_challenges = row_count;

  delete from public.security_travel_plans
   where delete_after <= now();
  get diagnostics v_deleted_travel = row_count;

  delete from public.security_connection_events
   where retention_until <= now();
  get diagnostics v_deleted_connections = row_count;

  delete from public.security_events
   where retention_until <= now();
  get diagnostics v_deleted_events = row_count;

  delete from public.security_devices
   where revoked_at is not null
     and revoked_at <= now() - interval '90 days';
  get diagnostics v_deleted_devices = row_count;

  return jsonb_build_object(
    'ok', true,
    'expired_travel_plans', v_expired_travel,
    'expired_challenges', v_expired_challenges,
    'deleted_travel_plans', v_deleted_travel,
    'deleted_challenges', v_deleted_challenges,
    'deleted_connection_events', v_deleted_connections,
    'deleted_security_events', v_deleted_events,
    'deleted_revoked_devices', v_deleted_devices,
    'ran_at', now()
  );
end;
$$;

revoke all on function private.security_cleanup_expired() from public, anon, authenticated;
grant execute on function private.security_cleanup_expired() to service_role;

comment on table public.security_devices is
  'Appareils de sécurité identifiés par une clé aléatoire locale; un appareil révoqué est purgé après 90 jours.';

commit;
