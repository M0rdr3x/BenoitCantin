do $$
declare
  r record;
  v_count integer;
  v_body text;
begin
  select count(*) into v_count
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.prokind='f' and p.prosecdef and p.proname='redeem_family_link_invite';
  if v_count <> 1 then
    raise exception 'V24.5.19 attend redeem_family_link_invite SECURITY DEFINER publique; trouvé %',v_count;
  end if;

  select p.oid,p.proname,pg_get_function_arguments(p.oid) all_arguments,
         oidvectortypes(p.proargtypes) arg_types,pg_get_function_result(p.oid) result_type
  into r
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.prokind='f' and p.prosecdef and p.proname='redeem_family_link_invite';

  execute format('alter function public.%I(%s) set schema sinjira_family_playtest_internal',r.proname,r.arg_types);
  execute format('revoke all on function sinjira_family_playtest_internal.%I(%s) from public, anon',r.proname,r.arg_types);
  execute format('grant execute on function sinjira_family_playtest_internal.%I(%s) to authenticated, service_role',r.proname,r.arg_types);

  v_body:='select sinjira_family_playtest_internal.redeem_family_link_invite($1,$2,$3,$4)';
  execute format(
    'create function public.%I(%s) returns %s language sql security invoker set search_path = '''' as %L',
    r.proname,r.all_arguments,r.result_type,v_body
  );
  execute format('revoke all on function public.%I(%s) from public, anon',r.proname,r.arg_types);
  execute format('grant execute on function public.%I(%s) to authenticated, service_role',r.proname,r.arg_types);
end
$$;

create or replace function public.sinjira_family_link_health()
returns jsonb
language sql
stable
security invoker
set search_path='pg_catalog'
as $$
  with fn as (
    select lower(pg_get_functiondef('sinjira_family_playtest_internal.redeem_family_link_invite(text,text,date,boolean)'::regprocedure)) as def
  ), checks as (
    select
      position('''confirmed''' in def) > 0 as confirmed_status,
      position('when ''adult_child'' then ''child''' in def) > 0 as adult_child_mapped,
      position('when ''family'' then ''other''' in def) > 0 as family_mapped,
      position('p_mirror_to_fiction boolean default false' in def) > 0
        and position('mirror_to_fiction,' in def) > 0
        and position('false,' in def) > 0 as mirror_defaults_private
    from fn
  )
  select jsonb_build_object(
    'ok',confirmed_status and adult_child_mapped and family_mapped and mirror_defaults_private,
    'version','24.5.19',
    'confirmed_status',confirmed_status,
    'legacy_relationship_mapping',adult_child_mapped and family_mapped,
    'mirror_defaults_private',mirror_defaults_private
  )
  from checks;
$$;

revoke all on function public.sinjira_family_link_health() from public,anon,authenticated;
grant execute on function public.sinjira_family_link_health() to service_role;
