-- SINJIRA™ V25 — reconvergence de la frontière RPC publique privilégiée
--
-- V25 a redéfini plusieurs RPC utilisateur/Junior en public SECURITY DEFINER
-- après les frontières V24.5.x. Cette migration forward-only remet les
-- implémentations privilégiées hors du schéma API public et conserve des
-- wrappers publics SECURITY INVOKER. Aucun droit métier n'est élargi.

begin;

create schema if not exists sinjira_v25_internal;
revoke all on schema sinjira_v25_internal from public, anon, authenticated;
grant usage on schema sinjira_v25_internal to anon, authenticated, service_role;

comment on schema sinjira_v25_internal is
  'Implémentations privilégiées V25 Compte/Enfant/Junior. Hors schéma API public; wrappers public SECURITY INVOKER seulement.';

do $$
declare
  r record;
  v_count integer;
  v_anon_count integer;
  v_call_args text;
  v_body text;
  v_targets text[] := array[
    'create_guardian_signup_invite',
    'get_guardian_youth_contacts',
    'guardian_junior_community_children',
    'guardian_set_junior_community',
    'has_accepted_junior_community_rules',
    'junior_community_accept_rules',
    'junior_community_create_comment',
    'junior_community_create_post',
    'junior_community_delete_comment',
    'junior_community_delete_post',
    'junior_community_feed',
    'junior_community_report_content',
    'junior_guardian_summary',
    'redeem_guardian_signup_invite',
    'revoke_guardian_link',
    'set_my_guardian_contact_metadata',
    'sinjira_can_read_guardian_link',
    'sinjira_child_document_available',
    'sinjira_child_project_available',
    'sinjira_junior_community_enabled',
    'sinjira_my_account_capabilities',
    'sinjira_my_age_band',
    'sinjira_my_novel_catalog'
  ];
  v_anon_targets text[] := array[
    'sinjira_child_document_available',
    'sinjira_child_project_available',
    'sinjira_my_age_band'
  ];
begin
  if array_length(v_targets,1) <> 23 then
    raise exception 'V25 RPC boundary: liste cible invalide';
  end if;

  select count(*) into v_count
  from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public'
    and p.prokind='f'
    and p.prosecdef
    and p.proname=any(v_targets);

  if v_count <> 23 then
    raise exception 'V25 RPC boundary attend 23 RPC public SECURITY DEFINER; trouvé %',v_count;
  end if;

  -- Le total seul ne suffit pas : un overload inattendu ne doit jamais pouvoir
  -- masquer une cible manquante. Chaque nom attendu correspond exactement à
  -- une fonction public SECURITY DEFINER avant déplacement.
  if exists(
    select 1
    from unnest(v_targets) as t(name)
    left join (
      select p.oid,p.proname
      from pg_proc p
      join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='public'
        and p.prokind='f'
        and p.prosecdef
    ) candidate on candidate.proname=t.name
    group by t.name
    having count(candidate.oid) <> 1
  ) then
    raise exception 'V25 RPC boundary: chaque cible doit correspondre à exactement une RPC public SECURITY DEFINER';
  end if;

  if exists(
    select 1
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.prokind='f'
      and p.prosecdef
      and p.proname=any(v_targets)
      and not has_function_privilege('authenticated',p.oid,'EXECUTE')
  ) then
    raise exception 'V25 RPC boundary: une RPC cible n est pas exécutable par authenticated avant déplacement';
  end if;

  select count(*) into v_anon_count
  from pg_proc p
  join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public'
    and p.prokind='f'
    and p.prosecdef
    and p.proname=any(v_targets)
    and has_function_privilege('anon',p.oid,'EXECUTE');

  if v_anon_count <> 3 then
    raise exception 'V25 RPC boundary attend exactement 3 RPC anonymes; trouvé %',v_anon_count;
  end if;

  -- Même exigence par nom pour le sous-ensemble anonyme : chacune des trois
  -- cibles doit exister une seule fois et être réellement exécutable par anon.
  if exists(
    select 1
    from unnest(v_anon_targets) as t(name)
    left join (
      select p.oid,p.proname
      from pg_proc p
      join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='public'
        and p.prokind='f'
        and p.prosecdef
        and has_function_privilege('anon',p.oid,'EXECUTE')
    ) candidate on candidate.proname=t.name
    group by t.name
    having count(candidate.oid) <> 1
  ) then
    raise exception 'V25 RPC boundary: chaque cible anon doit correspondre à exactement une RPC anonyme';
  end if;

  if exists(
    select 1
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.prokind='f'
      and p.prosecdef
      and p.proname=any(v_targets)
      and has_function_privilege('anon',p.oid,'EXECUTE')
      and not (p.proname=any(v_anon_targets))
  ) then
    raise exception 'V25 RPC boundary: privilège anon inattendu sur une RPC cible';
  end if;

  for r in
    select p.oid,p.proname,pg_get_function_arguments(p.oid) all_arguments,
           oidvectortypes(p.proargtypes) arg_types,
           pg_get_function_result(p.oid) result_type,p.pronargs
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.prokind='f'
      and p.prosecdef
      and p.proname=any(v_targets)
    order by p.proname,p.oid
  loop
    select coalesce(string_agg(format('$%s',g),', ' order by g),'')
      into v_call_args
    from generate_series(1,r.pronargs) g;

    execute format(
      'alter function public.%I(%s) set schema sinjira_v25_internal',
      r.proname,r.arg_types
    );
    execute format(
      'revoke all on function sinjira_v25_internal.%I(%s) from public, anon, authenticated',
      r.proname,r.arg_types
    );
    execute format(
      'grant execute on function sinjira_v25_internal.%I(%s) to authenticated, service_role',
      r.proname,r.arg_types
    );
    if r.proname=any(v_anon_targets) then
      execute format(
        'grant execute on function sinjira_v25_internal.%I(%s) to anon',
        r.proname,r.arg_types
      );
    end if;

    if r.result_type like 'TABLE(%' then
      v_body:=format(
        'select * from sinjira_v25_internal.%I(%s)',
        r.proname,v_call_args
      );
    else
      v_body:=format(
        'select sinjira_v25_internal.%I(%s)',
        r.proname,v_call_args
      );
    end if;

    execute format(
      'create function public.%I(%s) returns %s language sql security invoker set search_path = '''' as %L',
      r.proname,r.all_arguments,r.result_type,v_body
    );
    execute format(
      'revoke all on function public.%I(%s) from public, anon, authenticated',
      r.proname,r.arg_types
    );
    execute format(
      'grant execute on function public.%I(%s) to authenticated, service_role',
      r.proname,r.arg_types
    );
    if r.proname=any(v_anon_targets) then
      execute format(
        'grant execute on function public.%I(%s) to anon',
        r.proname,r.arg_types
      );
    end if;
  end loop;
end
$$;

commit;
