-- Convergence immédiate vers la frontière canonique déjà existante.
-- Les wrappers publics appellent directement sinjira_user_rights_internal.
-- Aucun droit métier n'est modifié; anon reste révoqué.

do $$
declare
  r record;
  v_call_args text;
  v_wrapper text;
begin
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
    if r.pronargs = 0 then
      v_call_args := '';
    else
      select string_agg(format('$%s', i), ', ' order by i)
      into v_call_args
      from generate_series(1, r.pronargs) g(i);
    end if;

    if r.proretset or r.result_type like 'TABLE(%' then
      v_wrapper := format(
        'create or replace function public.%I(%s) returns %s language sql security invoker set search_path=public,pg_temp as $fn$ select * from sinjira_user_rights_internal.%I(%s); $fn$',
        r.proname, r.full_args, r.result_type, r.proname, v_call_args
      );
    else
      v_wrapper := format(
        'create or replace function public.%I(%s) returns %s language sql security invoker set search_path=public,pg_temp as $fn$ select sinjira_user_rights_internal.%I(%s); $fn$',
        r.proname, r.full_args, r.result_type, r.proname, v_call_args
      );
    end if;

    execute v_wrapper;
    execute format('revoke all on function public.%I(%s) from public, anon', r.proname, r.identity_args);
    execute format('grant execute on function public.%I(%s) to authenticated, service_role', r.proname, r.identity_args);
  end loop;
end $$;

do $$
declare r record;
begin
  if exists(select 1 from pg_namespace where nspname='sinjira_privacy_moderation_internal') then
    for r in
      select p.proname, pg_get_function_identity_arguments(p.oid) as identity_args
      from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='sinjira_privacy_moderation_internal'
    loop
      execute format('drop function sinjira_privacy_moderation_internal.%I(%s)', r.proname, r.identity_args);
    end loop;
    execute 'drop schema sinjira_privacy_moderation_internal';
  end if;
end $$;
