-- SINJIRA V32 — emplacement intrapage synchronisé pour les romans privés.
-- Migration additive : les anciennes progressions conservent NULL, qui signifie
-- « page sauvegardée sans emplacement précis ».
-- Les politiques RLS existantes continuent de limiter chaque ligne à son lecteur.
alter table public.sinjira_reader_library
  add column if not exists scroll_ratio numeric(5,4);

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid='public.sinjira_reader_library'::regclass
      and conname='sinjira_reader_library_scroll_ratio_range'
  ) then
    alter table public.sinjira_reader_library
      add constraint sinjira_reader_library_scroll_ratio_range
      check (scroll_ratio is null or (scroll_ratio >= 0 and scroll_ratio <= 1));
  end if;
end
$$;

comment on column public.sinjira_reader_library.scroll_ratio
  is 'Défilement intrapage normalisé (0 à 1). NULL = progression héritée sans position précise; aucun contenu du roman.';
