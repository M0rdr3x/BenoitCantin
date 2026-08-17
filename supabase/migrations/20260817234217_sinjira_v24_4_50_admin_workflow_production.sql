-- SINJIRA V24.4.50 — journal admin + historique des statuts personnages.
-- Correctif ciblé requis par admin-sinjira-v18 et le compte personnage.

create table if not exists public.character_status_events(
  id uuid primary key default gen_random_uuid(),
  submission_id uuid not null references public.character_submissions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null,
  note text,
  created_at timestamptz not null default now()
);

alter table public.character_status_events enable row level security;
revoke all on public.character_status_events from public,anon,authenticated;
grant select on public.character_status_events to authenticated;
grant all on public.character_status_events to service_role;

drop policy if exists character_events_own_read on public.character_status_events;
create policy character_events_own_read
on public.character_status_events
for select to authenticated
using ((select auth.uid())=user_id);

create index if not exists character_status_events_submission_idx
  on public.character_status_events(submission_id,created_at);
create index if not exists character_status_events_user_idx
  on public.character_status_events(user_id,created_at);

create table if not exists public.admin_audit_log(
  id bigserial primary key,
  admin_user_id uuid references auth.users(id) on delete set null,
  action text not null,
  entity_type text,
  entity_id text,
  summary text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.admin_audit_log enable row level security;
revoke all on public.admin_audit_log from public,anon,authenticated;
grant all on public.admin_audit_log to service_role;
create index if not exists admin_audit_log_created_idx
  on public.admin_audit_log(created_at desc);
create index if not exists admin_audit_log_admin_idx
  on public.admin_audit_log(admin_user_id,created_at desc);

-- Reconstituer une première entrée de suivi pour les dossiers déjà existants.
insert into public.character_status_events(submission_id,user_id,status,note,created_at)
select s.id,s.user_id,s.status,'Dossier importé dans le suivi administratif.',s.created_at
from public.character_submissions s
where not exists(
  select 1 from public.character_status_events e where e.submission_id=s.id
);

create or replace function public.sinjira_admin_workflow_health()
returns jsonb
language sql
stable
security invoker
set search_path=public
as $$
  select jsonb_build_object(
    'ok',
      to_regclass('public.admin_audit_log') is not null and
      to_regclass('public.character_status_events') is not null,
    'admin_audit_log',to_regclass('public.admin_audit_log') is not null,
    'character_status_events',to_regclass('public.character_status_events') is not null,
    'version','24.4.50'
  );
$$;

revoke all on function public.sinjira_admin_workflow_health() from public,anon,authenticated;
grant execute on function public.sinjira_admin_workflow_health() to service_role;
