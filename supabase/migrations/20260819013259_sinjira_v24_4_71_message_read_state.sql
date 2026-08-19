-- SINJIRA™ V24.4.71 — état lu/non-lu des messageries internes.
-- Gratuit: aucune notification externe, aucun courriel/SMS/push.

revoke update on table public.social_real_messages from authenticated;
revoke update on table public.social_character_messages from authenticated;

grant update (read_at) on table public.social_real_messages to authenticated;
grant update (read_at) on table public.social_character_messages to authenticated;

drop policy if exists real_messages_mark_read on public.social_real_messages;
create policy real_messages_mark_read
on public.social_real_messages
for update
to authenticated
using ((select auth.uid()) = recipient_user_id)
with check ((select auth.uid()) = recipient_user_id and read_at is not null);

drop policy if exists char_messages_mark_read on public.social_character_messages;
create policy char_messages_mark_read
on public.social_character_messages
for update
to authenticated
using ((select auth.uid()) = recipient_user_id)
with check ((select auth.uid()) = recipient_user_id and read_at is not null);

create index if not exists social_real_messages_unread_recipient_idx
on public.social_real_messages(recipient_user_id, created_at desc)
where read_at is null;

create index if not exists social_character_messages_unread_recipient_idx
on public.social_character_messages(recipient_user_id, created_at desc)
where read_at is null;
