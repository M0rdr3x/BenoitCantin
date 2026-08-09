-- Exécuter APRÈS avoir créé et confirmé votre propre Compte SINJIRA.
-- Remplacez l'adresse ci-dessous par votre courriel de compte administrateur.

insert into public.internal_admin_users(user_id)
select id from auth.users where email = 'VOTRE_COURRIEL_ADMIN'
on conflict (user_id) do nothing;

select u.email,a.created_at
from public.internal_admin_users a
join auth.users u on u.id=a.user_id;
