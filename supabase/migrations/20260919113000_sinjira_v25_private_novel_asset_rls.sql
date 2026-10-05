-- SINJIRA™ V25 — défense en profondeur du registre privé des romans.
-- Migration forward-only : ne réécrit pas la création historique du catalogue.
-- Aucune policy membre n'est créée; sans policy, la table reste fail-closed pour
-- les rôles soumis à RLS. Les accès directs public/anon/authenticated restent révoqués.

alter table private.sinjira_private_novel_assets
  enable row level security;

revoke all on table private.sinjira_private_novel_assets
from public,anon,authenticated;

grant select,insert,update,delete
on table private.sinjira_private_novel_assets
to service_role;

comment on table private.sinjira_private_novel_assets is
  'V25: registre serveur des actifs intégraux privés; RLS activée, aucun accès membre direct, livraison uniquement via les contrôles serveur dédiés.';
