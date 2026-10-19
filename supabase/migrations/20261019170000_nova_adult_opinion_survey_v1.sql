-- Projet Nova : consultation volontaire 18+, opinions politiques sensibles.
-- Agrégats uniquement : aucune réponse individuelle, identité ou date de
-- naissance n'est conservée dans les tables de sondage.
-- Ne PAS appliquer avant revue de confidentialité, hébergement et approbation.
create table if not exists public.nova_survey_participants (
  survey_version text not null,
  participant_hash text not null check (participant_hash ~ '^[0-9a-f]{64}$'),
  submitted_at timestamptz not null default now(),
  primary key (survey_version, participant_hash),
  constraint nova_survey_participant_version_ck
    check (survey_version = 'nova-consultation-64-v1')
);

create table if not exists public.nova_survey_aggregate_counts (
  survey_version text not null,
  question_id text not null check (question_id ~ '^q(0[1-9]|[1-5][0-9]|6[0-4])$'),
  response_value text not null
    check (response_value in ('-3','-2','-1','0','1','2','3','skip')),
  answer_count bigint not null default 0 check (answer_count >= 0),
  primary key (survey_version, question_id, response_value),
  constraint nova_survey_aggregate_version_ck
    check (survey_version = 'nova-consultation-64-v1')
);

alter table public.nova_survey_participants enable row level security;
alter table public.nova_survey_aggregate_counts enable row level security;
revoke all on public.nova_survey_participants from public, anon, authenticated;
revoke all on public.nova_survey_aggregate_counts from public, anon, authenticated;
-- Aucun accès public, même aux agrégats. Publication ultérieure uniquement
-- après contrôle méthodologique et seuil empêchant les petites cellules.

create or replace function public.nova_survey_submit_v1(
  p_survey_version text,
  p_participant_hash text,
  p_answers jsonb
)
returns text
language plpgsql security definer set search_path = ''
as $$
declare
  inserted smallint;
begin
  if p_survey_version is distinct from 'nova-consultation-64-v1'
     or p_participant_hash is null
     or p_participant_hash !~ '^[0-9a-f]{64}$'
     or pg_catalog.jsonb_typeof(p_answers) is distinct from 'object'
  then
    raise exception 'INVALID_SURVEY_PAYLOAD' using errcode='22023';
  end if;

  -- 64 clés q01..q64 et valeur explicite même pour « Sans opinion » :
  -- une soumission partielle ou une question injectée n'est jamais agrégée.
  if (select count(*) from pg_catalog.jsonb_each_text(p_answers)) != 64
     or exists (
       select 1 from pg_catalog.jsonb_each_text(p_answers) as a(key,value)
       where a.key !~ '^q(0[1-9]|[1-5][0-9]|6[0-4])$'
          or a.value not in ('-3','-2','-1','0','1','2','3','skip')
     )
  then
    raise exception 'INVALID_SURVEY_ANSWERS' using errcode='22023';
  end if;

  insert into public.nova_survey_participants(survey_version, participant_hash)
  values (p_survey_version, p_participant_hash)
  on conflict do nothing returning 1 into inserted;
  if inserted is null then
    raise exception 'ALREADY_SUBMITTED' using errcode='23505';
  end if;

  -- Le décompte et la déduplication sont une seule transaction atomique.
  insert into public.nova_survey_aggregate_counts
    (survey_version, question_id, response_value, answer_count)
  select p_survey_version, a.key, a.value, 1
  from pg_catalog.jsonb_each_text(p_answers) as a(key,value)
  on conflict (survey_version, question_id, response_value)
  do update set answer_count = public.nova_survey_aggregate_counts.answer_count + 1;

  return 'RECORDED';
end;
$$;

revoke all on function public.nova_survey_submit_v1(text,text,jsonb)
  from public, anon, authenticated;
grant execute on function public.nova_survey_submit_v1(text,text,jsonb)
  to service_role;
