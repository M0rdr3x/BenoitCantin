create schema if not exists sinjira_rls_internal;
revoke all on schema sinjira_rls_internal from public, anon;
grant usage on schema sinjira_rls_internal to authenticated, service_role;

comment on schema sinjira_rls_internal is
  'Implémentations privilégiées des helpers de politiques RLS et gardes structurels. Hors schéma API public; wrappers public SECURITY INVOKER seulement.';

do $$
declare
  r record;
  v_count integer;
  v_call_args text;
  v_body text;
  v_targets text[] := array[
    'is_fracture_party_member',
    'moderation_content_visible',
    'sinjira_can_social_interact',
    'sinjira_content_allowed',
    'sinjira_cycle_allowed',
    'sinjira_mfa_access_allowed',
    'sinjira_my_age_band',
    'social_is_blocked',
    'social_is_suspended'
  ];
begin
  select count(*) into v_count
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.prokind='f' and p.prosecdef and p.proname=any(v_targets);

  if v_count <> 9 then
    raise exception 'V24.5.22 attend 9 helpers SECURITY DEFINER publics; trouvé %',v_count;
  end if;

  for r in
    select p.oid,p.proname,pg_get_function_arguments(p.oid) all_arguments,
           oidvectortypes(p.proargtypes) arg_types,pg_get_function_result(p.oid) result_type,p.pronargs,
           p.provolatile
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.prokind='f' and p.prosecdef and p.proname=any(v_targets)
    order by p.proname,p.oid
  loop
    select coalesce(string_agg(format('$%s',g),', ' order by g),'') into v_call_args
    from generate_series(1,r.pronargs) g;

    execute format('alter function public.%I(%s) set schema sinjira_rls_internal',r.proname,r.arg_types);
    execute format('revoke all on function sinjira_rls_internal.%I(%s) from public, anon',r.proname,r.arg_types);
    execute format('grant execute on function sinjira_rls_internal.%I(%s) to authenticated, service_role',r.proname,r.arg_types);

    v_body:=format('select sinjira_rls_internal.%I(%s)',r.proname,v_call_args);
    execute format(
      'create function public.%I(%s) returns %s language sql stable security invoker set search_path = '''' as %L',
      r.proname,r.all_arguments,r.result_type,v_body
    );
    execute format('revoke all on function public.%I(%s) from public, anon',r.proname,r.arg_types);
    execute format('grant execute on function public.%I(%s) to authenticated, service_role',r.proname,r.arg_types);
  end loop;
end
$$;
