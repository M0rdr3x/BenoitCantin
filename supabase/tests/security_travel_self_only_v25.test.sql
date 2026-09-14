-- SINJIRA V25 — contrat A1 de frontière self-only du Mode Voyage
--
-- Ce test est destiné à une base Supabase locale/migrée. Il ne crée aucun voyage,
-- n'ajoute aucune donnée personnelle et vérifie la frontière d'autorisation à
-- partir des catalogues PostgreSQL et des définitions RPC effectivement chargées.
-- Principe : L'HUMAIN AVANT TOUT. PROTÉGER SANS SURVEILLER.

begin;

do $$
declare
  v_rls boolean;
  v_policy_count integer;
  v_policy_qual text;
  v_create_def text;
  v_cancel_def text;
begin
  select c.relrowsecurity
    into v_rls
    from pg_catalog.pg_class c
    join pg_catalog.pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public'
     and c.relname = 'security_travel_plans';

  if v_rls is distinct from true then
    raise exception 'SELF_ONLY_RLS_REQUIRED';
  end if;

  if not has_table_privilege('authenticated', 'public.security_travel_plans', 'SELECT') then
    raise exception 'SELF_ONLY_AUTHENTICATED_SELECT_REQUIRED';
  end if;

  if has_table_privilege('authenticated', 'public.security_travel_plans', 'INSERT')
     or has_table_privilege('authenticated', 'public.security_travel_plans', 'UPDATE')
     or has_table_privilege('authenticated', 'public.security_travel_plans', 'DELETE') then
    raise exception 'SELF_ONLY_DIRECT_DML_FORBIDDEN';
  end if;

  if has_table_privilege('anon', 'public.security_travel_plans', 'SELECT')
     or has_table_privilege('anon', 'public.security_travel_plans', 'INSERT')
     or has_table_privilege('anon', 'public.security_travel_plans', 'UPDATE')
     or has_table_privilege('anon', 'public.security_travel_plans', 'DELETE') then
    raise exception 'SELF_ONLY_ANON_TABLE_ACCESS_FORBIDDEN';
  end if;

  select count(*), max(qual)
    into v_policy_count, v_policy_qual
    from pg_catalog.pg_policies
   where schemaname = 'public'
     and tablename = 'security_travel_plans'
     and policyname = 'security_travel_plans_read_own'
     and cmd = 'SELECT'
     and 'authenticated' = any(roles);

  if v_policy_count <> 1 then
    raise exception 'SELF_ONLY_READ_POLICY_REQUIRED';
  end if;

  if position('auth.uid()' in coalesce(v_policy_qual, '')) = 0
     or position('user_id' in coalesce(v_policy_qual, '')) = 0 then
    raise exception 'SELF_ONLY_READ_POLICY_MUST_BIND_AUTH_UID';
  end if;

  if has_function_privilege(
      'anon',
      'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)',
      'EXECUTE'
    ) then
    raise exception 'SELF_ONLY_ANON_CREATE_RPC_FORBIDDEN';
  end if;

  if has_function_privilege(
      'anon',
      'public.security_cancel_travel_plan(uuid)',
      'EXECUTE'
    ) then
    raise exception 'SELF_ONLY_ANON_CANCEL_RPC_FORBIDDEN';
  end if;

  if not has_function_privilege(
      'authenticated',
      'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)',
      'EXECUTE'
    ) then
    raise exception 'SELF_ONLY_AUTHENTICATED_CREATE_RPC_REQUIRED';
  end if;

  if not has_function_privilege(
      'authenticated',
      'public.security_cancel_travel_plan(uuid)',
      'EXECUTE'
    ) then
    raise exception 'SELF_ONLY_AUTHENTICATED_CANCEL_RPC_REQUIRED';
  end if;

  select pg_catalog.pg_get_functiondef(
    'public.security_create_travel_plan(timestamptz,timestamptz,text[],boolean)'::regprocedure
  ) into v_create_def;

  if position('auth.uid()' in v_create_def) = 0
     or position('user_id,starts_at,ends_at,destinations,multi_country,delete_after' in replace(v_create_def, ' ', '')) = 0
     or position('values(v_user,' in replace(lower(v_create_def), ' ', '')) = 0 then
    raise exception 'SELF_ONLY_CREATE_RPC_MUST_DERIVE_OWNER_FROM_AUTH_UID';
  end if;

  select pg_catalog.pg_get_functiondef(
    'public.security_cancel_travel_plan(uuid)'::regprocedure
  ) into v_cancel_def;

  if position('auth.uid()' in v_cancel_def) = 0
     or position('whereid=p_plan_idanduser_id=v_user' in replace(replace(lower(v_cancel_def), ' ', ''), E'\n', '')) = 0 then
    raise exception 'SELF_ONLY_CANCEL_RPC_MUST_MATCH_PLAN_AND_CALLER';
  end if;
end;
$$;

rollback;
