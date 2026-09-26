-- SINJIRA™ V25 — frontière serveur 11–12 ans pour les modules non encore certifiés.
-- La navigation Junior est fail-closed, mais la sécurité ne dépend jamais de l'interface.
-- Toute mutation sensible déclenchée par un compte child est refusée côté base.

create or replace function private.sinjira_child_sensitive_write_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $child$
declare
  uid uuid:=auth.uid();
  band text;
  target_band text;
begin
  if uid is not null then
    band:=public.sinjira_age_band(uid);
    if band='child' then
      raise exception 'CHILD_ACTION_NOT_AVAILABLE_11_12' using errcode='42501';
    elsif coalesce(band,'unverified') not in ('adult','youth') then
      raise exception 'ACCOUNT_ACTION_NOT_AVAILABLE_RESTRICTED' using errcode='42501';
    end if;
  end if;

  -- Un adulte/admin ne peut pas créer ou maintenir une participation Playtest
  -- ciblant un compte child ou une bande restreinte. DELETE reste permis pour nettoyage.
  if tg_table_name='playtest_participants' and tg_op<>'DELETE' then
    target_band:=public.sinjira_age_band(new.user_id);
    if target_band='child' then
      raise exception 'CHILD_TARGET_NOT_AVAILABLE_11_12' using errcode='42501';
    elsif coalesce(target_band,'unverified') not in ('adult','youth') then
      raise exception 'ACCOUNT_TARGET_NOT_AVAILABLE_RESTRICTED' using errcode='42501';
    end if;
  end if;

  if tg_op='DELETE' then return old; end if;
  return new;
end;
$child$;
revoke all on function private.sinjira_child_sensitive_write_guard() from public,anon,authenticated;

do $child$
declare t text;
begin
  foreach t in array array[
    'access_requests','playtest_participants',
    'parallel_responses','parallel_character_state',
    'market_listings','market_favorites',
    'license_redemptions','product_preorders','orders','order_items',
    'employment_profiles','employment_applications',
    'game_sessions','player_sheets','endgame_sheets',
    'novel_comments','reader_comments','sinjira_novel_comments'
  ] loop
    if to_regclass('public.'||t) is not null then
      execute format('drop trigger if exists sinjira_child_sensitive_write_guard on public.%I',t);
      execute format('create trigger sinjira_child_sensitive_write_guard before insert or update or delete on public.%I for each row execute function private.sinjira_child_sensitive_write_guard()',t);
    end if;
  end loop;
end;
$child$;

-- Le consentement recherche/contribution reste modifiable vers OFF, jamais vers ON à 11–12 ans.
create or replace function private.sinjira_child_research_consent_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $child$
declare
  uid uuid:=auth.uid();
  band text;
begin
  if uid is not null then
    band:=public.sinjira_age_band(uid);
  end if;
  if uid is not null and coalesce(band,'unverified') not in ('adult','youth') then
    new.participate:=false;
    new.share_free_text:=false;
    new.consented_at:=null;
  end if;
  return new;
end;
$child$;
revoke all on function private.sinjira_child_research_consent_guard() from public,anon,authenticated;

drop trigger if exists sinjira_child_research_consent_guard on public.research_consents;
create trigger sinjira_child_research_consent_guard
before insert or update on public.research_consents
for each row execute function private.sinjira_child_research_consent_guard();

-- Avant le classement explicite 11–12, un compte child authentifié ne reçoit aucun projet/document via le catalogue.
-- Les visiteurs anonymes conservent la lecture des contenus réellement publics; 20260918013000 rouvre ensuite uniquement le contenu explicitement approved_11_12.
drop policy if exists "projects readable when accessible" on public.projects;
drop policy if exists admin_read_all_projects on public.projects;
drop policy if exists projects_read on public.projects;
drop policy if exists projects_public_read on public.projects;
drop policy if exists projects_authenticated_read on public.projects;
create policy "projects readable when accessible" on public.projects for select to anon,authenticated
using(
  status<>'draft' and (
    (
      visibility='public'
      and (
        (select auth.uid()) is null
        or public.sinjira_my_age_band() in ('adult','youth')
      )
    )
    or (
      (select auth.uid()) is not null
      and public.sinjira_my_age_band() in ('adult','youth')
      and (visibility='account' or public.project_access_rank(id,(select auth.uid()))>=20)
    )
  )
);

drop policy if exists "approved documents visible by access" on public.documents;
drop policy if exists documents_read_by_access on public.documents;
drop policy if exists admin_read_all_documents on public.documents;
drop policy if exists documents_anon_read on public.documents;
drop policy if exists documents_authenticated_read on public.documents;
create policy "approved documents visible by access" on public.documents for select to anon,authenticated
using(
  status='approved'
  and public.project_access_rank(project_id,(select auth.uid()))>=public.document_access_rank(access_level)
  and (
    (select auth.uid()) is null
    or public.sinjira_my_age_band() in ('adult','youth')
  )
);

-- Une seule politique SELECT Playtests doit rester active. Les anciennes politiques
-- permissives seraient combinées par OR et pourraient sinon contourner la fermeture child.
drop policy if exists "playtests readable" on public.playtests;
drop policy if exists playtests_read on public.playtests;
drop policy if exists admin_read_all_playtests on public.playtests;
drop policy if exists playtests_read_authorized on public.playtests;
create policy playtests_read_authorized on public.playtests for select to authenticated
using(
  (select auth.uid()) is not null
  and public.sinjira_my_age_band() in ('adult','youth')
  and (
    public.is_sinjira_admin((select auth.uid()))
    or exists(
      select 1
      from public.playtest_participants pp
      where pp.playtest_id=playtests.id
        and pp.user_id=(select auth.uid())
    )
    or (
      status in ('open','active')
      and public.project_access_rank(project_id,(select auth.uid()))>=case required_access
        when 'tester' then 30
        when 'player' then 20
        else 10
      end
    )
  )
);

-- Même règle pour l'historique des participations : un ancien compte 12 ans
-- devenu child ne doit pas pouvoir relire ses anciennes participations.
drop policy if exists "participants own select" on public.playtest_participants;
drop policy if exists playtest_participants_select_own on public.playtest_participants;
drop policy if exists admin_read_all_playtest_participants on public.playtest_participants;
drop policy if exists playtest_participants_read_authorized on public.playtest_participants;
create policy playtest_participants_read_authorized on public.playtest_participants for select to authenticated
using(
  (select auth.uid()) is not null
  and public.sinjira_my_age_band() in ('adult','youth')
  and (
    (select auth.uid())=user_id
    or public.is_sinjira_admin((select auth.uid()))
  )
);

drop policy if exists "requests own insert" on public.access_requests;
create policy "requests own insert" on public.access_requests for insert to authenticated
with check(
  (select auth.uid())=user_id
  and public.sinjira_my_age_band() in ('adult','youth')
  and status='pending'
);

drop policy if exists "participants own apply" on public.playtest_participants;
create policy "participants own apply" on public.playtest_participants for insert to authenticated
with check(
  (select auth.uid())=user_id
  and public.sinjira_my_age_band() in ('adult','youth')
  and status='applied'
);

comment on function private.sinjira_child_sensitive_write_guard() is
  'Refuse côté base toute mutation vers les modules non certifiés 11–12 ans, indépendamment de la navigation client.';
