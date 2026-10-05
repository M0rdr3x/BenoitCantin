-- SINJIRA V25 — contrat A1 : rétention interne != droit de lecture client

begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(28);

select ok(
  (select c.relrowsecurity
     from pg_catalog.pg_class c
     join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname = 'security_travel_plans'),
  'Mode Voyage: RLS active'
);

select ok(
  has_table_privilege('authenticated', 'public.security_travel_plans', 'SELECT'),
  'authenticated conserve uniquement la lecture RLS'
);

select ok(
  not has_table_privilege('authenticated', 'public.security_travel_plans', 'INSERT')
  and not has_table_privilege('authenticated', 'public.security_travel_plans', 'UPDATE')
  and not has_table_privilege('authenticated', 'public.security_travel_plans', 'DELETE'),
  'authenticated ne peut pas modifier directement les voyages'
);

select ok(
  not has_table_privilege('anon', 'public.security_travel_plans', 'SELECT')
  and not has_table_privilege('anon', 'public.security_travel_plans', 'INSERT')
  and not has_table_privilege('anon', 'public.security_travel_plans', 'UPDATE')
  and not has_table_privilege('anon', 'public.security_travel_plans', 'DELETE'),
  'anon ne peut pas accéder aux voyages'
);

select is(
  (select count(*)
     from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'security_travel_plans'
      and cmd = 'SELECT'
      and 'authenticated' = any(roles)),
  1::bigint,
  'une seule politique SELECT authenticated protège les voyages'
);

select is(
  (select policyname
     from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'security_travel_plans'
      and cmd = 'SELECT'
      and 'authenticated' = any(roles)),
  'security_travel_plans_read_own'::name,
  'la politique canonique reste security_travel_plans_read_own'
);

select ok(
  (select position('auth.uid()' in lower(coalesce(qual, ''))) > 0
     from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'security_travel_plans'
      and policyname = 'security_travel_plans_read_own'),
  'la politique lie la lecture à auth.uid()'
);

select ok(
  (select position('user_id' in lower(coalesce(qual, ''))) > 0
     from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'security_travel_plans'
      and policyname = 'security_travel_plans_read_own'),
  'la politique lie auth.uid() au propriétaire de ligne'
);

select ok(
  (select position('status' in lower(coalesce(qual, ''))) > 0
          and position('active' in lower(coalesce(qual, ''))) > 0
     from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'security_travel_plans'
      and policyname = 'security_travel_plans_read_own'),
  'les voyages annulés ne sont jamais lisibles par le client'
);

select ok(
  (select position('ends_at' in lower(coalesce(qual, ''))) > 0
          and position('statement_timestamp()' in lower(coalesce(qual, ''))) > 0
     from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'security_travel_plans'
      and policyname = 'security_travel_plans_read_own'),
  'les voyages terminés ne sont jamais lisibles par le client'
);

select ok(
  (select position('delete_after' in lower(coalesce(qual, ''))) = 0
     from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'security_travel_plans'
      and policyname = 'security_travel_plans_read_own'),
  'delete_after reste une donnée de rétention serveur, jamais une autorisation client'
);

select ok(
  has_table_privilege('service_role', 'public.security_travel_plans', 'SELECT')
  and has_table_privilege('service_role', 'public.security_travel_plans', 'DELETE'),
  'service_role conserve les droits nécessaires aux chemins serveur et à la purge'
);

select ok(
  (select permissive = 'PERMISSIVE'
     from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'security_travel_plans'
      and policyname = 'security_travel_plans_read_own'),
  'la politique conserve la sémantique PostgreSQL attendue'
);

select ok(
  to_regprocedure('public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)') is not null,
  'le wrapper public de création existe'
);

select ok(
  not (select p.prosecdef
         from pg_catalog.pg_proc p
        where p.oid = 'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure),
  'le wrapper public de création reste SECURITY INVOKER'
);

select ok(
  position('jsonb_build_object' in lower(pg_catalog.pg_get_functiondef(
    'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
  ))) > 0,
  'le wrapper de création construit une réponse explicite'
);

select ok(
  position('delete_after' in lower(pg_catalog.pg_get_functiondef(
    'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
  ))) = 0
  and position('user_id' in lower(pg_catalog.pg_get_functiondef(
    'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
  ))) = 0
  and position('created_at' in lower(pg_catalog.pg_get_functiondef(
    'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
  ))) = 0
  and position('updated_at' in lower(pg_catalog.pg_get_functiondef(
    'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
  ))) = 0,
  'le wrapper de création ne réexpose aucune métadonnée interne'
);

select ok(
  not has_function_privilege('anon', 'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)', 'EXECUTE')
  and has_function_privilege('authenticated', 'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)', 'EXECUTE'),
  'la création reste réservée aux comptes authentifiés'
);

select ok(
  to_regprocedure('public.security_cancel_travel_plan(uuid)') is not null,
  'le wrapper public d’annulation existe'
);

select ok(
  not (select p.prosecdef
         from pg_catalog.pg_proc p
        where p.oid = 'public.security_cancel_travel_plan(uuid)'::regprocedure),
  'le wrapper public d’annulation reste SECURITY INVOKER'
);

select ok(
  position('jsonb_build_object' in lower(pg_catalog.pg_get_functiondef(
    'public.security_cancel_travel_plan(uuid)'::regprocedure
  ))) > 0
  and position('delete_after' in lower(pg_catalog.pg_get_functiondef(
    'public.security_cancel_travel_plan(uuid)'::regprocedure
  ))) = 0
  and position('user_id' in lower(pg_catalog.pg_get_functiondef(
    'public.security_cancel_travel_plan(uuid)'::regprocedure
  ))) = 0
  and position('destinations' in lower(pg_catalog.pg_get_functiondef(
    'public.security_cancel_travel_plan(uuid)'::regprocedure
  ))) = 0,
  'le wrapper d’annulation ne renvoie que l’accusé minimal'
);

select ok(
  not has_function_privilege('anon', 'public.security_cancel_travel_plan(uuid)', 'EXECUTE')
  and has_function_privilege('authenticated', 'public.security_cancel_travel_plan(uuid)', 'EXECUTE'),
  'l’annulation reste réservée aux comptes authentifiés'
);

select ok(
  to_regprocedure('sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)') is not null,
  'l’implémentation interne de création existe'
);

select ok(
  not has_function_privilege('anon', 'sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)', 'EXECUTE')
  and has_function_privilege('authenticated', 'sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)', 'EXECUTE'),
  'l’appel direct interne reste borné aux comptes authentifiés'
);

select ok(
  position('jsonb_build_object' in lower(pg_catalog.pg_get_functiondef(
    'sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
  ))) > 0
  and position('return to_jsonb(v_row)' in lower(pg_catalog.pg_get_functiondef(
    'sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
  ))) = 0,
  'l’implémentation interne de création ne renvoie plus la ligne complète'
);

select ok(
  to_regprocedure('sinjira_security_internal.security_cancel_travel_plan(uuid)') is not null,
  'l’implémentation interne d’annulation existe'
);

select ok(
  not has_function_privilege('anon', 'sinjira_security_internal.security_cancel_travel_plan(uuid)', 'EXECUTE')
  and has_function_privilege('authenticated', 'sinjira_security_internal.security_cancel_travel_plan(uuid)', 'EXECUTE'),
  'l’annulation interne directe reste bornée aux comptes authentifiés'
);

select ok(
  position('jsonb_build_object' in lower(pg_catalog.pg_get_functiondef(
    'sinjira_security_internal.security_cancel_travel_plan(uuid)'::regprocedure
  ))) > 0
  and position('return to_jsonb(v_row)' in lower(pg_catalog.pg_get_functiondef(
    'sinjira_security_internal.security_cancel_travel_plan(uuid)'::regprocedure
  ))) = 0,
  'l’implémentation interne d’annulation ne renvoie plus la ligne complète'
);

select * from finish();
rollback;
