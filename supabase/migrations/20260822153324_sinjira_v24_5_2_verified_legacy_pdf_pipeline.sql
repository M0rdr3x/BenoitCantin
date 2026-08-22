create table public.life_story_posthumous_cases (
  id uuid primary key default gen_random_uuid(),
  memorial_request_id uuid not null unique references public.memorial_requests(id) on delete restrict,
  subject_user_id uuid not null references auth.users(id) on delete restrict,
  status text not null default 'verified_hold' check (status = any (array['verified_hold','contested','rejected','ready_for_export','closed_no_delivery','completed']::text[])),
  date_of_death date not null,
  verification_basis text not null check (verification_basis = any (array['official_record','funeral_home','family_document','other_verified']::text[])),
  first_verified_by uuid references auth.users(id) on delete set null,
  first_verified_at timestamptz not null default now(),
  hold_until timestamptz not null,
  second_confirmed_by uuid references auth.users(id) on delete set null,
  second_confirmed_at timestamptz,
  source_boundary text not null default 'life_story_only' check (source_boundary='life_story_only'),
  registry_access_prohibited boolean not null default true check (registry_access_prohibited=true),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id,subject_user_id)
);

create unique index life_story_one_active_case_per_subject_idx
on public.life_story_posthumous_cases(subject_user_id)
where status in ('verified_hold','contested','ready_for_export');
create index life_story_posthumous_cases_status_idx on public.life_story_posthumous_cases(status,hold_until);
create index life_story_posthumous_cases_subject_idx on public.life_story_posthumous_cases(subject_user_id,created_at desc);

create table public.life_story_posthumous_contests (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null,
  subject_user_id uuid not null,
  reason text not null check (char_length(btrim(reason)) between 5 and 3000),
  status text not null default 'open' check (status = any (array['open','upheld','dismissed']::text[])),
  submitted_at timestamptz not null default now(),
  resolved_at timestamptz,
  resolved_by uuid references auth.users(id) on delete set null,
  resolution_note text check (resolution_note is null or char_length(resolution_note)<=3000),
  constraint life_story_contests_case_subject_fkey foreign key (case_id,subject_user_id)
    references public.life_story_posthumous_cases(id,subject_user_id) on delete cascade
);
create unique index life_story_one_open_contest_idx on public.life_story_posthumous_contests(case_id) where status='open';
create index life_story_contests_subject_idx on public.life_story_posthumous_contests(subject_user_id,submitted_at desc);

create table public.life_story_exports (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references public.life_story_posthumous_cases(id) on delete restrict,
  subject_user_id uuid not null references auth.users(id) on delete restrict,
  version_id uuid not null references public.life_story_versions(id) on delete restrict,
  audience text not null check (audience = any (array['family','personal','general']::text[])),
  status text not null default 'prepared' check (status = any (array['prepared','generated','delivered','revoked','purged']::text[])),
  content_snapshot jsonb not null,
  recipients_snapshot jsonb not null default '[]'::jsonb,
  source_boundary text not null default 'life_story_only' check (source_boundary='life_story_only'),
  registry_access_prohibited boolean not null default true check (registry_access_prohibited=true),
  storage_bucket text check (storage_bucket is null or storage_bucket='sinjira-life-story-exports'),
  storage_path text,
  sha256 text check (sha256 is null or sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz,
  delivery_completed_at timestamptz,
  purge_after timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (case_id,version_id),
  constraint life_story_export_subject_case_fkey foreign key (case_id,subject_user_id)
    references public.life_story_posthumous_cases(id,subject_user_id) on delete restrict
);
create index life_story_exports_subject_idx on public.life_story_exports(subject_user_id,created_at desc);
create index life_story_exports_purge_idx on public.life_story_exports(status,purge_after) where purge_after is not null;

create table public.life_story_delivery_links (
  id uuid primary key default gen_random_uuid(),
  export_id uuid not null references public.life_story_exports(id) on delete cascade,
  recipient_index integer not null check (recipient_index>=0),
  recipient_label text not null check (char_length(btrim(recipient_label)) between 1 and 160),
  token_hash text not null unique check (token_hash ~ '^[a-f0-9]{64}$'),
  expires_at timestamptz not null,
  max_downloads integer not null default 3 check (max_downloads between 1 and 10),
  download_count integer not null default 0 check (download_count>=0),
  last_downloaded_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  unique (export_id,recipient_index)
);
create index life_story_delivery_expiry_idx on public.life_story_delivery_links(expires_at) where revoked_at is null;

create table public.life_story_cleanup_tasks (
  id uuid primary key default gen_random_uuid(),
  case_id uuid not null references public.life_story_posthumous_cases(id) on delete restrict,
  subject_user_id uuid not null references auth.users(id) on delete restrict,
  task_type text not null check (task_type = any (array['life_story_source_review','registry_private_data_review']::text[])),
  status text not null default 'pending' check (status = any (array['pending','completed','skipped']::text[])),
  due_after timestamptz not null,
  completed_by uuid references auth.users(id) on delete set null,
  completed_at timestamptz,
  completion_note text check (completion_note is null or char_length(completion_note)<=3000),
  created_at timestamptz not null default now(),
  unique(case_id,task_type)
);
create index life_story_cleanup_due_idx on public.life_story_cleanup_tasks(status,due_after);

comment on table public.life_story_posthumous_cases is 'Dossier posthume humainement vérifié. Aucun accès au Registre n est autorisé par ce pipeline.';
comment on table public.life_story_exports is 'Instantané figé exclusivement depuis Histoire de vie explicitement autorisée; jamais depuis le Registre.';
comment on table public.life_story_delivery_links is 'Jetons de remise limités; seul le hash du jeton est conservé.';
comment on table public.life_story_cleanup_tasks is 'Revue humaine obligatoire avant toute suppression irréversible de données sources posthumes.';

create trigger life_story_posthumous_cases_touch before update on public.life_story_posthumous_cases for each row execute function private.life_story_touch_updated_at();
create trigger life_story_exports_touch before update on public.life_story_exports for each row execute function private.life_story_touch_updated_at();

alter table public.life_story_posthumous_cases enable row level security;
alter table public.life_story_posthumous_contests enable row level security;
alter table public.life_story_exports enable row level security;
alter table public.life_story_delivery_links enable row level security;
alter table public.life_story_cleanup_tasks enable row level security;

revoke all on public.life_story_posthumous_cases,public.life_story_posthumous_contests,public.life_story_exports,public.life_story_delivery_links,public.life_story_cleanup_tasks from public,anon,authenticated;

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values ('sinjira-life-story-exports','sinjira-life-story-exports',false,15728640,array['application/pdf']::text[])
on conflict(id) do update set public=false,file_size_limit=excluded.file_size_limit,allowed_mime_types=excluded.allowed_mime_types;

create or replace function public.life_story_my_posthumous_case()
returns jsonb
language plpgsql
stable
security definer
set search_path to 'pg_catalog','public','auth'
as $$
declare
  v_user uuid:=auth.uid();
  v_result jsonb;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.sinjira_mfa_access_allowed(v_user) then raise exception 'MFA_REQUIRED'; end if;
  select jsonb_build_object(
    'case_id',c.id,
    'status',c.status,
    'date_of_death',c.date_of_death,
    'first_verified_at',c.first_verified_at,
    'hold_until',c.hold_until,
    'second_confirmed_at',c.second_confirmed_at,
    'can_contest',c.status in ('verified_hold','ready_for_export'),
    'open_contest',exists(select 1 from public.life_story_posthumous_contests x where x.case_id=c.id and x.status='open')
  ) into v_result
  from public.life_story_posthumous_cases c
  where c.subject_user_id=v_user
  order by c.created_at desc limit 1;
  return coalesce(v_result,'{}'::jsonb);
end;
$$;

create or replace function public.life_story_contest_death_verification(p_case_id uuid,p_reason text)
returns uuid
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth'
as $$
declare
  v_user uuid:=auth.uid();
  v_case public.life_story_posthumous_cases%rowtype;
  v_id uuid;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.sinjira_mfa_access_allowed(v_user) then raise exception 'MFA_REQUIRED'; end if;
  if char_length(btrim(coalesce(p_reason,'')))<5 then raise exception 'CONTEST_REASON_REQUIRED'; end if;
  select * into v_case from public.life_story_posthumous_cases where id=p_case_id and subject_user_id=v_user for update;
  if not found then raise exception 'CASE_NOT_FOUND'; end if;
  if v_case.status not in ('verified_hold','ready_for_export') then raise exception 'CASE_NOT_CONTESTABLE'; end if;
  if exists(select 1 from public.life_story_posthumous_contests where case_id=p_case_id and status='open') then raise exception 'CONTEST_ALREADY_OPEN'; end if;
  insert into public.life_story_posthumous_contests(case_id,subject_user_id,reason)
  values(p_case_id,v_user,btrim(p_reason)) returning id into v_id;
  update public.life_story_posthumous_cases set status='contested' where id=p_case_id;
  return v_id;
end;
$$;

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
      case when c.id is null then null else c.id end as case_id,
      c.status as case_status,c.hold_until,c.first_verified_at,c.second_confirmed_at,
      exists(select 1 from public.life_story_posthumous_contests z where z.case_id=c.id and z.status='open') as has_open_contest
    from public.memorial_requests r
    left join public.life_story_posthumous_cases c on c.memorial_request_id=r.id
    where r.status in ('pending','verified') or c.status in ('verified_hold','contested','ready_for_export')
    order by r.created_at desc
    limit least(greatest(coalesce(p_limit,100),1),250)
  ) x;
  return v_result;
end;
$$;

create or replace function public.admin_life_story_verify_death(
  p_memorial_request_id uuid,
  p_date_of_death date,
  p_verification_basis text
)
returns uuid
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare
  v_admin uuid;
  v_request public.memorial_requests%rowtype;
  v_case_id uuid;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  if p_date_of_death is null or p_date_of_death>current_date then raise exception 'INVALID_DATE_OF_DEATH'; end if;
  if p_verification_basis not in ('official_record','funeral_home','family_document','other_verified') then raise exception 'INVALID_VERIFICATION_BASIS'; end if;
  select * into v_request from public.memorial_requests where id=p_memorial_request_id for update;
  if not found then raise exception 'MEMORIAL_REQUEST_NOT_FOUND'; end if;
  if v_request.status not in ('pending','verified') then raise exception 'MEMORIAL_REQUEST_NOT_PENDING'; end if;
  if exists(select 1 from public.life_story_posthumous_cases where memorial_request_id=p_memorial_request_id) then raise exception 'CASE_ALREADY_EXISTS'; end if;
  update public.memorial_requests
  set status='verified',verified_by=v_admin,verified_at=now(),date_of_death=p_date_of_death,
      verification_note='Vérification humaine SINJIRA V24.5.2 — aucune preuve brute conservée dans le dossier applicatif.'
  where id=p_memorial_request_id;
  insert into public.life_story_posthumous_cases(
    memorial_request_id,subject_user_id,date_of_death,verification_basis,first_verified_by,first_verified_at,hold_until
  ) values(
    p_memorial_request_id,v_request.subject_user_id,p_date_of_death,p_verification_basis,v_admin,now(),now()+interval '30 days'
  ) returning id into v_case_id;
  return v_case_id;
end;
$$;

create or replace function public.admin_life_story_resolve_contest(p_case_id uuid,p_resolution text,p_note text default null)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid; v_contest public.life_story_posthumous_contests%rowtype; v_request uuid;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  if p_resolution not in ('upheld','dismissed') then raise exception 'INVALID_RESOLUTION'; end if;
  select * into v_contest from public.life_story_posthumous_contests where case_id=p_case_id and status='open' for update;
  if not found then raise exception 'OPEN_CONTEST_NOT_FOUND'; end if;
  update public.life_story_posthumous_contests set status=p_resolution,resolved_at=now(),resolved_by=v_admin,resolution_note=nullif(btrim(coalesce(p_note,'')),'') where id=v_contest.id;
  if p_resolution='upheld' then
    update public.life_story_posthumous_cases set status='rejected',second_confirmed_by=null,second_confirmed_at=null where id=p_case_id returning memorial_request_id into v_request;
    update public.memorial_requests set status='rejected' where id=v_request;
  else
    update public.life_story_posthumous_cases set status='verified_hold',hold_until=now()+interval '30 days',second_confirmed_by=null,second_confirmed_at=null where id=p_case_id;
  end if;
end;
$$;

create or replace function public.admin_life_story_confirm_case(p_case_id uuid)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid; v_case public.life_story_posthumous_cases%rowtype; v_enabled boolean;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select * into v_case from public.life_story_posthumous_cases where id=p_case_id for update;
  if not found then raise exception 'CASE_NOT_FOUND'; end if;
  if v_case.status<>'verified_hold' then raise exception 'CASE_NOT_IN_HOLD'; end if;
  if v_case.hold_until>now() then raise exception 'SAFETY_HOLD_NOT_ELAPSED'; end if;
  if exists(select 1 from public.life_story_posthumous_contests where case_id=p_case_id and status='open') then raise exception 'OPEN_CONTEST_EXISTS'; end if;
  select delivery_enabled into v_enabled from public.life_story_legacy_settings where user_id=v_case.subject_user_id;
  if coalesce(v_enabled,false) is false then raise exception 'POSTHUMOUS_DELIVERY_NOT_AUTHORIZED'; end if;
  update public.life_story_posthumous_cases set status='ready_for_export',second_confirmed_by=v_admin,second_confirmed_at=now() where id=p_case_id;
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
  if exists(select 1 from public.life_story_posthumous_contests where case_id=p_case_id and status='open') then raise exception 'OPEN_CONTEST_EXISTS'; end if;
  select count(*) into v_recipient_count from public.life_story_recipients where user_id=v_case.subject_user_id and status='active';
  if v_recipient_count>0 then raise exception 'ACTIVE_RECIPIENTS_EXIST'; end if;
  update public.life_story_posthumous_cases set status='closed_no_delivery',second_confirmed_by=coalesce(second_confirmed_by,v_admin),second_confirmed_at=coalesce(second_confirmed_at,now()) where id=p_case_id;
  insert into public.life_story_cleanup_tasks(case_id,subject_user_id,task_type,due_after)
  values(p_case_id,v_case.subject_user_id,'life_story_source_review',now()+interval '90 days'),(p_case_id,v_case.subject_user_id,'registry_private_data_review',now()+interval '90 days')
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
    'entry_id',e.id,'title',e.title,'body',e.body,'occurred_on',e.occurred_on,
    'entry_type',e.entry_type,'knowledge_status',e.knowledge_status,'source_kind',e.source_kind,
    'sort_order',m.sort_order,'user_approved_at',e.user_approved_at
  ) order by m.sort_order,e.created_at),'[]'::jsonb)
  into v_entries
  from public.life_story_version_entries m
  join public.life_story_entries e on e.id=m.entry_id and e.user_id=m.user_id
  where m.version_id=v_version.id and m.user_id=v_case.subject_user_id
    and e.approval_status='approved' and e.posthumous_disclosure='selected_versions' and e.user_approved_at is not null;
  if jsonb_array_length(v_entries)=0 then raise exception 'LIFE_STORY_VERSION_EMPTY'; end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'recipient_id',r.id,'recipient_kind',r.recipient_kind,'recipient_label',r.recipient_label,
    'recipient_email',r.recipient_email,'recipient_user_id',r.recipient_user_id
  ) order by r.created_at),'[]'::jsonb)
  into v_recipients
  from public.life_story_recipients r
  where r.user_id=v_case.subject_user_id and r.version_id=v_version.id and r.status='active';
  if jsonb_array_length(v_recipients)=0 then raise exception 'LIFE_STORY_NO_RECIPIENTS'; end if;
  insert into public.life_story_exports(
    case_id,subject_user_id,version_id,audience,status,content_snapshot,recipients_snapshot
  ) values(
    p_case_id,v_case.subject_user_id,v_version.id,v_version.audience,'prepared',
    jsonb_build_object(
      'schema_version','24.5.2','source_boundary','life_story_only','registry_access_prohibited',true,
      'version',jsonb_build_object('id',v_version.id,'audience',v_version.audience,'name',v_version.name,'title',v_version.title,'instructions',v_version.instructions),
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

create or replace function public.admin_life_story_get_export(p_export_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid; v_result jsonb;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select jsonb_build_object(
    'id',e.id,'case_id',e.case_id,'subject_user_id',e.subject_user_id,'version_id',e.version_id,
    'audience',e.audience,'status',e.status,'content_snapshot',e.content_snapshot,'recipients_snapshot',e.recipients_snapshot,
    'storage_bucket',e.storage_bucket,'storage_path',e.storage_path,'sha256',e.sha256,'generated_at',e.generated_at,
    'delivery_completed_at',e.delivery_completed_at,'purge_after',e.purge_after
  ) into v_result from public.life_story_exports e where e.id=p_export_id;
  if v_result is null then raise exception 'EXPORT_NOT_FOUND'; end if;
  return v_result;
end;
$$;

create or replace function public.admin_life_story_case_detail(p_case_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid; v_result jsonb;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  select jsonb_build_object(
    'case',jsonb_build_object('id',c.id,'memorial_request_id',c.memorial_request_id,'status',c.status,'date_of_death',c.date_of_death,'verification_basis',c.verification_basis,'first_verified_at',c.first_verified_at,'hold_until',c.hold_until,'second_confirmed_at',c.second_confirmed_at),
    'contests',coalesce((select jsonb_agg(jsonb_build_object('id',x.id,'reason',x.reason,'status',x.status,'submitted_at',x.submitted_at,'resolved_at',x.resolved_at,'resolution_note',x.resolution_note) order by x.submitted_at desc) from public.life_story_posthumous_contests x where x.case_id=c.id),'[]'::jsonb),
    'versions',coalesce((select jsonb_agg(jsonb_build_object('id',v.id,'audience',v.audience,'name',v.name,'title',v.title,'status',v.status,'recipient_count',(select count(*) from public.life_story_recipients r where r.version_id=v.id and r.status='active'),'authorized_entry_count',(select count(*) from public.life_story_version_entries m where m.version_id=v.id)) order by v.audience) from public.life_story_versions v where v.user_id=c.subject_user_id),'[]'::jsonb),
    'exports',coalesce((select jsonb_agg(jsonb_build_object('id',e.id,'version_id',e.version_id,'audience',e.audience,'status',e.status,'generated_at',e.generated_at,'delivery_completed_at',e.delivery_completed_at,'purge_after',e.purge_after) order by e.created_at) from public.life_story_exports e where e.case_id=c.id),'[]'::jsonb),
    'cleanup_tasks',coalesce((select jsonb_agg(jsonb_build_object('id',t.id,'task_type',t.task_type,'status',t.status,'due_after',t.due_after,'completed_at',t.completed_at) order by t.due_after) from public.life_story_cleanup_tasks t where t.case_id=c.id),'[]'::jsonb)
  ) into v_result from public.life_story_posthumous_cases c where c.id=p_case_id;
  if v_result is null then raise exception 'CASE_NOT_FOUND'; end if;
  return v_result;
end;
$$;

create or replace function public.service_life_story_mark_export_generated(p_export_id uuid,p_storage_path text,p_sha256 text)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth'
as $$
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'SERVICE_ROLE_REQUIRED'; end if;
  if p_storage_path is null or p_storage_path='' or p_sha256 !~ '^[a-f0-9]{64}$' then raise exception 'INVALID_EXPORT_METADATA'; end if;
  update public.life_story_exports set status='generated',storage_bucket='sinjira-life-story-exports',storage_path=p_storage_path,sha256=p_sha256,generated_at=now() where id=p_export_id and status in ('prepared','generated');
  if not found then raise exception 'EXPORT_NOT_PREPARED'; end if;
end;
$$;

create or replace function public.service_life_story_register_download(p_link_id uuid)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth'
as $$
declare v_export uuid; v_all_downloaded boolean; v_result jsonb;
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'SERVICE_ROLE_REQUIRED'; end if;
  update public.life_story_delivery_links set download_count=download_count+1,last_downloaded_at=now()
  where id=p_link_id and revoked_at is null and expires_at>now() and download_count<max_downloads
  returning export_id into v_export;
  if v_export is null then raise exception 'DELIVERY_LINK_NOT_AVAILABLE'; end if;
  select not exists(select 1 from public.life_story_delivery_links where export_id=v_export and revoked_at is null and download_count=0) into v_all_downloaded;
  if v_all_downloaded then
    update public.life_story_exports set status='delivered',delivery_completed_at=coalesce(delivery_completed_at,now()),purge_after=coalesce(purge_after,now()+interval '90 days') where id=v_export and status='generated';
  end if;
  select jsonb_build_object('export_id',v_export,'all_recipients_downloaded',v_all_downloaded) into v_result;
  return v_result;
end;
$$;

create or replace function public.service_life_story_mark_export_purged(p_export_id uuid)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth'
as $$
declare v_case uuid; v_subject uuid;
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then raise exception 'SERVICE_ROLE_REQUIRED'; end if;
  update public.life_story_exports set status='purged',content_snapshot='{}'::jsonb,recipients_snapshot='[]'::jsonb,storage_bucket=null,storage_path=null,sha256=null
  where id=p_export_id and purge_after is not null and purge_after<=now() and status in ('delivered','revoked')
  returning case_id,subject_user_id into v_case,v_subject;
  if v_case is null then raise exception 'EXPORT_NOT_PURGEABLE'; end if;
  delete from public.life_story_delivery_links where export_id=p_export_id;
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
  if not exists(select 1 from public.life_story_exports where case_id=p_case_id and status in ('delivered','revoked','purged')) then raise exception 'NO_COMPLETED_EXPORT'; end if;
  update public.life_story_posthumous_cases set status='completed' where id=p_case_id;
  insert into public.life_story_cleanup_tasks(case_id,subject_user_id,task_type,due_after)
  values(p_case_id,v_case.subject_user_id,'life_story_source_review',now()+interval '90 days'),(p_case_id,v_case.subject_user_id,'registry_private_data_review',now()+interval '90 days')
  on conflict(case_id,task_type) do nothing;
end;
$$;

create or replace function public.admin_life_story_complete_cleanup_task(p_task_id uuid,p_status text,p_note text default null)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth','private'
as $$
declare v_admin uuid;
begin
  v_admin:=private.require_sinjira_admin_aal2();
  if p_status not in ('completed','skipped') then raise exception 'INVALID_CLEANUP_STATUS'; end if;
  update public.life_story_cleanup_tasks set status=p_status,completed_by=v_admin,completed_at=now(),completion_note=nullif(btrim(coalesce(p_note,'')),'')
  where id=p_task_id and status='pending' and due_after<=now();
  if not found then raise exception 'CLEANUP_TASK_NOT_DUE'; end if;
end;
$$;

revoke all on function public.life_story_my_posthumous_case() from public,anon;
revoke all on function public.life_story_contest_death_verification(uuid,text) from public,anon;
revoke all on function public.admin_life_story_pending_requests(integer) from public,anon;
revoke all on function public.admin_life_story_verify_death(uuid,date,text) from public,anon;
revoke all on function public.admin_life_story_resolve_contest(uuid,text,text) from public,anon;
revoke all on function public.admin_life_story_confirm_case(uuid) from public,anon;
revoke all on function public.admin_life_story_close_without_delivery(uuid,text) from public,anon;
revoke all on function public.admin_life_story_prepare_export(uuid,uuid) from public,anon;
revoke all on function public.admin_life_story_get_export(uuid) from public,anon;
revoke all on function public.admin_life_story_case_detail(uuid) from public,anon;
revoke all on function public.service_life_story_mark_export_generated(uuid,text,text) from public,anon,authenticated;
revoke all on function public.service_life_story_register_download(uuid) from public,anon,authenticated;
revoke all on function public.service_life_story_mark_export_purged(uuid) from public,anon,authenticated;
revoke all on function public.admin_life_story_complete_case(uuid) from public,anon;
revoke all on function public.admin_life_story_complete_cleanup_task(uuid,text,text) from public,anon;

grant execute on function public.life_story_my_posthumous_case() to authenticated;
grant execute on function public.life_story_contest_death_verification(uuid,text) to authenticated;
grant execute on function public.admin_life_story_pending_requests(integer) to authenticated;
grant execute on function public.admin_life_story_verify_death(uuid,date,text) to authenticated;
grant execute on function public.admin_life_story_resolve_contest(uuid,text,text) to authenticated;
grant execute on function public.admin_life_story_confirm_case(uuid) to authenticated;
grant execute on function public.admin_life_story_close_without_delivery(uuid,text) to authenticated;
grant execute on function public.admin_life_story_prepare_export(uuid,uuid) to authenticated;
grant execute on function public.admin_life_story_get_export(uuid) to authenticated;
grant execute on function public.admin_life_story_case_detail(uuid) to authenticated;
grant execute on function public.admin_life_story_complete_case(uuid) to authenticated;
grant execute on function public.admin_life_story_complete_cleanup_task(uuid,text,text) to authenticated;
grant execute on function public.service_life_story_mark_export_generated(uuid,text,text) to service_role;
grant execute on function public.service_life_story_register_download(uuid) to service_role;
grant execute on function public.service_life_story_mark_export_purged(uuid) to service_role;

select cron.unschedule(jobid) from cron.job where jobname='sinjira-life-story-delivery-token-cleanup';
select cron.schedule('sinjira-life-story-delivery-token-cleanup','23 4 * * *',$$delete from public.life_story_delivery_links where (expires_at<now()-interval '7 days') or (revoked_at is not null and revoked_at<now()-interval '7 days');$$);