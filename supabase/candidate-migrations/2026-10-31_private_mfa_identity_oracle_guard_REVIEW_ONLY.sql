-- CANDIDAT DE REVUE UNIQUEMENT. Ne pas appliquer à Supabase en production.
-- Aucun ajout au registre des migrations immuables n'est autorisé sans
-- revue indépendante, génération CLI, tests pgtap et prévol de déploiement.
--
-- Lecture catalogue en production (31 octobre 2026):
-- private.security_require_aal2_if_available(uuid) est SECURITY DEFINER,
-- EXECUTE accessible à authenticated, USAGE sur private autorisé.
-- Le contrôle présent interroge le MFA d'un p_user_id arbitraire sans
-- comparer d'abord ce paramètre au sujet JWT courant. Un rôle avec accès
-- SQL au schéma peut distinguer, via AAL2_REQUIRED, des états MFA de tiers.
-- Aucun accès via HTTP/PostgREST au schéma private n'a été démontré.
--
-- Les appels connus de security_after_password_recovery,
-- security_cancel_travel_plan, security_compromise_account,
-- security_create_travel_plan et security_report_lost_device utilisent
-- déjà v_user := auth.uid(). Aucune signature, ACL ou règle RLS modifiée.

CREATE OR REPLACE FUNCTION private.security_require_aal2_if_available(p_user_id uuid)
RETURNS void
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO 'pg_catalog', 'auth', 'private'
AS $function$
BEGIN
  -- Vérifier l'identité AVANT de lire auth.mfa_factors à travers
  -- private.security_verified_mfa_exists. Pas de statut MFA de tiers.
  IF p_user_id IS NULL THEN
    RAISE EXCEPTION 'AUTH_REQUIRED' USING errcode = '42501';
  END IF;

  IF COALESCE(auth.jwt()->>'role', '') <> 'service_role'
     AND p_user_id IS DISTINCT FROM auth.uid() THEN
    RAISE EXCEPTION 'AUTH_CONTEXT_MISMATCH' USING errcode = '42501';
  END IF;

  -- Politique MFA conditionnelle de l'utilisateur conservée à l'identique.
  IF private.security_verified_mfa_exists(p_user_id)
     AND COALESCE(auth.jwt()->>'aal','aal1') <> 'aal2' THEN
    RAISE EXCEPTION 'AAL2_REQUIRED' USING errcode = '42501';
  END IF;
END;
$function$;

-- ACL existantes intentionnellement inchangées:
-- anon ne dispose pas de EXECUTE; authenticated et service_role oui.
-- Vérifications préalables à la promotion:
-- (1) sans JWT: AUTH_REQUIRED / AUTH_CONTEXT_MISMATCH
-- (2) utilisateur A contre l'UUID B: AUTH_CONTEXT_MISMATCH, indépendamment
--     du facteur MFA de B et du niveau AAL de A
-- (3) utilisateur A avec son UUID: comportement MFA conditionnel historique
-- (4) service_role: sémantique MFA d'origine conservée
-- (5) vérifier que les fonctions clientes continuent à passer auth.uid()
-- (6) pgtap local/staging + catalogue/ACL/search_path avant toute migration.
