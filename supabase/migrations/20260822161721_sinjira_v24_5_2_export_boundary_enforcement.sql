create or replace function public.admin_life_story_get_export(p_export_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path='pg_catalog','public','auth','private'
as $$
declare v_admin uuid; v_result jsonb;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select jsonb_build_object(
    'id',e.id,'case_id',e.case_id,'subject_user_id',e.subject_user_id,'version_id',e.version_id,
    'audience',e.audience,'status',e.status,'source_boundary',e.source_boundary,
    'registry_access_prohibited',e.registry_access_prohibited,
    'content_snapshot',e.content_snapshot,'recipients_snapshot',e.recipients_snapshot,
    'storage_bucket',e.storage_bucket,'storage_path',e.storage_path,'sha256',e.sha256,'generated_at',e.generated_at,
    'delivery_completed_at',e.delivery_completed_at,'purge_after',e.purge_after
  ) into v_result from public.life_story_exports e where e.id=p_export_id;
  if v_result is null then raise exception 'EXPORT_NOT_FOUND'; end if;
  return v_result;
end;
$$;
revoke all on function public.admin_life_story_get_export(uuid) from public,anon;
grant execute on function public.admin_life_story_get_export(uuid) to authenticated;
