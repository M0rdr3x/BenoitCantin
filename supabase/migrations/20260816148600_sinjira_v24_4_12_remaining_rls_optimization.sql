-- SINJIRA™ V24.4.12 — élimination des WARN RLS restants.
-- Auth initialisé une seule fois et politiques SELECT redondantes consolidées.

-- Bibliothèque historique.
drop policy if exists reader_library_own on public.reader_library;
create policy reader_library_own on public.reader_library for all to authenticated
using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);

-- Commentaires romans historiques : public séparé de propriétaire.
drop policy if exists comments_read on public.novel_comments;
drop policy if exists comments_anon_read on public.novel_comments;
drop policy if exists comments_authenticated_read on public.novel_comments;
create policy comments_anon_read on public.novel_comments for select to anon
using (status='approved');
create policy comments_authenticated_read on public.novel_comments for select to authenticated
using (status='approved' or (select auth.uid())=user_id);
drop policy if exists comments_insert_own on public.novel_comments;
create policy comments_insert_own on public.novel_comments for insert to authenticated
with check ((select auth.uid())=user_id and status='pending');
drop policy if exists comments_delete_own_pending on public.novel_comments;
create policy comments_delete_own_pending on public.novel_comments for delete to authenticated
using ((select auth.uid())=user_id and status='pending');

-- Acceptation des règles communautaires.
drop policy if exists community_rules_own on public.community_rule_acceptances;
create policy community_rules_own on public.community_rule_acceptances for all to authenticated
using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);

-- Blocages et signalements.
drop policy if exists social_blocks_own on public.social_blocks;
create policy social_blocks_own on public.social_blocks for all to authenticated
using ((select auth.uid())=blocker_user_id) with check ((select auth.uid())=blocker_user_id);
drop policy if exists social_reports_own_insert on public.social_reports;
create policy social_reports_own_insert on public.social_reports for insert to authenticated
with check ((select auth.uid())=reporter_user_id and public.has_accepted_community_rules((select auth.uid())));
drop policy if exists social_reports_own_read on public.social_reports;
create policy social_reports_own_read on public.social_reports for select to authenticated
using ((select auth.uid())=reporter_user_id);

-- Commandes.
drop policy if exists orders_own_read on public.orders;
create policy orders_own_read on public.orders for select to authenticated
using ((select auth.uid())=user_id);
drop policy if exists order_items_own_read on public.order_items;
create policy order_items_own_read on public.order_items for select to authenticated
using (exists(select 1 from public.orders o where o.id=order_items.order_id and o.user_id=(select auth.uid())));

-- Bibliothèque SINJIRA actuelle.
drop policy if exists "sinjira reader library own" on public.sinjira_reader_library;
create policy "sinjira reader library own" on public.sinjira_reader_library for all to authenticated
using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);

-- Directives de legs.
drop policy if exists legacy_own on public.legacy_directives;
create policy legacy_own on public.legacy_directives for all to authenticated
using ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())))
with check ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())));

-- Mémorial.
drop policy if exists memorial_request_create on public.memorial_requests;
create policy memorial_request_create on public.memorial_requests for insert to authenticated
with check ((select auth.uid())=requested_by_user_id);
drop policy if exists memorial_request_parties on public.memorial_requests;
create policy memorial_request_parties on public.memorial_requests for select to authenticated
using ((select auth.uid())=subject_user_id or (select auth.uid())=requested_by_user_id);

-- Liens familiaux privés : lecture unique, écritures séparées pour éviter ALL+SELECT.
drop policy if exists family_owner_write on public.private_family_links;
drop policy if exists family_parties_read on public.private_family_links;
drop policy if exists family_owner_insert on public.private_family_links;
drop policy if exists family_owner_update on public.private_family_links;
drop policy if exists family_owner_delete on public.private_family_links;
create policy family_parties_read on public.private_family_links for select to authenticated
using (((select auth.uid())=owner_user_id or (select auth.uid())=related_user_id) and public.sinjira_mfa_access_allowed((select auth.uid())));
create policy family_owner_insert on public.private_family_links for insert to authenticated
with check ((select auth.uid())=owner_user_id and public.sinjira_mfa_access_allowed((select auth.uid())));
create policy family_owner_update on public.private_family_links for update to authenticated
using ((select auth.uid())=owner_user_id and public.sinjira_mfa_access_allowed((select auth.uid())))
with check ((select auth.uid())=owner_user_id and public.sinjira_mfa_access_allowed((select auth.uid())));
create policy family_owner_delete on public.private_family_links for delete to authenticated
using ((select auth.uid())=owner_user_id and public.sinjira_mfa_access_allowed((select auth.uid())));

-- Monde parallèle : adhésion / groupes / réponses / état.
drop policy if exists parallel_membership_own_read on public.parallel_world_memberships;
create policy parallel_membership_own_read on public.parallel_world_memberships for select to authenticated
using ((select auth.uid())=user_id);

drop policy if exists parallel_groups_member_read on public.parallel_groups;
drop policy if exists parallel_groups_owner_write on public.parallel_groups;
drop policy if exists parallel_groups_owner_insert on public.parallel_groups;
drop policy if exists parallel_groups_owner_update on public.parallel_groups;
drop policy if exists parallel_groups_owner_delete on public.parallel_groups;
create policy parallel_groups_member_read on public.parallel_groups for select to authenticated
using (
  owner_user_id=(select auth.uid())
  or exists(select 1 from public.parallel_group_members m where m.group_id=parallel_groups.id and m.user_id=(select auth.uid()))
);
create policy parallel_groups_owner_insert on public.parallel_groups for insert to authenticated
with check (
  owner_user_id=(select auth.uid())
  and public.sinjira_mfa_access_allowed((select auth.uid()))
  and audience=public.sinjira_my_age_band()
  and audience in ('adult','youth')
);
create policy parallel_groups_owner_update on public.parallel_groups for update to authenticated
using (owner_user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())))
with check (owner_user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())) and audience=public.sinjira_my_age_band() and audience in ('adult','youth'));
create policy parallel_groups_owner_delete on public.parallel_groups for delete to authenticated
using (owner_user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())));

drop policy if exists parallel_group_members_read on public.parallel_group_members;
create policy parallel_group_members_read on public.parallel_group_members for select to authenticated
using (
  user_id=(select auth.uid())
  or exists(select 1 from public.parallel_groups g where g.id=parallel_group_members.group_id and g.owner_user_id=(select auth.uid()))
);

drop policy if exists parallel_responses_own on public.parallel_cycle_responses;
create policy parallel_responses_own on public.parallel_cycle_responses for all to authenticated
using (user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())))
with check (
  user_id=(select auth.uid())
  and public.sinjira_mfa_access_allowed((select auth.uid()))
  and public.sinjira_cycle_allowed(cycle_id,(select auth.uid()))
  and public.sinjira_content_allowed((select auth.uid()),response_text)
);

drop policy if exists parallel_state_own on public.parallel_character_state;
create policy parallel_state_own on public.parallel_character_state for select to authenticated
using (user_id=(select auth.uid()));

drop policy if exists fictional_relationships_participants_read on public.fictional_relationships;
create policy fictional_relationships_participants_read on public.fictional_relationships for select to authenticated
using (exists(select 1 from public.sinjira_characters c where c.id=any(array[fictional_relationships.character_a_id,fictional_relationships.character_b_id]) and c.user_id=(select auth.uid())));

-- Invitations et événements familiaux.
drop policy if exists family_invites_own on public.family_link_invites;
create policy family_invites_own on public.family_link_invites for all to authenticated
using (owner_user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())))
with check (owner_user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())));

drop policy if exists family_events_owner_insert on public.family_relationship_events;
create policy family_events_owner_insert on public.family_relationship_events for insert to authenticated
with check (owner_user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())));
drop policy if exists family_events_owner_update on public.family_relationship_events;
create policy family_events_owner_update on public.family_relationship_events for update to authenticated
using (owner_user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())))
with check (owner_user_id=(select auth.uid()) and public.sinjira_mfa_access_allowed((select auth.uid())));
drop policy if exists family_events_parties_read on public.family_relationship_events;
create policy family_events_parties_read on public.family_relationship_events for select to authenticated
using (((select auth.uid())=owner_user_id or (select auth.uid())=related_user_id) and public.sinjira_mfa_access_allowed((select auth.uid())));

-- Préférences héritage et événements de vie.
drop policy if exists legacy_pref_own on public.account_legacy_preferences;
create policy legacy_pref_own on public.account_legacy_preferences for all to authenticated
using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
drop policy if exists life_events_own on public.private_life_events;
create policy life_events_own on public.private_life_events for all to authenticated
using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);

-- Lecteur : public séparé de membre/admin afin d'éviter plusieurs politiques SELECT pour authenticated.
drop policy if exists reader_characters_public_read on public.reader_characters;
drop policy if exists reader_characters_own_read on public.reader_characters;
drop policy if exists reader_characters_admin_read on public.reader_characters;
drop policy if exists reader_characters_anon_read on public.reader_characters;
drop policy if exists reader_characters_authenticated_read on public.reader_characters;
create policy reader_characters_anon_read on public.reader_characters for select to anon
using (is_public=true and status='published');
create policy reader_characters_authenticated_read on public.reader_characters for select to authenticated
using (public.is_sinjira_admin((select auth.uid())) or user_id=(select auth.uid()) or (is_public=true and status='published'));

drop policy if exists reader_comments_public_read on public.reader_comments;
drop policy if exists reader_comments_own_read on public.reader_comments;
drop policy if exists reader_comments_admin_read on public.reader_comments;
drop policy if exists reader_comments_anon_read on public.reader_comments;
drop policy if exists reader_comments_authenticated_read on public.reader_comments;
create policy reader_comments_anon_read on public.reader_comments for select to anon
using (status='approved');
create policy reader_comments_authenticated_read on public.reader_comments for select to authenticated
using (public.is_sinjira_admin((select auth.uid())) or user_id=(select auth.uid()) or status='approved');

drop policy if exists reader_works_public_read on public.reader_works;
drop policy if exists reader_works_admin_read on public.reader_works;
drop policy if exists reader_works_anon_read on public.reader_works;
drop policy if exists reader_works_authenticated_read on public.reader_works;
create policy reader_works_anon_read on public.reader_works for select to anon
using (status='active');
create policy reader_works_authenticated_read on public.reader_works for select to authenticated
using (status='active' or public.is_sinjira_admin((select auth.uid())));

drop policy if exists registry_links_own_read on public.registry_account_links;
drop policy if exists registry_links_admin_read on public.registry_account_links;
drop policy if exists registry_links_read_authorized on public.registry_account_links;
create policy registry_links_read_authorized on public.registry_account_links for select to authenticated
using (user_id=(select auth.uid()) or public.is_sinjira_admin((select auth.uid())));
