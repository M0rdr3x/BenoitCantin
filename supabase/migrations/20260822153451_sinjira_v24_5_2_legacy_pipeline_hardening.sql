create or replace function public.admin_life_story_pending_requests(p_limit integer default 100)
returns jsonb
language plpgsql
stable
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid; v_result jsonb;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select coalesce(jsonb_agg(to_jsonb(x) order by x.created_at desc),'[]'::jsonb) into v_result
  from (
    select r.id,r.status,r.relationship_claim,r.date_of_death,r.created_at,
      coalesce(nullif(p.display_name,''),nullif(p.pseudo,''),'Compte SINJIRA') as subject_display_name,
      c.id as case_id,c.status as case_status,c.hold_until,c.first_verified_at,c.second_confirmed_at,
      exists(select 1 from public.life_story_posthumous_contests z where z.case_id=c.id and z.status='open') as has_open_contest
    from public.memorial_requests r
    left join public.profiles p on p.user_id=r.subject_user_id
    left join public.life_story_posthumous_cases c on c.memorial_request_id=r.id
    where r.status in ('pending','verified') or c.status in ('verified_hold','contested','ready_for_export')
    order by r.created_at desc
    limit least(greatest(coalesce(p_limit,100),1),250)
  ) x;
  return v_result;
end;
$$;

create or replace function public.admin_life_story_close_without_delivery(p_case_id uuid,p_note text default null)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid; v_case public.life_story_posthumous_cases%rowtype; v_recipient_count integer;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select * into v_case from public.life_story_posthumous_cases where id=p_case_id for update;
  if not found then raise exception 'CASE_NOT_FOUND'; end if;
  if v_case.status not in ('verified_hold','ready_for_export') then raise exception 'CASE_NOT_CLOSABLE'; end if;
  if v_case.hold_until>now() then raise exception 'SAFETY_HOLD_NOT_ELAPSED'; end if;
  if exists(select 1 from public.life_story_posthumous_contests where case_id=p_case_id and status='open') then raise exception 'OPEN_CONTEST_EXISTS'; end if;
  select count(*) into v_recipient_count from public.life_story_recipients where user_id=v_case.subject_user_id and status='active';
  if v_recipient_count>0 then raise exception 'ACTIVE_RECIPIENTS_EXIST'; end if;
  update public.life_story_posthumous_cases set status='closed_no_delivery',second_confirmed_by=coalesce(second_confirmed_by,v_admin),second_confirmed_at=coalesce(second_confirmed_at,now()) where id=p_case_id;
  insert into public.life_story_cleanup_tasks(case_id,subject_user_id,task_type,due_after,completion_note)
  values(p_case_id,v_case.subject_user_id,'life_story_source_review',now()+interval '90 days',null),(p_case_id,v_case.subject_user_id,'registry_private_data_review',now()+interval '90 days',null)
  on conflict(case_id,task_type) do nothing;
end;
$$;

create or replace function public.admin_life_story_prepare_export(p_case_id uuid,p_version_id uuid)
returns uuid
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare
  v_admin uuid;
  v_case public.life_story_posthumous_cases%rowtype;
  v_version public.life_story_versions%rowtype;
  v_entries jsonb;
  v_recipients jsonb;
  v_export_id uuid;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select * into v_case from public.life_story_posthumous_cases where id=p_case_id for update;
  if not found or v_case.status<>'ready_for_export' then raise exception 'CASE_NOT_READY_FOR_EXPORT'; end if;
  if exists(select 1 from public.life_story_posthumous_contests where case_id=p_case_id and status='open') then raise exception 'OPEN_CONTEST_EXISTS'; end if;
  select * into v_version from public.life_story_versions where id=p_version_id and user_id=v_case.subject_user_id;
  if not found then raise exception 'LIFE_STORY_VERSION_NOT_FOUND'; end if;
  if v_version.status<>'ready' then raise exception 'LIFE_STORY_VERSION_NOT_READY'; end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'title',e.title,'body',e.body,'occurred_on',e.occurred_on,
    'entry_type',e.entry_type,'knowledge_status',e.knowledge_status,'source_kind',e.source_kind,
    'sort_order',m.sort_order,'approved_at',e.user_approved_at
  ) order by m.sort_order,e.created_at),'[]'::jsonb)
  into v_entries
  from public.life_story_version_entries m
  join public.life_story_entries e on e.id=m.entry_id and e.user_id=m.user_id
  where m.version_id=v_version.id and m.user_id=v_case.subject_user_id
    and e.approval_status='approved' and e.posthumous_disclosure='selected_versions' and e.user_approved_at is not null;
  if jsonb_array_length(v_entries)=0 then raise exception 'LIFE_STORY_VERSION_EMPTY'; end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'recipient_kind',r.recipient_kind,'recipient_label',r.recipient_label,'recipient_email',r.recipient_email
  ) order by r.created_at),'[]'::jsonb)
  into v_recipients
  from public.life_story_recipients r
  where r.user_id=v_case.subject_user_id and r.version_id=v_version.id and r.status='active';
  if jsonb_array_length(v_recipients)=0 then raise exception 'LIFE_STORY_NO_RECIPIENTS'; end if;
  insert into public.life_story_exports(case_id,subject_user_id,version_id,audience,status,content_snapshot,recipients_snapshot)
  values(
    p_case_id,v_case.subject_user_id,v_version.id,v_version.audience,'prepared',
    jsonb_build_object(
      'schema_version','24.5.2','source_boundary','life_story_only','registry_access_prohibited',true,
      'version',jsonb_build_object('audience',v_version.audience,'name',v_version.name,'title',v_version.title,'instructions',v_version.instructions),
      'entries',v_entries,'prepared_at',now()
    ),v_recipients
  )
  on conflict(case_id,version_id) do update set
    status='prepared',content_snapshot=excluded.content_snapshot,recipients_snapshot=excluded.recipients_snapshot,
    storage_bucket=null,storage_path=null,sha256=null,generated_at=null,delivery_completed_at=null,purge_after=null
  returning id into v_export_id;
  delete from public.life_story_delivery_links where export_id=v_export_id;
  return v_export_id;
end;
$$;

create or replace function public.admin_life_story_complete_case(p_case_id uuid)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid; v_case public.life_story_posthumous_cases%rowtype;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select * into v_case from public.life_story_posthumous_cases where id=p_case_id for update;
  if not found or v_case.status<>'ready_for_export' then raise exception 'CASE_NOT_READY'; end if;
  if exists(select 1 from public.life_story_exports where case_id=p_case_id and status in ('prepared','generated')) then raise exception 'EXPORTS_NOT_FINISHED'; end if;
  if exists(
    select 1
    from public.life_story_recipients r
    where r.user_id=v_case.subject_user_id and r.status='active'
      and not exists(
        select 1 from public.life_story_exports e
        where e.case_id=p_case_id and e.version_id=r.version_id and e.status in ('delivered','revoked','purged')
      )
  ) then raise exception 'RECIPIENT_VERSION_NOT_DELIVERED'; end if;
  if not exists(select 1 from public.life_story_exports where case_id=p_case_id and status in ('delivered','revoked','purged')) then raise exception 'NO_COMPLETED_EXPORT'; end if;
  update public.life_story_posthumous_cases set status='completed' where id=p_case_id;
  insert into public.life_story_cleanup_tasks(case_id,subject_user_id,task_type,due_after)
  values(p_case_id,v_case.subject_user_id,'life_story_source_review',now()+interval '90 days'),(p_case_id,v_case.subject_user_id,'registry_private_data_review',now()+interval '90 days')
  on conflict(case_id,task_type) do nothing;
end;
$$;

create or replace function public.admin_life_story_revoke_export(p_export_id uuid)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  update public.life_story_exports set status='revoked',purge_after=coalesce(purge_after,now()+interval '90 days') where id=p_export_id and status in ('generated','delivered');
  if not found then raise exception 'EXPORT_NOT_REVOCABLE'; end if;
  update public.life_story_delivery_links set revoked_at=coalesce(revoked_at,now()) where export_id=p_export_id;
end;
$$;

create or replace function public.admin_life_story_get_purgeable_export(p_export_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid; v_result jsonb;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select jsonb_build_object('id',e.id,'storage_bucket',e.storage_bucket,'storage_path',e.storage_path,'status',e.status,'purge_after',e.purge_after)
  into v_result from public.life_story_exports e
  where e.id=p_export_id and e.status in ('delivered','revoked') and e.purge_after is not null and e.purge_after<=now();
  if v_result is null then raise exception 'EXPORT_NOT_PURGEABLE'; end if;
  return v_result;
end;
$$;

revoke all on function public.admin_life_story_revoke_export(uuid) from public,anon;
revoke all on function public.admin_life_story_get_purgeable_export(uuid) from public,anon;
grant execute on function public.admin_life_story_revoke_export(uuid) to authenticated;
grant execute on function public.admin_life_story_get_purgeable_export(uuid) to authenticated;