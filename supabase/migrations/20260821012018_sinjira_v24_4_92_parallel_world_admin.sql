-- SINJIRA V24.4.92 — administration humaine du Monde parallèle.
-- Migration déjà appliquée en production le 2026-08-21; ce fichier restaure le DDL canonique
-- pour la reconstruction locale et les environnements neufs.

create or replace function public.admin_parallel_list_cycles()
returns jsonb
language plpgsql
stable security definer
set search_path to 'pg_catalog','public','private','auth'
as $$
declare
  v_admin uuid;
  v_rows jsonb;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select coalesce(jsonb_agg(to_jsonb(x) order by x.cycle_month desc),'[]'::jsonb)
  into v_rows
  from (
    select c.id,c.cycle_month,c.title,c.monthly_question,c.response_mode,c.audience,c.status,
           c.opens_at,c.closes_at,c.published_at,c.created_at,
           (select count(*) from public.parallel_cycle_responses r where r.cycle_id=c.id) as response_count,
           (select count(*) from public.parallel_story_installments s where s.cycle_id=c.id and s.published_at is not null) as published_story_count
    from public.parallel_world_cycles c
    order by c.cycle_month desc
    limit 120
  ) x;
  return jsonb_build_object('ok',true,'cycles',v_rows);
end;
$$;

create or replace function public.admin_parallel_list_responses(p_cycle_id uuid)
returns jsonb
language plpgsql
stable security definer
set search_path to 'pg_catalog','public','private','auth'
as $$
declare
  v_admin uuid;
  v_rows jsonb;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  if not exists(select 1 from public.parallel_world_cycles where id=p_cycle_id) then raise exception 'CYCLE_NOT_FOUND'; end if;
  select coalesce(jsonb_agg(to_jsonb(x) order by x.submitted_at asc),'[]'::jsonb)
  into v_rows
  from (
    select r.id as response_id,
           coalesce(pi.public_name,'Identité parallèle') as identity_name,
           r.response_text,r.response_kind,r.submitted_at,
           (select count(*) from public.parallel_story_installments s where s.cycle_id=r.cycle_id and s.character_id=r.character_id and s.story_kind='individual') as individual_story_count
    from public.parallel_cycle_responses r
    left join private.parallel_identities pi on pi.user_id=r.user_id and pi.status='active'
    where r.cycle_id=p_cycle_id
    order by r.submitted_at asc
  ) x;
  return jsonb_build_object('ok',true,'responses',v_rows);
end;
$$;

create or replace function public.admin_parallel_list_stories(p_cycle_id uuid)
returns jsonb
language plpgsql
stable security definer
set search_path to 'pg_catalog','public','private','auth'
as $$
declare
  v_admin uuid;
  v_rows jsonb;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select coalesce(jsonb_agg(to_jsonb(x) order by x.created_at desc),'[]'::jsonb)
  into v_rows
  from (
    select s.id as story_id,s.story_kind,s.title,s.content,s.audience,s.published_at,s.created_at,
           case when s.story_kind='individual' then coalesce(pi.public_name,'Identité parallèle') else null end as identity_name
    from public.parallel_story_installments s
    left join private.parallel_identities pi on pi.source_character_id=s.character_id and pi.status='active'
    where s.cycle_id=p_cycle_id
    order by s.created_at desc
  ) x;
  return jsonb_build_object('ok',true,'stories',v_rows);
end;
$$;

create or replace function public.admin_parallel_save_cycle(
  p_cycle_id uuid,
  p_cycle_month date,
  p_title text,
  p_monthly_question text,
  p_response_mode text,
  p_audience text,
  p_opens_at timestamptz,
  p_closes_at timestamptz
)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public','private','auth'
as $$
declare
  v_admin uuid;
  v_title text:=btrim(coalesce(p_title,''));
  v_question text:=btrim(coalesce(p_monthly_question,''));
  v_row public.parallel_world_cycles%rowtype;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  if p_cycle_month is null then raise exception 'CYCLE_MONTH_REQUIRED'; end if;
  if extract(day from p_cycle_month)<>1 then raise exception 'CYCLE_MONTH_FIRST_DAY_REQUIRED'; end if;
  if char_length(v_title)<3 or char_length(v_title)>160 then raise exception 'CYCLE_TITLE_LENGTH'; end if;
  if char_length(v_question)<10 or char_length(v_question)>1200 then raise exception 'CYCLE_QUESTION_LENGTH'; end if;
  if p_response_mode not in ('solo','group','solo_or_group') then raise exception 'CYCLE_RESPONSE_MODE'; end if;
  if p_audience not in ('all','adult','youth') then raise exception 'CYCLE_AUDIENCE'; end if;
  if p_opens_at is null or p_closes_at is null or p_closes_at<=p_opens_at then raise exception 'CYCLE_WINDOW_INVALID'; end if;
  if not public.sinjira_content_allowed(v_admin,v_title) or not public.sinjira_content_allowed(v_admin,v_question) then raise exception 'CONTENT_NOT_ALLOWED'; end if;

  if p_cycle_id is null then
    insert into public.parallel_world_cycles(cycle_month,title,monthly_question,response_mode,audience,opens_at,closes_at,status)
    values(p_cycle_month,v_title,v_question,p_response_mode,p_audience,p_opens_at,p_closes_at,'draft')
    returning * into v_row;
  else
    select * into v_row from public.parallel_world_cycles where id=p_cycle_id for update;
    if v_row.id is null then raise exception 'CYCLE_NOT_FOUND'; end if;
    if v_row.status<>'draft' then raise exception 'CYCLE_EDIT_DRAFT_ONLY'; end if;
    update public.parallel_world_cycles
    set cycle_month=p_cycle_month,title=v_title,monthly_question=v_question,response_mode=p_response_mode,
        audience=p_audience,opens_at=p_opens_at,closes_at=p_closes_at
    where id=p_cycle_id returning * into v_row;
  end if;

  return jsonb_build_object('ok',true,'cycle',jsonb_build_object(
    'id',v_row.id,'cycle_month',v_row.cycle_month,'title',v_row.title,'monthly_question',v_row.monthly_question,
    'response_mode',v_row.response_mode,'audience',v_row.audience,'status',v_row.status,
    'opens_at',v_row.opens_at,'closes_at',v_row.closes_at,'published_at',v_row.published_at
  ));
end;
$$;

create or replace function public.admin_parallel_set_cycle_status(p_cycle_id uuid,p_status text)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public','private','auth'
as $$
declare
  v_admin uuid;
  v_row public.parallel_world_cycles%rowtype;
  v_status text:=lower(btrim(coalesce(p_status,'')));
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select * into v_row from public.parallel_world_cycles where id=p_cycle_id for update;
  if v_row.id is null then raise exception 'CYCLE_NOT_FOUND'; end if;
  if not (
    (v_row.status='draft' and v_status in ('open','archived')) or
    (v_row.status='open' and v_status='closed') or
    (v_row.status='closed' and v_status in ('published','archived')) or
    (v_row.status='published' and v_status='archived')
  ) then raise exception 'CYCLE_STATUS_TRANSITION_INVALID'; end if;
  if v_status='open' and now()>v_row.closes_at then raise exception 'CYCLE_WINDOW_ALREADY_CLOSED'; end if;

  update public.parallel_world_cycles
  set status=v_status,
      published_at=case when v_status='published' then coalesce(published_at,now()) when v_status='archived' then null else published_at end
  where id=p_cycle_id returning * into v_row;

  return jsonb_build_object('ok',true,'cycle_id',v_row.id,'status',v_row.status,'published_at',v_row.published_at);
end;
$$;

create or replace function public.admin_parallel_publish_story(
  p_cycle_id uuid,
  p_story_kind text,
  p_response_id uuid,
  p_title text,
  p_content text,
  p_audience text
)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public','private','auth'
as $$
declare
  v_admin uuid;
  v_title text:=btrim(coalesce(p_title,''));
  v_content text:=btrim(coalesce(p_content,''));
  v_kind text:=lower(btrim(coalesce(p_story_kind,'')));
  v_character uuid:=null;
  v_story uuid;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  if not exists(select 1 from public.parallel_world_cycles where id=p_cycle_id and status in ('closed','published')) then raise exception 'CYCLE_MUST_BE_CLOSED'; end if;
  if v_kind not in ('collective','individual') then raise exception 'STORY_KIND_INVALID'; end if;
  if p_audience not in ('all','adult','youth') then raise exception 'STORY_AUDIENCE_INVALID'; end if;
  if char_length(v_title)<3 or char_length(v_title)>200 then raise exception 'STORY_TITLE_LENGTH'; end if;
  if char_length(v_content)<20 or char_length(v_content)>20000 then raise exception 'STORY_CONTENT_LENGTH'; end if;
  if not public.sinjira_content_allowed(v_admin,v_title) or not public.sinjira_content_allowed(v_admin,v_content) then raise exception 'CONTENT_NOT_ALLOWED'; end if;

  if v_kind='individual' then
    if p_response_id is null then raise exception 'INDIVIDUAL_RESPONSE_REQUIRED'; end if;
    select r.character_id into v_character from public.parallel_cycle_responses r where r.id=p_response_id and r.cycle_id=p_cycle_id;
    if v_character is null then raise exception 'RESPONSE_NOT_FOUND'; end if;
  end if;

  insert into public.parallel_story_installments(cycle_id,story_kind,character_id,title,content,published_at,audience)
  values(p_cycle_id,v_kind,v_character,v_title,v_content,now(),case when v_kind='individual' then 'all' else p_audience end)
  returning id into v_story;

  return jsonb_build_object('ok',true,'story_id',v_story,'story_kind',v_kind,'published_at',now());
end;
$$;

create or replace function public.admin_parallel_retract_story(p_story_id uuid)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public','private','auth'
as $$
declare
  v_admin uuid;
  v_story uuid;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  update public.parallel_story_installments set published_at=null where id=p_story_id and published_at is not null returning id into v_story;
  if v_story is null then raise exception 'STORY_NOT_PUBLISHED'; end if;
  return jsonb_build_object('ok',true,'story_id',v_story,'published_at',null);
end;
$$;

revoke all on function public.admin_parallel_list_cycles() from public,anon;
revoke all on function public.admin_parallel_list_responses(uuid) from public,anon;
revoke all on function public.admin_parallel_list_stories(uuid) from public,anon;
revoke all on function public.admin_parallel_save_cycle(uuid,date,text,text,text,text,timestamptz,timestamptz) from public,anon;
revoke all on function public.admin_parallel_set_cycle_status(uuid,text) from public,anon;
revoke all on function public.admin_parallel_publish_story(uuid,text,uuid,text,text,text) from public,anon;
revoke all on function public.admin_parallel_retract_story(uuid) from public,anon;

grant execute on function public.admin_parallel_list_cycles() to authenticated,service_role;
grant execute on function public.admin_parallel_list_responses(uuid) to authenticated,service_role;
grant execute on function public.admin_parallel_list_stories(uuid) to authenticated,service_role;
grant execute on function public.admin_parallel_save_cycle(uuid,date,text,text,text,text,timestamptz,timestamptz) to authenticated,service_role;
grant execute on function public.admin_parallel_set_cycle_status(uuid,text) to authenticated,service_role;
grant execute on function public.admin_parallel_publish_story(uuid,text,uuid,text,text,text) to authenticated,service_role;
grant execute on function public.admin_parallel_retract_story(uuid) to authenticated,service_role;

comment on function public.admin_parallel_list_cycles() is 'Administration AAL2 du Monde parallèle : liste cycles et compteurs.';
comment on function public.admin_parallel_list_responses(uuid) is 'Administration AAL2 : réponses d’un cycle, sans exposer les identifiants techniques de compte.';
comment on function public.admin_parallel_list_stories(uuid) is 'Administration AAL2 : chroniques d’un cycle.';
comment on function public.admin_parallel_save_cycle(uuid,date,text,text,text,text,timestamptz,timestamptz) is 'Administration AAL2 : création/modification des cycles brouillon.';
comment on function public.admin_parallel_set_cycle_status(uuid,text) is 'Administration AAL2 : transitions contrôlées du cycle.';
comment on function public.admin_parallel_publish_story(uuid,text,uuid,text,text,text) is 'Administration AAL2 : publication humaine d’une chronique collective ou individuelle.';
comment on function public.admin_parallel_retract_story(uuid) is 'Administration AAL2 : retrait réversible d’une chronique publiée.';
