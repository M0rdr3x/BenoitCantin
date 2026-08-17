begin;

-- V24.4.25
-- Durcit la frontière de confidentialité Fracture : avant la fin, aucune
-- identité n'est transportée dans la collection publique des sièges, y compris
-- celle du joueur courant. Sa propre faction reste disponible uniquement via
-- le champ top-level my_identity, réservé à sa carte d'identité privée.

create or replace function public.fracture_engine_sanitize_state(p_state jsonb)
returns jsonb
language plpgsql
immutable
set search_path = public, pg_temp
as $$
declare
  v_state jsonb := coalesce(p_state, '{}'::jsonb);
  v_my_seat text := coalesce(p_state->>'my_seat','');
  v_finished boolean := coalesce(p_state->>'phase','') = 'finished';
  v_items jsonb;
begin
  v_state := v_state - array[
    'all_hands','hands','deck','private_state','secret_state','engine_secret','raw_cards'
  ]::text[];

  if not v_finished then
    v_state := v_state - array[
      'identities','all_identities','secret_identities','identity_map'
    ]::text[];
  end if;

  -- Avant la fin, toutes les lignes de sièges sont strictement publiques :
  -- aucune identité n'y est présente. L'identité propre du joueur existe
  -- seulement dans v_state.my_identity. À la fin, les identités peuvent être
  -- révélées ensemble dans la liste des sièges.
  if jsonb_typeof(v_state->'seats') = 'array' then
    select coalesce(jsonb_agg(
      case
        when v_finished then
          item - array['hand','cards','picks','private','secret','suspect']::text[]
        else
          item - array['identity','hand','cards','picks','private','secret','suspect']::text[]
      end
      order by ord
    ), '[]'::jsonb)
    into v_items
    from jsonb_array_elements(v_state->'seats') with ordinality as e(item,ord);

    v_state := jsonb_set(v_state,'{seats}',v_items,true);
  end if;

  if jsonb_typeof(v_state->'reports') = 'array' then
    select coalesce(jsonb_agg(
      case
        when coalesce(item->>'seat','') = v_my_seat then
          item - array['private','secret']::text[]
        else
          item - array['suspect','private','secret']::text[]
      end
      order by ord
    ), '[]'::jsonb)
    into v_items
    from jsonb_array_elements(v_state->'reports') with ordinality as e(item,ord);

    v_state := jsonb_set(v_state,'{reports}',v_items,true);
  end if;

  return v_state;
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
      and to_regprocedure('public.fracture_engine_sanitize_state(jsonb)') is not null,
    'privacy_version','24.4.15',
    'hardening_version','24.4.25',
    'safe_state_rpc',to_regprocedure('public.fracture_engine_get_state_safe(text)') is not null,
    'sanitizer',to_regprocedure('public.fracture_engine_sanitize_state(jsonb)') is not null,
    'seat_identity_isolation',true
  );
$$;

revoke all on function public.fracture_engine_sanitize_state(jsonb) from public, anon;
revoke all on function public.fracture_engine_get_state_safe(text) from public, anon;
revoke all on function public.fracture_engine_privacy_health() from public, anon;

grant execute on function public.fracture_engine_sanitize_state(jsonb) to authenticated;
grant execute on function public.fracture_engine_get_state_safe(text) to authenticated;
grant execute on function public.fracture_engine_privacy_health() to authenticated;

commit;
