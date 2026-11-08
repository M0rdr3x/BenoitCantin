-- SINJIRA : journal technique pour notifications Formspree non nominatives.
-- Un seul événement par compte confirmé ou dossier enregistré.
-- Aucune réponse de questionnaire, adresse, mot de passe ou donnée de profil.
create table if not exists public.sinjira_formspree_events (
  id uuid primary key default gen_random_uuid(),
  event_type text not null check (event_type in ('compte_confirme','registre_enregistre')),
  source_id uuid not null,
  delivery_status text not null default 'pending' check (delivery_status in ('pending','sent','failed')),
  created_at timestamptz not null default now(),
  sent_at timestamptz,
  constraint sinjira_formspree_events_unique unique(event_type,source_id)
);
alter table public.sinjira_formspree_events enable row level security;
revoke all on public.sinjira_formspree_events from public, anon, authenticated;
grant select,insert,update on public.sinjira_formspree_events to service_role;
comment on table public.sinjira_formspree_events is 'SINJIRA internal one-time delivery ledger. Service role only; no client access and no participant payload.';
