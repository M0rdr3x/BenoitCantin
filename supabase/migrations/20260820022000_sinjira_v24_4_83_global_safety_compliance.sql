-- SINJIRA™ V24.4.83 — socle de conformité et de sécurité globale.
-- Objectifs: 13+ en libre-service, autorisation parentale à 13 ans, registre d'incidents 5 ans,
-- demandes de droits structurées, dossiers d'escalade sécurité et confidentialité élevée par défaut.
-- Aucun fournisseur payant, paiement, IA distante ou service d'identité externe n'est activé ici.

-- -----------------------------------------------------------------------------
-- 1. Âge minimal : 13+ en libre-service; à 13 ans, autorisation parent/tuteur obligatoire.
-- -----------------------------------------------------------------------------
create or replace function public.enforce_sinjira_account_safety_age()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
declare years integer;
begin
  if new.date_of_birth is null then raise exception 'BIRTH_DATE_REQUIRED'; end if;
  if new.date_of_birth>current_date then raise exception 'INVALID_BIRTH_DATE'; end if;
  years:=extract(year from age(current_date,new.date_of_birth))::integer;
  if years<13 then raise exception 'SINJIRA_MINIMUM_AGE_13'; end if;
  if years>120 then raise exception 'INVALID_BIRTH_DATE'; end if;
  if new.sex is not null and new.sex not in ('female','male') then raise exception 'SEX_REQUIRED_FEMALE_OR_MALE'; end if;
  return new;
end;
$$;

create or replace function public.handle_new_sinjira_user()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
declare
  c boolean:=coalesce((new.raw_user_meta_data->>'initial_contributor_opt_in')::boolean,false);
  f boolean:=coalesce((new.raw_user_meta_data->>'initial_share_free_text')::boolean,false);
  dob date;
  sx text;
  raw_dob text;
  raw_sex text;
  years integer;
  guardian_code text:=upper(trim(coalesce(new.raw_user_meta_data->>'guardian_code','')));
  inv public.guardian_signup_invites%rowtype;
begin
  raw_dob:=coalesce(nullif(new.raw_user_meta_data->>'birth_date',''),nullif(new.raw_user_meta_data->>'date_of_birth',''));
  begin dob:=raw_dob::date; exception when others then dob:=null; end;
  if dob is null then raise exception 'BIRTH_DATE_REQUIRED'; end if;
  if dob>current_date then raise exception 'INVALID_BIRTH_DATE'; end if;
  years:=extract(year from age(current_date,dob))::integer;
  if years<13 then raise exception 'SINJIRA_MINIMUM_AGE_13'; end if;
  if years>120 then raise exception 'INVALID_BIRTH_DATE'; end if;

  raw_sex:=trim(coalesce(new.raw_user_meta_data->>'gender',new.raw_user_meta_data->>'sex',''));
  sx:=case lower(raw_sex)
    when 'femme' then 'female' when 'female' then 'female'
    when 'homme' then 'male' when 'male' then 'male'
    else null end;
  if sx is null then raise exception 'SEX_REQUIRED_FEMALE_OR_MALE'; end if;

  -- Québec: moins de 14 ans => autorisation parent/tuteur. Avec le minimum 13+, cela vise l'âge de 13 ans.
  if years<14 then
    if guardian_code='' then raise exception 'GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14'; end if;
    select * into inv from public.guardian_signup_invites
      where invite_code=guardian_code and used_at is null and expires_at>now()
      for update;
    if inv.id is null then raise exception 'INVALID_OR_EXPIRED_GUARDIAN_CODE'; end if;
    if public.sinjira_age_band(inv.guardian_user_id)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;
  elsif guardian_code<>'' then
    select * into inv from public.guardian_signup_invites
      where invite_code=guardian_code and used_at is null and expires_at>now()
      for update;
    if inv.id is null then raise exception 'INVALID_OR_EXPIRED_GUARDIAN_CODE'; end if;
    if public.sinjira_age_band(inv.guardian_user_id)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;
  end if;

  insert into public.profiles(user_id,pseudo,display_name)
    values(new.id,coalesce(nullif(new.raw_user_meta_data->>'pseudo',''),'Joueur SINJIRA'),nullif(new.raw_user_meta_data->>'display_name',''))
    on conflict(user_id) do update set pseudo=excluded.pseudo,display_name=excluded.display_name,updated_at=now();

  insert into public.research_consents(user_id,participate,share_free_text,consent_version,consented_at)
    values(new.id,c,c and f,'sinjira-gameplay-v2',case when c then now() else null end)
    on conflict(user_id) do nothing;

  insert into public.account_safety_profiles(user_id,date_of_birth,sex,birthday_greeting_opt_in,real_life_to_fiction_opt_in,relationship_data_opt_in,relationship_status,legacy_status)
    values(new.id,dob,sx,true,false,false,'not_specified','active')
    on conflict(user_id) do update set date_of_birth=excluded.date_of_birth,sex=excluded.sex,updated_at=now();

  insert into public.account_legacy_preferences(user_id,account_after_death,final_story_tone,memorial_public_opt_in,transfer_private_story_to_family)
    values(new.id,'memorialize','peaceful',true,false) on conflict(user_id) do nothing;

  if inv.id is not null and years<18 then
    insert into public.guardian_links(minor_user_id,guardian_user_id,status,guardian_role,can_view_contact_metadata,consented_at)
      values(new.id,inv.guardian_user_id,'verified','parent',true,inv.consented_at)
      on conflict do nothing;
    update public.guardian_signup_invites set used_at=now(),minor_user_id=new.id where id=inv.id;
  end if;
  return new;
end;
$$;

-- -----------------------------------------------------------------------------
-- 2. Registre interne des incidents de confidentialité, conservation >= 5 ans.
-- -----------------------------------------------------------------------------
create table if not exists private.privacy_incident_register(
  id uuid primary key default gen_random_uuid(),
  incident_code text not null unique default ('INC-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,12))),
  occurred_at timestamptz,
  discovered_at timestamptz not null default now(),
  circumstances text not null,
  personal_data_categories text not null,
  affected_people_estimate integer check (affected_people_estimate is null or affected_people_estimate>=0),
  sensitivity_assessment text not null default 'à évaluer',
  malicious_use_assessment text not null default 'à évaluer',
  consequence_assessment text not null default 'à évaluer',
  likelihood_assessment text not null default 'à évaluer',
  serious_harm boolean,
  measures_taken text not null default '',
  authority_notification_required boolean,
  authority_notified_at timestamptz,
  affected_people_notification_required boolean,
  affected_people_notified_at timestamptz,
  public_notice_used boolean not null default false,
  public_notice_reason text,
  jurisdiction_notes text,
  status text not null default 'open' check(status in ('open','contained','assessing','notifications','closed')),
  retention_until timestamptz not null default (now()+interval '5 years'),
  created_by uuid references auth.users(id) on delete set null,
  updated_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function private.privacy_incident_retention_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,private
as $$
begin
  if tg_op='DELETE' then
    if old.retention_until>now() then raise exception 'PRIVACY_INCIDENT_RETENTION_ACTIVE'; end if;
    return old;
  end if;
  new.retention_until:=greatest(coalesce(new.retention_until,new.discovered_at+interval '5 years'),new.discovered_at+interval '5 years');
  new.updated_at:=now();
  return new;
end;
$$;

drop trigger if exists privacy_incident_retention_guard on private.privacy_incident_register;
create trigger privacy_incident_retention_guard
before insert or update or delete on private.privacy_incident_register
for each row execute function private.privacy_incident_retention_guard();

alter table private.privacy_incident_register enable row level security;
revoke all on private.privacy_incident_register from public,anon,authenticated;

-- -----------------------------------------------------------------------------
-- 3. Demandes relatives aux renseignements personnels / droits des personnes.
-- -----------------------------------------------------------------------------
create table if not exists private.privacy_requests(
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  request_type text not null check(request_type in ('access','portability','rectification','deletion','consent_withdrawal','objection','complaint','other')),
  details text,
  status text not null default 'open' check(status in ('open','identity_check','in_review','waiting_user','completed','refused','cancelled')),
  created_at timestamptz not null default now(),
  due_at timestamptz not null default (now()+interval '30 days'),
  completed_at timestamptz,
  response_note text,
  updated_at timestamptz not null default now()
);
create index if not exists privacy_requests_user_created_idx on private.privacy_requests(user_id,created_at desc);
create index if not exists privacy_requests_open_due_idx on private.privacy_requests(status,due_at) where status not in ('completed','refused','cancelled');
alter table private.privacy_requests enable row level security;
revoke all on private.privacy_requests from public,anon,authenticated;

create table if not exists private.privacy_legal_holds(
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  source_type text not null,
  source_id uuid,
  reason text not null,
  jurisdiction text,
  starts_at timestamptz not null default now(),
  expires_at timestamptz,
  released_at timestamptz,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  check(expires_at is null or expires_at>starts_at)
);
alter table private.privacy_legal_holds enable row level security;
revoke all on private.privacy_legal_holds from public,anon,authenticated;

create or replace function public.privacy_create_request(p_request_type text,p_details text default null)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare v_user uuid:=auth.uid(); v_id uuid; v_type text:=lower(btrim(coalesce(p_request_type,''))); v_details text:=nullif(btrim(coalesce(p_details,'')),'');
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if v_type not in ('access','portability','rectification','deletion','consent_withdrawal','objection','complaint','other') then raise exception 'PRIVACY_REQUEST_TYPE_INVALID'; end if;
  if v_details is not null and char_length(v_details)>4000 then raise exception 'PRIVACY_REQUEST_DETAILS_TOO_LONG'; end if;
  if (select count(*) from private.privacy_requests r where r.user_id=v_user and r.status not in ('completed','refused','cancelled'))>=5 then raise exception 'PRIVACY_REQUEST_OPEN_LIMIT'; end if;
  insert into private.privacy_requests(user_id,request_type,details) values(v_user,v_type,v_details) returning id into v_id;
  insert into public.admin_notifications(notification_type,title,body,related_user_id,related_entity_type,related_entity_id)
    values('privacy_request','Nouvelle demande de vie privée','Une demande relative aux renseignements personnels requiert une révision.',v_user,'privacy_request',v_id);
  return jsonb_build_object('ok',true,'request_id',v_id,'target_days',30);
end;
$$;

create or replace function public.privacy_my_requests(p_limit integer default 20)
returns table(id uuid,request_type text,status text,created_at timestamptz,due_at timestamptz,completed_at timestamptz,response_note text)
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $$
  select r.id,r.request_type,r.status,r.created_at,r.due_at,r.completed_at,r.response_note
  from private.privacy_requests r
  where r.user_id=auth.uid()
  order by r.created_at desc
  limit greatest(1,least(coalesce(p_limit,20),50));
$$;

create or replace function public.privacy_admin_requests(p_limit integer default 100)
returns table(id uuid,user_id uuid,request_type text,status text,details text,created_at timestamptz,due_at timestamptz,completed_at timestamptz,response_note text)
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $$
begin
  if auth.uid() is null or not public.is_sinjira_admin(auth.uid()) then raise exception 'ADMIN_REQUIRED'; end if;
  return query select r.id,r.user_id,r.request_type,r.status,r.details,r.created_at,r.due_at,r.completed_at,r.response_note
  from private.privacy_requests r order by (r.status in ('completed','refused','cancelled')),r.due_at,r.created_at desc
  limit greatest(1,least(coalesce(p_limit,100),250));
end;
$$;

create or replace function public.privacy_admin_update_request(p_request_id uuid,p_status text,p_response_note text default null)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare v_status text:=lower(btrim(coalesce(p_status,''))); v_count integer;
begin
  if auth.uid() is null or not public.is_sinjira_admin(auth.uid()) then raise exception 'ADMIN_REQUIRED'; end if;
  if v_status not in ('open','identity_check','in_review','waiting_user','completed','refused','cancelled') then raise exception 'PRIVACY_REQUEST_STATUS_INVALID'; end if;
  update private.privacy_requests set status=v_status,response_note=nullif(btrim(coalesce(p_response_note,'')),''),
    completed_at=case when v_status in ('completed','refused','cancelled') then coalesce(completed_at,now()) else null end,updated_at=now()
  where id=p_request_id;
  get diagnostics v_count=row_count;
  if v_count=0 then raise exception 'PRIVACY_REQUEST_NOT_FOUND'; end if;
  return jsonb_build_object('ok',true,'status',v_status);
end;
$$;

-- -----------------------------------------------------------------------------
-- 4. Dossiers d'escalade sécurité: références minimales, jamais une copie d'un média illicite.
-- -----------------------------------------------------------------------------
create table if not exists private.safety_escalation_cases(
  id uuid primary key default gen_random_uuid(),
  source_report_id uuid not null unique references public.social_reports(id) on delete restrict,
  category text not null,
  status text not null default 'triage' check(status in ('triage','review','preserve','reported','closed')),
  jurisdiction text,
  external_report_reference text,
  legal_preservation_until timestamptz,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table private.safety_escalation_cases enable row level security;
revoke all on private.safety_escalation_cases from public,anon,authenticated;

create or replace function private.safety_create_escalation_case()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
begin
  if new.reason in ('minor_safety','grooming','sexual_exploitation','human_trafficking','paid_sexual_content','drugs_or_illicit_sales','off_platform_minor_contact') then
    insert into private.safety_escalation_cases(source_report_id,category)
      values(new.id,new.reason) on conflict(source_report_id) do nothing;
  end if;
  return new;
end;
$$;
drop trigger if exists trg_safety_create_escalation_case on public.social_reports;
create trigger trg_safety_create_escalation_case after insert on public.social_reports
for each row execute function private.safety_create_escalation_case();

create or replace function public.safety_admin_escalation_cases(p_limit integer default 100)
returns table(id uuid,source_report_id uuid,category text,status text,jurisdiction text,external_report_reference text,legal_preservation_until timestamptz,notes text,created_at timestamptz,updated_at timestamptz)
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $$
begin
  if auth.uid() is null or not public.is_sinjira_admin(auth.uid()) then raise exception 'ADMIN_REQUIRED'; end if;
  return query select c.id,c.source_report_id,c.category,c.status,c.jurisdiction,c.external_report_reference,c.legal_preservation_until,c.notes,c.created_at,c.updated_at
    from private.safety_escalation_cases c order by (c.status='closed'),c.created_at desc limit greatest(1,least(coalesce(p_limit,100),250));
end;
$$;

create or replace function public.privacy_admin_record_incident(
  p_circumstances text,
  p_personal_data_categories text,
  p_occurred_at timestamptz default null,
  p_affected_people_estimate integer default null,
  p_jurisdiction_notes text default null
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare v_id uuid; v_code text;
begin
  if auth.uid() is null or not public.is_sinjira_admin(auth.uid()) then raise exception 'ADMIN_REQUIRED'; end if;
  if btrim(coalesce(p_circumstances,''))='' or btrim(coalesce(p_personal_data_categories,''))='' then raise exception 'INCIDENT_DESCRIPTION_REQUIRED'; end if;
  insert into private.privacy_incident_register(occurred_at,circumstances,personal_data_categories,affected_people_estimate,jurisdiction_notes,created_by,updated_by)
  values(p_occurred_at,btrim(p_circumstances),btrim(p_personal_data_categories),p_affected_people_estimate,nullif(btrim(coalesce(p_jurisdiction_notes,'')),''),auth.uid(),auth.uid())
  returning id,incident_code into v_id,v_code;
  insert into public.admin_notifications(notification_type,title,body,related_user_id,related_entity_type,related_entity_id)
    values('privacy_incident','Incident de confidentialité à évaluer','Un incident a été inscrit au registre; évaluer immédiatement le risque de préjudice sérieux et les obligations de notification.',auth.uid(),'privacy_incident',v_id);
  return jsonb_build_object('ok',true,'incident_id',v_id,'incident_code',v_code);
end;
$$;

create or replace function public.privacy_admin_incidents(p_limit integer default 100)
returns table(id uuid,incident_code text,occurred_at timestamptz,discovered_at timestamptz,circumstances text,personal_data_categories text,affected_people_estimate integer,serious_harm boolean,measures_taken text,authority_notification_required boolean,authority_notified_at timestamptz,affected_people_notification_required boolean,affected_people_notified_at timestamptz,status text,retention_until timestamptz,created_at timestamptz,updated_at timestamptz)
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $$
begin
  if auth.uid() is null or not public.is_sinjira_admin(auth.uid()) then raise exception 'ADMIN_REQUIRED'; end if;
  return query select i.id,i.incident_code,i.occurred_at,i.discovered_at,i.circumstances,i.personal_data_categories,i.affected_people_estimate,i.serious_harm,i.measures_taken,i.authority_notification_required,i.authority_notified_at,i.affected_people_notification_required,i.affected_people_notified_at,i.status,i.retention_until,i.created_at,i.updated_at
  from private.privacy_incident_register i order by (i.status='closed'),i.discovered_at desc limit greatest(1,least(coalesce(p_limit,100),250));
end;
$$;

revoke all on function public.privacy_create_request(text,text),public.privacy_my_requests(integer),public.privacy_admin_requests(integer),public.privacy_admin_update_request(uuid,text,text),public.safety_admin_escalation_cases(integer),public.privacy_admin_record_incident(text,text,timestamptz,integer,text),public.privacy_admin_incidents(integer) from public,anon;
grant execute on function public.privacy_create_request(text,text),public.privacy_my_requests(integer) to authenticated;
grant execute on function public.privacy_admin_requests(integer),public.privacy_admin_update_request(uuid,text,text),public.safety_admin_escalation_cases(integer),public.privacy_admin_record_incident(text,text,timestamptz,integer,text),public.privacy_admin_incidents(integer) to authenticated;

comment on table private.privacy_incident_register is 'Registre interne des incidents de confidentialité; conservation minimale de cinq ans à partir de la découverte.';
comment on table private.privacy_requests is 'Demandes structurées d’accès, portabilité, rectification, suppression, retrait de consentement, opposition et plainte.';
comment on table private.safety_escalation_cases is 'Dossiers internes de triage pour signalements prioritaires; conserve des références et métadonnées, pas une copie de média illicite.';
