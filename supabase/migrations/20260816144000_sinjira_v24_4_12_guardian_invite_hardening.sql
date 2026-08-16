-- SINJIRA™ V24.4.12 — durcissement du cycle d'autorisation parentale
-- Un seul code non consommé par tuteur, format contrôlé et réactivation sûre d'un lien révoqué.

-- Nettoyage idempotent des anciens codes non consommés en doublon : conserver le plus récent.
with ranked as (
  select id,
         row_number() over(partition by guardian_user_id order by created_at desc,id desc) as rn
  from public.guardian_signup_invites
  where used_at is null
)
delete from public.guardian_signup_invites g
using ranked r
where g.id=r.id and r.rn>1;

create unique index if not exists guardian_signup_invites_one_open_per_guardian_idx
  on public.guardian_signup_invites(guardian_user_id)
  where used_at is null;

-- Contraintes métier indépendantes du navigateur.
do $$
begin
  if not exists(select 1 from pg_constraint where conname='guardian_signup_invites_code_format_check') then
    alter table public.guardian_signup_invites
      add constraint guardian_signup_invites_code_format_check
      check (invite_code ~ '^YOUTH-[A-Z0-9]{10}$');
  end if;
  if not exists(select 1 from pg_constraint where conname='guardian_signup_invites_expiry_check') then
    alter table public.guardian_signup_invites
      add constraint guardian_signup_invites_expiry_check
      check (expires_at > consented_at);
  end if;
  if not exists(select 1 from pg_constraint where conname='guardian_signup_invites_used_after_consent_check') then
    alter table public.guardian_signup_invites
      add constraint guardian_signup_invites_used_after_consent_check
      check (used_at is null or used_at >= consented_at);
  end if;
  if not exists(select 1 from pg_constraint where conname='guardian_signup_invites_not_self_check') then
    alter table public.guardian_signup_invites
      add constraint guardian_signup_invites_not_self_check
      check (minor_user_id is null or minor_user_id <> guardian_user_id);
  end if;
end $$;

create or replace function public.create_guardian_signup_invite()
returns text
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  v_code text;
begin
  if auth.uid() is null then raise exception 'AUTH_REQUIRED'; end if;
  if public.sinjira_age_band(auth.uid()) <> 'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;
  if not public.sinjira_mfa_access_allowed(auth.uid()) then raise exception 'MFA_REQUIRED'; end if;

  -- Générer un nouveau code invalide tous les anciens codes non consommés de ce tuteur.
  delete from public.guardian_signup_invites
  where guardian_user_id=auth.uid() and used_at is null;

  loop
    v_code:='YOUTH-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,10));
    exit when not exists(select 1 from public.guardian_signup_invites where invite_code=v_code);
  end loop;

  insert into public.guardian_signup_invites(guardian_user_id,invite_code)
  values(auth.uid(),v_code);
  return v_code;
end;
$$;
revoke all on function public.create_guardian_signup_invite() from public,anon;
grant execute on function public.create_guardian_signup_invite() to authenticated;

-- Quand un code est consommé par le trigger d'inscription, garantir que le lien
-- guardian_links reflète le consentement, même si une ancienne relation avait été révoquée.
create or replace function public.sync_guardian_signup_invite_link()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
begin
  if new.used_at is not null and new.minor_user_id is not null then
    insert into public.guardian_links(
      minor_user_id,guardian_user_id,status,guardian_role,
      can_view_contact_metadata,consented_at,revoked_at
    )
    values(
      new.minor_user_id,new.guardian_user_id,'verified','parent',
      true,new.consented_at,null
    )
    on conflict(minor_user_id,guardian_user_id) do update
      set status='verified',
          guardian_role='parent',
          can_view_contact_metadata=true,
          consented_at=excluded.consented_at,
          revoked_at=null,
          updated_at=now();
  end if;
  return new;
end;
$$;
revoke all on function public.sync_guardian_signup_invite_link() from public,anon,authenticated;

drop trigger if exists sync_guardian_signup_invite_link_trigger on public.guardian_signup_invites;
create trigger sync_guardian_signup_invite_link_trigger
after insert or update of used_at,minor_user_id on public.guardian_signup_invites
for each row
when (new.used_at is not null and new.minor_user_id is not null)
execute function public.sync_guardian_signup_invite_link();
