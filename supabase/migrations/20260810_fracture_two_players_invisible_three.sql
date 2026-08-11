-- Fracture V8 - deux joueurs humains + Joueur invisible 3 avec fiches privées séparées

alter table public.game_sessions add column if not exists party_code text;
alter table public.player_sheets add column if not exists sheet_key text not null default 'self';
alter table public.player_sheets add column if not exists sheet_label text;

alter table public.player_sheets drop constraint if exists player_sheets_session_id_key;
alter table public.player_sheets drop constraint if exists player_sheets_session_sheet_key_key;
alter table public.player_sheets add constraint player_sheets_session_sheet_key_key unique(session_id,sheet_key);

create index if not exists player_sheets_session_idx on public.player_sheets(session_id);
create index if not exists game_sessions_party_code_idx on public.game_sessions(party_code);
create unique index if not exists game_sessions_user_game_party_unique
  on public.game_sessions(user_id,game_slug,party_code)
  where party_code is not null;

update public.game_sessions
set effective_player_count=3
where game_slug='fracture-du-reseau-mere' and human_player_count between 1 and 3;

update public.documents d
set description='Prépare automatiquement Fracture du Réseau-Mère : solo = une fiche pour le joueur humain et deux invisibles; 2 joueurs humains = chaque humain reçoit sa fiche personnelle et sa propre fiche indépendante du Joueur invisible 3; 3 joueurs humains = une fiche personnelle séparée par joueur.',
    version='2.0',updated_at=now()
from public.projects p
where d.project_id=p.id and p.slug='fracture-du-reseau-mere' and d.title='Préparation dynamique des joueurs';
