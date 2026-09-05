begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

-- Contrat dérivé de l'état production vérifié le 2026-09-05.
-- Une table RLS sans policy est ici volontairement server-only et deny-by-default.
-- Toute nouvelle table de cette catégorie doit être classifiée explicitement.
-- `service_role_allowed` est une permission maximale, jamais une obligation :
-- retirer un privilège service_role reste compatible avec ce contrat.
create temporary table expected_server_only_rls (
  schema_name text not null,
  table_name text not null,
  access_class text not null check (access_class in ('strict_no_direct','service_role_allowed')),
  primary key (schema_name,table_name)
) on commit drop;

insert into expected_server_only_rls(schema_name,table_name,access_class) values
  ('private','account_identities','strict_no_direct'),
  ('private','conscience_entries','strict_no_direct'),
  ('private','conscience_vault_audit','strict_no_direct'),
  ('private','conscience_vault_sessions','strict_no_direct'),
  ('private','moderation_appeals','strict_no_direct'),
  ('private','moderation_decisions','strict_no_direct'),
  ('private','parallel_identities','strict_no_direct'),
  ('private','personal_ai_audit','strict_no_direct'),
  ('private','personal_ai_settings','strict_no_direct'),
  ('private','personal_ai_source_permissions','strict_no_direct'),
  ('private','privacy_incident_register','strict_no_direct'),
  ('private','privacy_legal_holds','strict_no_direct'),
  ('private','privacy_requests','strict_no_direct'),
  ('private','safety_escalation_cases','strict_no_direct'),

  ('private','preorder_admin_workflow','service_role_allowed'),
  ('public','activation_codes','service_role_allowed'),
  ('public','admin_audit_log','service_role_allowed'),
  ('public','character_generation_runs','service_role_allowed'),
  ('public','dating_connections','service_role_allowed'),
  ('public','dating_meet_requests','service_role_allowed'),
  ('public','dating_messages','service_role_allowed'),
  ('public','fracture_engine_actions','service_role_allowed'),
  ('public','fracture_engine_cards','service_role_allowed'),
  ('public','fracture_engine_events','service_role_allowed'),
  ('public','fracture_engine_games','service_role_allowed'),
  ('public','fracture_engine_rounds','service_role_allowed'),
  ('public','fracture_engine_seats','service_role_allowed'),
  ('public','fracture_engine_votes','service_role_allowed'),
  ('public','internal_contribution_ownership','service_role_allowed'),
  ('public','internal_gameplay_contributions','service_role_allowed'),
  ('public','license_batches','service_role_allowed'),
  ('public','license_redemptions','service_role_allowed'),
  ('public','life_story_cleanup_tasks','service_role_allowed'),
  ('public','life_story_delivery_links','service_role_allowed'),
  ('public','life_story_exports','service_role_allowed'),
  ('public','life_story_posthumous_cases','service_role_allowed'),
  ('public','life_story_posthumous_contests','service_role_allowed'),
  ('public','life_story_report_codes','service_role_allowed'),
  ('public','preorder_commercial_plans','service_role_allowed'),
  ('public','preorder_fulfillment_settings','service_role_allowed'),
  ('public','preorder_pickup_points','service_role_allowed'),
  ('public','preorder_sales_announcements','service_role_allowed'),
  ('public','preorder_shipping_zones','service_role_allowed'),
  ('public','security_push_endpoints','service_role_allowed'),
  ('public','sinjira_canon_context','service_role_allowed'),
  ('public','sinjira_points_accounts','service_role_allowed'),
  ('public','sinjira_points_ledger','service_role_allowed'),
  ('public','sinjira_security_settings','service_role_allowed'),
  ('public','social_suspensions','service_role_allowed');

select plan(9);

select is(
  (select count(*)::int from expected_server_only_rls),
  49,
  'le contrat classifie exactement les 49 tables RLS sans policy observées'
);

select is(
  (select count(*)::int from expected_server_only_rls where access_class='strict_no_direct'),
  14,
  '14 tables ultra-sensibles interdisent aussi le CRUD direct service_role'
);

select is(
  (select count(*)::int from expected_server_only_rls where access_class='service_role_allowed'),
  35,
  '35 tables serveur peuvent conserver un CRUD direct service_role explicitement autorisé'
);

select is(
  (
    select count(*)::int
    from expected_server_only_rls e
    left join pg_namespace n on n.nspname=e.schema_name
    left join pg_class c on c.relnamespace=n.oid and c.relname=e.table_name and c.relkind='r'
    where c.oid is null
  ),
  0,
  'toutes les tables server-only classifiées existent dans le schéma reconstruit'
);

select is(
  (
    select count(*)::int
    from expected_server_only_rls e
    join pg_namespace n on n.nspname=e.schema_name
    join pg_class c on c.relnamespace=n.oid and c.relname=e.table_name and c.relkind='r'
    where not c.relrowsecurity
       or exists(select 1 from pg_policy p where p.polrelid=c.oid)
  ),
  0,
  'toutes les tables classifiées restent RLS sans policy et donc deny-by-default'
);

select is(
  (
    select count(*)::int
    from pg_class c
    join pg_namespace n on n.oid=c.relnamespace
    where n.nspname in ('public','private')
      and c.relkind='r'
      and c.relrowsecurity
      and not exists(select 1 from pg_policy p where p.polrelid=c.oid)
      and not exists(
        select 1
        from expected_server_only_rls e
        where e.schema_name=n.nspname and e.table_name=c.relname
      )
  ),
  0,
  'aucune nouvelle table RLS sans policy ne peut apparaître sans classification explicite'
);

select is(
  (
    select count(*)::int
    from pg_class c
    join pg_namespace n on n.oid=c.relnamespace
    join expected_server_only_rls e on e.schema_name=n.nspname and e.table_name=c.relname
    where c.relkind='r'
      and (
        has_table_privilege('anon',c.oid,'SELECT')
        or has_table_privilege('anon',c.oid,'INSERT')
        or has_table_privilege('anon',c.oid,'UPDATE')
        or has_table_privilege('anon',c.oid,'DELETE')
        or has_table_privilege('authenticated',c.oid,'SELECT')
        or has_table_privilege('authenticated',c.oid,'INSERT')
        or has_table_privilege('authenticated',c.oid,'UPDATE')
        or has_table_privilege('authenticated',c.oid,'DELETE')
      )
  ),
  0,
  'aucune table server-only classifiée n’accorde de CRUD direct à anon/authenticated'
);

select is(
  (
    select count(*)::int
    from expected_server_only_rls e
    join pg_namespace n on n.nspname=e.schema_name
    join pg_class c on c.relnamespace=n.oid and c.relname=e.table_name and c.relkind='r'
    where e.access_class='strict_no_direct'
      and (
        has_table_privilege('service_role',c.oid,'SELECT')
        or has_table_privilege('service_role',c.oid,'INSERT')
        or has_table_privilege('service_role',c.oid,'UPDATE')
        or has_table_privilege('service_role',c.oid,'DELETE')
      )
  ),
  0,
  'les 14 tables ultra-sensibles restent sans CRUD direct même pour service_role'
);

select is(
  (
    select count(*)::int
    from pg_class c
    join pg_namespace n on n.oid=c.relnamespace
    where n.nspname in ('public','private')
      and c.relkind='r'
      and c.relrowsecurity
      and not exists(select 1 from pg_policy p where p.polrelid=c.oid)
      and (
        has_table_privilege('service_role',c.oid,'SELECT')
        or has_table_privilege('service_role',c.oid,'INSERT')
        or has_table_privilege('service_role',c.oid,'UPDATE')
        or has_table_privilege('service_role',c.oid,'DELETE')
      )
      and not exists(
        select 1
        from expected_server_only_rls e
        where e.schema_name=n.nspname
          and e.table_name=c.relname
          and e.access_class='service_role_allowed'
      )
  ),
  0,
  'tout CRUD direct service_role sur une table RLS sans policy doit appartenir à l’allowlist explicite'
);

select * from finish();
rollback;
