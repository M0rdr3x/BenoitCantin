-- SINJIRA™ V25 — consentement réel du compte jeunesse pour les métadonnées de contacts.
-- Privacy by default :
--   * aucun nouveau lien de supervision n'autorise ces métadonnées automatiquement;
--   * toute réactivation d'un lien remet cette permission à false;
--   * les liens actifs existants sont remis à false;
--   * seul le compte enfant/jeunesse concerné peut l'activer ou la retirer.

alter table public.guardian_links
  alter column can_view_contact_metadata set default false;

create or replace function private.sinjira_guardian_contact_metadata_default_off()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
begin
  if new.status='verified' and new.revoked_at is null then
    new.can_view_contact_metadata:=false;
  end if;
  return new;
end;
$$;

revoke all on function private.sinjira_guardian_contact_metadata_default_off()
from public,anon,authenticated;

drop trigger if exists guardian_contact_metadata_default_off
on public.guardian_links;

create trigger guardian_contact_metadata_default_off
before insert or update of status,revoked_at
on public.guardian_links
for each row
execute function private.sinjira_guardian_contact_metadata_default_off();

-- Les permissions historiques activées implicitement ne sont pas considérées
-- comme un consentement explicite de la personne mineure.
update public.guardian_links
set can_view_contact_metadata=false,
    updated_at=now()
where status='verified'
  and revoked_at is null
  and can_view_contact_metadata is true;

create or replace function public.set_my_guardian_contact_metadata(
  p_link_id uuid,
  p_allowed boolean
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  uid uuid:=auth.uid();
  r public.guardian_links%rowtype;
  band text;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  select *
  into r
  from public.guardian_links
  where id=p_link_id
    and minor_user_id=uid
    and status='verified'
    and revoked_at is null
  for update;

  if r.id is null then
    raise exception 'GUARDIAN_LINK_NOT_ACTIVE';
  end if;

  band:=public.sinjira_age_band(uid);
  if band not in ('child','youth') then
    raise exception 'MINOR_ACCOUNT_REQUIRED';
  end if;

  update public.guardian_links
  set can_view_contact_metadata=coalesce(p_allowed,false),
      updated_at=now()
  where id=r.id;

  return jsonb_build_object(
    'ok',true,
    'link_id',r.id,
    'can_view_contact_metadata',coalesce(p_allowed,false)
  );
end;
$$;

revoke all on function public.set_my_guardian_contact_metadata(uuid,boolean)
from public,anon;
grant execute on function public.set_my_guardian_contact_metadata(uuid,boolean)
to authenticated;

comment on function private.sinjira_guardian_contact_metadata_default_off() is
  'V25 privacy-by-default: création/réactivation d un guardian_link remet can_view_contact_metadata à false.';
comment on function public.set_my_guardian_contact_metadata(uuid,boolean) is
  'V25 self-only: le compte child/youth lié décide explicitement si son tuteur peut consulter les métadonnées de contacts; retrait disponible immédiatement.';
