-- SINJIRA V25 — finalisation atomique de la fin de partie Fracture.
-- La fonction est exclusivement appelée par l'Edge Function authentifiée via service_role.
-- Elle regroupe contribution + rapport + partie + sessions dans une seule transaction et
-- répare les anciennes tentatives partielles où la contribution avait déjà été insérée.

create or replace function public.service_submit_fracture_endgame(
  p_user_id uuid,
  p_party_id uuid,
  p_party_updated_at timestamptz,
  p_report_id uuid,
  p_report_updated_at timestamptz,
  p_metrics jsonb,
  p_feedback jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth'
as $$
declare
  v_party public.fracture_parties%rowtype;
  v_report public.fracture_endgame_reports%rowtype;
  v_contribution_id uuid;
  v_session_count integer := 0;
  v_repaired boolean := false;
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED';
  end if;
  if p_user_id is null or p_party_id is null or p_report_id is null then
    raise exception 'INVALID_ENDGAME_CONTEXT';
  end if;
  if p_metrics is null or jsonb_typeof(p_metrics) <> 'object' then
    raise exception 'INVALID_ENDGAME_METRICS';
  end if;
  if p_feedback is null or jsonb_typeof(p_feedback) <> 'object' then
    raise exception 'INVALID_ENDGAME_FEEDBACK';
  end if;

  select * into v_party
  from public.fracture_parties
  where id = p_party_id
  for update;
  if not found then raise exception 'FRACTURE_PARTY_NOT_FOUND'; end if;
  if v_party.owner_user_id <> p_user_id then raise exception 'FRACTURE_OWNER_REQUIRED'; end if;

  select * into v_report
  from public.fracture_endgame_reports
  where id = p_report_id and party_id = p_party_id and owner_user_id = p_user_id
  for update;
  if not found then raise exception 'FRACTURE_ENDGAME_REPORT_NOT_FOUND'; end if;

  select c.id into v_contribution_id
  from public.internal_gameplay_contributions c
  where c.source_party_id = p_party_id
    and c.source_kind = 'fracture_endgame'
  limit 1;

  -- Réparation idempotente des anciennes finalisations partielles :
  -- si la contribution existe déjà, on termine seulement les marqueurs manquants.
  -- Une partie archivée est un état humain/terminal intentionnel et ne doit jamais
  -- être rétrogradée vers "finished" par une simple répétition de requête.
  if v_contribution_id is not null then
    if v_party.status = 'archived' then
      return jsonb_build_object(
        'contribution_id', v_contribution_id,
        'already_submitted', true,
        'repaired_partial_state', false
      );
    end if;

    v_repaired := v_report.submitted_at is null or v_party.status = 'in_progress';

    update public.fracture_endgame_reports
    set submitted_at = coalesce(submitted_at, now())
    where id = p_report_id;

    update public.fracture_parties
    set status = 'finished'
    where id = p_party_id and status = 'in_progress';

    update public.game_sessions
    set status = 'finished', finished_at = coalesce(finished_at, now())
    where game_slug = 'fracture-du-reseau-mere'
      and party_code = v_party.party_code;
    get diagnostics v_session_count = row_count;
    if v_session_count < 1 then raise exception 'FRACTURE_SESSION_NOT_FOUND'; end if;

    return jsonb_build_object(
      'contribution_id', v_contribution_id,
      'already_submitted', true,
      'repaired_partial_state', v_repaired
    );
  end if;

  if v_party.status <> 'in_progress' then raise exception 'FRACTURE_PARTY_NOT_ACTIVE'; end if;
  if v_report.submitted_at is not null then raise exception 'FRACTURE_ENDGAME_INCONSISTENT'; end if;
  if p_party_updated_at is null or v_party.updated_at is distinct from p_party_updated_at then
    raise exception 'FRACTURE_PARTY_CHANGED';
  end if;
  if p_report_updated_at is null or v_report.updated_at is distinct from p_report_updated_at then
    raise exception 'FRACTURE_ENDGAME_REPORT_CHANGED';
  end if;

  insert into public.internal_gameplay_contributions(
    game_slug, metrics, feedback, contribution_version, source_party_id, source_kind
  ) values (
    'fracture-du-reseau-mere', p_metrics, p_feedback, 'fracture-endgame-v9', p_party_id, 'fracture_endgame'
  ) returning id into v_contribution_id;

  update public.fracture_endgame_reports
  set submitted_at = now()
  where id = p_report_id;

  update public.fracture_parties
  set status = 'finished'
  where id = p_party_id;

  update public.game_sessions
  set status = 'finished', finished_at = coalesce(finished_at, now())
  where game_slug = 'fracture-du-reseau-mere'
    and party_code = v_party.party_code;
  get diagnostics v_session_count = row_count;
  if v_session_count < 1 then raise exception 'FRACTURE_SESSION_NOT_FOUND'; end if;

  return jsonb_build_object(
    'contribution_id', v_contribution_id,
    'already_submitted', false,
    'repaired_partial_state', false
  );
end;
$$;

revoke all on function public.service_submit_fracture_endgame(uuid,uuid,timestamptz,uuid,timestamptz,jsonb,jsonb)
from public, anon, authenticated;
grant execute on function public.service_submit_fracture_endgame(uuid,uuid,timestamptz,uuid,timestamptz,jsonb,jsonb)
to service_role;

comment on function public.service_submit_fracture_endgame(uuid,uuid,timestamptz,uuid,timestamptz,jsonb,jsonb) is
  'Finalisation transactionnelle service_role de Fracture: contribution interne et états rapport/partie/sessions, avec réparation idempotente des anciennes écritures partielles sans modifier une partie archivée.';
