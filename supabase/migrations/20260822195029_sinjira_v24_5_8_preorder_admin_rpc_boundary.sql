create schema if not exists preorder_admin_internal;
revoke all on schema preorder_admin_internal from public;
grant usage on schema preorder_admin_internal to authenticated;

comment on schema preorder_admin_internal is
  'Implémentations privilégiées des RPC administratives de précommande. Hors schéma API public; wrappers public SECURITY INVOKER seulement.';

do $$
declare
  r record;
  v_call_args text;
  v_body text;
begin
  for r in
    select
      p.oid,
      p.proname,
      pg_get_function_arguments(p.oid) as all_arguments,
      oidvectortypes(p.proargtypes) as arg_types,
      pg_get_function_result(p.oid) as result_type,
      p.pronargs
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public'
      and p.proname like 'admin_preorder_%'
      and p.prosecdef
    order by p.proname
  loop
    select coalesce(string_agg(format('$%s', g), ', ' order by g), '')
      into v_call_args
    from generate_series(1, r.pronargs) g;

    execute format(
      'alter function public.%I(%s) set schema preorder_admin_internal',
      r.proname,
      r.arg_types
    );

    execute format(
      'revoke all on function preorder_admin_internal.%I(%s) from public',
      r.proname,
      r.arg_types
    );
    execute format(
      'grant execute on function preorder_admin_internal.%I(%s) to authenticated',
      r.proname,
      r.arg_types
    );

    if r.result_type like 'TABLE(%' then
      v_body := format(
        'select * from preorder_admin_internal.%I(%s)',
        r.proname,
        v_call_args
      );
    else
      v_body := format(
        'select preorder_admin_internal.%I(%s)',
        r.proname,
        v_call_args
      );
    end if;

    execute format(
      'create function public.%I(%s) returns %s language sql security invoker set search_path = '''' as %L',
      r.proname,
      r.all_arguments,
      r.result_type,
      v_body
    );

    execute format(
      'revoke all on function public.%I(%s) from public',
      r.proname,
      r.arg_types
    );
    execute format(
      'grant execute on function public.%I(%s) to authenticated',
      r.proname,
      r.arg_types
    );
  end loop;
end
$$;
