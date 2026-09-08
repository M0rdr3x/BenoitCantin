-- SINJIRA V25 — durcissement d'éligibilité Realtime « En direct ».
-- Une adhésion persistée ne suffit jamais à conserver l'accès au canal.
-- Les règles, la suspension et la cohorte courante restent autoritaires.

-- Lecture Broadcast + Presence.
drop policy if exists sinjira_live_realtime_read on realtime.messages;
create policy sinjira_live_realtime_read
on realtime.messages
for select to authenticated
using (
  realtime.messages.extension in ('broadcast','presence')
  and public.has_accepted_community_rules((select auth.uid()))
  and not public.social_is_suspended((select auth.uid()))
  and exists(
    select 1
    from public.social_live_room_members m
    join public.social_live_rooms r on r.id=m.room_id
    where m.user_id=(select auth.uid())
      and not r.is_archived
      and r.audience=public.sinjira_my_age_band()
      and (r.owner_user_id=(select auth.uid()) or not public.social_is_blocked((select auth.uid()),r.owner_user_id))
      and ('sinjira-live:'||m.room_id::text)=(select realtime.topic())
  )
);

-- Garde restrictive : aucune politique permissive future ne peut contourner
-- les règles SINJIRA sur le namespace réservé sinjira-live:*.
drop policy if exists sinjira_live_realtime_read_guard on realtime.messages;
create policy sinjira_live_realtime_read_guard
on realtime.messages as restrictive
for select to authenticated
using (
  (select realtime.topic()) not like 'sinjira-live:%'
  or (
    realtime.messages.extension in ('broadcast','presence')
    and public.has_accepted_community_rules((select auth.uid()))
    and not public.social_is_suspended((select auth.uid()))
    and exists(
      select 1
      from public.social_live_room_members m
      join public.social_live_rooms r on r.id=m.room_id
      where m.user_id=(select auth.uid())
        and not r.is_archived
        and r.audience=public.sinjira_my_age_band()
        and (r.owner_user_id=(select auth.uid()) or not public.social_is_blocked((select auth.uid()),r.owner_user_id))
        and ('sinjira-live:'||m.room_id::text)=(select realtime.topic())
    )
  )
);

-- Le client ne peut publier que Presence; les messages de chat sont Broadcast
-- exclusivement par le trigger serveur de la migration de fondation.
drop policy if exists sinjira_live_realtime_presence_write on realtime.messages;
create policy sinjira_live_realtime_presence_write
on realtime.messages
for insert to authenticated
with check (
  realtime.messages.extension='presence'
  and public.has_accepted_community_rules((select auth.uid()))
  and not public.social_is_suspended((select auth.uid()))
  and exists(
    select 1
    from public.social_live_room_members m
    join public.social_live_rooms r on r.id=m.room_id
    where m.user_id=(select auth.uid())
      and not r.is_archived
      and r.audience=public.sinjira_my_age_band()
      and (r.owner_user_id=(select auth.uid()) or not public.social_is_blocked((select auth.uid()),r.owner_user_id))
      and ('sinjira-live:'||m.room_id::text)=(select realtime.topic())
  )
);

drop policy if exists sinjira_live_realtime_write_guard on realtime.messages;
create policy sinjira_live_realtime_write_guard
on realtime.messages as restrictive
for insert to authenticated
with check (
  (select realtime.topic()) not like 'sinjira-live:%'
  or (
    realtime.messages.extension='presence'
    and public.has_accepted_community_rules((select auth.uid()))
    and not public.social_is_suspended((select auth.uid()))
    and exists(
      select 1
      from public.social_live_room_members m
      join public.social_live_rooms r on r.id=m.room_id
      where m.user_id=(select auth.uid())
        and not r.is_archived
        and r.audience=public.sinjira_my_age_band()
        and (r.owner_user_id=(select auth.uid()) or not public.social_is_blocked((select auth.uid()),r.owner_user_id))
        and ('sinjira-live:'||m.room_id::text)=(select realtime.topic())
    )
  )
);
