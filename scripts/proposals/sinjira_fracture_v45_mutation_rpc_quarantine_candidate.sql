-- SINJIRA V45 — CANDIDAT DE QUARANTAINE DES RPC MUTATRICES FRACTURE.
-- NON AUTORISÉ POUR LA PRODUCTION, ne pas déposer dans supabase/migrations.
-- Ce fichier est un plan de remédiation, exécuté automatiquement UNIQUEMENT
-- sur une base PostgreSQL fictive éphémère. Le déploiement requiert approbation
-- et vérification des parties existantes / processus de reprise / rollback.
-- Aucun secret, aucune identité, aucune ligne de partie n'est consultée.
-- Seules cinq actions de jeu, dans deux schémas chacune, sont concernées.
-- Les fonctions de lecture / statut / documents ne sont PAS modifiées.
-- Les droits effectifs du rôle service_role doivent rester disponibles
-- pour les opérations de maintenance explicitement autorisées.
BEGIN;
REVOKE EXECUTE ON FUNCTION public.fracture_engine_start(text) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.fracture_engine_pick(text, bigint) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.fracture_engine_submit_keep(text, bigint[]) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.fracture_engine_submit_report(text, text, integer, bigint) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.fracture_engine_submit_accusation(text, integer[]) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_start(text) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_pick(text, bigint) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_keep(text, bigint[]) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_report(text, text, integer, bigint) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_accusation(text, integer[]) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fracture_engine_start(text) TO service_role;
GRANT EXECUTE ON FUNCTION public.fracture_engine_pick(text, bigint) TO service_role;
GRANT EXECUTE ON FUNCTION public.fracture_engine_submit_keep(text, bigint[]) TO service_role;
GRANT EXECUTE ON FUNCTION public.fracture_engine_submit_report(text, text, integer, bigint) TO service_role;
GRANT EXECUTE ON FUNCTION public.fracture_engine_submit_accusation(text, integer[]) TO service_role;
GRANT EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_start(text) TO service_role;
GRANT EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_pick(text, bigint) TO service_role;
GRANT EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_keep(text, bigint[]) TO service_role;
GRANT EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_report(text, text, integer, bigint) TO service_role;
GRANT EXECUTE ON FUNCTION sinjira_fracture_internal.fracture_engine_submit_accusation(text, integer[]) TO service_role;
COMMIT;
