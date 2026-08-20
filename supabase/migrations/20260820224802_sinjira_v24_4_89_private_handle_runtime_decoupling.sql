-- Définition reconstructible du pare-feu d’identité SINJIRA™.
-- Aucune valeur d’identifiant technique propre à un compte de production n’est versionnée ici.

create table if not exists private.account_identities (
  user_id uuid primary key references auth.users(id) on delete cascade,
  account_handle text not null check (char_length(btrim(account_handle)) between 3 and 80),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists account_identities_handle_ci_uidx
  on private.account_identities(lower(account_handle));

alter table private.account_identities enable row level security;
revoke all on table private.account_identities from anon, authenticated;

comment on table private.account_identities is
  'Identifiants techniques prives des comptes. Ne jamais utiliser comme nom public, nom de personnage ou identite communautaire.';

insert into private.account_identities(user_id,account_handle)
select u.id,'SIN-' || upper(replace(u.id::text,'-',''))
from auth.users u
on conflict(user_id) do nothing;

create or replace function private.ensure_account_identity_for_new_user()
returns trigger
language plpgsql
security definer
set search_path = private, public, auth, pg_temp
as $$
begin
  insert into private.account_identities(user_id,account_handle)
  values(new.id,'SIN-' || upper(replace(new.id::text,'-','')))
  on conflict(user_id) do nothing;
  return new;
end;
$$;

revoke all on function private.ensure_account_identity_for_new_user() from public, anon, authenticated;

drop trigger if exists sinjira_private_account_identity_after_signup on auth.users;
create trigger sinjira_private_account_identity_after_signup
after insert on auth.users
for each row execute function private.ensure_account_identity_for_new_user();

create table if not exists private.parallel_identities (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  source_character_id uuid not null references public.characters(id) on delete cascade,
  public_name text not null check (char_length(btrim(public_name)) between 2 and 80),
  public_bio text null check (public_bio is null or char_length(public_bio) <= 600),
  status text not null default 'active' check (status in ('active','archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id)
);

alter table private.parallel_identities enable row level security;
revoke all on table private.parallel_identities from anon, authenticated;
create index if not exists parallel_identities_character_idx on private.parallel_identities(source_character_id);

create or replace function public.sync_social_profile_from_profile()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_display text := coalesce(nullif(btrim(new.display_name),''),nullif(btrim(new.pseudo),''),'Membre SINJIRA');
begin
  insert into public.social_profiles(user_id,pseudo,display_name,avatar_path,updated_at)
  values(new.user_id,v_display,v_display,new.avatar_path,now())
  on conflict(user_id) do update
  set pseudo=excluded.pseudo,
      display_name=excluded.display_name,
      avatar_path=excluded.avatar_path,
      updated_at=now();
  return new;
end;
$$;

create or replace function public.ensure_sinjira_owner_character()
returns jsonb
language plpgsql
security definer
set search_path = public, private, auth
as $$
declare
  v_user uuid;
  v_submission uuid;
  v_character uuid;
  v_caller uuid := auth.uid();
  v_social_ok boolean := false;
  v_parallel_state_ok boolean := false;
  v_parallel_membership_ok boolean := false;
begin
  select a.user_id into v_user
  from public.internal_admin_users a
  where a.role='owner'
  limit 1;

  if v_user is null then
    return jsonb_build_object('ok',false,'code','OWNER_ACCOUNT_NOT_FOUND');
  end if;

  if v_caller is not null
     and v_caller <> v_user
     and coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'OWNER_ONLY';
  end if;

  insert into private.account_identities(user_id,account_handle)
  values(v_user,'SIN-' || upper(replace(v_user::text,'-','')))
  on conflict(user_id) do nothing;

  insert into public.profiles(user_id,pseudo,display_name)
  values(v_user,'Benoit Cantin','Benoit Cantin')
  on conflict(user_id) do update
  set pseudo='Benoit Cantin',display_name='Benoit Cantin',updated_at=now();

  select id into v_submission
  from public.character_submissions
  where user_id=v_user
  order by created_at desc
  limit 1;

  select id into v_character
  from public.characters
  where user_id=v_user
  order by case when lower(coalesce(public_name,''))='seth tremblay' then 0 else 1 end,
           updated_at desc
  limit 1;

  if v_character is null then
    insert into public.characters(
      submission_id,user_id,public_name,public_description,status,novel_id,
      novel_note,bible,ai_generated,visible_to_user,canon_status,canon_version,portrait_path
    )
    values(
      v_submission,v_user,'Seth Tremblay',
      'Une presence reservee, inventive et tenace. Seth ne confond pas l echec d une tentative avec celui du but : il constate, cherche la cause, change de methode et continue tant qu une piste raisonnable existe.',
      'assigned',null,null,
      jsonb_build_object('identity_scope','parallel_world','identity_version','24.4.89'),
      false,true,'PROVISOIRE','v1.1',null
    )
    returning id into v_character;
  else
    update public.characters
    set public_name='Seth Tremblay',
        submission_id=coalesce(submission_id,v_submission),
        status='assigned',
        novel_id=null,
        novel_note=null,
        bible=(coalesce(bible,'{}'::jsonb)-'owner'-'account'-'placement'-'source')
              || jsonb_build_object('identity_scope','parallel_world','identity_version','24.4.89'),
        visible_to_user=true,
        canon_version='v1.1',
        portrait_path=null,
        updated_at=now()
    where id=v_character;
  end if;

  update public.characters
  set status='archived',visible_to_user=false,updated_at=now()
  where user_id=v_user and id<>v_character;

  if v_submission is not null then
    update public.character_submissions
    set status=case when id=v_submission then 'assigned' else 'archived' end,
        updated_at=now()
    where user_id=v_user;
  end if;

  insert into public.character_social_profiles(
    character_id,user_id,public_name,public_description,portrait_path,status,updated_at
  )
  select c.id,c.user_id,c.public_name,c.public_description,c.portrait_path,c.status,now()
  from public.characters c
  where c.id=v_character
  on conflict(character_id) do update
  set user_id=excluded.user_id,
      public_name=excluded.public_name,
      public_description=excluded.public_description,
      portrait_path=excluded.portrait_path,
      status=excluded.status,
      updated_at=now();

  insert into private.parallel_identities(user_id,source_character_id,public_name,public_bio)
  values(v_user,v_character,'Seth Tremblay','Identite narrative du Monde parallele SINJIRA™.')
  on conflict(user_id) do update
  set source_character_id=excluded.source_character_id,
      public_name='Seth Tremblay',
      public_bio=excluded.public_bio,
      status='active',
      updated_at=now();

  insert into public.parallel_character_state(character_id,user_id)
  values(v_character,v_user)
  on conflict(character_id) do update
  set user_id=excluded.user_id,updated_at=now();

  insert into public.parallel_world_memberships(
    character_id,user_id,main_canon_eligible,parallel_world_only,status
  )
  values(v_character,v_user,true,false,'active')
  on conflict(character_id) do update
  set user_id=excluded.user_id,
      main_canon_eligible=true,
      parallel_world_only=false,
      status='active';

  insert into public.user_entitlements(user_id,product_id,source)
  select v_user,p.id,'owner'
  from public.products p
  on conflict(user_id,product_id) do nothing;

  insert into public.reader_library(user_id,novel_id,last_opened_at)
  select v_user,n.id,now()
  from public.novels n
  on conflict(user_id,novel_id) do update
  set last_opened_at=greatest(public.reader_library.last_opened_at,excluded.last_opened_at);

  insert into public.project_access(user_id,project_id,access_level,granted_by,source)
  select v_user,p.id,'tester',v_user,'migration'
  from public.projects p
  on conflict(user_id,project_id) do update
  set access_level='tester',granted_by=v_user,source='migration',expires_at=null,updated_at=now();

  select exists(
    select 1 from public.character_social_profiles
    where user_id=v_user and character_id=v_character and status='assigned' and public_name='Seth Tremblay'
  ) into v_social_ok;
  select exists(
    select 1 from public.parallel_character_state
    where user_id=v_user and character_id=v_character
  ) into v_parallel_state_ok;
  select exists(
    select 1 from public.parallel_world_memberships
    where user_id=v_user and character_id=v_character
      and status='active' and main_canon_eligible=true and parallel_world_only=false
  ) into v_parallel_membership_ok;

  return jsonb_build_object(
    'ok',v_social_ok and v_parallel_state_ok and v_parallel_membership_ok,
    'repair_version','24.4.89',
    'character_id',v_character,
    'submission_id',v_submission,
    'public_name','Seth Tremblay',
    'visible_to_user',true,
    'status','assigned',
    'social_profile',v_social_ok,
    'parallel_state',v_parallel_state_ok,
    'parallel_membership',v_parallel_membership_ok,
    'unlimited_tokens',true,
    'all_content',true
  );
end;
$$;

create or replace function public.sinjira_owner_character_health()
returns jsonb
language plpgsql
stable security definer
set search_path = public, private
as $$
declare
  v_user uuid;
  v_character uuid;
  v_count integer := 0;
  v_visible integer := 0;
  v_social boolean := false;
  v_state boolean := false;
  v_membership boolean := false;
  v_account boolean := false;
begin
  select a.user_id into v_user
  from public.internal_admin_users a
  where a.role='owner'
  limit 1;

  if v_user is null then
    return jsonb_build_object('ok',false,'repair_version','24.4.89','code','OWNER_ACCOUNT_NOT_FOUND');
  end if;

  select count(*),count(*) filter(where status<>'archived' and visible_to_user=true)
  into v_count,v_visible
  from public.characters
  where user_id=v_user;

  select id into v_character
  from public.characters
  where user_id=v_user and status<>'archived' and visible_to_user=true and public_name='Seth Tremblay'
  order by updated_at desc
  limit 1;

  select exists(select 1 from private.account_identities where user_id=v_user) into v_account;

  if v_character is not null then
    select exists(select 1 from public.character_social_profiles where user_id=v_user and character_id=v_character and public_name='Seth Tremblay') into v_social;
    select exists(select 1 from public.parallel_character_state where user_id=v_user and character_id=v_character) into v_state;
    select exists(select 1 from public.parallel_world_memberships where user_id=v_user and character_id=v_character and status='active' and main_canon_eligible=true and parallel_world_only=false) into v_membership;
  end if;

  return jsonb_build_object(
    'ok',v_visible=1 and v_account and v_social and v_state and v_membership,
    'repair_version','24.4.89',
    'character_rows',v_count,
    'visible_active_rows',v_visible,
    'private_account_identity',v_account,
    'social_profile',v_social,
    'parallel_state',v_state,
    'parallel_membership',v_membership
  );
end;
$$;

create or replace function public.parallel_my_identity()
returns jsonb
language plpgsql
security definer
set search_path = public, private, auth
as $$
declare
  v_user uuid := auth.uid();
  v_source uuid;
  v_identity private.parallel_identities%rowtype;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;

  select c.id into v_source
  from public.characters c
  where c.user_id=v_user and c.status<>'archived' and c.visible_to_user=true
  order by c.updated_at desc
  limit 1;

  if v_source is null then
    return jsonb_build_object('ok',false,'code','PARALLEL_CHARACTER_NOT_READY');
  end if;

  insert into private.parallel_identities(user_id,source_character_id,public_name)
  select v_user,v_source,coalesce(nullif(btrim(c.public_name),''),'Identite parallele')
  from public.characters c
  where c.id=v_source
  on conflict(user_id) do update
  set source_character_id=excluded.source_character_id,
      updated_at=case when private.parallel_identities.source_character_id is distinct from excluded.source_character_id then now() else private.parallel_identities.updated_at end
  returning * into v_identity;

  return jsonb_build_object(
    'ok',true,
    'character_id',v_identity.id,
    'public_name',v_identity.public_name,
    'public_bio',v_identity.public_bio,
    'status',v_identity.status
  );
end;
$$;
revoke all on function public.parallel_my_identity() from public, anon;
grant execute on function public.parallel_my_identity() to authenticated;

create or replace function public.parallel_set_my_identity(p_public_name text,p_public_bio text default null)
returns jsonb
language plpgsql
security definer
set search_path = public, private, auth
as $$
declare
  v_user uuid := auth.uid();
  v_name text := btrim(coalesce(p_public_name,''));
  v_bio text := nullif(btrim(coalesce(p_public_bio,'')),'');
  v_current jsonb;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if char_length(v_name)<2 or char_length(v_name)>80 then raise exception 'PARALLEL_NAME_LENGTH'; end if;
  if v_bio is not null and char_length(v_bio)>600 then raise exception 'PARALLEL_BIO_LENGTH'; end if;
  if not public.sinjira_content_allowed(v_user,v_name) then raise exception 'PARALLEL_NAME_NOT_ALLOWED'; end if;
  if v_bio is not null and not public.sinjira_content_allowed(v_user,v_bio) then raise exception 'PARALLEL_BIO_NOT_ALLOWED'; end if;

  v_current:=public.parallel_my_identity();
  if coalesce((v_current->>'ok')::boolean,false) is not true then return v_current; end if;

  update private.parallel_identities
  set public_name=v_name,public_bio=v_bio,updated_at=now()
  where user_id=v_user
  returning jsonb_build_object(
    'ok',true,'character_id',id,'public_name',public_name,'public_bio',public_bio,'status',status
  ) into v_current;
  return v_current;
end;
$$;
revoke all on function public.parallel_set_my_identity(text,text) from public, anon;
grant execute on function public.parallel_set_my_identity(text,text) to authenticated;

create or replace function public.parallel_my_context()
returns jsonb
language plpgsql
security definer
set search_path = public, private, auth
as $$
declare
  v_user uuid := auth.uid();
  v_identity private.parallel_identities%rowtype;
  v_cycle public.parallel_world_cycles%rowtype;
  v_membership jsonb := null;
  v_state jsonb := null;
  v_response jsonb := null;
  v_personal jsonb := '[]'::jsonb;
  v_collective jsonb := '[]'::jsonb;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  perform public.parallel_my_identity();
  select * into v_identity from private.parallel_identities where user_id=v_user and status='active';
  if v_identity.id is null then return jsonb_build_object('ok',false,'code','PARALLEL_IDENTITY_NOT_READY'); end if;

  select jsonb_build_object(
    'pioneer_number',m.pioneer_number,'main_canon_eligible',m.main_canon_eligible,
    'parallel_world_only',m.parallel_world_only,'status',m.status,'joined_at',m.joined_at
  ) into v_membership
  from public.parallel_world_memberships m
  where m.character_id=v_identity.source_character_id and m.user_id=v_user;

  select jsonb_build_object(
    'life_state',s.life_state,'location_name',s.location_name,'faction_name',s.faction_name,
    'reputation',s.reputation,'state_data',s.state_data,'updated_at',s.updated_at
  ) into v_state
  from public.parallel_character_state s
  where s.character_id=v_identity.source_character_id and s.user_id=v_user;

  select c.* into v_cycle
  from public.parallel_world_cycles c
  where c.status='open' and public.sinjira_cycle_allowed(c.id,v_user)
  order by c.cycle_month desc
  limit 1;

  if v_cycle.id is not null then
    select jsonb_build_object('id',r.id,'response_text',r.response_text,'submitted_at',r.submitted_at)
    into v_response
    from public.parallel_cycle_responses r
    where r.cycle_id=v_cycle.id and r.user_id=v_user;
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
    'id',x.id,'title',x.title,'content',x.content,'published_at',x.published_at,
    'cycle_id',x.cycle_id,'story_kind',x.story_kind
  ) order by x.published_at desc),'[]'::jsonb)
  into v_personal
  from (
    select id,title,content,published_at,cycle_id,story_kind
    from public.parallel_story_installments
    where story_kind='individual' and character_id=v_identity.source_character_id and published_at is not null
    order by published_at desc
    limit 3
  ) x;

  select coalesce(jsonb_agg(jsonb_build_object(
    'id',x.id,'title',x.title,'content',x.content,'published_at',x.published_at,
    'cycle_id',x.cycle_id,'story_kind',x.story_kind
  ) order by x.published_at desc),'[]'::jsonb)
  into v_collective
  from (
    select id,title,content,published_at,cycle_id,story_kind
    from public.parallel_story_installments
    where story_kind='collective' and published_at is not null
      and (audience='all' or audience=public.sinjira_my_age_band())
    order by published_at desc
    limit 3
  ) x;

  return jsonb_build_object(
    'ok',true,
    'identity',jsonb_build_object(
      'character_id',v_identity.id,'public_name',v_identity.public_name,
      'public_bio',v_identity.public_bio,'status',v_identity.status
    ),
    'membership',v_membership,
    'state',v_state,
    'cycle',case when v_cycle.id is null then null else jsonb_build_object(
      'id',v_cycle.id,'cycle_month',v_cycle.cycle_month,'title',v_cycle.title,
      'monthly_question',v_cycle.monthly_question,'response_mode',v_cycle.response_mode,
      'opens_at',v_cycle.opens_at,'closes_at',v_cycle.closes_at,'status',v_cycle.status,
      'audience',v_cycle.audience,'published_at',v_cycle.published_at
    ) end,
    'existing_response',v_response,
    'personal_stories',v_personal,
    'collective_stories',v_collective
  );
end;
$$;
revoke all on function public.parallel_my_context() from public, anon;
grant execute on function public.parallel_my_context() to authenticated;

create or replace function public.parallel_save_cycle_response(p_cycle_id uuid,p_response_text text)
returns jsonb
language plpgsql
security definer
set search_path = public, private, auth
as $$
declare
  v_user uuid := auth.uid();
  v_identity private.parallel_identities%rowtype;
  v_text text := btrim(coalesce(p_response_text,''));
  v_row public.parallel_cycle_responses%rowtype;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.sinjira_mfa_access_allowed(v_user) then raise exception 'MFA_REQUIRED'; end if;
  if char_length(v_text)<1 or char_length(v_text)>4000 then raise exception 'PARALLEL_RESPONSE_LENGTH'; end if;
  if not public.sinjira_content_allowed(v_user,v_text) then raise exception 'PARALLEL_RESPONSE_NOT_ALLOWED'; end if;
  if not public.sinjira_cycle_allowed(p_cycle_id,v_user) then raise exception 'PARALLEL_CYCLE_NOT_ALLOWED'; end if;

  perform public.parallel_my_identity();
  select * into v_identity from private.parallel_identities where user_id=v_user and status='active';
  if v_identity.id is null then raise exception 'PARALLEL_IDENTITY_NOT_READY'; end if;

  insert into public.parallel_cycle_responses(
    cycle_id,user_id,character_id,group_id,response_text,response_kind,submitted_at
  )
  values(p_cycle_id,v_user,v_identity.source_character_id,null,v_text,'solo',now())
  on conflict(cycle_id,user_id) do update
  set character_id=excluded.character_id,
      group_id=null,
      response_text=excluded.response_text,
      response_kind='solo',
      submitted_at=now()
  returning * into v_row;

  return jsonb_build_object(
    'ok',true,'id',v_row.id,'character_id',v_identity.id,'submitted_at',v_row.submitted_at
  );
end;
$$;
revoke all on function public.parallel_save_cycle_response(uuid,text) from public, anon;
grant execute on function public.parallel_save_cycle_response(uuid,text) to authenticated;

select public.ensure_sinjira_owner_character();
