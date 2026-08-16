-- SINJIRA™ V24.4.12 — défense en profondeur des tables internes.
-- Les tables sans policy sont volontairement non exposées : RLS + REVOKE direct.
-- Les RPC de simple diagnostic n'ont besoin d'aucun privilège SECURITY DEFINER.

alter function public.get_sinjira_server_version() security invoker;
alter function public.get_sinjira_runtime_health() security invoker;
alter function public.fracture_engine_health() security invoker;

comment on function public.get_sinjira_server_version() is
  'Diagnostic public non secret : version de plateforme, SECURITY INVOKER.';
comment on function public.get_sinjira_runtime_health() is
  'Diagnostic non secret de présence des composants, SECURITY INVOKER.';
comment on function public.fracture_engine_health() is
  'Diagnostic non secret du moteur Fracture, SECURITY INVOKER.';

-- Tables de moteur / génération / canon / audit : service_role ou fonctions serveur uniquement.
revoke all on table public.sinjira_character_generation_runs from anon,authenticated;
revoke all on table public.character_generation_runs from anon,authenticated;
revoke all on table public.sinjira_canon_context from anon,authenticated;
revoke all on table public.admin_audit_log from anon,authenticated;
revoke all on table public.fracture_engine_games from anon,authenticated;
revoke all on table public.fracture_engine_seats from anon,authenticated;
revoke all on table public.fracture_engine_cards from anon,authenticated;
revoke all on table public.fracture_engine_actions from anon,authenticated;
revoke all on table public.fracture_engine_rounds from anon,authenticated;
revoke all on table public.fracture_engine_votes from anon,authenticated;
revoke all on table public.fracture_engine_events from anon,authenticated;

-- Tables internes de workflow / identité / consentement sans route client directe.
revoke all on table public.age_verification_cases from anon,authenticated;
revoke all on table public.bridge_entities from anon,authenticated;
revoke all on table public.extension_contributions from anon,authenticated;
revoke all on table public.family_link_consents from anon,authenticated;
revoke all on table public.relationship_consents from anon,authenticated;
revoke all on table public.sinjira_character_change_events from anon,authenticated;
revoke all on table public.sinjira_license_codes from anon,authenticated;
revoke all on table public.social_hidden_posts from anon,authenticated;
revoke all on table public.sync_state from anon,authenticated;
revoke all on table public.identity_migration_log from anon,authenticated;
revoke all on table public.internal_contribution_ownership from anon,authenticated;
revoke all on table public.purchase_entitlements from anon,authenticated;

-- Ancienne chaîne lecteur/Registre conservée pour compatibilité administrative seulement.
revoke all on table public.reader_character_admin_history from anon,authenticated;
revoke all on table public.reader_character_bible from anon,authenticated;
revoke all on table public.reader_character_links from anon,authenticated;
revoke all on table public.reader_private_profiles from anon,authenticated;
revoke all on table public.reader_processing_jobs from anon,authenticated;
revoke all on table public.reader_user_consents from anon,authenticated;
revoke all on table public.relation_catalog from anon,authenticated;
revoke all on table public.source_documents from anon,authenticated;

-- Les catalogues internes de licence restent accessibles via RPC, pas par table directe.
revoke all on table public.sinjira_products from anon,authenticated;

-- Re-grants explicites des trois diagnostics, après conversion en invoker.
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;
revoke all on function public.get_sinjira_runtime_health() from public,anon;
grant execute on function public.get_sinjira_runtime_health() to authenticated,service_role;
revoke all on function public.fracture_engine_health() from public,anon;
grant execute on function public.fracture_engine_health() to authenticated,service_role;
