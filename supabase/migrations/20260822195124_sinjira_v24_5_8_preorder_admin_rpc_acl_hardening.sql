do $$
declare
  r record;
begin
  for r in
    select p.proname, oidvectortypes(p.proargtypes) as arg_types
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.proname like 'admin_preorder_%'
  loop
    execute format(
      'revoke execute on function public.%I(%s) from anon',
      r.proname,
      r.arg_types
    );
  end loop;
end
$$;
