-- CANDIDAT DE REVUE / STAGING UNIQUEMENT - NE PAS EXECUTER EN PRODUCTION.
-- Reconstitution des deux definitions privees lues via pg_get_functiondef
-- le 21 novembre 2026, apres verification des SHA-256 originaux.
-- Aucune migration de production, aucune modification de GRANT/RLS.
-- Toutes les modifications sont annulees par le ROLLBACK final.
BEGIN;

-- Identite administrateur : aucun role client ne peut tester l'UUID d'un tiers.
-- Seule l'identite du JWT valide ou un JWT service_role verifie par Supabase
-- peut etre consultee. Toutes les references sont qualifiees.
CREATE OR REPLACE FUNCTION private.is_sinjira_admin(p_user_id uuid DEFAULT auth.uid())
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'pg_catalog'
AS $function$
  SELECT p_user_id IS NOT NULL
    AND (
      coalesce(auth.jwt()->>'role','') = 'service_role'
      OR p_user_id = (SELECT auth.uid())
    )
    AND EXISTS(
      SELECT 1 FROM public.internal_admin_users a WHERE a.user_id=p_user_id
    );
$function$;

-- Preserve le classement historique : 100 admin, 30 tester, 20 player,
-- 10 public/account authentifie, 1 projet public anonyme, sinon 0.
-- Refus strict de la demande relative a un utilisateur tiers.
-- Le role serveur est conservé pour les routines admin verifiees par JWT.
CREATE OR REPLACE FUNCTION private.project_access_rank(p_project_id uuid, p_user_id uuid DEFAULT auth.uid())
 RETURNS integer
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'pg_catalog'
AS $function$
 SELECT CASE
   WHEN coalesce(auth.jwt()->>'role','') <> 'service_role'
        AND p_user_id IS DISTINCT FROM (SELECT auth.uid()) THEN 0
   WHEN private.is_sinjira_admin(p_user_id) THEN 100
   WHEN EXISTS(
     SELECT 1 FROM public.project_access pa
     WHERE pa.project_id=p_project_id AND pa.user_id=p_user_id
       AND (pa.expires_at IS NULL OR pa.expires_at>now())
       AND pa.access_level='tester'
   ) THEN 30
   WHEN EXISTS(
     SELECT 1 FROM public.project_access pa
     WHERE pa.project_id=p_project_id AND pa.user_id=p_user_id
       AND (pa.expires_at IS NULL OR pa.expires_at>now())
       AND pa.access_level='player'
   ) THEN 20
   WHEN p_user_id IS NOT NULL AND EXISTS(
     SELECT 1 FROM public.projects p WHERE p.id=p_project_id
       AND p.visibility IN('public','account')
   ) THEN 10
   WHEN EXISTS(
     SELECT 1 FROM public.projects p WHERE p.id=p_project_id
       AND p.visibility='public'
   ) THEN 1
   ELSE 0
 END;
$function$;

-- NE PAS remplacer ce ROLLBACK par COMMIT : ce fichier n'est pas une migration.
ROLLBACK;
