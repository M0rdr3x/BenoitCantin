-- SINJIRA™ V25 — minimisation du secret d'autorisation parentale.
-- guardian_code est une capacité à usage unique : après consommation réussie par
-- handle_new_sinjira_user(), il ne doit pas rester dans auth.users.raw_user_meta_data.
--
-- Les triggers AFTER INSERT de même type sont exécutés par ordre alphabétique.
-- Le préfixe zz_ garantit que ce nettoyage s'exécute après on_auth_user_created_sinjira.

create or replace function private.sinjira_strip_guardian_signup_secret()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,auth
as $$
begin
  if coalesce(new.raw_user_meta_data,'{}'::jsonb) ? 'guardian_code' then
    update auth.users
    set raw_user_meta_data=coalesce(raw_user_meta_data,'{}'::jsonb)-'guardian_code'
    where id=new.id;
  end if;
  return new;
end;
$$;

revoke all on function private.sinjira_strip_guardian_signup_secret()
from public,anon,authenticated;

drop trigger if exists zz_sinjira_strip_guardian_signup_secret on auth.users;

create trigger zz_sinjira_strip_guardian_signup_secret
after insert on auth.users
for each row
when (coalesce(new.raw_user_meta_data,'{}'::jsonb) ? 'guardian_code')
execute function private.sinjira_strip_guardian_signup_secret();

comment on function private.sinjira_strip_guardian_signup_secret() is
  'V25: supprime guardian_code des métadonnées Auth après consommation réussie; aucune conservation du secret à usage unique.';
