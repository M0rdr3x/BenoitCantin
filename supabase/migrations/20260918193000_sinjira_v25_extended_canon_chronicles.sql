-- SINJIRA™ V25 — fondation du Canon étendu et des Chroniques
-- Les 14 romans principaux restent le Canon central verrouillé.
-- Cette migration ajoute une couche narrative distincte pour les histoires
-- des Consciences et les Chroniques du Monde. Elle ne modifie aucun roman.

create table if not exists public.sinjira_extended_stories(
  id uuid primary key default gen_random_uuid(),
  story_type text not null check(story_type in (
    'character_chronicle',
    'world_chronicle',
    'quebec_chronicle',
    'archive',
    'fragment',
    'novella'
  )),
  character_id uuid references public.characters(id) on delete set null,
  title text not null,
  slug text unique,
  summary text,
  content text,
  region_name text,
  anchor_scope text not null default 'UNASSIGNED' check(anchor_scope in (
    'LIVRES_1_12',
    'ORIGINES_13_14',
    'MULTI_PERIODE',
    'UNASSIGNED'
  )),
  canon_status text not null default 'PROVISOIRE' check(canon_status in (
    'PROVISOIRE',
    'CANON_ETENDU',
    'A_ARBITRER',
    'NON_CANON'
  )),
  status text not null default 'draft' check(status in (
    'draft',
    'author_review',
    'validated',
    'published',
    'archived'
  )),
  starts_at timestamptz,
  ends_at timestamptz,
  continuity_data jsonb not null default '{}'::jsonb,
  audience text not null default 'private' check(audience in ('private','members','public')),
  visible_to_character_owner boolean not null default true,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check(ends_at is null or starts_at is null or ends_at >= starts_at),
  check(story_type <> 'character_chronicle' or character_id is not null),
  check(published_at is null or status='published'),
  check(
    status <> 'published'
    or (
      canon_status='CANON_ETENDU'
      and audience in ('members','public')
      and published_at is not null
    )
  )
);

create table if not exists public.sinjira_story_character_presence(
  id uuid primary key default gen_random_uuid(),
  story_id uuid not null references public.sinjira_extended_stories(id) on delete cascade,
  character_id uuid not null references public.characters(id) on delete cascade,
  starts_at timestamptz,
  ends_at timestamptz,
  location_name text,
  certainty text not null default 'confirmed' check(certainty in ('confirmed','approximate','unknown')),
  presence_kind text not null default 'story_span' check(presence_kind in ('story_span','scene','travel','reference')),
  segment_key text not null default 'primary' check(char_length(segment_key) between 1 and 120),
  source_note text,
  created_at timestamptz not null default now(),
  unique(story_id,character_id,segment_key),
  check(ends_at is null or starts_at is null or ends_at >= starts_at)
);

create index if not exists sinjira_extended_stories_character_idx
  on public.sinjira_extended_stories(character_id,status,updated_at desc);
create index if not exists sinjira_extended_stories_canon_idx
  on public.sinjira_extended_stories(canon_status,status,published_at desc);
create index if not exists sinjira_extended_stories_region_idx
  on public.sinjira_extended_stories(region_name,starts_at);
create index if not exists sinjira_story_presence_character_time_idx
  on public.sinjira_story_character_presence(character_id,starts_at,ends_at);
create index if not exists sinjira_story_presence_story_idx
  on public.sinjira_story_character_presence(story_id);

drop trigger if exists sinjira_extended_stories_updated_at on public.sinjira_extended_stories;
create trigger sinjira_extended_stories_updated_at
before update on public.sinjira_extended_stories
for each row execute function public.set_updated_at();

alter table public.sinjira_extended_stories enable row level security;
alter table public.sinjira_story_character_presence enable row level security;

-- Publication publique : uniquement les récits explicitement publiés dans le Canon étendu.
drop policy if exists sinjira_extended_stories_public_read on public.sinjira_extended_stories;
create policy sinjira_extended_stories_public_read
on public.sinjira_extended_stories
for select to anon,authenticated
using(
  status='published'
  and canon_status='CANON_ETENDU'
  and audience='public'
  and published_at is not null
);

-- Les membres peuvent lire les récits publiés pour les membres.
drop policy if exists sinjira_extended_stories_members_read on public.sinjira_extended_stories;
create policy sinjira_extended_stories_members_read
on public.sinjira_extended_stories
for select to authenticated
using(
  status='published'
  and canon_status='CANON_ETENDU'
  and audience in ('members','public')
  and published_at is not null
);

-- Le propriétaire d'une Conscience peut voir les récits qui lui sont explicitement rendus visibles,
-- même pendant la préparation. Aucun droit d'écriture client n'est accordé ici.
drop policy if exists sinjira_extended_stories_character_owner_read on public.sinjira_extended_stories;
create policy sinjira_extended_stories_character_owner_read
on public.sinjira_extended_stories
for select to authenticated
using(
  visible_to_character_owner
  and character_id is not null
  and exists(
    select 1 from public.characters c
    where c.id=sinjira_extended_stories.character_id
      and c.user_id=(select auth.uid())
  )
);

-- Les présences publiées suivent la visibilité de leur récit.
drop policy if exists sinjira_story_presence_published_read on public.sinjira_story_character_presence;
create policy sinjira_story_presence_published_read
on public.sinjira_story_character_presence
for select to anon,authenticated
using(
  exists(
    select 1 from public.sinjira_extended_stories s
    where s.id=sinjira_story_character_presence.story_id
      and s.status='published'
      and s.canon_status='CANON_ETENDU'
      and s.audience='public'
      and s.published_at is not null
  )
);

drop policy if exists sinjira_story_presence_character_owner_read on public.sinjira_story_character_presence;
create policy sinjira_story_presence_character_owner_read
on public.sinjira_story_character_presence
for select to authenticated
using(
  exists(
    select 1
    from public.sinjira_extended_stories s
    join public.characters c on c.id=s.character_id
    where s.id=sinjira_story_character_presence.story_id
      and s.visible_to_character_owner
      and c.user_id=(select auth.uid())
  )
);

comment on table public.sinjira_extended_stories is
  'Canon étendu SINJIRA : Chroniques des personnages, Chroniques du Monde, Chroniques de Québec, archives et formats courts. Ne remplace jamais les 14 romans du Canon central.';

comment on table public.sinjira_story_character_presence is
  'Présences temporelles et géographiques des personnages dans le Canon étendu. Un même personnage peut avoir plusieurs segments dans une Chronique; segment_key=primary représente la présence générale de l’éditeur.';

comment on column public.parallel_world_memberships.main_canon_eligible is
  'LEGACY V22 : ne doit plus servir à déterminer l’admissibilité d’une Conscience au Canon étendu. Les 14 romans centraux sont verrouillés; les Chroniques officielles utilisent sinjira_extended_stories.';

comment on column public.parallel_world_memberships.parallel_world_only is
  'LEGACY V22 : décrit uniquement l’ancien modèle du Monde parallèle. Ne limite pas l’admissibilité d’un personnage approuvé à une Chronique du Canon étendu.';
