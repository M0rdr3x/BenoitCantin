-- SINJIRA V24.4.77 — compatibilité explicable, sans exposition des réponses privées.
-- Aucune donnée brute du Registre ni préférence de l'autre membre n'est retournée.

create or replace function public.dating_import_registry_traits()
returns text[]
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_user uuid:=auth.uid();
  v_answers jsonb;
  v_traits text[]:='{}'::text[];
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if not exists(
    select 1 from public.dating_profiles
    where user_id=v_user and use_registry_answers=true
  ) then
    raise exception 'REGISTRY_CONSENT_REQUIRED';
  end if;

  select a.answers
  into v_answers
  from public.sinjira_character_applications a
  where a.user_id=v_user
    and a.answers is not null
    and a.source_purged_at is null
  order by coalesce(a.submitted_at,a.updated_at,a.created_at) desc
  limit 1;

  if v_answers is null then raise exception 'NO_REGISTRY_SOURCE'; end if;

  select coalesce(array_agg(distinct val order by val),'{}'::text[])
  into v_traits
  from (
    select left(btrim(v_answers->>k),80) as val
    from unnest(array[
      'core_value',
      'conflict_style',
      'decision_style',
      'sociability',
      'trust_style',
      'natural_role',
      'danger_style',
      'pressure_style',
      'archetype',
      'main_strength',
      'main_weakness'
    ]) as k
    where nullif(btrim(v_answers->>k),'') is not null
  ) q;

  update public.dating_profiles
  set registry_traits=v_traits,updated_at=now()
  where user_id=v_user;

  return v_traits;
end;
$$;

revoke all on function public.dating_import_registry_traits() from public,anon;
grant execute on function public.dating_import_registry_traits() to authenticated;

create or replace function public.dating_compatibility_detail(p_candidate_profile_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_overall integer;
  v_values integer;
  v_goals integer;
  v_communication integer;
  v_lifestyle integer;
  v_interests integer;
  v_registry integer;
  v_registry_on boolean:=false;
  m record;
  o record;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if not private.dating_is_eligible(v_user) then raise exception 'DATING_NOT_ELIGIBLE'; end if;

  select dc.compatibility_score
  into v_overall
  from public.dating_compatibility_candidates(20) dc
  where dc.profile_id=p_candidate_profile_id
  limit 1;

  if v_overall is null then raise exception 'CANDIDATE_NOT_AVAILABLE'; end if;

  select
    p.values_tags,p.interests_tags,p.lifestyle_tags,p.communication_tags,p.goals_tags,
    p.registry_traits,p.use_registry_answers,
    d.wanted_values,d.wanted_interests,d.wanted_lifestyle,d.wanted_communication,d.wanted_goals
  into m
  from public.dating_profiles p
  join public.dating_preferences d on d.user_id=p.user_id
  where p.user_id=v_user;

  select
    p.values_tags,p.interests_tags,p.lifestyle_tags,p.communication_tags,p.goals_tags,
    p.registry_traits,p.use_registry_answers,
    d.wanted_values,d.wanted_interests,d.wanted_lifestyle,d.wanted_communication,d.wanted_goals
  into o
  from public.dating_profiles p
  join public.dating_preferences d on d.user_id=p.user_id
  where p.id=p_candidate_profile_id;

  if not found then raise exception 'CANDIDATE_NOT_AVAILABLE'; end if;

  v_values:=round(100*private.dating_dimension_fit(m.values_tags,m.wanted_values,o.values_tags,o.wanted_values))::int;
  v_goals:=round(100*private.dating_dimension_fit(m.goals_tags,m.wanted_goals,o.goals_tags,o.wanted_goals))::int;
  v_communication:=round(100*private.dating_dimension_fit(m.communication_tags,m.wanted_communication,o.communication_tags,o.wanted_communication))::int;
  v_lifestyle:=round(100*private.dating_dimension_fit(m.lifestyle_tags,m.wanted_lifestyle,o.lifestyle_tags,o.wanted_lifestyle))::int;
  v_interests:=round(100*private.dating_dimension_fit(m.interests_tags,m.wanted_interests,o.interests_tags,o.wanted_interests))::int;
  v_registry_on:=coalesce(m.use_registry_answers,false) and coalesce(o.use_registry_answers,false);
  if v_registry_on then
    v_registry:=round(100*private.dating_overlap_ratio(m.registry_traits,o.registry_traits))::int;
  end if;

  return jsonb_build_object(
    'overall',v_overall,
    'method','local_explainable_v24_4_77',
    'remote_ai_used',false,
    'dimensions',jsonb_build_array(
      jsonb_build_object('key','values','label','Valeurs','score',v_values,'weight',25),
      jsonb_build_object('key','goals','label','Projets de relation','score',v_goals,'weight',25),
      jsonb_build_object('key','communication','label','Communication','score',v_communication,'weight',20),
      jsonb_build_object('key','lifestyle','label','Rythme de vie','score',v_lifestyle,'weight',15),
      jsonb_build_object('key','interests','label','Intérêts','score',v_interests,'weight',case when v_registry_on then 10 else 15 end)
    ),
    'registry_context',case when v_registry_on then jsonb_build_object(
      'used',true,
      'label','Repères du Registre',
      'score',v_registry,
      'weight',5
    ) else jsonb_build_object('used',false) end,
    'privacy',jsonb_build_object(
      'raw_profile_data_returned',false,
      'raw_registry_answers_returned',false
    )
  );
end;
$$;

revoke all on function public.dating_compatibility_detail(uuid) from public,anon;
grant execute on function public.dating_compatibility_detail(uuid) to authenticated;

comment on function public.dating_compatibility_detail(uuid) is
'Explique une compatibilité actuellement proposée avec des scores agrégés uniquement; ne retourne aucune préférence brute ni réponse brute du Registre.';
