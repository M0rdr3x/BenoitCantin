-- SINJIRA™ V24.4.12 — confidentialité RPC + optimisation RLS des parcours actifs
-- Évite l'énumération d'UUID arbitraires et réduit les appels auth.uid() réévalués ligne par ligne.

-- ---------------------------------------------------------------------------
-- COHORTE : seul l'état du compte courant est exposé au navigateur.
-- ---------------------------------------------------------------------------
create or replace function public.sinjira_my_age_band()
returns text
language sql
stable
security definer
set search_path=public,auth
as $$ select public.sinjira_age_band(auth.uid()); $$;
revoke all on function public.sinjira_my_age_band() from public,anon;
grant execute on function public.sinjira_my_age_band() to anon,authenticated;

revoke execute on function public.sinjira_age_band(uuid) from authenticated;
grant execute on function public.sinjira_age_band(uuid) to service_role;

-- ---------------------------------------------------------------------------
-- HELPERS : un membre ne peut tester que lui-même ou une relation qui l'implique.
-- ---------------------------------------------------------------------------
create or replace function public.is_sinjira_admin(p_user_id uuid default auth.uid())
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when p_user_id is null then false
    when coalesce(auth.jwt()->>'role','')='service_role' or auth.uid() is null or p_user_id=auth.uid() then
      exists(
        select 1 from public.internal_admin_users a
        join auth.users u on u.id=a.user_id
        where a.user_id=p_user_id and lower(coalesce(u.email,''))='kingtyrano@gmail.com'
      )
    else false
  end;
$$;
revoke all on function public.is_sinjira_admin(uuid) from public,anon;
grant execute on function public.is_sinjira_admin(uuid) to authenticated,service_role;

create or replace function public.social_is_suspended(p_user_id uuid default auth.uid())
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when p_user_id is null then false
    when coalesce(auth.jwt()->>'role','')='service_role' or auth.uid() is null or p_user_id=auth.uid() then
      exists(select 1 from public.social_suspensions s where s.user_id=p_user_id and (s.until_at is null or s.until_at>now()))
    else false
  end;
$$;
revoke all on function public.social_is_suspended(uuid) from public,anon;
grant execute on function public.social_is_suspended(uuid) to authenticated,service_role;

create or replace function public.social_is_blocked(a uuid,b uuid)
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when a is null or b is null then false
    when coalesce(auth.jwt()->>'role','')<>'service_role' and auth.uid() is not null and auth.uid()<>a and auth.uid()<>b then false
    else exists(
      select 1 from public.social_blocks x
      where (x.blocker_user_id=a and x.blocked_user_id=b) or (x.blocker_user_id=b and x.blocked_user_id=a)
    )
  end;
$$;
revoke all on function public.social_is_blocked(uuid,uuid) from public,anon;
grant execute on function public.social_is_blocked(uuid,uuid) to authenticated,service_role;

create or replace function public.sinjira_can_social_interact(p_a uuid,p_b uuid)
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when p_a is null or p_b is null then false
    when coalesce(auth.jwt()->>'role','')<>'service_role' and auth.uid() is not null and auth.uid()<>p_a and auth.uid()<>p_b then false
    when p_a=p_b then public.sinjira_age_band(p_a) in ('adult','youth')
    when public.sinjira_age_band(p_a)='adult' and public.sinjira_age_band(p_b)='adult' then true
    when public.sinjira_age_band(p_a)='youth' and public.sinjira_age_band(p_b)='youth' then true
    else false
  end;
$$;
revoke all on function public.sinjira_can_social_interact(uuid,uuid) from public,anon;
grant execute on function public.sinjira_can_social_interact(uuid,uuid) to authenticated,service_role;

-- ---------------------------------------------------------------------------
-- PROFIL / COMPTE / PERSONNAGE / LICENCES
-- ---------------------------------------------------------------------------
drop policy if exists admin_read_all_profiles on public.profiles;
drop policy if exists profile_select_own on public.profiles;
create policy profile_read_own_or_admin on public.profiles
for select to authenticated
using ((select auth.uid())=user_id or public.is_sinjira_admin((select auth.uid())));

drop policy if exists profile_update_own on public.profiles;
create policy profile_update_own on public.profiles
for update to authenticated
using ((select auth.uid())=user_id)
with check ((select auth.uid())=user_id);

revoke all on public.profiles from anon;
revoke insert,delete,truncate,references,trigger,update on public.profiles from authenticated;
grant select on public.profiles to authenticated;
grant update(pseudo,display_name,avatar_path) on public.profiles to authenticated;

drop policy if exists safety_own_read on public.account_safety_profiles;
create policy safety_own_read on public.account_safety_profiles
for select to authenticated using ((select auth.uid())=user_id);

drop policy if exists submissions_own_read on public.character_submissions;
create policy submissions_own_read on public.character_submissions
for select to authenticated using ((select auth.uid())=user_id);

drop policy if exists characters_own_read on public.characters;
create policy characters_own_read on public.characters
for select to authenticated using ((select auth.uid())=user_id and visible_to_user=true);

drop policy if exists entitlements_own_read on public.user_entitlements;
create policy entitlements_own_read on public.user_entitlements
for select to authenticated using ((select auth.uid())=user_id);

-- ---------------------------------------------------------------------------
-- ADMIN : même capacité, sans recalcul auth.uid() pour chaque ligne.
-- ---------------------------------------------------------------------------
drop policy if exists admin_notifications_owner_read on public.admin_notifications;
create policy admin_notifications_owner_read on public.admin_notifications
for select to authenticated
using (
  public.is_sinjira_owner((select auth.uid()))
  or exists(select 1 from public.internal_admin_users a where a.user_id=(select auth.uid()))
);

drop policy if exists admin_notifications_owner_update on public.admin_notifications;
create policy admin_notifications_owner_update on public.admin_notifications
for update to authenticated
using (
  public.is_sinjira_owner((select auth.uid()))
  or exists(select 1 from public.internal_admin_users a where a.user_id=(select auth.uid()))
)
with check (
  public.is_sinjira_owner((select auth.uid()))
  or exists(select 1 from public.internal_admin_users a where a.user_id=(select auth.uid()))
);

-- ---------------------------------------------------------------------------
-- FRACTURE : fusion des politiques SELECT admin + membre.
-- ---------------------------------------------------------------------------
drop policy if exists admin_read_all_fracture_parties on public.fracture_parties;
drop policy if exists "fracture parties members read" on public.fracture_parties;
create policy fracture_parties_read_authorized on public.fracture_parties
for select to authenticated
using (
  public.is_sinjira_admin((select auth.uid()))
  or owner_user_id=(select auth.uid())
  or public.is_fracture_party_member(id,(select auth.uid()))
);

drop policy if exists admin_read_all_fracture_members on public.fracture_party_members;
drop policy if exists "fracture members party read" on public.fracture_party_members;
create policy fracture_members_read_authorized on public.fracture_party_members
for select to authenticated
using (
  public.is_sinjira_admin((select auth.uid()))
  or user_id=(select auth.uid())
  or public.is_fracture_party_member(party_id,(select auth.uid()))
);

-- ---------------------------------------------------------------------------
-- PROFILS SOCIAUX
-- ---------------------------------------------------------------------------
drop policy if exists social_profiles_read on public.social_profiles;
create policy social_profiles_read on public.social_profiles
for select to authenticated
using (
  (select auth.uid())=user_id
  or (public.sinjira_can_social_interact((select auth.uid()),user_id) and not public.social_is_blocked((select auth.uid()),user_id))
);

drop policy if exists character_social_profiles_read on public.character_social_profiles;
create policy character_social_profiles_read on public.character_social_profiles
for select to authenticated
using (
  (select auth.uid())=user_id
  or (public.sinjira_can_social_interact((select auth.uid()),user_id) and not public.social_is_blocked((select auth.uid()),user_id))
);

-- ---------------------------------------------------------------------------
-- RÉSEAU RÉEL
-- ---------------------------------------------------------------------------
drop policy if exists real_posts_read on public.social_real_posts;
create policy real_posts_read on public.social_real_posts for select to authenticated
using (public.sinjira_can_social_interact((select auth.uid()),user_id) and not public.social_is_blocked((select auth.uid()),user_id));
drop policy if exists real_posts_insert on public.social_real_posts;
create policy real_posts_insert on public.social_real_posts for insert to authenticated
with check ((select auth.uid())=user_id and public.sinjira_my_age_band() in ('youth','adult') and public.has_accepted_community_rules((select auth.uid())) and not public.social_is_suspended((select auth.uid())));
drop policy if exists real_posts_update on public.social_real_posts;
create policy real_posts_update on public.social_real_posts for update to authenticated using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
drop policy if exists real_posts_delete on public.social_real_posts;
create policy real_posts_delete on public.social_real_posts for delete to authenticated using ((select auth.uid())=user_id);

drop policy if exists real_comments_read on public.social_real_comments;
create policy real_comments_read on public.social_real_comments for select to authenticated
using (public.sinjira_can_social_interact((select auth.uid()),user_id) and not public.social_is_blocked((select auth.uid()),user_id) and exists(select 1 from public.social_real_posts p where p.id=social_real_comments.post_id and public.sinjira_can_social_interact((select auth.uid()),p.user_id)));
drop policy if exists real_comments_insert on public.social_real_comments;
create policy real_comments_insert on public.social_real_comments for insert to authenticated
with check ((select auth.uid())=user_id and public.has_accepted_community_rules((select auth.uid())) and not public.social_is_suspended((select auth.uid())) and exists(select 1 from public.social_real_posts p where p.id=social_real_comments.post_id and public.sinjira_can_social_interact((select auth.uid()),p.user_id)));
drop policy if exists real_comments_update on public.social_real_comments;
create policy real_comments_update on public.social_real_comments for update to authenticated using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
drop policy if exists real_comments_delete on public.social_real_comments;
create policy real_comments_delete on public.social_real_comments for delete to authenticated using ((select auth.uid())=user_id);

drop policy if exists real_likes_read on public.social_real_likes;
create policy real_likes_read on public.social_real_likes for select to authenticated
using (public.sinjira_can_social_interact((select auth.uid()),user_id) and exists(select 1 from public.social_real_posts p where p.id=social_real_likes.post_id and public.sinjira_can_social_interact((select auth.uid()),p.user_id)));
drop policy if exists real_likes_own on public.social_real_likes;
create policy real_likes_own on public.social_real_likes for insert to authenticated
with check ((select auth.uid())=user_id and public.has_accepted_community_rules((select auth.uid())) and not public.social_is_suspended((select auth.uid())) and exists(select 1 from public.social_real_posts p where p.id=social_real_likes.post_id and public.sinjira_can_social_interact((select auth.uid()),p.user_id)));
drop policy if exists real_likes_delete on public.social_real_likes;
create policy real_likes_delete on public.social_real_likes for delete to authenticated using ((select auth.uid())=user_id);

drop policy if exists real_messages_read on public.social_real_messages;
create policy real_messages_read on public.social_real_messages for select to authenticated
using (((select auth.uid())=sender_user_id or (select auth.uid())=recipient_user_id) and public.sinjira_can_social_interact(sender_user_id,recipient_user_id));
drop policy if exists real_messages_insert on public.social_real_messages;
create policy real_messages_insert on public.social_real_messages for insert to authenticated
with check ((select auth.uid())=sender_user_id and public.sinjira_can_social_interact(sender_user_id,recipient_user_id) and public.has_accepted_community_rules((select auth.uid())) and not public.social_is_suspended((select auth.uid())) and not public.social_is_blocked(sender_user_id,recipient_user_id));

-- ---------------------------------------------------------------------------
-- RÉSEAU PERSONNAGE : publication active + messages liés aux profils exacts non archivés.
-- ---------------------------------------------------------------------------
drop policy if exists char_posts_insert on public.social_character_posts;
create policy char_posts_insert on public.social_character_posts for insert to authenticated
with check (
  (select auth.uid())=user_id
  and public.sinjira_my_age_band() in ('youth','adult')
  and public.has_accepted_community_rules((select auth.uid()))
  and not public.social_is_suspended((select auth.uid()))
  and exists(select 1 from public.character_social_profiles c where c.character_id=social_character_posts.character_id and c.user_id=(select auth.uid()) and lower(coalesce(c.status,''))<>'archived')
);

drop policy if exists char_messages_read on public.social_character_messages;
create policy char_messages_read on public.social_character_messages for select to authenticated
using (((select auth.uid())=sender_user_id or (select auth.uid())=recipient_user_id) and public.sinjira_can_social_interact(sender_user_id,recipient_user_id));
drop policy if exists char_messages_insert on public.social_character_messages;
create policy char_messages_insert on public.social_character_messages for insert to authenticated
with check (
  (select auth.uid())=sender_user_id
  and public.sinjira_can_social_interact(sender_user_id,recipient_user_id)
  and public.has_accepted_community_rules((select auth.uid()))
  and not public.social_is_suspended((select auth.uid()))
  and not public.social_is_blocked(sender_user_id,recipient_user_id)
  and exists(select 1 from public.character_social_profiles c where c.character_id=social_character_messages.sender_character_id and c.user_id=(select auth.uid()) and lower(coalesce(c.status,''))<>'archived')
  and exists(select 1 from public.character_social_profiles c where c.character_id=social_character_messages.recipient_character_id and c.user_id=social_character_messages.recipient_user_id and lower(coalesce(c.status,''))<>'archived')
);

-- ---------------------------------------------------------------------------
-- MONDE PARALLÈLE : remplacer l'accès direct à age_band(uuid) par l'état du compte courant.
-- ---------------------------------------------------------------------------
drop policy if exists parallel_group_members_own_insert on public.parallel_group_members;
create policy parallel_group_members_own_insert on public.parallel_group_members
for insert to authenticated
with check (
  user_id=(select auth.uid())
  and public.sinjira_mfa_access_allowed((select auth.uid()))
  and exists(select 1 from public.parallel_groups g where g.id=parallel_group_members.group_id and g.audience=public.sinjira_my_age_band() and public.sinjira_can_social_interact(g.owner_user_id,(select auth.uid())))
);

drop policy if exists parallel_groups_owner_write on public.parallel_groups;
create policy parallel_groups_owner_write on public.parallel_groups
for all to authenticated
using (owner_user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())))
with check (owner_user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())) and audience=public.sinjira_my_age_band() and audience in ('adult','youth'));

drop policy if exists parallel_stories_public on public.parallel_story_installments;
create policy parallel_stories_public on public.parallel_story_installments
for select to anon,authenticated
using (
  published_at is not null and (
    (story_kind='collective' and audience='all')
    or (story_kind='collective' and (select auth.uid()) is not null and audience=public.sinjira_my_age_band())
    or (story_kind='individual' and (select auth.uid()) is not null and exists(select 1 from public.sinjira_characters c where c.id=parallel_story_installments.character_id and c.user_id=(select auth.uid())))
  )
);

drop policy if exists parallel_cycles_public_read on public.parallel_world_cycles;
create policy parallel_cycles_public_read on public.parallel_world_cycles
for select to anon,authenticated
using (
  (published_at is not null or status='open')
  and (audience='all' or ((select auth.uid()) is not null and audience=public.sinjira_my_age_band()))
);

-- ---------------------------------------------------------------------------
-- COMMENTAIRES ROMANS : grants minimaux. La RPC publique reste volontairement
-- SECURITY DEFINER car elle n'expose que les commentaires approuvés + pseudo/avatar.
-- ---------------------------------------------------------------------------
revoke insert,update,delete,truncate,references,trigger on public.sinjira_novels from anon,authenticated;
grant select on public.sinjira_novels to anon,authenticated;

revoke insert,update,delete,truncate,references,trigger on public.sinjira_novel_comments from anon;
grant select on public.sinjira_novel_comments to anon;
revoke truncate,references,trigger on public.sinjira_novel_comments from authenticated;
grant select,insert,update,delete on public.sinjira_novel_comments to authenticated;

create or replace function public.list_sinjira_novel_comments(p_novel_slug text)
returns table(id uuid,body text,spoiler boolean,created_at timestamptz,pseudo text,avatar_path text)
language sql
stable
security definer
set search_path=public,pg_temp
as $$
  select c.id,c.body,c.spoiler,c.created_at,
         coalesce(nullif(p.pseudo,''),nullif(p.display_name,''),'Lecteur SINJIRA') as pseudo,
         p.avatar_path
  from public.sinjira_novel_comments c
  join public.sinjira_novels n on n.id=c.novel_id
  left join public.profiles p on p.user_id=c.user_id
  where char_length(trim(coalesce(p_novel_slug,''))) between 1 and 120
    and n.slug=trim(p_novel_slug)
    and n.comments_enabled=true
    and c.status='approved'
  order by c.created_at desc
  limit 250;
$$;
revoke all on function public.list_sinjira_novel_comments(text) from public;
grant execute on function public.list_sinjira_novel_comments(text) to anon,authenticated,service_role;
comment on function public.list_sinjira_novel_comments(text) is
  'SECURITY DEFINER intentionnel : expose uniquement les commentaires approuvés et le pseudo/avatar public, sans ouvrir la table profiles aux visiteurs anonymes.';
