-- SINJIRA V18 — structure du contexte CANON privé.
-- IMPORTANT : ce fichier crée uniquement la structure.
-- Les contenus issus de la Bible maîtresse et du dossier narratif sont importés directement
-- dans Supabase et ne doivent PAS être publiés dans GitHub.
create table if not exists public.sinjira_canon_context (
  context_key text primary key,
  classification text not null check (classification in ('CANON','SECRET_AUTEUR','A_ARBITRER','PROVISOIRE','META')),
  title text not null,
  source_name text not null,
  source_version text not null default 'v1.0',
  source_date date,
  source_sha256 text,
  public_safe boolean not null default false,
  content jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.sinjira_canon_context enable row level security;
revoke all on public.sinjira_canon_context from anon, authenticated;
