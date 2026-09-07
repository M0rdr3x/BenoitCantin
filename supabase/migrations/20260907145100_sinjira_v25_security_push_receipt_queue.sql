-- SINJIRA™ V25 — file minimale de reçus Expo pour les notifications de sécurité
-- Métadonnées techniques uniquement: aucun contenu de notification, score, localisation ou donnée de session.

begin;

create table if not exists public.security_push_receipt_queue (
  expo_receipt_id text primary key check (char_length(expo_receipt_id) between 8 and 200),
  endpoint_id uuid not null references public.security_push_endpoints(id) on delete cascade,
  created_at timestamptz not null default now(),
  available_after timestamptz not null default (now() + interval '15 minutes'),
  expires_at timestamptz not null default (now() + interval '24 hours'),
  check (available_after >= created_at),
  check (expires_at > available_after)
);

create index if not exists security_push_receipt_queue_available_idx
  on public.security_push_receipt_queue(available_after, expires_at);

alter table public.security_push_receipt_queue enable row level security;
revoke all on table public.security_push_receipt_queue from public, anon, authenticated;
grant select, insert, delete on table public.security_push_receipt_queue to service_role;

commit;
