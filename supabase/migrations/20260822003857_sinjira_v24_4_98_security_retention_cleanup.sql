-- SINJIRA™ V24.4.98 — purge automatique des données de sécurité à rétention courte
-- Principe canonique : protéger sans surveiller. Une date de rétention doit mener à une suppression réelle.

begin;

create extension if not exists pg_cron with schema pg_catalog;
grant usage on schema cron to postgres;
grant all privileges on all tables in schema cron to postgres;

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

  return jsonb_build_object(
    'ok', true,
    'expired_travel_plans', v_expired_travel,
    'expired_challenges', v_expired_challenges,
    'deleted_travel_plans', v_deleted_travel,
    'deleted_challenges', v_deleted_challenges,
    'deleted_connection_events', v_deleted_connections,
    'deleted_security_events', v_deleted_events,
    'ran_at', now()
  );
end;
$$;

revoke all on function private.security_cleanup_expired() from public, anon, authenticated;
grant execute on function private.security_cleanup_expired() to service_role;

-- Idempotence : une reconstruction ou réapplication ne doit jamais créer deux tâches.
do $$
declare
  v_jobid bigint;
begin
  for v_jobid in
    select jobid from cron.job where jobname = 'sinjira-security-retention-cleanup'
  loop
    perform cron.unschedule(v_jobid);
  end loop;
end;
$$;

select cron.schedule(
  'sinjira-security-retention-cleanup',
  '17 3 * * *',
  $cron$select private.security_cleanup_expired();$cron$
);

commit;
