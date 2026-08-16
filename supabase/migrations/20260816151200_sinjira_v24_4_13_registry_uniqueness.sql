-- SINJIRA™ V24.4.13 — unicité Registre
-- Copie conforme de la migration déjà appliquée en production.

create unique index if not exists character_submissions_one_per_user_uidx
  on public.character_submissions(user_id);

create unique index if not exists characters_one_active_per_user_uidx
  on public.characters(user_id)
  where status <> 'archived';

comment on index public.character_submissions_one_per_user_uidx
  is 'Invariant SINJIRA V24.4.13 : un seul dossier Registre par compte.';

comment on index public.characters_one_active_per_user_uidx
  is 'Invariant SINJIRA V24.4.13 : un seul personnage actif/non archivé par compte.';
