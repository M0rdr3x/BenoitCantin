begin;

-- V24.4.15
-- Couche de confidentialité indépendante placée devant l'état du moteur Fracture.
-- Elle ne modifie pas les règles du jeu : elle retire seulement les informations
-- qui ne doivent jamais quitter le serveur avant la fin de la partie.

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
  -- Les agrégats globaux suivants ne doivent jamais être envoyés au navigateur.
  v_state := v_state - array[
    'all_hands','hands','deck','private_state','secret_state','engine_secret','raw_cards'
  ]::text[];

  -- Avant la fin, aucune collection globale d'identités n'est permise.
  if not v_finished then
    v_state := v_state - array[
      'identities','all_identities','secret_identities','identity_map'
    ]::text[];
  end if;

  -- Les sièges publics gardent le nom, le type et l'état de tour.
  -- L'identité d'un autre siège n'est révélée qu'après la fin officielle.
  if jsonb_typeof(v_state->'seats') = 'array' then
    select coalesce(jsonb_agg(
      case
        when coalesce(item->>'seat','') = v_my_seat then
          item - array['hand','cards','picks','private','secret','suspect']::text[]
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

  -- Un rapport public peut contenir le rapport annoncé et la Preuve.
  -- Le soupçon ne reste visible que dans le propre état du joueur.
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

create or replace function public.fracture_engine_get_state_safe(p_party_code text)
returns jsonb
language sql
security invoker
set search_path = public, pg_temp
as $$
  select public.fracture_engine_sanitize_state(
    public.fracture_engine_get_state(p_party_code)::jsonb
  );
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
    'safe_state_rpc',to_regprocedure('public.fracture_engine_get_state_safe(text)') is not null,
    'sanitizer',to_regprocedure('public.fracture_engine_sanitize_state(jsonb)') is not null
  );
$$;

revoke all on function public.fracture_engine_sanitize_state(jsonb) from public, anon;
revoke all on function public.fracture_engine_get_state_safe(text) from public, anon;
revoke all on function public.fracture_engine_privacy_health() from public, anon;

grant execute on function public.fracture_engine_sanitize_state(jsonb) to authenticated;
grant execute on function public.fracture_engine_get_state_safe(text) to authenticated;
grant execute on function public.fracture_engine_privacy_health() to authenticated;

commit;
