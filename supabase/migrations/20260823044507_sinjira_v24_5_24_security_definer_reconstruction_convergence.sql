-- SINJIRA V24.5.24 — convergence reproductible des fonctions privilégiées
-- Production ne contient plus quatre fonctions historiques; project_access_rank reste service_role-only.
-- Aucun CASCADE : seuls les triggers qui appellent directement ces fonctions historiques sont supprimés explicitement.
-- Toute autre dépendance cachée doit encore faire échouer la reconstruction plutôt que disparaître silencieusement.

do $$
declare
  r record;
  v_targets text[] := array[
    'grant_owner_novel_library',
    'grant_owner_product_entitlement',
    'grant_owner_project_access',
    'spend_sinjira_tokens'
  ];
begin
  for r in
    select tn.nspname as table_schema,
           c.relname as table_name,
           t.tgname as trigger_name
    from pg_trigger t
    join pg_proc p on p.oid=t.tgfoid
    join pg_namespace pn on pn.oid=p.pronamespace
    join pg_class c on c.oid=t.tgrelid
    join pg_namespace tn on tn.oid=c.relnamespace
    where pn.nspname='public'
      and p.proname=any(v_targets)
      and not t.tgisinternal
    order by tn.nspname,c.relname,t.tgname
  loop
    execute format('drop trigger if exists %I on %I.%I',r.trigger_name,r.table_schema,r.table_name);
  end loop;
end
$$;

DROP FUNCTION IF EXISTS public.grant_owner_novel_library();
DROP FUNCTION IF EXISTS public.grant_owner_product_entitlement();
DROP FUNCTION IF EXISTS public.grant_owner_project_access();
DROP FUNCTION IF EXISTS public.spend_sinjira_tokens(integer, text, text, text, uuid);

REVOKE ALL PRIVILEGES ON FUNCTION public.project_access_rank(uuid, uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.project_access_rank(uuid, uuid) TO service_role;
