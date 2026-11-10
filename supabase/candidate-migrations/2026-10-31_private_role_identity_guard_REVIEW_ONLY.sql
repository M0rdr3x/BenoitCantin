-- CANDIDAT DE REVUE : NE PAS DÉPLOYER DIRECTEMENT / NE PAS AJOUTER
-- AU REGISTRE IMMUTABLE supabase/migrations/ SANS PREVOL ET TESTS RLS.
--
-- Risque : fonctions SECURITY DEFINER privées exécutables par anon et
-- authenticated avec p_user_id arbitraire. La fonction est aussi appelée
-- par RLS dans documents, projects, playtests. Ne pas révoquer les grants
-- aveuglément : public.documents exige private.project_access_rank(id,NULL).
--
-- Garanties :
-- * utilisateur ordinaire : uniquement auth.uid() ;
-- * anon : p_user_id=NULL -> rang strictement public sans identité ;
-- * service_role JWT vérifié par Supabase : consultation de tiers autorisée ;
-- * identités tierces : booléen FALSE / rang 0, pas de détails.
-- Aucun SQL dynamique, pas de changement de signature ni de droits.

CREATE OR REPLACE FUNCTION private.is_sinjira_admin(
    p_user_id uuid DEFAULT auth.uid()
)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, auth, public, private, pg_temp
AS $function$
    SELECT
        p_user_id IS NOT NULL
        AND (
            COALESCE(auth.jwt()->>'role', '') = 'service_role'
            OR p_user_id = (SELECT auth.uid())
        )
        AND EXISTS (
            SELECT 1
            FROM public.internal_admin_users AS a
            WHERE a.user_id = p_user_id
        );
$function$;

CREATE OR REPLACE FUNCTION private.project_access_rank(
    p_project_id uuid,
    p_user_id uuid DEFAULT auth.uid()
)
RETURNS integer
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, auth, public, private, pg_temp
AS $function$
    SELECT CASE
        -- Requête utilisateur vers l'identité d'un tiers :
        -- répondre 0 sans même examiner ses droits ou son rôle admin.
        WHEN p_user_id IS NOT NULL
             AND COALESCE(auth.jwt()->>'role', '') <> 'service_role'
             AND p_user_id IS DISTINCT FROM (SELECT auth.uid())
            THEN 0
        WHEN private.is_sinjira_admin(p_user_id)
            THEN 100
        WHEN EXISTS (
            SELECT 1
            FROM public.project_access AS pa
            WHERE pa.project_id = p_project_id
              AND pa.user_id = p_user_id
              AND (pa.expires_at IS NULL OR pa.expires_at > now())
              AND pa.access_level = 'tester'
        ) THEN 30
        WHEN EXISTS (
            SELECT 1
            FROM public.project_access AS pa
            WHERE pa.project_id = p_project_id
              AND pa.user_id = p_user_id
              AND (pa.expires_at IS NULL OR pa.expires_at > now())
              AND pa.access_level = 'player'
        ) THEN 20
        WHEN p_user_id IS NOT NULL
             AND EXISTS (
                 SELECT 1
                 FROM public.projects AS p
                 WHERE p.id = p_project_id
                   AND p.visibility IN ('public','account')
             ) THEN 10
        WHEN EXISTS (
            SELECT 1
            FROM public.projects AS p
            WHERE p.id = p_project_id
              AND p.visibility = 'public'
        ) THEN 1
        ELSE 0
    END;
$function$;

-- Les GRANT sont intentionnellement inchangés. Le helper RLS anonyme
-- nécessite EXECUTE pour les documents approuvés. La restriction est
-- appliquée DANS LE CORPS de la fonction, même si elle reste exécutable.
--
-- Tests obligatoires avant promotion :
-- (1) rôle anon + NULL → document public consultable / document privé refusé ;
-- (2) user A : son rang inchangé, rang de user B toujours 0 ;
-- (3) user A : is_sinjira_admin(user B) = false ;
-- (4) user admin A : is_sinjira_admin(A) = true, contrôle MFA inchangé ;
-- (5) service_role : lecture voulue de l'identité cible permise ;
-- (6) RLS documents/projects/playtests sans régression ou récursion ;
-- (7) vérification catalogues, signatures, ACL, search_path et propriétaires.
