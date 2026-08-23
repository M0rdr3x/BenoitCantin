create schema if not exists sinjira_fracture_internal;
revoke all on schema sinjira_fracture_internal from public, anon;
grant usage on schema sinjira_fracture_internal to authenticated, service_role;

comment on schema sinjira_fracture_internal is
  'Implémentations privilégiées des RPC joueur Fracture. Les helpers RLS restent dans public; wrappers public SECURITY INVOKER seulement.';

do $$
declare
  r record;
  v_count integer;
  v_call_args text;
  v_body text;
  v_targets text[] := array[
    'create_fracture_party',
    'fracture_engine_get_state',
    'fracture_engine_pick',
    'fracture_engine_start',
    'fracture_engine_submit_accusation',
    'fracture_engine_submit_keep',
    'fracture_engine_submit_report',
    'join_fracture_party'
  ];
begin
  select count(*) into v_count
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.prokind='f' and p.prosecdef and p.proname=any(v_targets);

  if v_count <> 8 then
    raise exception 'V24.5.21 attend 8 RPC joueur Fracture SECURITY DEFINER publiques; trouvé %',v_count;
  end if;

  for r in
    select p.oid,p.proname,pg_get_function_arguments(p.oid) all_arguments,
           oidvectortypes(p.proargtypes) arg_types,pg_get_function_result(p.oid) result_type,p.pronargs
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.prokind='f' and p.prosecdef and p.proname=any(v_targets)
    order by p.proname,p.oid
  loop
    select coalesce(string_agg(format('$%s',g),', ' order by g),'') into v_call_args
    from generate_series(1,r.pronargs) g;

    execute format('alter function public.%I(%s) set schema sinjira_fracture_internal',r.proname,r.arg_types);
    execute format('revoke all on function sinjira_fracture_internal.%I(%s) from public, anon',r.proname,r.arg_types);
    execute format('grant execute on function sinjira_fracture_internal.%I(%s) to authenticated, service_role',r.proname,r.arg_types);

    if r.result_type like 'TABLE(%' then
      v_body:=format('select * from sinjira_fracture_internal.%I(%s)',r.proname,v_call_args);
    else
      v_body:=format('select sinjira_fracture_internal.%I(%s)',r.proname,v_call_args);
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
