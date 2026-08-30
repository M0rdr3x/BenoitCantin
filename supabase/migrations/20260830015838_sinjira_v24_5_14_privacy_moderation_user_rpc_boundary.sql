-- Migration de traçabilité : couche intermédiaire appliquée en production puis supprimée
-- immédiatement par 20260830015937. Ne pas réutiliser cette architecture.

do $$
declare
  v_count int;
begin
  create schema if not exists sinjira_privacy_moderation_internal;
  revoke all on schema sinjira_privacy_moderation_internal from public;
  grant usage on schema sinjira_privacy_moderation_internal to authenticated, service_role;

  select count(*) into v_count from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and (
    (p.proname='moderation_my_decisions' and pg_get_function_identity_arguments(p.oid)='p_limit integer') or
    (p.proname='moderation_submit_appeal' and pg_get_function_identity_arguments(p.oid)='p_decision_id uuid, p_appeal_text text') or
    (p.proname='privacy_create_request' and pg_get_function_identity_arguments(p.oid)='p_request_type text, p_details text') or
    (p.proname='privacy_export_my_extended_data' and pg_get_function_identity_arguments(p.oid)='') or
    (p.proname='privacy_my_requests' and pg_get_function_identity_arguments(p.oid)='p_limit integer')
  );
  if v_count <> 5 then raise exception 'EXPECTED_5_TARGETS_FOUND_%',v_count; end if;

  alter function public.moderation_my_decisions(integer) set schema sinjira_privacy_moderation_internal;
  alter function public.moderation_submit_appeal(uuid,text) set schema sinjira_privacy_moderation_internal;
  alter function public.privacy_create_request(text,text) set schema sinjira_privacy_moderation_internal;
  alter function public.privacy_export_my_extended_data() set schema sinjira_privacy_moderation_internal;
  alter function public.privacy_my_requests(integer) set schema sinjira_privacy_moderation_internal;

  revoke all on function sinjira_privacy_moderation_internal.moderation_my_decisions(integer) from public, anon;
  revoke all on function sinjira_privacy_moderation_internal.moderation_submit_appeal(uuid,text) from public, anon;
  revoke all on function sinjira_privacy_moderation_internal.privacy_create_request(text,text) from public, anon;
  revoke all on function sinjira_privacy_moderation_internal.privacy_export_my_extended_data() from public, anon;
  revoke all on function sinjira_privacy_moderation_internal.privacy_my_requests(integer) from public, anon;

  grant execute on function sinjira_privacy_moderation_internal.moderation_my_decisions(integer) to authenticated, service_role;
  grant execute on function sinjira_privacy_moderation_internal.moderation_submit_appeal(uuid,text) to authenticated, service_role;
  grant execute on function sinjira_privacy_moderation_internal.privacy_create_request(text,text) to authenticated, service_role;
  grant execute on function sinjira_privacy_moderation_internal.privacy_export_my_extended_data() to authenticated, service_role;
  grant execute on function sinjira_privacy_moderation_internal.privacy_my_requests(integer) to authenticated, service_role;
end $$;

create function public.moderation_my_decisions(p_limit integer)
returns jsonb language sql security invoker set search_path=public,pg_temp
as $$ select sinjira_privacy_moderation_internal.moderation_my_decisions(p_limit) $$;

create function public.moderation_submit_appeal(p_decision_id uuid,p_appeal_text text)
returns jsonb language sql security invoker set search_path=public,pg_temp
as $$ select sinjira_privacy_moderation_internal.moderation_submit_appeal(p_decision_id,p_appeal_text) $$;

create function public.privacy_create_request(p_request_type text,p_details text)
returns jsonb language sql security invoker set search_path=public,pg_temp
as $$ select sinjira_privacy_moderation_internal.privacy_create_request(p_request_type,p_details) $$;

create function public.privacy_export_my_extended_data()
returns jsonb language sql security invoker set search_path=public,pg_temp
as $$ select sinjira_privacy_moderation_internal.privacy_export_my_extended_data() $$;

create function public.privacy_my_requests(p_limit integer)
returns table(id uuid,request_type text,status text,created_at timestamptz,due_at timestamptz,completed_at timestamptz,response_note text)
language sql security invoker set search_path=public,pg_temp
as $$ select * from sinjira_privacy_moderation_internal.privacy_my_requests(p_limit) $$;

revoke all on function public.moderation_my_decisions(integer) from public, anon;
revoke all on function public.moderation_submit_appeal(uuid,text) from public, anon;
revoke all on function public.privacy_create_request(text,text) from public, anon;
revoke all on function public.privacy_export_my_extended_data() from public, anon;
revoke all on function public.privacy_my_requests(integer) from public, anon;

grant execute on function public.moderation_my_decisions(integer) to authenticated, service_role;
grant execute on function public.moderation_submit_appeal(uuid,text) to authenticated, service_role;
grant execute on function public.privacy_create_request(text,text) to authenticated, service_role;
grant execute on function public.privacy_export_my_extended_data() to authenticated, service_role;
grant execute on function public.privacy_my_requests(integer) to authenticated, service_role;