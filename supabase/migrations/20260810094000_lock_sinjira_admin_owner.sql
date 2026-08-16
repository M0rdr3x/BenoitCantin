-- SINJIRA — verrouillage du compte administrateur propriétaire
-- Cette migration a déjà été appliquée dans Supabase.
-- Elle est incluse ici comme copie de référence.

delete from public.internal_admin_users a
where not exists (
  select 1
  from auth.users u
  where u.id = a.user_id
    and lower(u.email) = lower('kingtyrano@gmail.com')
);

insert into public.internal_admin_users(user_id)
select u.id
from auth.users u
where lower(u.email) = lower('kingtyrano@gmail.com')
on conflict (user_id) do nothing;

create or replace function public.enforce_sinjira_single_admin()
returns trigger
language plpgsql
security definer
set search_path = public, auth
as $$
begin
  if not exists (
    select 1
    from auth.users u
    where u.id = new.user_id
      and lower(u.email) = lower('kingtyrano@gmail.com')
  ) then
    raise exception 'Le rôle administrateur SINJIRA est réservé au compte propriétaire.';
  end if;
  return new;
end;
$$;

drop trigger if exists enforce_sinjira_single_admin_trigger on public.internal_admin_users;
create trigger enforce_sinjira_single_admin_trigger
before insert or update on public.internal_admin_users
for each row execute function public.enforce_sinjira_single_admin();

create or replace function public.is_sinjira_admin(p_user_id uuid default auth.uid())
returns boolean
language sql
stable
security definer
set search_path = public, auth
as $$
  select exists (
    select 1
    from public.internal_admin_users a
    join auth.users u on u.id = a.user_id
    where a.user_id = p_user_id
      and lower(u.email) = lower('kingtyrano@gmail.com')
  );
$$;

revoke all on public.internal_admin_users from anon, authenticated;
revoke all on function public.enforce_sinjira_single_admin() from public, anon, authenticated;
revoke all on function public.is_sinjira_admin(uuid) from public;
grant execute on function public.is_sinjira_admin(uuid) to authenticated, service_role;
