-- SINJIRA™ V24.4.20 — résilience du personnage propriétaire
--
-- Le Compte propriétaire doit pouvoir réparer sa fiche AbyssTime sans dépendre
-- d'une migration historique : personnage, profil social, Monde parallèle,
-- accès produits, bibliothèque et projets restent synchronisés par une seule RPC.

begin;

create or replace function public.ensure_sinjira_owner_character()
returns jsonb
language plpgsql
security definer
set search_path = public, auth
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
  select id into v_user
  from auth.users
  where lower(coalesce(email,''))='kingtyrano@gmail.com'
  limit 1;

  if v_user is null then
    return jsonb_build_object('ok',false,'code','OWNER_ACCOUNT_NOT_FOUND');
  end if;

  if v_caller is not null
     and v_caller <> v_user
     and coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'OWNER_ONLY';
  end if;

  insert into public.internal_admin_users(user_id)
  values(v_user)
  on conflict(user_id) do nothing;

  insert into public.profiles(user_id,pseudo,display_name)
  values(v_user,'AbyssTime','Benoit Cantin')
  on conflict(user_id) do update
  set pseudo='AbyssTime',
      display_name='Benoit Cantin',
      updated_at=now();

  select id into v_submission
  from public.character_submissions
  where user_id=v_user
  order by created_at desc
  limit 1;

  select id into v_character
  from public.characters
  where user_id=v_user
  order by case when lower(coalesce(public_name,''))='abysstime' then 0 else 1 end,
           updated_at desc
  limit 1;

  if v_character is null then
    insert into public.characters(
      submission_id,user_id,public_name,public_description,status,novel_id,
      novel_note,bible,ai_generated,visible_to_user,canon_status,canon_version,
      portrait_path
    )
    values(
      v_submission,v_user,'AbyssTime',
      'Personnage officiel associé au compte de Benoit Cantin.',
      'assigned',null,'SINJIRA — Livre II (titre à confirmer)',
      jsonb_build_object(
        'owner','Benoit Cantin',
        'account','AbyssTime',
        'placement','SINJIRA — Livre II (titre à confirmer)',
        'source','Synchronisation propriétaire V24.4.20'
      ),
      false,true,'PROVISOIRE','v1.0','/assets/media/characters/abysstime.webp'
    )
    returning id into v_character;
  else
    update public.characters
    set public_name='AbyssTime',
        public_description=coalesce(
          nullif(public_description,''),
          'Personnage officiel associé au compte de Benoit Cantin.'
        ),
        submission_id=coalesce(submission_id,v_submission),
        status='assigned',
        novel_id=null,
        novel_note='SINJIRA — Livre II (titre à confirmer)',
        visible_to_user=true,
        portrait_path='/assets/media/characters/abysstime.webp',
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

  insert into public.parallel_character_state(character_id,user_id)
  values(v_character,v_user)
  on conflict(character_id) do update
  set user_id=excluded.user_id,
      updated_at=now();

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
  set last_opened_at=greatest(
    public.reader_library.last_opened_at,
    excluded.last_opened_at
  );

  insert into public.project_access(user_id,project_id,access_level,granted_by,source)
  select v_user,p.id,'tester',v_user,'migration'
  from public.projects p
  on conflict(user_id,project_id) do update
  set access_level='tester',
      granted_by=v_user,
      source='migration',
      expires_at=null,
      updated_at=now();

  select exists(
    select 1 from public.character_social_profiles
    where user_id=v_user and character_id=v_character and status='assigned'
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
    'repair_version','24.4.20',
    'character_id',v_character,
    'submission_id',v_submission,
    'public_name','AbyssTime',
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

revoke all on function public.ensure_sinjira_owner_character() from public, anon;
grant execute on function public.ensure_sinjira_owner_character() to authenticated, service_role;

create or replace function public.sinjira_owner_character_health()
returns jsonb
language plpgsql
stable
security definer
set search_path = public, auth
as $$
declare
  v_user uuid;
  v_character uuid;
  v_count integer := 0;
  v_visible integer := 0;
  v_social boolean := false;
  v_state boolean := false;
  v_membership boolean := false;
begin
  select id into v_user
  from auth.users
  where lower(coalesce(email,''))='kingtyrano@gmail.com'
  limit 1;

  if v_user is null then
    return jsonb_build_object('ok',false,'repair_version','24.4.20','code','OWNER_ACCOUNT_NOT_FOUND');
  end if;

  select count(*),
         count(*) filter(where status<>'archived' and visible_to_user=true)
  into v_count,v_visible
  from public.characters
  where user_id=v_user;

  select id into v_character
  from public.characters
  where user_id=v_user and status<>'archived' and visible_to_user=true
  order by updated_at desc
  limit 1;

  if v_character is not null then
    select exists(
      select 1 from public.character_social_profiles
      where user_id=v_user and character_id=v_character and public_name='AbyssTime'
    ) into v_social;
    select exists(
      select 1 from public.parallel_character_state
      where user_id=v_user and character_id=v_character
    ) into v_state;
    select exists(
      select 1 from public.parallel_world_memberships
      where user_id=v_user and character_id=v_character and status='active'
        and main_canon_eligible=true and parallel_world_only=false
    ) into v_membership;
  end if;

  return jsonb_build_object(
    'ok',v_visible=1 and v_social and v_state and v_membership,
    'repair_version','24.4.20',
    'character_rows',v_count,
    'visible_active_rows',v_visible,
    'social_profile',v_social,
    'parallel_state',v_state,
    'parallel_membership',v_membership
  );
end;
$$;

revoke all on function public.sinjira_owner_character_health() from public, anon, authenticated;
grant execute on function public.sinjira_owner_character_health() to service_role;

commit;
