-- SINJIRA™ V25 — rebaseline forward-only du Livre I sur le maître reçu le 2026-10-04.
-- Ne publie aucun PDF, ne configure aucun chemin Storage et n'active aucune diffusion.
-- Les migrations historiques 20260919093000 / 20260919103000 restent immuables.

begin;

update private.sinjira_private_novel_assets a
set total_pages = 1027,
    updated_at = now()
from public.sinjira_novels n
where a.novel_id = n.id
  and n.slug = 'la-cendre-du-jugement'
  and a.total_pages is distinct from 1027;

commit;
