-- SINJIRA V24.5.24 — convergence reproductible des fonctions privilégiées
-- Production ne contient plus quatre fonctions historiques; project_access_rank reste service_role-only.
-- Aucun CASCADE : toute dépendance cachée doit faire échouer la reconstruction plutôt que disparaître silencieusement.

DROP FUNCTION IF EXISTS public.grant_owner_novel_library();
DROP FUNCTION IF EXISTS public.grant_owner_product_entitlement();
DROP FUNCTION IF EXISTS public.grant_owner_project_access();
DROP FUNCTION IF EXISTS public.spend_sinjira_tokens(integer, text, text, text, uuid);

REVOKE ALL PRIVILEGES ON FUNCTION public.project_access_rank(uuid, uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.project_access_rank(uuid, uuid) TO service_role;
