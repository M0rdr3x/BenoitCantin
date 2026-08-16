-- SINJIRA™ — VÉRIFICATION PRODUCTION V24.3.6
-- Lecture seulement : ce fichier ne modifie aucune donnée.

select
  public.get_sinjira_server_version() as server_version,
  to_regclass('public.private_profiles') is not null as private_profiles_ok,
  to_regclass('public.family_relationships') is not null as family_relationships_ok,
  to_regclass('public.character_social_profiles') is not null as character_social_profiles_ok,
  to_regclass('public.parallel_character_state') is not null as parallel_character_state_ok,
  to_regclass('public.fracture_parties') is not null as fracture_parties_ok,
  to_regclass('public.fracture_party_members') is not null as fracture_party_members_ok,
  to_regclass('public.fracture_player_documents') is not null as fracture_player_documents_ok,
  to_regclass('public.fracture_endgame_reports') is not null as fracture_endgame_reports_ok,
  to_regclass('public.products') is not null as products_ok,
  to_regclass('public.user_entitlements') is not null as user_entitlements_ok,
  to_regclass('public.token_ledger') is not null as token_ledger_ok,
  to_regclass('public.market_listings') is not null as market_listings_ok,
  to_regprocedure('public.get_sinjira_account_capabilities()') is not null as capabilities_rpc_ok,
  to_regprocedure('public.has_sinjira_product(text,uuid)') is not null as product_access_rpc_ok,
  to_regprocedure('public.create_fracture_party(integer,integer,integer)') is not null as create_fracture_party_rpc_ok,
  to_regprocedure('public.join_fracture_party(text,integer)') is not null as join_fracture_party_rpc_ok,
  to_regprocedure('public.ensure_sinjira_owner_character()') is not null as owner_character_rpc_ok;

select
  u.id as owner_user_id,
  u.email as owner_email,
  p.pseudo,
  p.display_name,
  c.id as character_id,
  c.public_name as character_name,
  c.status as character_status,
  c.visible_to_user,
  c.portrait_path,
  c.novel_note,
  exists(select 1 from public.character_social_profiles csp where csp.user_id=u.id) as social_profile_ok,
  exists(select 1 from public.parallel_character_state pcs where pcs.user_id=u.id) as parallel_state_ok
from auth.users u
left join public.profiles p on p.user_id=u.id
left join lateral (
  select c.* from public.characters c
  where c.user_id=u.id
  order by case when lower(coalesce(c.public_name,''))='abysstime' then 0 else 1 end,
           c.updated_at desc
  limit 1
) c on true
where lower(coalesce(u.email,''))='kingtyrano@gmail.com';

select
  p.id,
  p.name as project_identifier,
  p.slug as technical_slug,
  p.status,
  p.visibility
from public.projects p
where p.slug='fracture-du-reseau-mere';

select
  pr.slug,
  pr.name,
  pr.active,
  public.has_sinjira_product(pr.slug,u.id) as owner_has_access
from public.products pr
cross join lateral (
  select id from auth.users where lower(coalesce(email,''))='kingtyrano@gmail.com' limit 1
) u
where pr.slug='fracture-du-reseau-mere';
