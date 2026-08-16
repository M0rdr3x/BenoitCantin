-- SINJIRA™ Fracture V24.4.2 — confidentialité des soupçons
-- Un soupçon de ronde reste privé au joueur qui l'a inscrit; seuls rapports et Preuves sont publics.

alter function public.fracture_engine_get_state(text) rename to _fracture_engine_get_state_raw;
revoke all on function public._fracture_engine_get_state_raw(text) from public,anon,authenticated;

create or replace function public.fracture_engine_get_state(p_party_code text)
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  base jsonb;
  cleaned_reports jsonb;
  my_seat integer;
begin
  base:=public._fracture_engine_get_state_raw(p_party_code);
  my_seat:=nullif(base->>'my_seat','')::integer;
  select coalesce(jsonb_agg(
    case when nullif(r->>'seat','')::integer=my_seat then r else r-'suspect' end
  ),'[]'::jsonb)
  into cleaned_reports
  from jsonb_array_elements(coalesce(base->'reports','[]'::jsonb)) r;
  return jsonb_set(base,'{reports}',cleaned_reports,true);
end $$;
revoke all on function public.fracture_engine_get_state(text) from public,anon;
grant execute on function public.fracture_engine_get_state(text) to authenticated;

create or replace function public.get_sinjira_server_version()
returns text language sql stable security definer set search_path=public as $$ select '24.4.2'::text; $$;
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;
