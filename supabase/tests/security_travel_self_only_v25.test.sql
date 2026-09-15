-- SINJIRA V25 — contrat A1 de frontière self-only du Mode Voyage
--
-- Vérifie la frontière réellement chargée après V24.5.10 + V25 :
-- wrappers public SECURITY INVOKER, implémentations privilégiées internes,
-- propriétaire dérivé de auth.uid() et annulation bornée à id + user_id.
-- Aucune donnée de voyage n'est créée par ce test.
-- Principe : L'HUMAIN AVANT TOUT. PROTÉGER SANS SURVEILLER.

begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(20);

select ok(
  (select c.relrowsecurity
     from pg_catalog.pg_class c
     join pg_catalog.pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname = 'security_travel_plans'),
  'Mode Voyage: RLS active sur security_travel_plans'
);

select ok(
  has_table_privilege('authenticated', 'public.security_travel_plans', 'SELECT'),
  'Mode Voyage: authenticated conserve uniquement la lecture médiée par RLS'
);

select ok(
  not has_table_privilege('authenticated', 'public.security_travel_plans', 'INSERT'),
  'SELF_ONLY_DIRECT_DML_FORBIDDEN: pas INSERT direct authenticated'
);
select ok(
  not has_table_privilege('authenticated', 'public.security_travel_plans', 'UPDATE'),
  'SELF_ONLY_DIRECT_DML_FORBIDDEN: pas UPDATE direct authenticated'
);
select ok(
  not has_table_privilege('authenticated', 'public.security_travel_plans', 'DELETE'),
  'SELF_ONLY_DIRECT_DML_FORBIDDEN: pas DELETE direct authenticated'
);

select ok(
  not has_table_privilege('anon', 'public.security_travel_plans', 'SELECT')
  and not has_table_privilege('anon', 'public.security_travel_plans', 'INSERT')
  and not has_table_privilege('anon', 'public.security_travel_plans', 'UPDATE')
  and not has_table_privilege('anon', 'public.security_travel_plans', 'DELETE'),
  'Mode Voyage: anon ne peut pas accéder à la table'
);

select is(
  (select count(*)
     from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'security_travel_plans'
      and policyname = 'security_travel_plans_read_own'
      and cmd = 'SELECT'
      and 'authenticated' = any(roles)),
  1::bigint,
  'Mode Voyage: une seule politique de lecture self-only nommée'
);

select ok(
  (select position('auth.uid()' in coalesce(qual, '')) > 0
          and position('user_id' in coalesce(qual, '')) > 0
     from pg_catalog.pg_policies
    where schemaname = 'public'
      and tablename = 'security_travel_plans'
      and policyname = 'security_travel_plans_read_own'
      and cmd = 'SELECT'),
  'Mode Voyage: la politique RLS relie auth.uid() à user_id'
);

select ok(
  not has_function_privilege(
    'anon',
    'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)',
    'EXECUTE'
  ),
  'SELF_ONLY_ANON_CREATE_RPC_FORBIDDEN'
);

select ok(
  not has_function_privilege('anon', 'public.security_cancel_travel_plan(uuid)', 'EXECUTE'),
  'SELF_ONLY_ANON_CANCEL_RPC_FORBIDDEN'
);

select ok(
  has_function_privilege(
    'authenticated',
    'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)',
    'EXECUTE'
  ),
  'Mode Voyage: authenticated peut appeler le wrapper de création contrôlé'
);

select ok(
  has_function_privilege('authenticated', 'public.security_cancel_travel_plan(uuid)', 'EXECUTE'),
  'Mode Voyage: authenticated peut appeler le wrapper d annulation contrôlé'
);

select ok(
  not (select p.prosecdef
         from pg_catalog.pg_proc p
         join pg_catalog.pg_namespace n on n.oid = p.pronamespace
        where n.nspname = 'public'
          and p.oid = 'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure),
  'Mode Voyage: wrapper public de création reste SECURITY INVOKER'
);

select ok(
  not (select p.prosecdef
         from pg_catalog.pg_proc p
         join pg_catalog.pg_namespace n on n.oid = p.pronamespace
        where n.nspname = 'public'
          and p.oid = 'public.security_cancel_travel_plan(uuid)'::regprocedure),
  'Mode Voyage: wrapper public d annulation reste SECURITY INVOKER'
);

select ok(
  (select p.prosecdef
     from pg_catalog.pg_proc p
     join pg_catalog.pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'sinjira_security_internal'
      and p.oid = 'sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure),
  'Mode Voyage: implémentation interne de création garde SECURITY DEFINER'
);

select ok(
  (select p.prosecdef
     from pg_catalog.pg_proc p
     join pg_catalog.pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'sinjira_security_internal'
      and p.oid = 'sinjira_security_internal.security_cancel_travel_plan(uuid)'::regprocedure),
  'Mode Voyage: implémentation interne d annulation garde SECURITY DEFINER'
);

select ok(
  position(
    'v_useruuid:=auth.uid();'
    in regexp_replace(
      lower(pg_catalog.pg_get_functiondef(
        'sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
      )),
      '[[:space:]]+', '', 'g'
    )
  ) > 0
  and position(
    'values(v_user,'
    in regexp_replace(
      lower(pg_catalog.pg_get_functiondef(
        'sinjira_security_internal.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
      )),
      '[[:space:]]+', '', 'g'
    )
  ) > 0,
  'SELF_ONLY_CREATE_RPC_MUST_DERIVE_OWNER_FROM_AUTH_UID'
);

select ok(
  position(
    'v_useruuid:=auth.uid();'
    in regexp_replace(
      lower(pg_catalog.pg_get_functiondef(
        'sinjira_security_internal.security_cancel_travel_plan(uuid)'::regprocedure
      )),
      '[[:space:]]+', '', 'g'
    )
  ) > 0
  and position(
    'whereid=p_plan_idanduser_id=v_user'
    in regexp_replace(
      lower(pg_catalog.pg_get_functiondef(
        'sinjira_security_internal.security_cancel_travel_plan(uuid)'::regprocedure
      )),
      '[[:space:]]+', '', 'g'
    )
  ) > 0,
  'SELF_ONLY_CANCEL_RPC_MUST_MATCH_PLAN_AND_CALLER'
);

select ok(
  position(
    'sinjira_security_internal.security_create_travel_plan'
    in lower(pg_catalog.pg_get_functiondef(
      'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
    ))
  ) > 0,
  'Mode Voyage: wrapper public de création délègue uniquement à l implémentation interne'
);

select ok(
  position(
    'sinjira_security_internal.security_cancel_travel_plan'
    in lower(pg_catalog.pg_get_functiondef('public.security_cancel_travel_plan(uuid)'::regprocedure))
  ) > 0,
  'Mode Voyage: wrapper public d annulation délègue uniquement à l implémentation interne'
);

select * from finish();
rollback;
