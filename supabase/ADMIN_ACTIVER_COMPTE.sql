-- SINJIRA — administrateur propriétaire unique
-- Le compte administrateur officiel est verrouillé sur :
-- kingtyrano@gmail.com / AbyssTime
--
-- Tout autre compte est refusé par le trigger de sécurité installé en V13.

insert into public.internal_admin_users(user_id)
select id
from auth.users
where lower(email) = lower('kingtyrano@gmail.com')
on conflict (user_id) do nothing;

select u.email, p.pseudo, a.created_at
from public.internal_admin_users a
join auth.users u on u.id = a.user_id
left join public.profiles p on p.user_id = u.id;
