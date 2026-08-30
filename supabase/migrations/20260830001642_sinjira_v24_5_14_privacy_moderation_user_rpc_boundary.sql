-- Migration déjà appliquée en production le 2026-08-30.
-- Cette étape a créé temporairement une frontière intermédiaire supplémentaire
-- pour 5 RPC utilisateur déjà protégées par sinjira_user_rights_internal.
-- La migration suivante 20260830001742 restaure immédiatement la frontière canonique.

create schema if not exists sinjira_privacy_moderation_internal;
revoke all on schema sinjira_privacy_moderation_internal from public;
grant usage on schema sinjira_privacy_moderation_internal to authenticated, service_role;

do $$
declare
  r record;
  v_count integer;
  v_call_args text;
  v_wrapper text;
begin
  select count(*) into v_count
  from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public'
    and p.proname in (
      'privacy_create_request',
      'privacy_export_my_extended_data',
      'privacy_my_requests',
      'moderation_my_decisions',
      'moderation_submit_appeal'
    );

  if v_count <> 5 then
    raise exception 'V24.5.14 expected 5 target RPCs, found %', v_count;
  end if;

  for r in
    select p.oid,
           p.proname,
           pg_get_function_identity_arguments(p.oid) as identity_args,
           pg_get_function_arguments(p.oid) as full_args,
           pg_get_function_result(p.oid) as result_type,
           p.pronargs,
           p.proretset
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.proname in (
        'privacy_create_request',
        'privacy_export_my_extended_data',
        'privacy_my_requests',
        'moderation_my_decisions',
        'moderation_submit_appeal'
      )
    order by p.proname
  loop
    execute format('alter function public.%I(%s) set schema sinjira_privacy_moderation_internal', r.proname, r.identity_args);
    execute format('revoke all on function sinjira_privacy_moderation_internal.%I(%s) from public, anon', r.proname, r.identity_args);
    execute format('grant execute on function sinjira_privacy_moderation_internal.%I(%s) to authenticated, service_role', r.proname, r.identity_args);

    if r.pronargs = 0 then
      v_call_args := '';
    else
      select string_agg(format('$%s', i), ', ' order by i)
        into v_call_args
      from generate_series(1, r.pronargs) g(i);
    end if;

    if r.proretset or r.result_type like 'TABLE(%' then
      v_wrapper := format(
        'create function public.%I(%s) returns %s language sql security invoker set search_path=public,pg_temp as $fn$ select * from sinjira_privacy_moderation_internal.%I(%s); $fn$',
        r.proname, r.full_args, r.result_type, r.proname, v_call_args
      );
    else
      v_wrapper := format(
        'create function public.%I(%s) returns %s language sql security invoker set search_path=public,pg_temp as $fn$ select sinjira_privacy_moderation_internal.%I(%s); $fn$',
        r.proname, r.full_args, r.result_type, r.proname, v_call_args
      );
    end if;

    execute v_wrapper;
    execute format('revoke all on function public.%I(%s) from public, anon', r.proname, r.identity_args);
    execute format('grant execute on function public.%I(%s) to authenticated, service_role', r.proname, r.identity_args);
  end loop;
end $$;
