-- SINJIRA™ V24.4.19 — contrat de sécurité interne
--
-- Objectif : rendre explicite et testable le fait que les tables internes
-- sensibles sont accessibles uniquement via les RPC/Edge Functions prévues.
-- Cette migration ne rend aucune donnée publique et ne change aucune règle
-- métier. Elle réaffirme les révocations déjà attendues en production.

begin;

-- Tables volontairement scellées : aucune lecture/écriture directe depuis un
-- navigateur anonyme ou authentifié. Les opérations légitimes passent par les
-- fonctions contrôlées du backend.
revoke all privileges on table public.character_generation_runs from public, anon, authenticated;
revoke all privileges on table public.fracture_engine_actions from public, anon, authenticated;
revoke all privileges on table public.fracture_engine_cards from public, anon, authenticated;
revoke all privileges on table public.fracture_engine_events from public, anon, authenticated;
revoke all privileges on table public.fracture_engine_games from public, anon, authenticated;
revoke all privileges on table public.fracture_engine_rounds from public, anon, authenticated;
revoke all privileges on table public.fracture_engine_seats from public, anon, authenticated;
revoke all privileges on table public.fracture_engine_votes from public, anon, authenticated;
revoke all privileges on table public.internal_admin_users from public, anon, authenticated;
revoke all privileges on table public.internal_contribution_ownership from public, anon, authenticated;
revoke all privileges on table public.internal_gameplay_contributions from public, anon, authenticated;
revoke all privileges on table public.sinjira_canon_context from public, anon, authenticated;
revoke all privileges on table public.sinjira_security_settings from public, anon, authenticated;
revoke all privileges on table public.social_suspensions from public, anon, authenticated;

-- L'état brut de Fracture ne doit jamais être appelable depuis PostgREST par un
-- navigateur. Seule la couche serveur privilégiée peut l'utiliser; l'état
-- exposé au joueur reste fracture_engine_get_state_safe / état assaini.
revoke all on function public._fracture_engine_get_state_raw(text) from public, anon, authenticated;
grant execute on function public._fracture_engine_get_state_raw(text) to service_role;

-- Diagnostic interne du contrat. Il est réservé au service_role afin de ne pas
-- agrandir la surface RPC publique. Un résultat ok=false indique une dérive de
-- privilèges qui doit bloquer une livraison.
create or replace function public.sinjira_security_contract_health()
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, public
as $$
declare
  sealed_tables constant text[] := array[
    'character_generation_runs',
    'fracture_engine_actions',
    'fracture_engine_cards',
    'fracture_engine_events',
    'fracture_engine_games',
    'fracture_engine_rounds',
    'fracture_engine_seats',
    'fracture_engine_votes',
    'internal_admin_users',
    'internal_contribution_ownership',
    'internal_gameplay_contributions',
    'sinjira_canon_context',
    'sinjira_security_settings',
    'social_suspensions'
  ];
  table_name text;
  violations text[] := array[]::text[];
  raw_anon boolean;
  raw_authenticated boolean;
  raw_service boolean;
begin
  foreach table_name in array sealed_tables loop
    if pg_catalog.has_table_privilege('anon', format('public.%I', table_name), 'SELECT')
       or pg_catalog.has_table_privilege('anon', format('public.%I', table_name), 'INSERT')
       or pg_catalog.has_table_privilege('anon', format('public.%I', table_name), 'UPDATE')
       or pg_catalog.has_table_privilege('anon', format('public.%I', table_name), 'DELETE')
       or pg_catalog.has_table_privilege('authenticated', format('public.%I', table_name), 'SELECT')
       or pg_catalog.has_table_privilege('authenticated', format('public.%I', table_name), 'INSERT')
       or pg_catalog.has_table_privilege('authenticated', format('public.%I', table_name), 'UPDATE')
       or pg_catalog.has_table_privilege('authenticated', format('public.%I', table_name), 'DELETE') then
      violations := array_append(violations, table_name);
    end if;
  end loop;

  raw_anon := pg_catalog.has_function_privilege(
    'anon', 'public._fracture_engine_get_state_raw(text)', 'EXECUTE'
  );
  raw_authenticated := pg_catalog.has_function_privilege(
    'authenticated', 'public._fracture_engine_get_state_raw(text)', 'EXECUTE'
  );
  raw_service := pg_catalog.has_function_privilege(
    'service_role', 'public._fracture_engine_get_state_raw(text)', 'EXECUTE'
  );

  return jsonb_build_object(
    'ok', cardinality(violations) = 0 and not raw_anon and not raw_authenticated and raw_service,
    'security_version', '24.4.19',
    'sealed_table_count', cardinality(sealed_tables),
    'sealed_table_violations', to_jsonb(violations),
    'raw_state_internal_only', not raw_anon and not raw_authenticated and raw_service
  );
end;
$$;

revoke all on function public.sinjira_security_contract_health() from public, anon, authenticated;
grant execute on function public.sinjira_security_contract_health() to service_role;

commit;
