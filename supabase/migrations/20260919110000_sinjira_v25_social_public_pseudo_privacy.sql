-- SINJIRA™ V25 — cloisonner le pseudonyme public du nom affiché privé.
-- Le profil social est lisible par les membres authentifiés : il ne doit donc jamais
-- recevoir le display_name privé du Compte. Pour compatibilité, social_profiles.display_name
-- reste présent mais devient un miroir du pseudonyme public uniquement.

create or replace function public.sync_social_profile_from_profile()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_public_pseudo text:=coalesce(nullif(btrim(new.pseudo),''),'Membre SINJIRA');
begin
  insert into public.social_profiles(
    user_id,pseudo,display_name,avatar_path,updated_at
  )
  values(
    new.user_id,
    v_public_pseudo,
    v_public_pseudo,
    new.avatar_path,
    now()
  )
  on conflict(user_id) do update
  set pseudo=excluded.pseudo,
      display_name=excluded.display_name,
      avatar_path=excluded.avatar_path,
      updated_at=now();

  return new;
end;
$$;

drop trigger if exists sync_social_profile_trigger on public.profiles;
create trigger sync_social_profile_trigger
after insert or update of pseudo,display_name,avatar_path
on public.profiles
for each row
execute function public.sync_social_profile_from_profile();

with public_labels as (
  select
    p.user_id,
    coalesce(nullif(btrim(p.pseudo),''),'Membre SINJIRA') as public_pseudo
  from public.profiles p
)
update public.social_profiles sp
set pseudo=l.public_pseudo,
    display_name=l.public_pseudo,
    updated_at=now()
from public_labels l
where l.user_id=sp.user_id
  and (
    sp.pseudo is distinct from l.public_pseudo
    or sp.display_name is distinct from l.public_pseudo
  );

revoke all on function public.sync_social_profile_from_profile()
from public,anon,authenticated;

comment on function public.sync_social_profile_from_profile() is
  'V25 confidentialité: social_profiles utilise uniquement profiles.pseudo. Le display_name privé du Compte n est jamais copié vers le profil social.';
comment on column public.social_profiles.display_name is
  'Compatibilité V25 : miroir du pseudonyme public uniquement; ne contient jamais profiles.display_name privé.';
