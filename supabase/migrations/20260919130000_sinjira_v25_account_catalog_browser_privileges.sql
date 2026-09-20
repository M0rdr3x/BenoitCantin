-- SINJIRA™ V25 — convergence des privilèges navigateur du catalogue Compte
--
-- Les tables ci-dessous sont protégées par RLS et sont lues directement par les
-- clients Compte/Bibliothèque. La reconstruction locale ne conservait pas les
-- privilèges SQL explicites attendus, ce qui rendait les policies inatteignables.
--
-- Cette migration ne contourne aucune policy : elle retire d'abord les privilèges
-- navigateur implicites puis réaccorde uniquement les opérations utilisées par
-- les parcours publics/authentifiés. Administration et mutations privilégiées
-- restent côté serveur/service_role.

begin;

-- Catalogue projets : public/account filtré par RLS; aucune écriture navigateur.
revoke all on table public.projects from anon, authenticated;
grant select on table public.projects to anon, authenticated;

-- Accès projet : un membre relit uniquement ses propres lignes via RLS.
revoke all on table public.project_access from anon, authenticated;
grant select on table public.project_access to authenticated;

-- Demandes d'accès : lecture self-only + création d'une demande, sans décision client.
revoke all on table public.access_requests from anon, authenticated;
grant select, insert on table public.access_requests to authenticated;

-- Documents approuvés : lecture uniquement, bornée par RLS et les helpers d'accès.
revoke all on table public.documents from anon, authenticated;
grant select on table public.documents to anon, authenticated;

-- Playtests : consultation authentifiée uniquement.
revoke all on table public.playtests from anon, authenticated;
grant select on table public.playtests to authenticated;

-- Candidatures playtest : lecture self-only + candidature; aucune revue client.
revoke all on table public.playtest_participants from anon, authenticated;
grant select, insert on table public.playtest_participants to authenticated;

-- Extensions publiées : lecture uniquement, selon la policy publique existante.
revoke all on table public.extensions from anon, authenticated;
grant select on table public.extensions to anon, authenticated;

commit;
