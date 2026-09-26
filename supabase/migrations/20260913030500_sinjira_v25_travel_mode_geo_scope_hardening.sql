-- SINJIRA™ V25 — borner l’effet du Mode Voyage au risque géographique
-- L’HUMAIN AVANT TOUT : une déclaration de voyage ne doit jamais réduire un risque
-- sans rapport avec la géographie (appareil inconnu, récupération, action sensible, etc.).
-- Aucun nouveau signal, aucune IP brute et aucun GPS ne sont ajoutés.

begin;

create or replace function private.security_risk_score_v25(
  p_unknown_device boolean,
  p_unexpected_region boolean,
  p_impossible_travel boolean,
  p_recent_failures boolean,
  p_recent_recovery boolean,
  p_auth_factor_change boolean,
  p_sensitive_action boolean,
  p_primary_device boolean,
  p_trusted_device boolean,
  p_travel_match boolean
)
returns jsonb
language plpgsql
immutable
set search_path = pg_catalog, private
as $$
declare
  v_score integer := 0;
  v_reasons text[] := '{}'::text[];
  v_band text;
begin
  if coalesce(p_unknown_device,false) then
    v_score := v_score + 30;
    v_reasons := array_append(v_reasons,'unknown_device');
  end if;
  if coalesce(p_unexpected_region,false) then
    v_score := v_score + 20;
    v_reasons := array_append(v_reasons,'unexpected_region');
  end if;
  if coalesce(p_impossible_travel,false) then
    v_score := v_score + 30;
    v_reasons := array_append(v_reasons,'impossible_travel');
  end if;
  if coalesce(p_recent_failures,false) then
    v_score := v_score + 20;
    v_reasons := array_append(v_reasons,'recent_failures');
  end if;
  if coalesce(p_recent_recovery,false) then
    v_score := v_score + 25;
    v_reasons := array_append(v_reasons,'recent_recovery');
  end if;
  if coalesce(p_auth_factor_change,false) then
    v_score := v_score + 25;
    v_reasons := array_append(v_reasons,'auth_factor_change');
  end if;
  if coalesce(p_sensitive_action,false) then
    v_score := v_score + 20;
    v_reasons := array_append(v_reasons,'sensitive_action');
  end if;
  if coalesce(p_primary_device,false) then
    v_score := v_score - 20;
    v_reasons := array_append(v_reasons,'primary_device');
  end if;
  if coalesce(p_trusted_device,false) then
    v_score := v_score - 15;
    v_reasons := array_append(v_reasons,'trusted_device');
  end if;

  -- p_travel_match reste dans la signature pour compatibilité V25, mais n'accorde
  -- plus aucun bonus de confiance global. Le chemin réel security_evaluate_context
  -- neutralise uniquement unexpected_region lorsqu'un voyage actif correspond.
  -- Le voyage impossible et tous les autres signaux conservent donc leur poids.
  perform p_travel_match;

  v_score := greatest(0,least(100,v_score));
  v_band := case
    when v_score <= 24 then 'low'
    when v_score <= 49 then 'medium'
    when v_score <= 74 then 'high'
    else 'critical'
  end;

  return jsonb_build_object(
    'score',v_score,
    'band',v_band,
    'reasons',to_jsonb(v_reasons),
    'model_version','v25.0'
  );
end;
$$;

revoke all on function private.security_risk_score_v25(
  boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean
) from public, anon, authenticated;

grant execute on function private.security_risk_score_v25(
  boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean
) to service_role;

comment on function private.security_risk_score_v25(
  boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean,boolean
) is
  'Moteur de risque V25: le Mode Voyage n’accorde aucun bonus global; seul security_evaluate_context peut neutraliser l’anomalie géographique correspondante.';

commit;
