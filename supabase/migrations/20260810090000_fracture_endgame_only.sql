-- Fracture du Réseau-Mère : séparation stricte Fiche joueur / Feuille de fin de partie.
create table if not exists public.endgame_sheets (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null unique references public.game_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  fields jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.endgame_sheets enable row level security;
drop policy if exists endgame_all_own on public.endgame_sheets;
create policy endgame_all_own on public.endgame_sheets for all to authenticated using(auth.uid()=user_id) with check(auth.uid()=user_id);
create index if not exists endgame_sheets_user_idx on public.endgame_sheets(user_id);
