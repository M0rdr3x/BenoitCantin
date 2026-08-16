-- SINJIRA™ V24.4.12 — âge minimum appliqué sur le profil de sécurité canonique.
-- Le navigateur n'est jamais considéré comme autorité pour l'âge.

create or replace function public.enforce_sinjira_account_safety_age()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
declare years integer;
begin
  if new.date_of_birth is null then raise exception 'BIRTH_DATE_REQUIRED'; end if;
  if new.date_of_birth>current_date then raise exception 'INVALID_BIRTH_DATE'; end if;
  years:=extract(year from age(current_date,new.date_of_birth))::integer;
  if years<12 then raise exception 'SINJIRA_MINIMUM_AGE_12'; end if;
  if years>120 then raise exception 'INVALID_BIRTH_DATE'; end if;
  if new.sex is not null and new.sex not in ('female','male') then raise exception 'SEX_REQUIRED_FEMALE_OR_MALE'; end if;
  return new;
end;
$$;
revoke all on function public.enforce_sinjira_account_safety_age() from public,anon,authenticated;

drop trigger if exists enforce_sinjira_account_safety_age_trigger on public.account_safety_profiles;
create trigger enforce_sinjira_account_safety_age_trigger
before insert or update of date_of_birth,sex on public.account_safety_profiles
for each row execute function public.enforce_sinjira_account_safety_age();
