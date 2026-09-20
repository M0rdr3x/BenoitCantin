-- SINJIRA™ V25 — visibilité catalogue projets pour le créateur.
-- Forward-only : le rôle propriétaire peut relire tous les projets internes
-- (jeux et autres créations) sans créer de faux achat, entitlement ou project_access.
-- Aucun accès membre supplémentaire n'est accordé.

alter table public.projects
  enable row level security;

drop policy if exists projects_owner_catalog_read_v25 on public.projects;
create policy projects_owner_catalog_read_v25
on public.projects
for select
to authenticated
using (
  public.is_sinjira_owner((select auth.uid()))
);

comment on policy projects_owner_catalog_read_v25 on public.projects is
  'V25: le propriétaire SINJIRA voit le catalogue complet des projets, y compris brouillons et projets restreints; ce droit de gestion ne constitue pas un achat ni un accès membre.';
