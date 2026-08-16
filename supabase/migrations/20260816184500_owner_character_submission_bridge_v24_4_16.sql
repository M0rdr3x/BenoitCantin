begin;

-- V24.4.16 — pont de reprise du dossier historique du propriétaire.
-- Le personnage AbyssTime existait déjà dans public.characters, tandis que son
-- questionnaire historique vivait encore dans l'ancienne table V23/V24.
-- Cette migration rattache le dossier source au modèle canonique sans créer de
-- second personnage et crée une notification administrateur traçable.

with legacy as (
  select a.user_id,
         coalesce(a.account_pseudo_snapshot,'AbyssTime') as account_pseudo,
         coalesce(a.account_email_snapshot,'kingtyrano@gmail.com') as account_email,
         a.answers as source_payload,
         a.photo_path,
         coalesce(a.submitted_at,a.created_at,now()) as created_at
  from public.sinjira_character_applications a
  where a.user_id='185fcbe4-1da7-4222-a1da-f50aa209c1d1'::uuid
  order by a.submitted_at desc nulls last, a.created_at desc
  limit 1
), inserted as (
  insert into public.character_submissions(user_id,account_pseudo,account_email,status,source_payload,photo_path,created_at,updated_at)
  select l.user_id,l.account_pseudo,l.account_email,'assigned',l.source_payload,l.photo_path,l.created_at,now()
  from legacy l
  where not exists (
    select 1 from public.character_submissions cs where cs.user_id=l.user_id
  )
  returning id,user_id
), chosen as (
  select id,user_id from inserted
  union all
  select cs.id,cs.user_id
  from public.character_submissions cs
  where cs.user_id='185fcbe4-1da7-4222-a1da-f50aa209c1d1'::uuid
  order by id
  limit 1
)
update public.characters c
set submission_id=chosen.id,
    updated_at=now()
from chosen
where c.user_id=chosen.user_id
  and c.submission_id is null;

insert into public.admin_notifications(notification_type,title,body,related_user_id,related_entity_type,related_entity_id)
select 'character_submission',
       'Dossier AbyssTime synchronisé',
       'Le questionnaire historique d’AbyssTime a été rattaché au dossier canonique V24 et au personnage existant.',
       cs.user_id,
       'character_submission',
       cs.id
from public.character_submissions cs
where cs.user_id='185fcbe4-1da7-4222-a1da-f50aa209c1d1'::uuid
  and not exists (
    select 1 from public.admin_notifications n
    where n.related_entity_type='character_submission'
      and n.related_entity_id=cs.id
      and n.notification_type='character_submission'
  )
order by cs.created_at desc
limit 1;

commit;
