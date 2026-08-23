create schema if not exists sinjira_privacy_moderation_internal;
revoke all on schema sinjira_privacy_moderation_internal from public, anon;
grant usage on schema sinjira_privacy_moderation_internal to authenticated, service_role;

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

create or replace function public.moderation_my_decisions(p_limit integer default 50)
returns jsonb language sql security invoker set search_path = public, private, extensions
as $$select sinjira_privacy_moderation_internal.moderation_my_decisions(p_limit);$$;

create or replace function public.moderation_submit_appeal(p_decision_id uuid, p_appeal_text text)
returns jsonb language sql security invoker set search_path = public, private, extensions
as $$select sinjira_privacy_moderation_internal.moderation_submit_appeal(p_decision_id,p_appeal_text);$$;

create or replace function public.privacy_create_request(p_request_type text, p_details text default null)
returns jsonb language sql security invoker set search_path = public, private, extensions
as $$select sinjira_privacy_moderation_internal.privacy_create_request(p_request_type,p_details);$$;

create or replace function public.privacy_export_my_extended_data()
returns jsonb language sql security invoker set search_path = public, private, extensions
as $$select sinjira_privacy_moderation_internal.privacy_export_my_extended_data();$$;

create or replace function public.privacy_my_requests(p_limit integer default 50)
returns table(id uuid,request_type text,status text,created_at timestamptz,due_at timestamptz,completed_at timestamptz,response_note text)
language sql security invoker set search_path = public, private, extensions
as $$select * from sinjira_privacy_moderation_internal.privacy_my_requests(p_limit);$$;

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
