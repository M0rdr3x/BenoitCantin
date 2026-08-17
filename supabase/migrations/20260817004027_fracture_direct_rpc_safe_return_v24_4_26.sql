begin;

-- V24.4.26
-- Uniformise le contrat de sortie du moteur Fracture. Les RPC d'action sont
-- intentionnellement exécutables par les membres authentifiés parce qu'elles
-- appliquent elles-mêmes auth.uid(), l'appartenance, le tour et la phase.
-- Elles retournaient toutefois fracture_engine_get_state() directement.
-- Cette fonction applique désormais le sanitizer canonique avant tout retour,
-- de sorte qu'un appel direct à une RPC d'action ne puisse pas contourner la
-- frontière de confidentialité du gateway/safe-state.

create or replace function public.fracture_engine_get_state(p_party_code text)
returns jsonb
language plpgsql
security definer
set search_path = public, auth
as $$
declare
  base jsonb;
  cleaned_reports jsonb;
  my_seat integer;
  canonical_engine_version text;
begin
  base:=public._fracture_engine_get_state_raw(p_party_code);

  select coalesce(p.engine_version,'24.4.6')
    into canonical_engine_version
  from public.fracture_parties p
  where upper(p.party_code)=upper(trim(p_party_code))
  limit 1;

  base:=jsonb_set(
    base,
    '{engine_version}',
    to_jsonb(coalesce(canonical_engine_version,'24.4.6')),
    true
  );

  my_seat:=nullif(base->>'my_seat','')::integer;
  select coalesce(jsonb_agg(
    case when nullif(r->>'seat','')::integer=my_seat then r else r-'suspect' end
  ),'[]'::jsonb)
  into cleaned_reports
  from jsonb_array_elements(coalesce(base->'reports','[]'::jsonb)) r;

  base:=jsonb_set(base,'{reports}',cleaned_reports,true);
  return public.fracture_engine_sanitize_state(base);
end;
$$;

create or replace function public.fracture_engine_privacy_health()
returns jsonb
language sql
stable
security invoker
set search_path = public, pg_temp
as $$
  select jsonb_build_object(
    'ok',
      to_regprocedure('public.fracture_engine_get_state_safe(text)') is not null
      and to_regprocedure('public.fracture_engine_sanitize_state(jsonb)') is not null
      and to_regprocedure('public.fracture_engine_get_state(text)') is not null,
    'privacy_version','24.4.15',
    'hardening_version','24.4.26',
    'safe_state_rpc',to_regprocedure('public.fracture_engine_get_state_safe(text)') is not null,
    'sanitizer',to_regprocedure('public.fracture_engine_sanitize_state(jsonb)') is not null,
    'seat_identity_isolation',true,
    'direct_action_safe_return',true
  );
$$;

revoke all on function public.fracture_engine_privacy_health() from public, anon;
grant execute on function public.fracture_engine_privacy_health() to authenticated;

commit;
