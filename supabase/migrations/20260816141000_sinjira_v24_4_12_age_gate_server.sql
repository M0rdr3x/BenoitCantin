-- SINJIRA™ V24.4.12 — âge minimum appliqué au serveur
-- Le navigateur n'est jamais considéré comme autorité pour l'âge.

create or replace function public.enforce_sinjira_private_profile_age()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
declare
  years integer;
begin
  if new.birth_date is null then
    raise exception 'BIRTH_DATE_REQUIRED';
  end if;
  if new.birth_date > current_date then
    raise exception 'INVALID_BIRTH_DATE';
  end if;
  years := extract(year from age(current_date,new.birth_date))::integer;
  if years < 12 then
    raise exception 'SINJIRA_MINIMUM_AGE_12';
  end if;
  if years > 120 then
    raise exception 'INVALID_BIRTH_DATE';
  end if;
  if new.gender is null or new.gender not in ('Homme','Femme') then
    raise exception 'PROFILE_SEX_REQUIRED';
  end if;
  return new;
end;
$$;

revoke all on function public.enforce_sinjira_private_profile_age() from public,anon,authenticated;

drop trigger if exists enforce_sinjira_private_profile_age_trigger on public.private_profiles;
create trigger enforce_sinjira_private_profile_age_trigger
before insert or update of birth_date,gender on public.private_profiles
for each row execute function public.enforce_sinjira_private_profile_age();
