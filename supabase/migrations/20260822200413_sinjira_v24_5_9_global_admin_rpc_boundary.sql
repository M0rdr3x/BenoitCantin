create schema if not exists sinjira_admin_internal;
revoke all on schema sinjira_admin_internal from public;
grant usage on schema sinjira_admin_internal to authenticated, service_role;

comment on schema sinjira_admin_internal is
  'Implémentations privilégiées des RPC administratives SINJIRA. Hors schéma API public; wrappers public SECURITY INVOKER seulement.';

do $$
declare
  r record;
  v_count integer;
  v_call_args text;
  v_body text;
  v_targets text[] := array[
    'admin_life_story_case_detail','admin_life_story_cleanup_due','admin_life_story_close_without_delivery',
    'admin_life_story_complete_case','admin_life_story_complete_cleanup_task','admin_life_story_confirm_case',
    'admin_life_story_get_export','admin_life_story_get_purgeable_export','admin_life_story_pending_requests',
    'admin_life_story_prepare_export','admin_life_story_resolve_contest','admin_life_story_revoke_export',
    'admin_life_story_verify_death','admin_parallel_list_cycles','admin_parallel_list_responses',
    'admin_parallel_list_stories','admin_parallel_publish_story','admin_parallel_retract_story',
    'admin_parallel_save_cycle','admin_parallel_set_cycle_status','privacy_admin_incidents',
    'privacy_admin_record_incident','privacy_admin_requests','privacy_admin_update_request',
    'safety_admin_escalation_cases'
  ];
begin
  select count(*) into v_count
  from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public'
    and p.prosecdef
    and p.proname=any(v_targets);

  if v_count <> 25 then
    raise exception 'V24.5.9 attend 25 RPC administratives SECURITY DEFINER publiques; trouvé %', v_count;
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
      and p.proname=any(v_targets)
    order by p.proname, p.oid
  loop
    select coalesce(string_agg(format('$%s', g), ', ' order by g), '')
      into v_call_args
    from generate_series(1, r.pronargs) g;

    execute format('alter function public.%I(%s) set schema sinjira_admin_internal', r.proname, r.arg_types);

    execute format('revoke all on function sinjira_admin_internal.%I(%s) from public, anon', r.proname, r.arg_types);
    execute format('grant execute on function sinjira_admin_internal.%I(%s) to authenticated, service_role', r.proname, r.arg_types);

    if r.result_type like 'TABLE(%' then
      v_body := format('select * from sinjira_admin_internal.%I(%s)', r.proname, v_call_args);
    else
      v_body := format('select sinjira_admin_internal.%I(%s)', r.proname, v_call_args);
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
