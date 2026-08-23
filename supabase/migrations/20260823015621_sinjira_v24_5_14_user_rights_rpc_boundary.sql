create schema if not exists sinjira_user_rights_internal;
revoke all on schema sinjira_user_rights_internal from public;
grant usage on schema sinjira_user_rights_internal to authenticated, service_role;

comment on schema sinjira_user_rights_internal is
  'Implémentations privilégiées des RPC utilisateur Confidentialité et appels de modération. Hors schéma API public; wrappers public SECURITY INVOKER seulement.';

do $$
declare
  r record;
  v_count integer;
  v_call_args text;
  v_body text;
  v_targets text[] := array[
    'moderation_my_decisions',
    'moderation_submit_appeal',
    'privacy_create_request',
    'privacy_export_my_extended_data',
    'privacy_my_requests'
  ];
begin
  select count(*) into v_count
  from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public'
    and p.prosecdef
    and p.prokind='f'
    and p.proname=any(v_targets);

  if v_count <> 5 then
    raise exception 'V24.5.14 attend 5 RPC utilisateur Confidentialité/Appels SECURITY DEFINER publiques; trouvé %', v_count;
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

    execute format('alter function public.%I(%s) set schema sinjira_user_rights_internal',r.proname,r.arg_types);
    execute format('revoke all on function sinjira_user_rights_internal.%I(%s) from public, anon',r.proname,r.arg_types);
    execute format('grant execute on function sinjira_user_rights_internal.%I(%s) to authenticated, service_role',r.proname,r.arg_types);

    if r.result_type like 'TABLE(%' then
      v_body:=format('select * from sinjira_user_rights_internal.%I(%s)',r.proname,v_call_args);
    else
      v_body:=format('select sinjira_user_rights_internal.%I(%s)',r.proname,v_call_args);
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
