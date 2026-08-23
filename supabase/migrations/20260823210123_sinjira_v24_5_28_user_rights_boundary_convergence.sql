-- Convergence après détection d'une couche intermédiaire redondante.
-- Le contrat canonique reste: public SECURITY INVOKER -> sinjira_user_rights_internal SECURITY DEFINER.

do $$
declare
  r record;
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
  for r in
    select p.oid,p.proname,pg_get_function_arguments(p.oid) all_arguments,
           oidvectortypes(p.proargtypes) arg_types,pg_get_function_result(p.oid) result_type,p.pronargs
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='sinjira_user_rights_internal' and p.prokind='f' and p.proname=any(v_targets)
    order by p.proname,p.oid
  loop
    select coalesce(string_agg(format('$%s',g),', ' order by g),'') into v_call_args
    from generate_series(1,r.pronargs) g;

    if r.result_type like 'TABLE(%' then
      v_body:=format('select * from sinjira_user_rights_internal.%I(%s)',r.proname,v_call_args);
    else
      v_body:=format('select sinjira_user_rights_internal.%I(%s)',r.proname,v_call_args);
    end if;

    execute format('drop function if exists public.%I(%s)',r.proname,r.arg_types);
    execute format(
      'create function public.%I(%s) returns %s language sql security invoker set search_path = '''' as %L',
      r.proname,r.all_arguments,r.result_type,v_body
    );
    execute format('revoke all on function public.%I(%s) from public, anon',r.proname,r.arg_types);
    execute format('grant execute on function public.%I(%s) to authenticated, service_role',r.proname,r.arg_types);
  end loop;
end
$$;

drop function if exists sinjira_privacy_moderation_internal.moderation_my_decisions(integer);
drop function if exists sinjira_privacy_moderation_internal.moderation_submit_appeal(uuid,text);
drop function if exists sinjira_privacy_moderation_internal.privacy_create_request(text,text);
drop function if exists sinjira_privacy_moderation_internal.privacy_export_my_extended_data();
drop function if exists sinjira_privacy_moderation_internal.privacy_my_requests(integer);
drop schema if exists sinjira_privacy_moderation_internal;

revoke all on schema sinjira_user_rights_internal from public, anon;
grant usage on schema sinjira_user_rights_internal to authenticated, service_role;

revoke all on function sinjira_user_rights_internal.moderation_my_decisions(integer) from public, anon;
revoke all on function sinjira_user_rights_internal.moderation_submit_appeal(uuid,text) from public, anon;
revoke all on function sinjira_user_rights_internal.privacy_create_request(text,text) from public, anon;
revoke all on function sinjira_user_rights_internal.privacy_export_my_extended_data() from public, anon;
revoke all on function sinjira_user_rights_internal.privacy_my_requests(integer) from public, anon;

grant execute on function sinjira_user_rights_internal.moderation_my_decisions(integer) to authenticated, service_role;
grant execute on function sinjira_user_rights_internal.moderation_submit_appeal(uuid,text) to authenticated, service_role;
grant execute on function sinjira_user_rights_internal.privacy_create_request(text,text) to authenticated, service_role;
grant execute on function sinjira_user_rights_internal.privacy_export_my_extended_data() to authenticated, service_role;
grant execute on function sinjira_user_rights_internal.privacy_my_requests(integer) to authenticated, service_role;
