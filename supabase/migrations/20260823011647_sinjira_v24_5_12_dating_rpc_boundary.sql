create schema if not exists sinjira_dating_internal;
revoke all on schema sinjira_dating_internal from public;
grant usage on schema sinjira_dating_internal to authenticated, service_role;

comment on schema sinjira_dating_internal is
  'Implémentations privilégiées des RPC Rencontres SINJIRA. Hors schéma API public; wrappers public SECURITY INVOKER seulement.';

do $$
declare
  r record;
  v_count integer;
  v_call_args text;
  v_body text;
  v_targets text[] := array[
    'dating_block_connection',
    'dating_close_connection',
    'dating_compatibility_candidates',
    'dating_compatibility_detail',
    'dating_confirm_single_and_serious',
    'dating_connections_overview',
    'dating_conversation',
    'dating_import_registry_traits',
    'dating_pause_profile',
    'dating_report_connection',
    'dating_request_conversation',
    'dating_respond_connection',
    'dating_safe_meet_cancel',
    'dating_safe_meet_opt_in',
    'dating_safe_meet_status',
    'dating_self_status',
    'dating_send_message',
    'dating_set_photo_consent'
  ];
begin
  select count(*) into v_count
  from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public'
    and p.prosecdef
    and p.prokind='f'
    and p.proname=any(v_targets);

  if v_count <> 18 then
    raise exception 'V24.5.12 attend 18 RPC Rencontres SECURITY DEFINER publiques; trouvé %', v_count;
  end if;

  for r in
    select p.oid, p.proname,
           pg_get_function_arguments(p.oid) as all_arguments,
           oidvectortypes(p.proargtypes) as arg_types,
           pg_get_function_result(p.oid) as result_type,
           p.pronargs
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.prosecdef
      and p.prokind='f'
      and p.proname=any(v_targets)
    order by p.proname, p.oid
  loop
    select coalesce(string_agg(format('$%s', g), ', ' order by g), '')
      into v_call_args
    from generate_series(1, r.pronargs) g;

    execute format('alter function public.%I(%s) set schema sinjira_dating_internal', r.proname, r.arg_types);
    execute format('revoke all on function sinjira_dating_internal.%I(%s) from public, anon', r.proname, r.arg_types);
    execute format('grant execute on function sinjira_dating_internal.%I(%s) to authenticated, service_role', r.proname, r.arg_types);

    if r.result_type like 'TABLE(%' then
      v_body := format('select * from sinjira_dating_internal.%I(%s)', r.proname, v_call_args);
    else
      v_body := format('select sinjira_dating_internal.%I(%s)', r.proname, v_call_args);
    end if;

    execute format(
      'create function public.%I(%s) returns %s language sql security invoker set search_path = '''' as %L',
      r.proname, r.all_arguments, r.result_type, v_body
    );

    execute format('revoke all on function public.%I(%s) from public, anon', r.proname, r.arg_types);
    execute format('grant execute on function public.%I(%s) to authenticated, service_role', r.proname, r.arg_types);
  end loop;
end
$$;
