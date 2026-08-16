-- SINJIRA™ V24.4.11 — assainissement historique des signalements
-- Cette migration ne fait jamais confiance aux anciens snapshots pour déterminer une cible.

-- Les UUID de comptes ne sont pas nécessaires dans un snapshot lisible par le déclarant.
-- On les retire aussi des signalements historiques afin de respecter la séparation
-- identité de compte / identité narrative introduite par V24.4.11.
update public.social_reports
set snapshot=(coalesce(snapshot,'{}'::jsonb) - 'user_id' - 'sender_user_id' - 'recipient_user_id')
where snapshot ?| array['user_id','sender_user_id','recipient_user_id'];

-- Backfill de la cible privée uniquement à partir des tables autoritaires encore présentes.
insert into public.social_report_targets(report_id,target_user_id)
select r.id,p.user_id
from public.social_reports r
join public.social_real_posts p on p.id=r.target_id
where r.network='real' and r.target_type='post'
on conflict(report_id) do update set target_user_id=excluded.target_user_id;

insert into public.social_report_targets(report_id,target_user_id)
select r.id,c.user_id
from public.social_reports r
join public.social_real_comments c on c.id=r.target_id
where r.network='real' and r.target_type='comment'
on conflict(report_id) do update set target_user_id=excluded.target_user_id;

insert into public.social_report_targets(report_id,target_user_id)
select r.id,m.sender_user_id
from public.social_reports r
join public.social_real_messages m on m.id=r.target_id
where r.network='real' and r.target_type='message'
on conflict(report_id) do update set target_user_id=excluded.target_user_id;

insert into public.social_report_targets(report_id,target_user_id)
select r.id,p.user_id
from public.social_reports r
join public.social_profiles p on p.user_id=r.target_id
where r.network='real' and r.target_type='profile'
on conflict(report_id) do update set target_user_id=excluded.target_user_id;

insert into public.social_report_targets(report_id,target_user_id)
select r.id,p.user_id
from public.social_reports r
join public.social_character_posts p on p.id=r.target_id
where r.network='character' and r.target_type='post'
on conflict(report_id) do update set target_user_id=excluded.target_user_id;

insert into public.social_report_targets(report_id,target_user_id)
select r.id,c.user_id
from public.social_reports r
join public.social_character_comments c on c.id=r.target_id
where r.network='character' and r.target_type='comment'
on conflict(report_id) do update set target_user_id=excluded.target_user_id;

insert into public.social_report_targets(report_id,target_user_id)
select r.id,m.sender_user_id
from public.social_reports r
join public.social_character_messages m on m.id=r.target_id
where r.network='character' and r.target_type='message'
on conflict(report_id) do update set target_user_id=excluded.target_user_id;

insert into public.social_report_targets(report_id,target_user_id)
select r.id,p.user_id
from public.social_reports r
join public.character_social_profiles p on p.character_id=r.target_id
where r.network='character' and r.target_type='profile'
on conflict(report_id) do update set target_user_id=excluded.target_user_id;
