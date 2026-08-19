-- SINJIRA™ V24.4.72 — gestion self-only du contenu social.
-- Gratuit: aucune API externe ni service payant.

revoke all on table public.social_real_posts from public, anon, authenticated;
revoke all on table public.social_real_comments from public, anon, authenticated;
revoke all on table public.social_character_posts from public, anon, authenticated;
revoke all on table public.social_character_comments from public, anon, authenticated;

grant select on table public.social_real_posts to authenticated;
grant select on table public.social_real_comments to authenticated;
grant select on table public.social_character_posts to authenticated;
grant select on table public.social_character_comments to authenticated;

grant insert (user_id, body) on table public.social_real_posts to authenticated;
grant insert (post_id, user_id, body) on table public.social_real_comments to authenticated;
grant insert (user_id, character_id, body) on table public.social_character_posts to authenticated;
grant insert (post_id, user_id, character_id, body) on table public.social_character_comments to authenticated;

grant update (body) on table public.social_real_posts to authenticated;
grant update (body) on table public.social_real_comments to authenticated;
grant update (body) on table public.social_character_posts to authenticated;
grant update (body) on table public.social_character_comments to authenticated;

grant delete on table public.social_real_posts to authenticated;
grant delete on table public.social_real_comments to authenticated;
grant delete on table public.social_character_posts to authenticated;
grant delete on table public.social_character_comments to authenticated;

drop policy if exists real_posts_update on public.social_real_posts;
create policy real_posts_update
on public.social_real_posts
for update
to authenticated
using ((select auth.uid()) = user_id)
with check (
  (select auth.uid()) = user_id
  and sinjira_my_age_band() in ('youth','adult')
  and has_accepted_community_rules((select auth.uid()))
  and not social_is_suspended((select auth.uid()))
);

drop policy if exists real_comments_update on public.social_real_comments;
create policy real_comments_update
on public.social_real_comments
for update
to authenticated
using ((select auth.uid()) = user_id)
with check (
  (select auth.uid()) = user_id
  and has_accepted_community_rules((select auth.uid()))
  and not social_is_suspended((select auth.uid()))
  and exists (
    select 1
    from public.social_real_posts p
    where p.id = social_real_comments.post_id
      and sinjira_can_social_interact((select auth.uid()), p.user_id)
  )
);

drop policy if exists char_posts_update on public.social_character_posts;
create policy char_posts_update
on public.social_character_posts
for update
to authenticated
using ((select auth.uid()) = user_id)
with check (
  (select auth.uid()) = user_id
  and sinjira_my_age_band() in ('youth','adult')
  and has_accepted_community_rules((select auth.uid()))
  and not social_is_suspended((select auth.uid()))
  and exists (
    select 1
    from public.character_social_profiles c
    where c.character_id = social_character_posts.character_id
      and c.user_id = (select auth.uid())
      and lower(coalesce(c.status,'')) <> 'archived'
  )
);

drop policy if exists char_comments_update on public.social_character_comments;
create policy char_comments_update
on public.social_character_comments
for update
to authenticated
using ((select auth.uid()) = user_id)
with check (
  (select auth.uid()) = user_id
  and has_accepted_community_rules((select auth.uid()))
  and not social_is_suspended((select auth.uid()))
  and exists (
    select 1
    from public.character_social_profiles c
    where c.character_id = social_character_comments.character_id
      and c.user_id = (select auth.uid())
      and lower(coalesce(c.status,'')) <> 'archived'
  )
  and exists (
    select 1
    from public.social_character_posts p
    where p.id = social_character_comments.post_id
      and sinjira_can_social_interact((select auth.uid()), p.user_id)
  )
);
