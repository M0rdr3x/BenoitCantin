-- SINJIRA™ V24.4.74 — garde de cycle de vie Rencontres.
-- Une relation devenue inadmissible, une perte d'admissibilité d'âge ou un blocage ferme les présentations actives.

create or replace function private.dating_close_active_for_user(p_user_id uuid)
returns void
language sql volatile security definer
set search_path=pg_catalog,public
as $$
  update public.dating_introductions
  set status='closed',closed_at=coalesce(closed_at,now()),updated_at=now()
  where p_user_id in(user_a,user_b) and status in('requested','accepted');
$$;
revoke all on function private.dating_close_active_for_user(uuid) from public,anon,authenticated;
grant execute on function private.dating_close_active_for_user(uuid) to service_role;

create or replace function private.dating_deactivate_on_private_profile_change()
returns trigger
language plpgsql security definer
set search_path=pg_catalog,public,private
as $$
begin
  if not private.dating_allowed_relationship_status(new.relationship_status) then
    update public.dating_profiles set active=false,updated_at=now() where user_id=new.user_id and active=true;
    perform private.dating_close_active_for_user(new.user_id);
  end if;
  return new;
end;
$$;
revoke all on function private.dating_deactivate_on_private_profile_change() from public,anon,authenticated;

create or replace function private.dating_deactivate_on_safety_change()
returns trigger
language plpgsql security definer
set search_path=pg_catalog,public,private
as $$
begin
  if public.sinjira_age_band(new.user_id)<>'adult' then
    update public.dating_profiles set active=false,updated_at=now() where user_id=new.user_id and active=true;
    perform private.dating_close_active_for_user(new.user_id);
  end if;
  return new;
end;
$$;
revoke all on function private.dating_deactivate_on_safety_change() from public,anon,authenticated;

create or replace function private.dating_close_on_social_block()
returns trigger
language plpgsql security definer
set search_path=pg_catalog,public
as $$
begin
  update public.dating_introductions
  set status='closed',closed_at=coalesce(closed_at,now()),updated_at=now()
  where status in('requested','accepted')
    and ((user_a=new.blocker_user_id and user_b=new.blocked_user_id)
      or (user_a=new.blocked_user_id and user_b=new.blocker_user_id));
  return new;
end;
$$;
revoke all on function private.dating_close_on_social_block() from public,anon,authenticated;

drop trigger if exists dating_social_block_guard on public.social_blocks;
create trigger dating_social_block_guard
after insert on public.social_blocks
for each row execute function private.dating_close_on_social_block();

comment on function private.dating_close_active_for_user(uuid) is 'Ferme les présentations Rencontres lorsqu’un compte ne remplit plus les conditions 18+/statut.';
comment on function private.dating_close_on_social_block() is 'Ferme immédiatement une présentation Rencontres lorsqu’un participant bloque l’autre.';
