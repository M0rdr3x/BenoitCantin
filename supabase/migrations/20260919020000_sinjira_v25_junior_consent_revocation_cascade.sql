-- SINJIRA™ V25 — révocation durable du consentement Communauté Junior.
-- Une révocation/suppression de guardian_links met fin au mandat de supervision.
-- Le consentement Junior lié ne doit jamais ressusciter automatiquement si le lien
-- parent/tuteur est recréé ou réactivé plus tard.

begin;

create or replace function private.sinjira_revoke_junior_consent_on_guardian_link()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_minor uuid;
  v_guardian uuid;
begin
  if tg_op='DELETE' then
    v_minor:=old.minor_user_id;
    v_guardian:=old.guardian_user_id;
  elsif coalesce(new.status,'')<>'verified' or new.revoked_at is not null then
    v_minor:=new.minor_user_id;
    v_guardian:=new.guardian_user_id;
  else
    return new;
  end if;

  update public.junior_community_guardian_consents
  set revoked_at=coalesce(revoked_at,now())
  where minor_user_id=v_minor
    and guardian_user_id=v_guardian
    and revoked_at is null;

  if tg_op='DELETE' then return old; end if;
  return new;
end;
$$;

revoke all on function private.sinjira_revoke_junior_consent_on_guardian_link()
from public,anon,authenticated;

drop trigger if exists sinjira_revoke_junior_consent_on_guardian_link
on public.guardian_links;

create trigger sinjira_revoke_junior_consent_on_guardian_link
after update of status,revoked_at or delete on public.guardian_links
for each row
execute function private.sinjira_revoke_junior_consent_on_guardian_link();

comment on function private.sinjira_revoke_junior_consent_on_guardian_link() is
  'V25: une révocation ou suppression du lien tuteur révoque durablement le consentement Junior associé; réactivation de supervision != réactivation Junior.';

commit;
