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
    where r.status in ('pending','verified') or c.id is not null
    order by r.created_at desc
    limit least(greatest(coalesce(p_limit,100),1),250)
  ) x;
  return v_result;
end;
$$;

create or replace function public.admin_life_story_cleanup_due(p_limit integer default 100)
returns jsonb
language plpgsql
stable
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid; v_result jsonb;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select coalesce(jsonb_agg(to_jsonb(x) order by x.due_after),'[]'::jsonb) into v_result
  from (
    select t.id,t.case_id,t.task_type,t.status,t.due_after,t.created_at,
      c.status as case_status,
      coalesce(nullif(p.display_name,''),nullif(p.pseudo,''),'Compte SINJIRA') as subject_display_name
    from public.life_story_cleanup_tasks t
    join public.life_story_posthumous_cases c on c.id=t.case_id
    left join public.profiles p on p.user_id=t.subject_user_id
    where t.status='pending'
    order by t.due_after
    limit least(greatest(coalesce(p_limit,100),1),250)
  ) x;
  return v_result;
end;
$$;

revoke all on function public.admin_life_story_cleanup_due(integer) from public,anon;
grant execute on function public.admin_life_story_cleanup_due(integer) to authenticated;
