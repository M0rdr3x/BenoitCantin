create table public.life_story_report_codes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  label text not null check (char_length(btrim(label)) between 1 and 160),
  code_hash text not null unique check (code_hash ~ '^[a-f0-9]{64}$'),
  status text not null default 'active' check (status = any (array['active','used','revoked']::text[])),
  created_at timestamptz not null default now(),
  used_at timestamptz,
  revoked_at timestamptz
);
create index life_story_report_codes_user_idx on public.life_story_report_codes(user_id,status,created_at desc);
alter table public.life_story_report_codes enable row level security;
revoke all on public.life_story_report_codes from public,anon,authenticated;
comment on table public.life_story_report_codes is 'Codes privés de signalement de décès. Seul le hash SHA-256 est conservé; le code brut est affiché une seule fois au propriétaire.';

create or replace function public.life_story_list_report_codes()
returns jsonb
language plpgsql
stable
security definer
set search_path to 'pg_catalog','public','auth'
as $$
declare v_user uuid:=auth.uid(); v_result jsonb;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.sinjira_mfa_access_allowed(v_user) then raise exception 'MFA_REQUIRED'; end if;
  select coalesce(jsonb_agg(jsonb_build_object('id',id,'label',label,'status',status,'created_at',created_at,'used_at',used_at,'revoked_at',revoked_at) order by created_at desc),'[]'::jsonb)
  into v_result from public.life_story_report_codes where user_id=v_user;
  return v_result;
end;
$$;

create or replace function public.life_story_create_report_code(p_label text)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth','extensions'
as $$
declare v_user uuid:=auth.uid(); v_raw text; v_hash text; v_id uuid; v_active integer;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.sinjira_mfa_access_allowed(v_user) then raise exception 'MFA_REQUIRED'; end if;
  if char_length(btrim(coalesce(p_label,''))) not between 1 and 160 then raise exception 'LABEL_REQUIRED'; end if;
  select count(*) into v_active from public.life_story_report_codes where user_id=v_user and status='active';
  if v_active>=5 then raise exception 'REPORT_CODE_LIMIT_REACHED'; end if;
  v_raw:=encode(gen_random_bytes(32),'hex');
  v_hash:=encode(digest(v_raw,'sha256'),'hex');
  insert into public.life_story_report_codes(user_id,label,code_hash) values(v_user,btrim(p_label),v_hash) returning id into v_id;
  return jsonb_build_object('id',v_id,'code',v_raw,'display_once',true);
end;
$$;

create or replace function public.life_story_revoke_report_code(p_code_id uuid)
returns void
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth'
as $$
declare v_user uuid:=auth.uid();
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.sinjira_mfa_access_allowed(v_user) then raise exception 'MFA_REQUIRED'; end if;
  update public.life_story_report_codes set status='revoked',revoked_at=now() where id=p_code_id and user_id=v_user and status='active';
  if not found then raise exception 'REPORT_CODE_NOT_ACTIVE'; end if;
end;
$$;

create or replace function public.life_story_report_death_by_code(p_code text,p_relationship_claim text,p_date_of_death date)
returns jsonb
language plpgsql
security definer
set search_path to 'pg_catalog','public','auth','extensions'
as $$
declare v_requester uuid:=auth.uid(); v_hash text; v_code public.life_story_report_codes%rowtype; v_request_id uuid;
begin
  if v_requester is null then raise exception 'AUTH_REQUIRED'; end if;
  if p_code is null or p_code !~ '^[a-f0-9]{64}$' then raise exception 'REPORT_CODE_INVALID'; end if;
  if p_date_of_death is null or p_date_of_death>current_date then raise exception 'INVALID_DATE_OF_DEATH'; end if;
  if char_length(btrim(coalesce(p_relationship_claim,''))) not between 2 and 240 then raise exception 'RELATIONSHIP_CLAIM_REQUIRED'; end if;
  v_hash:=encode(digest(p_code,'sha256'),'hex');
  select * into v_code from public.life_story_report_codes where code_hash=v_hash and status='active' for update;
  if not found then raise exception 'REPORT_CODE_INVALID'; end if;
  if v_code.user_id=v_requester then raise exception 'SELF_DEATH_REPORT_FORBIDDEN'; end if;
  if exists(select 1 from public.memorial_requests where subject_user_id=v_code.user_id and status in ('pending','verified')) then raise exception 'REPORT_ALREADY_EXISTS'; end if;
  insert into public.memorial_requests(subject_user_id,requested_by_user_id,relationship_claim,status,date_of_death)
  values(v_code.user_id,v_requester,btrim(p_relationship_claim),'pending',p_date_of_death)
  returning id into v_request_id;
  update public.life_story_report_codes set status='used',used_at=now() where id=v_code.id;
  return jsonb_build_object('accepted',true,'request_id',v_request_id,'message','Signalement reçu. Une vérification humaine est obligatoire avant toute opération posthume.');
end;
$$;

revoke all on function public.life_story_list_report_codes() from public,anon;
revoke all on function public.life_story_create_report_code(text) from public,anon;
revoke all on function public.life_story_revoke_report_code(uuid) from public,anon;
revoke all on function public.life_story_report_death_by_code(text,text,date) from public,anon;
grant execute on function public.life_story_list_report_codes() to authenticated;
grant execute on function public.life_story_create_report_code(text) to authenticated;
grant execute on function public.life_story_revoke_report_code(uuid) to authenticated;
grant execute on function public.life_story_report_death_by_code(text,text,date) to authenticated;
