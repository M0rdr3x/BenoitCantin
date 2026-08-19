-- SINJIRA™ V24.4.73 — avis internes lors d'une réponse à une publication sociale.
-- Aucun courriel, SMS, push ou service externe. Respecte notification_preferences.community_activity.

create or replace function private.notify_social_comment_reply()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_owner_user_id uuid;
  v_type text;
  v_title text;
  v_body text;
  v_path text;
  v_pref_enabled boolean;
begin
  if tg_table_name = 'social_real_comments' then
    select p.user_id
      into v_owner_user_id
      from public.social_real_posts p
     where p.id = new.post_id;
    v_type := 'social_real_reply';
    v_title := 'Nouvelle réponse dans la Communauté';
    v_body := 'Un membre a commenté votre publication.';
    v_path := '/compte/communaute.html?post=' || new.post_id::text;
  elsif tg_table_name = 'social_character_comments' then
    select p.user_id
      into v_owner_user_id
      from public.social_character_posts p
     where p.id = new.post_id;
    v_type := 'social_character_reply';
    v_title := 'Nouvelle réponse en rôle-play';
    v_body := 'Un personnage a commenté une publication de votre personnage.';
    v_path := '/compte/reseau-personnage.html?post=' || new.post_id::text;
  else
    return new;
  end if;

  if v_owner_user_id is null or v_owner_user_id = new.user_id then
    return new;
  end if;

  select coalesce(np.community_activity, true)
    into v_pref_enabled
    from public.notification_preferences np
   where np.user_id = v_owner_user_id;
  if not found then
    v_pref_enabled := true;
  end if;
  if v_pref_enabled is not true then
    return new;
  end if;

  insert into public.user_notifications (
    user_id, notification_type, title, body,
    related_entity_type, related_entity_id, action_path
  ) values (
    v_owner_user_id, v_type, v_title, v_body,
    tg_table_name, new.id, v_path
  );

  return new;
end;
$$;

revoke all on function private.notify_social_comment_reply() from public, anon, authenticated;
grant execute on function private.notify_social_comment_reply() to service_role;

drop trigger if exists trg_user_notify_social_real_reply on public.social_real_comments;
create trigger trg_user_notify_social_real_reply
after insert on public.social_real_comments
for each row
execute function private.notify_social_comment_reply();

drop trigger if exists trg_user_notify_social_character_reply on public.social_character_comments;
create trigger trg_user_notify_social_character_reply
after insert on public.social_character_comments
for each row
execute function private.notify_social_comment_reply();
