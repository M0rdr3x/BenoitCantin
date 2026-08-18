create table if not exists public.user_notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  notification_type text not null check (char_length(notification_type) between 1 and 64),
  title text not null check (char_length(title) between 1 and 160),
  body text not null default '' check (char_length(body) <= 1000),
  related_entity_type text check (related_entity_type is null or char_length(related_entity_type) <= 64),
  related_entity_id uuid,
  action_path text check (action_path is null or (action_path like '/%' and char_length(action_path) <= 300)),
  read_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.user_notifications enable row level security;

revoke all on table public.user_notifications from public, anon, authenticated;
grant select on table public.user_notifications to authenticated;
grant update (read_at) on table public.user_notifications to authenticated;
grant select, insert, update, delete on table public.user_notifications to service_role;

drop policy if exists user_notifications_read_own on public.user_notifications;
create policy user_notifications_read_own
on public.user_notifications
for select
to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists user_notifications_mark_own_read on public.user_notifications;
create policy user_notifications_mark_own_read
on public.user_notifications
for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create index if not exists user_notifications_user_created_idx
  on public.user_notifications (user_id, created_at desc);
create index if not exists user_notifications_user_unread_idx
  on public.user_notifications (user_id, created_at desc)
  where read_at is null;

create or replace function private.notify_user_status_change()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_user_id uuid;
  v_entity_id uuid;
  v_status text;
  v_type text;
  v_title text;
  v_body text;
  v_path text;
  v_status_label text;
begin
  if tg_op = 'UPDATE' and old.status is not distinct from new.status then
    return new;
  end if;

  v_user_id := nullif(to_jsonb(new)->>'user_id','')::uuid;
  v_entity_id := coalesce(
    nullif(to_jsonb(new)->>'id','')::uuid,
    nullif(to_jsonb(new)->>'playtest_id','')::uuid
  );
  v_status := coalesce(to_jsonb(new)->>'status','');

  if v_user_id is null or v_status = '' then
    return new;
  end if;

  if tg_table_name = 'access_requests' then
    v_type := 'access_request';
    v_title := 'Demande d’accès mise à jour';
    v_path := '/compte/bibliotheque.html';
    v_status_label := case v_status
      when 'approved' then 'approuvée'
      when 'refused' then 'refusée'
      when 'cancelled' then 'annulée'
      else 'en attente'
    end;
    v_body := 'Votre demande d’accès est maintenant ' || v_status_label || '.';

  elsif tg_table_name = 'novel_comments' then
    v_type := 'novel_comment';
    v_title := 'Commentaire de roman mis à jour';
    v_path := '/compte/mes-commentaires.html';
    v_status_label := case v_status
      when 'approved' then 'approuvé et publié'
      when 'refused' then 'refusé'
      when 'removed' then 'retiré'
      else 'en attente de modération'
    end;
    v_body := 'Le statut de votre commentaire est maintenant : ' || v_status_label || '.';

  elsif tg_table_name = 'character_submissions' then
    v_type := 'character_submission';
    v_title := 'Dossier du Registre mis à jour';
    v_path := '/compte/mon-personnage.html';
    v_status_label := case v_status
      when 'ai_draft' then 'brouillon en préparation'
      when 'author_review' then 'en révision'
      when 'approved' then 'approuvé'
      when 'assigned' then 'attribué à un roman'
      when 'future' then 'prévu pour un futur roman'
      when 'published' then 'publié'
      when 'refused' then 'à revoir'
      when 'archived' then 'archivé'
      else 'reçu'
    end;
    v_body := 'Votre dossier du Registre est maintenant : ' || v_status_label || '.';

  elsif tg_table_name = 'characters' then
    if coalesce((to_jsonb(new)->>'visible_to_user')::boolean, false) is not true then
      return new;
    end if;
    v_type := 'character';
    v_title := 'Votre personnage SINJIRA™ a évolué';
    v_path := '/compte/mon-personnage.html';
    v_status_label := case v_status
      when 'ai_draft' then 'en préparation'
      when 'author_review' then 'en révision'
      when 'approved' then 'approuvé'
      when 'assigned' then 'attribué à un roman'
      when 'future' then 'prévu pour un futur roman'
      when 'published' then 'publié'
      when 'archived' then 'archivé'
      else v_status
    end;
    v_body := 'Le statut visible de votre personnage est maintenant : ' || v_status_label || '.';

  elsif tg_table_name = 'playtest_participants' then
    if tg_op = 'INSERT' and v_status = 'applied' then
      return new;
    end if;
    v_type := 'playtest';
    v_title := 'Playtest mis à jour';
    v_path := '/compte/playtests.html';
    v_status_label := case v_status
      when 'invited' then 'invité'
      when 'applied' then 'demande reçue'
      when 'approved' then 'participation approuvée'
      when 'refused' then 'participation refusée'
      when 'completed' then 'terminé'
      when 'withdrawn' then 'retiré'
      else v_status
    end;
    v_body := 'Votre statut de playtest est maintenant : ' || v_status_label || '.';
  else
    return new;
  end if;

  insert into public.user_notifications (
    user_id, notification_type, title, body,
    related_entity_type, related_entity_id, action_path
  ) values (
    v_user_id, v_type, v_title, v_body,
    tg_table_name, v_entity_id, v_path
  );

  return new;
end;
$$;

revoke all on function private.notify_user_status_change() from public, anon, authenticated;
grant execute on function private.notify_user_status_change() to service_role;

drop trigger if exists trg_user_notify_access_request_status on public.access_requests;
create trigger trg_user_notify_access_request_status
after update of status on public.access_requests
for each row
when (old.status is distinct from new.status)
execute function private.notify_user_status_change();

drop trigger if exists trg_user_notify_novel_comment_status on public.novel_comments;
create trigger trg_user_notify_novel_comment_status
after update of status on public.novel_comments
for each row
when (old.status is distinct from new.status)
execute function private.notify_user_status_change();

drop trigger if exists trg_user_notify_character_submission_status on public.character_submissions;
create trigger trg_user_notify_character_submission_status
after update of status on public.character_submissions
for each row
when (old.status is distinct from new.status)
execute function private.notify_user_status_change();

drop trigger if exists trg_user_notify_character_status on public.characters;
create trigger trg_user_notify_character_status
after insert or update of status on public.characters
for each row
execute function private.notify_user_status_change();

drop trigger if exists trg_user_notify_playtest_status on public.playtest_participants;
create trigger trg_user_notify_playtest_status
after insert or update of status on public.playtest_participants
for each row
execute function private.notify_user_status_change();
