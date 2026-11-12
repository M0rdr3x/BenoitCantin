-- CANDIDAT DE REVUE UNIQUEMENT — PAS UNE MIGRATION DE PRODUCTION.
-- Cette transaction se termine par ROLLBACK pour rendre toute exécution
-- accidentelle non persistante. Ne pas déployer avant tests RLS en staging.
-- Conserve les signatures et GRANT des fonctions existantes.
--
-- Objectif : interdire l'oracle de rôles sur un UUID tiers pour anon et
-- authenticated, sans casser les documents publics (p_user_id NULL).
-- Seul un JWT signé de service_role peut consulter un autre user_id.
BEGIN;

CREATE OR REPLACE FUNCTION private.is_sinjira_admin(
    p_user_id uuid DEFAULT auth.uid()
)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $function$
    SELECT COALESCE(
        p_user_id IS NOT NULL
        AND (
            COALESCE((auth.jwt() ->> 'role') = 'service_role', false)
            OR p_user_id = auth.uid()
        )
        AND EXISTS (
            SELECT 1 FROM public.internal_admin_users
            WHERE user_id = p_user_id
        ),
        false
    )
$function$;

CREATE OR REPLACE FUNCTION private.project_access_rank(
    p_project_id uuid,
    p_user_id uuid DEFAULT auth.uid()
)
RETURNS integer
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $function$
    SELECT CASE
        WHEN NOT (
            COALESCE((auth.jwt() ->> 'role') = 'service_role', false)
            OR p_user_id IS NOT DISTINCT FROM auth.uid()
        ) THEN 0
        WHEN private.is_sinjira_admin(p_user_id) THEN 100
        WHEN EXISTS (
            SELECT 1 FROM public.project_access pa
            WHERE pa.project_id = p_project_id
              AND pa.user_id = p_user_id
              AND (pa.expires_at IS NULL OR pa.expires_at > now())
              AND pa.access_level = 'tester'
        ) THEN 30
        WHEN EXISTS (
            SELECT 1 FROM public.project_access pa
            WHERE pa.project_id = p_project_id
              AND pa.user_id = p_user_id
              AND (pa.expires_at IS NULL OR pa.expires_at > now())
              AND pa.access_level = 'player'
        ) THEN 20
        WHEN p_user_id IS NOT NULL AND EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = p_project_id
              AND p.visibility IN ('public', 'account')
        ) THEN 10
        WHEN EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = p_project_id
              AND p.visibility = 'public'
        ) THEN 1
        ELSE 0
    END
$function$;

-- La transaction DOIT rester non persistante. Un futur changement de
-- production exige une migration canonique distincte, revue et testée.
ROLLBACK;
