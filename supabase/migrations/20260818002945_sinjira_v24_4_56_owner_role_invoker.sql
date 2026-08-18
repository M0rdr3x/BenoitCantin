-- SINJIRA V24.4.56 — rôles administrateur explicites et vérification SECURITY INVOKER.
-- Le compte connecté peut uniquement lire sa propre ligne de rôle; aucune table auth.users
-- n'est requise pour afficher son statut admin/propriétaire.

alter table public.internal_admin_users
  add column if not exists role text not null default 'admin';

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid='public.internal_admin_users'::regclass
      and conname='internal_admin_users_role_check'
  ) then
    alter table public.internal_admin_users
      add constraint internal_admin_users_role_check
      check (role in ('owner','admin'));
  end if;
end $$;

update public.internal_admin_users a
set role='owner'
from auth.users u
where u.id=a.user_id
  and lower(coalesce(u.email,''))='kingtyrano@gmail.com';

alter table public.internal_admin_users enable row level security;

grant select on public.internal_admin_users to authenticated;
revoke insert,update,delete on public.internal_admin_users from authenticated;
revoke all on public.internal_admin_users from anon;
grant all on public.internal_admin_users to service_role;

drop policy if exists internal_admin_users_self_read on public.internal_admin_users;
create policy internal_admin_users_self_read
on public.internal_admin_users
for select to authenticated
using (user_id=(select auth.uid()));

create or replace function public.is_sinjira_admin(p_user_id uuid default auth.uid())
returns boolean
language sql
stable
security invoker
set search_path=public,auth,pg_temp
as $$
  select p_user_id is not null
    and (
      coalesce(auth.jwt()->>'role','')='service_role'
      or p_user_id=(select auth.uid())
    )
    and exists(
      select 1 from public.internal_admin_users a
      where a.user_id=p_user_id
    );
$$;

create or replace function public.is_sinjira_owner(p_user_id uuid default auth.uid())
returns boolean
language sql
stable
security invoker
set search_path=public,auth,pg_temp
as $$
  select p_user_id is not null
    and (
      coalesce(auth.jwt()->>'role','')='service_role'
      or p_user_id=(select auth.uid())
    )
    and exists(
      select 1 from public.internal_admin_users a
      where a.user_id=p_user_id and a.role='owner'
    );
$$;

revoke all on function public.is_sinjira_admin(uuid) from public,anon;
revoke all on function public.is_sinjira_owner(uuid) from public,anon;
grant execute on function public.is_sinjira_admin(uuid) to authenticated,service_role;
grant execute on function public.is_sinjira_owner(uuid) to authenticated,service_role;

create or replace function public.sinjira_owner_role_health()
returns jsonb
language sql
stable
security invoker
set search_path=public,pg_temp
as $$
  select jsonb_build_object(
    'ok',
      (select count(*)=1 from public.internal_admin_users where role='owner')
      and exists(
        select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
        where n.nspname='public' and p.proname='is_sinjira_admin' and p.prosecdef=false
      )
      and exists(
        select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
        where n.nspname='public' and p.proname='is_sinjira_owner' and p.prosecdef=false
      )
      and exists(
        select 1 from pg_policies
        where schemaname='public' and tablename='internal_admin_users'
          and policyname='internal_admin_users_self_read'
      ),
    'owner_count',(select count(*) from public.internal_admin_users where role='owner'),
    'admin_invoker',exists(
      select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='public' and p.proname='is_sinjira_admin' and p.prosecdef=false
    ),
    'owner_invoker',exists(
      select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='public' and p.proname='is_sinjira_owner' and p.prosecdef=false
    ),
    'self_policy',exists(
      select 1 from pg_policies
      where schemaname='public' and tablename='internal_admin_users'
        and policyname='internal_admin_users_self_read'
    ),
    'version','24.4.56'
  );
$$;

revoke all on function public.sinjira_owner_role_health() from public,anon,authenticated;
grant execute on function public.sinjira_owner_role_health() to service_role;
