create or replace function public.record_sinjira_fracture_endgame_contribution(
  p_user_id uuid,
  p_session_id uuid,
  p_party_id uuid,
  p_metrics jsonb,
  p_version text default 'fracture-endgame-v9'
)
returns uuid
language plpgsql
security definer
set search_path = 'public'
as $$
declare
  cid uuid := gen_random_uuid();
  v_version text := coalesce(nullif(trim(p_version), ''), 'fracture-endgame-v9');
begin
  if p_user_id is null or p_session_id is null or p_party_id is null then
    raise exception 'INVALID_ARGUMENT';
  end if;

  if jsonb_typeof(coalesce(p_metrics, '{}'::jsonb)) <> 'object' then
    raise exception 'INVALID_METRICS';
  end if;

  if not exists (
    select 1
    from public.game_sessions gs
    join public.fracture_parties fp
      on fp.id = p_party_id
     and fp.party_code = gs.party_code
    where gs.id = p_session_id
      and gs.user_id = p_user_id
      and gs.game_slug = 'fracture-du-reseau-mere'
      and fp.owner_user_id = p_user_id
  ) then
    raise exception 'SESSION_PARTY_MISMATCH';
  end if;

  if not exists (
    select 1
    from public.fracture_endgame_reports
    where party_id = p_party_id
  ) then
    raise exception 'ENDGAME_REPORT_MISSING';
  end if;

  if exists (
    select 1
    from public.internal_contribution_ownership
    where user_id = p_user_id
      and session_id = p_session_id
  ) then
    raise exception 'Cette partie a déjà été partagée.';
  end if;

  insert into public.internal_gameplay_contributions(
    id, game_slug, metrics, feedback, contribution_version, source_party_id, source_kind
  ) values (
    cid, 'fracture-du-reseau-mere', coalesce(p_metrics, '{}'::jsonb), '{}'::jsonb,
    v_version, p_party_id, 'fracture_endgame'
  );

  insert into public.internal_contribution_ownership(
    contribution_id, user_id, session_id
  ) values (
    cid, p_user_id, p_session_id
  );

  insert into public.contribution_receipts(
    session_id, user_id, contribution_version
  ) values (
    p_session_id, p_user_id, v_version
  )
  on conflict (session_id) do update
    set contributed_at = now(),
        contribution_version = excluded.contribution_version;

  update public.fracture_endgame_reports
     set submitted_at = now()
   where party_id = p_party_id;

  update public.fracture_parties
     set status = 'finished',
         updated_at = now()
   where id = p_party_id
     and owner_user_id = p_user_id;

  update public.game_sessions
     set status = 'finished',
         finished_at = now()
   where id = p_session_id
     and user_id = p_user_id;

  return cid;
end;
$$;

revoke all on function public.record_sinjira_fracture_endgame_contribution(uuid,uuid,uuid,jsonb,text) from public, anon, authenticated;
grant execute on function public.record_sinjira_fracture_endgame_contribution(uuid,uuid,uuid,jsonb,text) to service_role;

comment on function public.record_sinjira_fracture_endgame_contribution(uuid,uuid,uuid,jsonb,text) is
  'Service-only V24.5.54: enregistre atomiquement une fin de partie Fracture, son ownership/réception et finalise la partie.';
