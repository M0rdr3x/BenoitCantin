-- SINJIRA™ V24.4.11 — vérité de production + confidentialité des RPC
-- Objectifs :
-- 1) distinguer clairement la version réellement installée côté Supabase;
-- 2) empêcher un compte authentifié d'interroger les droits d'un autre utilisateur;
-- 3) relancer de façon idempotente la réparation du compte propriétaire AbyssTime;
-- 4) exposer un diagnostic non secret de la fondation serveur.

-- ---------------------------------------------------------------------------
-- VERSION SERVEUR
-- ---------------------------------------------------------------------------
create or replace function public.get_sinjira_server_version()
returns text
language sql
stable
security definer
set search_path=public
as $$ select '24.4.11'::text; $$;
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;

-- ---------------------------------------------------------------------------
-- IDENTITÉ PROPRIÉTAIRE : un utilisateur authentifié ne peut vérifier que lui-même.
-- Le service_role conserve la possibilité de faire des vérifications serveur explicites.
-- ---------------------------------------------------------------------------
create or replace function public.is_sinjira_owner(p_user_id uuid default auth.uid())
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when p_user_id is null then false
    when coalesce(auth.jwt()->>'role','')='service_role' then exists(
      select 1 from auth.users u
      where u.id=p_user_id and lower(coalesce(u.email,''))='kingtyrano@gmail.com'
    )
    when auth.uid() is null or p_user_id<>auth.uid() then false
    else exists(
      select 1 from auth.users u
      where u.id=p_user_id and lower(coalesce(u.email,''))='kingtyrano@gmail.com'
    )
  end;
$$;
revoke all on function public.is_sinjira_owner(uuid) from public,anon;
grant execute on function public.is_sinjira_owner(uuid) to authenticated,service_role;

-- Même principe pour l'ancien helper administrateur utilisé par la navigation et les Edge Functions.
-- Un navigateur ne peut vérifier que son propre compte; le service_role peut faire les contrôles serveur.
create or replace function public.is_sinjira_admin(p_user_id uuid default auth.uid())
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when p_user_id is null then false
    when coalesce(auth.jwt()->>'role','')='service_role' then exists(
      select 1
      from public.internal_admin_users a
      join auth.users u on u.id=a.user_id
      where a.user_id=p_user_id and lower(coalesce(u.email,''))='kingtyrano@gmail.com'
    )
    when auth.uid() is null or p_user_id<>auth.uid() then false
    else exists(
      select 1
      from public.internal_admin_users a
      join auth.users u on u.id=a.user_id
      where a.user_id=p_user_id and lower(coalesce(u.email,''))='kingtyrano@gmail.com'
    )
  end;
$$;
revoke all on function public.is_sinjira_admin(uuid) from public,anon;
grant execute on function public.is_sinjira_admin(uuid) to authenticated,service_role;

-- ---------------------------------------------------------------------------
-- DROITS PRODUITS : même cloisonnement par utilisateur.
-- Un navigateur ne peut plus tester les entitlements d'un autre UUID.
-- ---------------------------------------------------------------------------
create or replace function public.has_sinjira_product(
  p_product_slug text,
  p_user_id uuid default auth.uid()
)
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when p_user_id is null then false
    when coalesce(auth.jwt()->>'role','')<>'service_role' and p_user_id is distinct from auth.uid() then false
    else public.is_sinjira_owner(p_user_id)
      or exists(
        select 1
        from public.user_entitlements ue
        join public.products p on p.id=ue.product_id
        where ue.user_id=p_user_id
          and p.slug=p_product_slug
          and p.active=true
      )
  end;
$$;
revoke all on function public.has_sinjira_product(text,uuid) from public,anon;
grant execute on function public.has_sinjira_product(text,uuid) to authenticated,service_role;

-- Les capacités publiques au compte connecté restent dérivées uniquement de auth.uid().
create or replace function public.get_sinjira_account_capabilities()
returns jsonb
language sql
stable
security definer
set search_path=public,auth
as $$
  select case when public.is_sinjira_owner(auth.uid()) then
    jsonb_build_object(
      'owner',true,
      'unlimited_tokens',true,
      'all_content',true,
      'all_games',true,
      'all_romans',true,
      'all_licenses',true,
      'admin',true,
      'server_version','24.4.11'
    )
  else
    jsonb_build_object(
      'owner',false,
      'unlimited_tokens',false,
      'all_content',false,
      'all_games',false,
      'all_romans',false,
      'all_licenses',false,
      'admin',false,
      'server_version','24.4.11'
    )
  end;
$$;
revoke all on function public.get_sinjira_account_capabilities() from public,anon;
grant execute on function public.get_sinjira_account_capabilities() to authenticated;

-- ---------------------------------------------------------------------------
-- DIAGNOSTIC NON SECRET
-- Il indique seulement la présence des fondations nécessaires, jamais leur contenu.
-- ---------------------------------------------------------------------------
create or replace function public.get_sinjira_runtime_health()
returns jsonb
language sql
stable
security definer
set search_path=public
as $$
  select jsonb_build_object(
    'ok',
      to_regclass('public.profiles') is not null and
      to_regclass('public.character_submissions') is not null and
      to_regclass('public.characters') is not null and
      to_regclass('public.admin_notifications') is not null and
      to_regclass('public.products') is not null and
      to_regclass('public.user_entitlements') is not null and
      to_regprocedure('public.ensure_sinjira_owner_character()') is not null and
      to_regprocedure('public.has_sinjira_product(text,uuid)') is not null and
      to_regprocedure('public.is_sinjira_admin(uuid)') is not null and
      to_regprocedure('public.fracture_engine_health()') is not null,
    'platform_version','24.4.11',
    'components',jsonb_build_object(
      'profiles',to_regclass('public.profiles') is not null,
      'character_submissions',to_regclass('public.character_submissions') is not null,
      'characters',to_regclass('public.characters') is not null,
      'admin_notifications',to_regclass('public.admin_notifications') is not null,
      'products',to_regclass('public.products') is not null,
      'user_entitlements',to_regclass('public.user_entitlements') is not null,
      'owner_repair',to_regprocedure('public.ensure_sinjira_owner_character()') is not null,
      'admin_check',to_regprocedure('public.is_sinjira_admin(uuid)') is not null,
      'fracture_health',to_regprocedure('public.fracture_engine_health()') is not null
    )
  );
$$;
revoke all on function public.get_sinjira_runtime_health() from public,anon;
grant execute on function public.get_sinjira_runtime_health() to authenticated,service_role;

-- Réapplique la réparation propriétaire lorsque la fonction V24.3.1 est installée.
-- L'appel est idempotent et s'exécute avec auth.uid() NULL depuis la migration.
do $$
begin
  if to_regprocedure('public.ensure_sinjira_owner_character()') is not null then
    perform public.ensure_sinjira_owner_character();
  end if;
end $$;
