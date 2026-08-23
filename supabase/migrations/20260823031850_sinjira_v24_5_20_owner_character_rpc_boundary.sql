create schema if not exists sinjira_owner_internal;
revoke all on schema sinjira_owner_internal from public, anon;
grant usage on schema sinjira_owner_internal to authenticated, service_role;

do $$
declare
  r record;
  v_count integer;
begin
  select count(*) into v_count
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.prokind='f' and p.prosecdef and p.proname='ensure_sinjira_owner_character';
  if v_count <> 1 then
    raise exception 'V24.5.20 attend ensure_sinjira_owner_character SECURITY DEFINER publique; trouvé %',v_count;
  end if;

  select p.oid,p.proname,pg_get_function_arguments(p.oid) all_arguments,
         oidvectortypes(p.proargtypes) arg_types,pg_get_function_result(p.oid) result_type
  into r
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.prokind='f' and p.prosecdef and p.proname='ensure_sinjira_owner_character';

  execute format('alter function public.%I(%s) set schema sinjira_owner_internal',r.proname,r.arg_types);
  execute format('revoke all on function sinjira_owner_internal.%I(%s) from public, anon',r.proname,r.arg_types);
  execute format('grant execute on function sinjira_owner_internal.%I(%s) to authenticated, service_role',r.proname,r.arg_types);

  execute format(
    'create function public.%I(%s) returns %s language sql security invoker set search_path = '''' as %L',
    r.proname,r.all_arguments,r.result_type,'select sinjira_owner_internal.ensure_sinjira_owner_character()'
  );
  execute format('revoke all on function public.%I(%s) from public, anon',r.proname,r.arg_types);
  execute format('grant execute on function public.%I(%s) to authenticated, service_role',r.proname,r.arg_types);
end
$$;
