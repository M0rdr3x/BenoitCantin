-- SINJIRA™ V24.4.12 — défense en profondeur des tables internes.
-- Toute table public avec RLS activée et zéro policy est, par définition, non exposée
-- aux clients. On ajoute REVOKE ALL pour rendre cette intention explicite et indépendante de RLS.
-- Les RPC de simple diagnostic n'ont besoin d'aucun privilège SECURITY DEFINER.

alter function public.get_sinjira_server_version() security invoker;
alter function public.get_sinjira_runtime_health() security invoker;
alter function public.fracture_engine_health() security invoker;

comment on function public.get_sinjira_server_version() is
  'Diagnostic non secret : version de plateforme, SECURITY INVOKER.';
comment on function public.get_sinjira_runtime_health() is
  'Diagnostic non secret de présence des composants, SECURITY INVOKER.';
comment on function public.fracture_engine_health() is
  'Diagnostic non secret du moteur Fracture, SECURITY INVOKER.';

-- Scellement générique : robuste aux anciennes/nouvelles bases qui n'ont pas exactement
-- les mêmes tables historiques. Aucune table ayant au moins une policy n'est touchée.
do $$
declare
  r record;
begin
  for r in
    select n.nspname as schema_name,c.relname as table_name
    from pg_class c
    join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='public'
      and c.relkind='r'
      and c.relrowsecurity=true
      and not exists(select 1 from pg_policy p where p.polrelid=c.oid)
  loop
    execute format('revoke all on table %I.%I from anon, authenticated',r.schema_name,r.table_name);
  end loop;
end $$;

-- Re-grants explicites des trois diagnostics, après conversion en invoker.
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;
revoke all on function public.get_sinjira_runtime_health() from public,anon;
grant execute on function public.get_sinjira_runtime_health() to authenticated,service_role;
revoke all on function public.fracture_engine_health() from public,anon;
grant execute on function public.fracture_engine_health() to authenticated,service_role;
