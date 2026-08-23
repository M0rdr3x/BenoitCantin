create schema if not exists sinjira_parallel_user_internal;
revoke all on schema sinjira_parallel_user_internal from public;
grant usage on schema sinjira_parallel_user_internal to authenticated, service_role;

comment on schema sinjira_parallel_user_internal is
  'Implémentations privilégiées des RPC utilisateur du Monde parallèle. Identité parallèle et compte réel restent séparés.';

do $$
declare
  r record;
  v_count integer;
  v_call_args text;
  v_body text;
  v_targets text[] := array[
    'parallel_my_context',
    'parallel_my_identity',
    'parallel_save_cycle_response',
    'parallel_set_my_identity'
  ];
begin
  select count(*) into v_count
  from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.prosecdef and p.prokind='f' and p.proname=any(v_targets);

  if v_count <> 4 then
    raise exception 'V24.5.16 attend 4 RPC utilisateur Monde parallèle SECURITY DEFINER publiques; trouvé %', v_count;
  end if;

  for r in
    select p.oid,p.proname,pg_get_function_arguments(p.oid) all_arguments,
           oidvectortypes(p.proargtypes) arg_types,pg_get_function_result(p.oid) result_type,p.pronargs
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.prosecdef and p.prokind='f' and p.proname=any(v_targets)
    order by p.proname,p.oid
  loop
    select coalesce(string_agg(format('$%s',g),', ' order by g),'') into v_call_args
    from generate_series(1,r.pronargs) g;

    execute format('alter function public.%I(%s) set schema sinjira_parallel_user_internal',r.proname,r.arg_types);
    execute format('revoke all on function sinjira_parallel_user_internal.%I(%s) from public, anon',r.proname,r.arg_types);
    execute format('grant execute on function sinjira_parallel_user_internal.%I(%s) to authenticated, service_role',r.proname,r.arg_types);

    if r.result_type like 'TABLE(%' then
      v_body:=format('select * from sinjira_parallel_user_internal.%I(%s)',r.proname,v_call_args);
    else
      v_body:=format('select sinjira_parallel_user_internal.%I(%s)',r.proname,v_call_args);
    end if;

    execute format(
      'create function public.%I(%s) returns %s language sql security invoker set search_path = '''' as %L',
      r.proname,r.all_arguments,r.result_type,v_body
    );
    execute format('revoke all on function public.%I(%s) from public, anon',r.proname,r.arg_types);
    execute format('grant execute on function public.%I(%s) to authenticated, service_role',r.proname,r.arg_types);
  end loop;
end
$$;
