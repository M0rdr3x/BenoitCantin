-- Fracture du Réseau-Mère - séparation des fiches 2/3 joueurs et mode solo 1 + 2 invisibles

alter table public.game_sessions add column if not exists human_player_count integer;
alter table public.game_sessions add column if not exists effective_player_count integer;
alter table public.game_sessions add column if not exists play_mode text;

update public.game_sessions
set human_player_count = coalesce(human_player_count, player_count),
    effective_player_count = coalesce(effective_player_count, player_count),
    play_mode = coalesce(play_mode, case when player_count=1 then 'solo' else 'multiplayer' end)
where game_slug='fracture-du-reseau-mere';

alter table public.game_sessions drop constraint if exists game_sessions_human_player_count_check;
alter table public.game_sessions add constraint game_sessions_human_player_count_check
  check (human_player_count is null or human_player_count between 1 and 3);

alter table public.game_sessions drop constraint if exists game_sessions_effective_player_count_check;
alter table public.game_sessions add constraint game_sessions_effective_player_count_check
  check (effective_player_count is null or effective_player_count between 1 and 3);

alter table public.game_sessions drop constraint if exists game_sessions_play_mode_check;
alter table public.game_sessions add constraint game_sessions_play_mode_check
  check (play_mode is null or play_mode in ('solo','multiplayer'));

update public.documents d
set description='Prépare automatiquement la partie : 1 joueur humain obtient une seule fiche solo regroupant lui-même et deux joueurs invisibles; 2 ou 3 joueurs humains obtiennent chacun une fiche privée séparée.',
    updated_at=now()
from public.projects p
where d.project_id=p.id and p.slug='fracture-du-reseau-mere' and d.title='Préparation dynamique des joueurs';

insert into public.documents(project_id,title,description,document_type,version,status,access_level,external_url,mime_type,sort_order,approved_at)
select p.id,
       'Mode solo - fiche 3 participants',
       'Une seule fiche privée pour le joueur humain et deux joueurs invisibles. Cette fiche peut être téléchargée, sauvegardée ou envoyée au joueur, mais n’est jamais transmise aux données d’équilibrage.',
       'Fiche joueur solo','1.0','approved','account',
       '/projets/sinjira/jeux/fracture-du-reseau-mere/documents/SINJIRA_Mode_Solo_3_Joueurs_Interactive.pdf',
       'application/pdf',15,now()
from public.projects p
where p.slug='fracture-du-reseau-mere'
  and not exists(select 1 from public.documents d where d.project_id=p.id and d.title='Mode solo - fiche 3 participants' and d.status='approved');
