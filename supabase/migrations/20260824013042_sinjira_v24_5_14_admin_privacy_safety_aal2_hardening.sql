-- SINJIRA — durcissement AAL2 des fonctions administratives confidentialité/sécurité.
-- Les wrappers publics restent SECURITY INVOKER; les implémentations internes sont SECURITY DEFINER.
-- Le rôle service_role reste accepté par require_sinjira_admin_aal2().

create or replace function sinjira_admin_internal.privacy_admin_incidents(p_limit integer default 100)
returns table(id uuid, incident_code text, occurred_at timestamptz, discovered_at timestamptz, circumstances text, personal_data_categories text, affected_people_estimate integer, serious_harm boolean, measures_taken text, authority_notification_required boolean, authority_notified_at timestamptz, affected_people_notification_required boolean, affected_people_notified_at timestamptz, status text, retention_until timestamptz, created_at timestamptz, updated_at timestamptz)
language plpgsql stable security definer set search_path to 'pg_catalog','public','private'
as $$
begin
  perform private.require_sinjira_admin_aal2();
  return query
    select i.id,i.incident_code,i.occurred_at,i.discovered_at,i.circumstances,i.personal_data_categories,i.affected_people_estimate,i.serious_harm,i.measures_taken,i.authority_notification_required,i.authority_notified_at,i.affected_people_notification_required,i.affected_people_notified_at,i.status,i.retention_until,i.created_at,i.updated_at
    from private.privacy_incident_register i
    order by (i.status='closed'),i.discovered_at desc
    limit greatest(1,least(coalesce(p_limit,100),250));
end;
$$;

create or replace function sinjira_admin_internal.privacy_admin_record_incident(p_circumstances text,p_personal_data_categories text,p_occurred_at timestamptz default null,p_affected_people_estimate integer default null,p_jurisdiction_notes text default null)
returns jsonb language plpgsql security definer set search_path to 'pg_catalog','public','private'
as $$
declare v_admin uuid; v_id uuid; v_code text;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  if btrim(coalesce(p_circumstances,''))='' or btrim(coalesce(p_personal_data_categories,''))='' then raise exception 'INCIDENT_DESCRIPTION_REQUIRED'; end if;
  insert into private.privacy_incident_register(occurred_at,circumstances,personal_data_categories,affected_people_estimate,jurisdiction_notes,created_by,updated_by)
  values(p_occurred_at,btrim(p_circumstances),btrim(p_personal_data_categories),p_affected_people_estimate,nullif(btrim(coalesce(p_jurisdiction_notes,'')),''),v_admin,v_admin)
  returning id,incident_code into v_id,v_code;
  insert into public.admin_notifications(notification_type,title,body,related_user_id,related_entity_type,related_entity_id)
  values('privacy_incident','Incident de confidentialité à évaluer','Un incident a été inscrit au registre; évaluer immédiatement le risque de préjudice sérieux et les obligations de notification.',v_admin,'privacy_incident',v_id);
  return jsonb_build_object('ok',true,'incident_id',v_id,'incident_code',v_code);
end;
$$;

create or replace function sinjira_admin_internal.privacy_admin_requests(p_limit integer default 100)
returns table(id uuid,user_id uuid,request_type text,status text,details text,created_at timestamptz,due_at timestamptz,completed_at timestamptz,response_note text)
language plpgsql stable security definer set search_path to 'pg_catalog','public','private'
as $$
begin
  perform private.require_sinjira_admin_aal2();
  return query
    select r.id,r.user_id,r.request_type,r.status,r.details,r.created_at,r.due_at,r.completed_at,r.response_note
    from private.privacy_requests r
    order by (r.status in ('completed','refused','cancelled')),r.due_at,r.created_at desc
    limit greatest(1,least(coalesce(p_limit,100),250));
end;
$$;

create or replace function sinjira_admin_internal.privacy_admin_update_request(p_request_id uuid,p_status text,p_response_note text default null)
returns jsonb language plpgsql security definer set search_path to 'pg_catalog','public','private'
as $$
declare v_status text:=lower(btrim(coalesce(p_status,''))); v_count integer;
begin
  perform private.require_sinjira_admin_aal2();
  if v_status not in ('open','identity_check','in_review','waiting_user','completed','refused','cancelled') then raise exception 'PRIVACY_REQUEST_STATUS_INVALID'; end if;
  update private.privacy_requests set status=v_status,response_note=nullif(btrim(coalesce(p_response_note,'')),''),completed_at=case when v_status in ('completed','refused','cancelled') then coalesce(completed_at,now()) else null end,updated_at=now() where id=p_request_id;
  get diagnostics v_count=row_count;
  if v_count=0 then raise exception 'PRIVACY_REQUEST_NOT_FOUND'; end if;
  return jsonb_build_object('ok',true,'status',v_status);
end;
$$;

create or replace function sinjira_admin_internal.safety_admin_escalation_cases(p_limit integer default 100)
returns table(id uuid,source_report_id uuid,category text,status text,jurisdiction text,external_report_reference text,legal_preservation_until timestamptz,notes text,created_at timestamptz,updated_at timestamptz)
language plpgsql stable security definer set search_path to 'pg_catalog','public','private'
as $$
begin
  perform private.require_sinjira_admin_aal2();
  return query
    select c.id,c.source_report_id,c.category,c.status,c.jurisdiction,c.external_report_reference,c.legal_preservation_until,c.notes,c.created_at,c.updated_at
    from private.safety_escalation_cases c
    order by (c.status='closed'),c.created_at desc
    limit greatest(1,least(coalesce(p_limit,100),250));
end;
$$;
