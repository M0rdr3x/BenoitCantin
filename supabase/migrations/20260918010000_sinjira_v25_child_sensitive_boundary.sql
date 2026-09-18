-- SINJIRA™ V25 — frontière serveur 11–12 ans pour les modules non encore certifiés.
-- La navigation Junior est fail-closed, mais la sécurité ne dépend jamais de l'interface.
-- Toute mutation sensible déclenchée par un compte child est refusée côté base.

create or replace function private.sinjira_child_sensitive_write_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $child$
declare uid uuid:=auth.uid();
begin
  if uid is not null and public.sinjira_age_band(uid)='child' then
    raise exception 'CHILD_ACTION_NOT_AVAILABLE_11_12' using errcode='42501';
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
declare uid uuid:=auth.uid();
begin
  if uid is not null and public.sinjira_age_band(uid)='child' then
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

-- Les contenus de compte/projet non encore classés pour 11–12 ans ne sont pas délivrés au child.
-- Les contenus réellement publics restent visibles comme ils le seraient sans connexion.
drop policy if exists "projects readable when accessible" on public.projects;
create policy "projects readable when accessible" on public.projects for select to anon,authenticated
using(
  status<>'draft' and (
    visibility='public'
    or (
      (select auth.uid()) is not null
      and public.sinjira_age_band((select auth.uid()))<>'child'
      and (visibility='account' or public.project_access_rank(id,(select auth.uid()))>=20)
    )
  )
);

drop policy if exists "approved documents visible by access" on public.documents;
create policy "approved documents visible by access" on public.documents for select to anon,authenticated
using(
  status='approved'
  and public.project_access_rank(project_id,(select auth.uid()))>=public.document_access_rank(access_level)
  and (
    (select auth.uid()) is null
    or public.sinjira_age_band((select auth.uid()))<>'child'
    or (
      access_level='public'
      and exists(
        select 1 from public.projects p
        where p.id=project_id and p.visibility='public' and p.status<>'draft'
      )
    )
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
  and public.sinjira_age_band((select auth.uid()))<>'child'
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
  and public.sinjira_age_band((select auth.uid()))<>'child'
  and (
    (select auth.uid())=user_id
    or public.is_sinjira_admin((select auth.uid()))
  )
);

drop policy if exists "requests own insert" on public.access_requests;
create policy "requests own insert" on public.access_requests for insert to authenticated
with check(
  (select auth.uid())=user_id
  and public.sinjira_age_band((select auth.uid()))<>'child'
  and status='pending'
);

drop policy if exists "participants own apply" on public.playtest_participants;
create policy "participants own apply" on public.playtest_participants for insert to authenticated
with check(
  (select auth.uid())=user_id
  and public.sinjira_age_band((select auth.uid()))<>'child'
  and status='applied'
);

comment on function private.sinjira_child_sensitive_write_guard() is
  'Refuse côté base toute mutation vers les modules non certifiés 11–12 ans, indépendamment de la navigation client.';
