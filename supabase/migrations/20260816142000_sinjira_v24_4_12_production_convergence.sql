-- SINJIRA™ V24.4.12 — convergence GitHub ↔ production
-- Migration idempotente : reflète les durcissements déjà appliqués directement à Supabase.

create or replace function public.is_sinjira_owner(p_user_id uuid default auth.uid())
returns boolean language sql stable security definer set search_path=public,auth as $$
 select exists(select 1 from auth.users u where u.id=p_user_id and lower(coalesce(u.email,''))='kingtyrano@gmail.com')
 and (coalesce(auth.jwt()->>'role','')='service_role' or auth.uid() is null or p_user_id=auth.uid());
$$;
revoke all on function public.is_sinjira_owner(uuid) from public,anon;
grant execute on function public.is_sinjira_owner(uuid) to authenticated,service_role;

create or replace function public.has_sinjira_product(p_product_slug text,p_user_id uuid default auth.uid())
returns boolean language sql stable security definer set search_path=public,auth as $$
 select case when p_user_id is null then false
 when coalesce(auth.jwt()->>'role','')<>'service_role' and auth.uid() is not null and p_user_id is distinct from auth.uid() then false
 else public.is_sinjira_owner(p_user_id) or exists(select 1 from public.user_entitlements ue join public.products p on p.id=ue.product_id where ue.user_id=p_user_id and p.slug=p_product_slug and p.active=true) end;
$$;
revoke all on function public.has_sinjira_product(text,uuid) from public,anon;
grant execute on function public.has_sinjira_product(text,uuid) to authenticated,service_role;

create table if not exists public.admin_notifications(
 id uuid primary key default gen_random_uuid(), notification_type text not null, title text not null,
 body text not null default '', related_user_id uuid references auth.users(id) on delete set null,
 related_entity_type text, related_entity_id uuid, read_at timestamptz, created_at timestamptz not null default now()
);
create index if not exists admin_notifications_created_idx on public.admin_notifications(created_at desc);
create index if not exists admin_notifications_related_user_idx on public.admin_notifications(related_user_id);
alter table public.admin_notifications enable row level security;
drop policy if exists admin_notifications_owner_read on public.admin_notifications;
create policy admin_notifications_owner_read on public.admin_notifications for select to authenticated using(public.is_sinjira_owner(auth.uid()) or exists(select 1 from public.internal_admin_users a where a.user_id=auth.uid()));
drop policy if exists admin_notifications_owner_update on public.admin_notifications;
create policy admin_notifications_owner_update on public.admin_notifications for update to authenticated using(public.is_sinjira_owner(auth.uid()) or exists(select 1 from public.internal_admin_users a where a.user_id=auth.uid())) with check(public.is_sinjira_owner(auth.uid()) or exists(select 1 from public.internal_admin_users a where a.user_id=auth.uid()));
revoke all on public.admin_notifications from anon;
grant select,update on public.admin_notifications to authenticated;
grant all on public.admin_notifications to service_role;

insert into public.products(slug,name,product_type,active) values('fracture-du-reseau-mere','Fracture du Réseau-Mère','game',true)
on conflict(slug) do update set name=excluded.name,product_type=excluded.product_type,active=true;
insert into public.user_entitlements(user_id,product_id,source)
select u.id,p.id,'owner' from auth.users u cross join public.products p
where lower(coalesce(u.email,''))='kingtyrano@gmail.com' and p.slug='fracture-du-reseau-mere'
on conflict(user_id,product_id) do nothing;

create or replace function public.get_sinjira_server_version()
returns text language sql stable security definer set search_path=public as $$ select '24.4.12'::text $$;
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;

create or replace function public.get_sinjira_runtime_health()
returns jsonb language sql stable security definer set search_path=public as $$
select jsonb_build_object('ok',to_regclass('public.profiles') is not null and to_regclass('public.characters') is not null and to_regclass('public.character_submissions') is not null and to_regclass('public.account_safety_profiles') is not null and to_regclass('public.guardian_links') is not null and to_regclass('public.products') is not null and to_regclass('public.user_entitlements') is not null and to_regclass('public.admin_notifications') is not null and to_regprocedure('public.ensure_sinjira_owner_character()') is not null and to_regprocedure('public.has_sinjira_product(text,uuid)') is not null,'platform_version','24.4.12','components',jsonb_build_object('profiles',to_regclass('public.profiles') is not null,'characters',to_regclass('public.characters') is not null,'character_submissions',to_regclass('public.character_submissions') is not null,'account_safety_profiles',to_regclass('public.account_safety_profiles') is not null,'guardian_links',to_regclass('public.guardian_links') is not null,'products',to_regclass('public.products') is not null,'user_entitlements',to_regclass('public.user_entitlements') is not null,'admin_notifications',to_regclass('public.admin_notifications') is not null,'owner_repair',to_regprocedure('public.ensure_sinjira_owner_character()') is not null,'product_check',to_regprocedure('public.has_sinjira_product(text,uuid)') is not null));
$$;
revoke all on function public.get_sinjira_runtime_health() from public,anon;
grant execute on function public.get_sinjira_runtime_health() to authenticated,service_role;

create or replace function public.get_sinjira_account_capabilities()
returns jsonb language sql stable security definer set search_path=public,auth as $$
 select case when public.is_sinjira_owner(auth.uid()) then jsonb_build_object('owner',true,'unlimited_tokens',true,'all_content',true,'all_games',true,'all_romans',true,'all_licenses',true,'admin',true,'server_version','24.4.12')
 else jsonb_build_object('owner',false,'unlimited_tokens',false,'all_content',false,'all_games',false,'all_romans',false,'all_licenses',false,'admin',false,'server_version','24.4.12') end;
$$;
revoke all on function public.get_sinjira_account_capabilities() from public,anon;
grant execute on function public.get_sinjira_account_capabilities() to authenticated;

-- Réduit la surface RPC des fonctions exclusivement destinées aux triggers.
revoke all on function public.assign_parallel_world_membership() from public,anon,authenticated;
revoke all on function public.enforce_one_character_per_user() from public,anon,authenticated;
revoke all on function public.enforce_one_character_submission_per_user() from public,anon,authenticated;
revoke all on function public.protect_parallel_character_life() from public,anon,authenticated;
revoke all on function public.sync_character_social_profile() from public,anon,authenticated;
revoke all on function public.sync_social_profile_from_profile() from public,anon,authenticated;
revoke execute on function public.has_accepted_community_rules(uuid) from public,anon;
revoke execute on function public.social_is_blocked(uuid,uuid) from public,anon;
revoke execute on function public.social_is_suspended(uuid) from public,anon;
grant execute on function public.has_accepted_community_rules(uuid) to authenticated,service_role;
grant execute on function public.social_is_blocked(uuid,uuid) to authenticated,service_role;
grant execute on function public.social_is_suspended(uuid) to authenticated,service_role;

-- Indexes des parcours chauds et clés étrangères.
create index if not exists access_requests_project_id_idx on public.access_requests(project_id);
create index if not exists access_requests_reviewed_by_idx on public.access_requests(reviewed_by);
create index if not exists characters_novel_id_idx on public.characters(novel_id);
create index if not exists character_generation_runs_submission_id_idx on public.character_generation_runs(submission_id);
create index if not exists character_generation_runs_character_id_idx on public.character_generation_runs(character_id);
create index if not exists fracture_parties_owner_user_id_idx on public.fracture_parties(owner_user_id);
create index if not exists fracture_endgame_reports_owner_user_id_idx on public.fracture_endgame_reports(owner_user_id);
create index if not exists guardian_links_guardian_user_id_idx on public.guardian_links(guardian_user_id);
create index if not exists family_link_invites_owner_user_id_idx on public.family_link_invites(owner_user_id);
create index if not exists project_access_project_id_idx on public.project_access(project_id);
create index if not exists project_access_granted_by_idx on public.project_access(granted_by);
create index if not exists reader_library_novel_id_idx on public.reader_library(novel_id);
create index if not exists user_entitlements_product_id_idx on public.user_entitlements(product_id);
create index if not exists novel_comments_user_id_idx on public.novel_comments(user_id);
create index if not exists social_real_posts_user_id_idx on public.social_real_posts(user_id);
create index if not exists social_real_comments_user_id_idx on public.social_real_comments(user_id);
create index if not exists social_real_messages_recipient_user_id_idx on public.social_real_messages(recipient_user_id);
create index if not exists social_character_posts_user_id_idx on public.social_character_posts(user_id);
create index if not exists social_character_posts_character_id_idx on public.social_character_posts(character_id);
create index if not exists social_character_comments_user_id_idx on public.social_character_comments(user_id);
create index if not exists social_character_comments_character_id_idx on public.social_character_comments(character_id);
create index if not exists social_character_messages_sender_user_id_idx on public.social_character_messages(sender_user_id);
create index if not exists social_character_messages_recipient_user_id_idx on public.social_character_messages(recipient_user_id);
create index if not exists social_character_messages_recipient_character_id_idx on public.social_character_messages(recipient_character_id);
drop index if exists public.sinjira_character_applications_user_idx;
drop index if exists public.sinjira_novel_comments_novel_idx;
