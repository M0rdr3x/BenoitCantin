create schema if not exists sinjira_family_playtest_internal;
revoke all on schema sinjira_family_playtest_internal from public;
grant usage on schema sinjira_family_playtest_internal to authenticated, service_role;

comment on schema sinjira_family_playtest_internal is
  'Implémentations privilégiées des RPC utilisateur famille/tuteur et invitations playtest. Hors schéma API public; wrappers public SECURITY INVOKER seulement.';

do $$
declare
  r record;
  v_count integer;
  v_call_args text;
  v_body text;
  v_targets text[] := array[
    'accept_sinjira_playtest_invitation',
    'create_family_link_invite',
    'create_guardian_signup_invite',
    'get_guardian_youth_contacts',
    'invite_sinjira_playtest_participant',
    'redeem_guardian_signup_invite',
    'revoke_guardian_link'
  ];
begin
  select count(*) into v_count
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.prokind='f' and p.prosecdef and p.proname=any(v_targets);

  if v_count <> 7 then
    raise exception 'V24.5.17 attend 7 RPC famille/playtest SECURITY DEFINER publiques; trouvé %', v_count;
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

    execute format('alter function public.%I(%s) set schema sinjira_family_playtest_internal',r.proname,r.arg_types);
    execute format('revoke all on function sinjira_family_playtest_internal.%I(%s) from public, anon',r.proname,r.arg_types);
    execute format('grant execute on function sinjira_family_playtest_internal.%I(%s) to authenticated, service_role',r.proname,r.arg_types);

    if r.result_type like 'TABLE(%' then
      v_body:=format('select * from sinjira_family_playtest_internal.%I(%s)',r.proname,v_call_args);
    else
      v_body:=format('select sinjira_family_playtest_internal.%I(%s)',r.proname,v_call_args);
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
