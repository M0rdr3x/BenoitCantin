-- SINJIRA™ V25 — accès catalogue famille du créateur sans exposer les courriels.
-- L'HUMAIN AVANT TOUT : le propriétaire et les membres familiaux explicitement
-- provisionnés voient les créations SINJIRA sans faux achat/entitlement.
-- Les comptes 11–12 peuvent voir un catalogue minimisé, mais les barrières
-- de contenu child restent fail-closed et ne sont jamais contournées.

begin;

create table if not exists private.sinjira_catalog_family_members(
  user_id uuid primary key references auth.users(id) on delete cascade,
  label text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table private.sinjira_catalog_family_members enable row level security;
revoke all on table private.sinjira_catalog_family_members from public,anon,authenticated;
grant select,insert,update,delete on table private.sinjira_catalog_family_members to service_role;

create or replace function public.is_sinjira_catalog_family_member(
  p_user_id uuid default auth.uid()
)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private,auth
as $family$
  select p_user_id is not null
    and (
      coalesce(auth.jwt()->>'role','')='service_role'
      or p_user_id=(select auth.uid())
    )
    and exists(
      select 1
      from private.sinjira_catalog_family_members f
      where f.user_id=p_user_id
    );
$family$;

revoke all on function public.is_sinjira_catalog_family_member(uuid)
from public,anon;
grant execute on function public.is_sinjira_catalog_family_member(uuid)
to authenticated,service_role;

create or replace function public.sinjira_has_full_catalog_access(
  p_user_id uuid default auth.uid()
)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private,auth
as $family$
  select p_user_id is not null
    and (
      coalesce(auth.jwt()->>'role','')='service_role'
      or p_user_id=(select auth.uid())
    )
    and (
      exists(
        select 1
        from public.internal_admin_users a
        where a.user_id=p_user_id
          and a.role='owner'
      )
      or exists(
        select 1
        from private.sinjira_catalog_family_members f
        where f.user_id=p_user_id
      )
    );
$family$;

revoke all on function public.sinjira_has_full_catalog_access(uuid)
from public,anon;
grant execute on function public.sinjira_has_full_catalog_access(uuid)
to authenticated,service_role;

create or replace function public.sinjira_my_catalog_access_mode()
returns text
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private,auth
as $family$
declare
  uid uuid:=auth.uid();
begin
  if uid is null then
    raise exception 'AUTH_REQUIRED' using errcode='42501';
  end if;

  if exists(
    select 1 from public.internal_admin_users a
    where a.user_id=uid and a.role='owner'
  ) then
    return 'owner';
  end if;

  if exists(
    select 1 from private.sinjira_catalog_family_members f
    where f.user_id=uid
  ) then
    return 'family';
  end if;

  return 'member';
end;
$family$;

revoke all on function public.sinjira_my_catalog_access_mode()
from public,anon;
grant execute on function public.sinjira_my_catalog_access_mode()
to authenticated,service_role;

create or replace function public.set_sinjira_catalog_family_access_by_email(
  p_email text,
  p_enabled boolean default true,
  p_label text default null
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private,auth
as $family$
declare
  v_email text:=lower(trim(coalesce(p_email,'')));
  v_user_id uuid;
  v_enabled boolean:=coalesce(p_enabled,false);
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED' using errcode='42501';
  end if;

  if v_email='' or length(v_email)>320 then
    raise exception 'INVALID_ACCOUNT_EMAIL';
  end if;

  select u.id
    into v_user_id
  from auth.users u
  where lower(coalesce(u.email,''))=v_email
  order by u.created_at
  limit 1;

  if v_user_id is null then
    raise exception 'SINJIRA_ACCOUNT_NOT_FOUND';
  end if;

  if v_enabled then
    insert into private.sinjira_catalog_family_members(user_id,label,updated_at)
    values(v_user_id,nullif(trim(coalesce(p_label,'')),''),now())
    on conflict(user_id) do update
      set label=excluded.label,
          updated_at=now();
  else
    delete from private.sinjira_catalog_family_members
    where user_id=v_user_id;
  end if;

  return jsonb_build_object(
    'ok',true,
    'enabled',v_enabled,
    'user_id',v_user_id
  );
end;
$family$;

revoke all on function public.set_sinjira_catalog_family_access_by_email(text,boolean,text)
from public,anon,authenticated;
grant execute on function public.set_sinjira_catalog_family_access_by_email(text,boolean,text)
to service_role;

drop policy if exists sinjira_novels_family_catalog_read_v25 on public.sinjira_novels;
create policy sinjira_novels_family_catalog_read_v25
on public.sinjira_novels
for select
to authenticated
using (
  public.is_sinjira_catalog_family_member((select auth.uid()))
  and public.sinjira_age_band((select auth.uid())) in ('adult','youth')
);

drop policy if exists products_family_catalog_read_v25 on public.products;
create policy products_family_catalog_read_v25
on public.products
for select
to authenticated
using (
  public.is_sinjira_catalog_family_member((select auth.uid()))
  and public.sinjira_age_band((select auth.uid())) in ('adult','youth')
);

drop policy if exists projects_family_catalog_read_v25 on public.projects;
create policy projects_family_catalog_read_v25
on public.projects
for select
to authenticated
using (
  public.is_sinjira_catalog_family_member((select auth.uid()))
  and public.sinjira_age_band((select auth.uid())) in ('adult','youth')
);

create or replace function public.sinjira_my_project_catalog()
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private,auth
as $family$
declare
  uid uuid:=auth.uid();
  band text;
  full_catalog boolean:=false;
  result jsonb;
begin
  if uid is null then
    raise exception 'AUTH_REQUIRED' using errcode='42501';
  end if;

  band:=public.sinjira_age_band(uid);
  full_catalog:=public.sinjira_has_full_catalog_access(uid);

  if not full_catalog then
    raise exception 'CATALOG_ACCESS_REQUIRED' using errcode='42501';
  end if;

  if band not in ('adult','youth','child') then
    return '[]'::jsonb;
  end if;

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',p.id,
        'slug',p.slug,
        'name',p.name,
        'type',p.type,
        'status',p.status,
        'visibility',p.visibility,
        'description',case
          when band='child'
               and not (
                 p.status<>'draft'
                 and p.visibility in ('public','account')
                 and p.child_access_status='approved_11_12'
               )
            then 'Création SINJIRA™ visible dans le catalogue familial. Contenu protégé selon l’âge.'
          else p.description
        end,
        'cover_url',p.cover_url,
        'public_path',case
          when band='child'
               and not (
                 p.status<>'draft'
                 and p.visibility in ('public','account')
                 and p.child_access_status='approved_11_12'
               )
            then null
          else p.public_path
        end,
        'play_path',case
          when band='child' then null
          else p.play_path
        end,
        'allow_tester_requests',case when band='child' then false else p.allow_tester_requests end,
        'sort_order',p.sort_order,
        'child_access_status',p.child_access_status,
        'content_available',case
          when band='child' then
            p.status<>'draft'
            and p.visibility in ('public','account')
            and p.child_access_status='approved_11_12'
          else true
        end
      )
      order by p.sort_order,p.name
    ),
    '[]'::jsonb
  )
  into result
  from public.projects p;

  return result;
end;
$family$;

revoke all on function public.sinjira_my_project_catalog()
from public,anon;
grant execute on function public.sinjira_my_project_catalog()
to authenticated,service_role;

create or replace function public.sinjira_my_novel_catalog()
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private,auth
as $family$
declare
  uid uuid:=auth.uid();
  band text;
  owner_mode boolean:=false;
  family_mode boolean:=false;
  full_catalog_mode boolean:=false;
  result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  band:=public.sinjira_age_band(uid);
  if band not in ('adult','youth','child') then
    return '[]'::jsonb;
  end if;

  select exists(
    select 1 from public.internal_admin_users a
    where a.user_id=uid and a.role='owner'
  ) into owner_mode;

  select exists(
    select 1 from private.sinjira_catalog_family_members f
    where f.user_id=uid
  ) into family_mode;

  full_catalog_mode:=owner_mode or family_mode;

  if band='child' and not full_catalog_mode then
    return '[]'::jsonb;
  end if;

  with catalogue as (
    select
      n.id,n.slug,n.title,n.subtitle,n.description,n.status,n.cover_url,
      n.public_path,n.demo_path,n.sort_order,
      a.product_slug,
      coalesce(a.enabled,false) as private_asset_configured,
      a.total_pages,
      exists(
        select 1
        from public.products p
        join public.user_entitlements ue
          on ue.product_id=p.id
         and ue.user_id=uid
        where p.slug=a.product_slug
      ) as entitled
    from public.sinjira_novels n
    left join private.sinjira_private_novel_assets a on a.novel_id=n.id
    where full_catalog_mode
       or n.status in ('announced','published')
       or exists(
         select 1
         from public.products p
         join public.user_entitlements ue
           on ue.product_id=p.id
          and ue.user_id=uid
         where p.slug=a.product_slug
       )
  )
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',id,
        'slug',slug,
        'title',title,
        'subtitle',subtitle,
        'description',case
          when band='child'
            then 'Roman SINJIRA™ visible dans le catalogue familial. Lecture intégrale protégée selon l’âge.'
          else description
        end,
        'status',status,
        'cover_url',cover_url,
        'public_path',case when band='child' then null else public_path end,
        'demo_path',case when band='child' then null else demo_path end,
        'sort_order',sort_order,
        'creator_mode',owner_mode,
        'family_mode',family_mode,
        'full_access',
          private_asset_configured
          and band in ('adult','youth')
          and (full_catalog_mode or entitled),
        'private_asset_configured',private_asset_configured,
        'total_pages',case when band='child' then null else total_pages end,
        'access_source',case
          when band='child' and family_mode then 'family_catalog'
          when private_asset_configured and owner_mode then 'owner'
          when private_asset_configured and family_mode then 'family'
          when private_asset_configured and entitled then 'entitlement'
          when family_mode then 'family_catalog'
          else 'catalogue'
        end
      )
      order by sort_order,title
    ),
    '[]'::jsonb
  ) into result
  from catalogue;

  return result;
end;
$family$;

create or replace function sinjira_catalog_internal.project_access_rank(
  p_project_id uuid,
  p_user_id uuid default auth.uid()
)
returns integer
language sql
stable
security definer
set search_path=pg_catalog,public,auth
as $family_rank$
  select case
    when coalesce(auth.jwt()->>'role','') <> 'service_role'
         and p_user_id is distinct from auth.uid() then 0
    when public.is_sinjira_admin(p_user_id) then 100
    when public.sinjira_has_full_catalog_access(p_user_id)
         and public.sinjira_age_band(p_user_id) in ('adult','youth') then 90
    when exists(
      select 1
      from public.project_access pa
      where pa.project_id=p_project_id
        and pa.user_id=p_user_id
        and (pa.expires_at is null or pa.expires_at>now())
        and pa.access_level='tester'
    ) then 30
    when exists(
      select 1
      from public.project_access pa
      where pa.project_id=p_project_id
        and pa.user_id=p_user_id
        and (pa.expires_at is null or pa.expires_at>now())
        and pa.access_level='player'
    ) then 20
    when p_user_id is not null
         and exists(
           select 1 from public.projects p
           where p.id=p_project_id and p.visibility in ('public','account')
         ) then 10
    when exists(
      select 1 from public.projects p
      where p.id=p_project_id and p.visibility='public'
    ) then 1
    else 0
  end;
$family_rank$;

revoke all on function sinjira_catalog_internal.project_access_rank(uuid,uuid)
from public,anon,authenticated;
grant execute on function sinjira_catalog_internal.project_access_rank(uuid,uuid)
to anon,authenticated,service_role;

comment on table private.sinjira_catalog_family_members is
  'Registre serveur par UUID des comptes familiaux bénéficiant du catalogue créateur. Aucun courriel n est stocké dans cette table.';
comment on function public.set_sinjira_catalog_family_access_by_email(text,boolean,text) is
  'Provisionnement service_role: résout temporairement un courriel Auth vers son UUID puis ne conserve que l UUID et un libellé facultatif.';
comment on function public.sinjira_my_project_catalog() is
  'Catalogue complet owner/famille; pour 11–12 ans, expose seulement des métadonnées minimisées et ne contourne jamais child_access_status.';
comment on function public.sinjira_my_novel_catalog() is
  'Catalogue roman self-only: owner/famille voit toutes les fiches; 11–12 famille voit les fiches minimisées sans accès intégral; les autres membres restent limités au catalogue public et à leurs entitlements.';

commit;
