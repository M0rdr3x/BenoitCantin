-- SINJIRA™ V24.4.98 — index de couverture des clés étrangères du Centre Ma sécurité
-- Évite les scans inutiles lors des suppressions/révocations liées aux appareils et événements.

begin;

create index if not exists security_connection_challenges_connection_event_idx
  on public.security_connection_challenges(connection_event_id);

create index if not exists security_connection_challenges_request_device_idx
  on public.security_connection_challenges(request_device_id);

create index if not exists security_connection_challenges_resolved_device_idx
  on public.security_connection_challenges(resolved_device_id);

create index if not exists security_connection_events_device_idx
  on public.security_connection_events(device_id);

create index if not exists security_events_device_idx
  on public.security_events(device_id);

create index if not exists security_push_endpoints_device_idx
  on public.security_push_endpoints(device_id);

commit;
