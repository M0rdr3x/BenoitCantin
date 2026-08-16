-- SINJIRA™ V24.4.13 — marqueur et diagnostic de plateforme
-- Copie conforme de la migration appliquée en production.

create or replace function public.get_sinjira_server_version()
returns text
language sql
stable
set search_path=public
as $$ select '24.4.13'::text; $$;
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;

create or replace function public.get_sinjira_account_capabilities()
returns jsonb
language sql
stable
set search_path=public,auth
as $$
  select case when public.is_sinjira_owner(auth.uid()) then
    jsonb_build_object('owner',true,'unlimited_tokens',true,'all_content',true,'all_games',true,'all_romans',true,'all_licenses',true,'admin',true,'server_version','24.4.13')
  else
    jsonb_build_object('owner',false,'unlimited_tokens',false,'all_content',false,'all_games',false,'all_romans',false,'all_licenses',false,'admin',false,'server_version','24.4.13')
  end;
$$;
revoke all on function public.get_sinjira_account_capabilities() from public,anon;
grant execute on function public.get_sinjira_account_capabilities() to authenticated;

create or replace function public.get_sinjira_runtime_health()
returns jsonb
language sql
stable
set search_path=public
as $$
select jsonb_build_object(
  'ok',
    to_regclass('public.profiles') is not null
    and to_regclass('public.characters') is not null
    and to_regclass('public.character_submissions') is not null
    and to_regclass('public.account_safety_profiles') is not null
    and to_regclass('public.guardian_links') is not null
    and to_regclass('public.products') is not null
    and to_regclass('public.user_entitlements') is not null
    and to_regclass('public.admin_notifications') is not null
    and to_regclass('public.character_submissions_one_per_user_uidx') is not null
    and to_regclass('public.characters_one_active_per_user_uidx') is not null
    and to_regprocedure('public.ensure_sinjira_owner_character()') is not null
    and to_regprocedure('public.has_sinjira_product(text,uuid)') is not null
    and to_regprocedure('public.is_fracture_party_member(uuid,uuid)') is not null
    and to_regprocedure('public.sinjira_content_allowed(uuid,text)') is not null
    and to_regprocedure('public.sinjira_cycle_allowed(uuid,uuid)') is not null,
  'platform_version','24.4.13',
  'components',jsonb_build_object(
    'profiles',to_regclass('public.profiles') is not null,
    'characters',to_regclass('public.characters') is not null,
    'character_submissions',to_regclass('public.character_submissions') is not null,
    'account_safety_profiles',to_regclass('public.account_safety_profiles') is not null,
    'guardian_links',to_regclass('public.guardian_links') is not null,
    'products',to_regclass('public.products') is not null,
    'user_entitlements',to_regclass('public.user_entitlements') is not null,
    'admin_notifications',to_regclass('public.admin_notifications') is not null,
    'registry_submission_unique',to_regclass('public.character_submissions_one_per_user_uidx') is not null,
    'active_character_unique',to_regclass('public.characters_one_active_per_user_uidx') is not null,
    'owner_repair',to_regprocedure('public.ensure_sinjira_owner_character()') is not null,
    'product_check',to_regprocedure('public.has_sinjira_product(text,uuid)') is not null,
    'fracture_membership_privacy',to_regprocedure('public.is_fracture_party_member(uuid,uuid)') is not null,
    'content_policy',to_regprocedure('public.sinjira_content_allowed(uuid,text)') is not null,
    'cycle_policy',to_regprocedure('public.sinjira_cycle_allowed(uuid,uuid)') is not null
  )
);
$$;
revoke all on function public.get_sinjira_runtime_health() from public,anon;
grant execute on function public.get_sinjira_runtime_health() to authenticated,service_role;
