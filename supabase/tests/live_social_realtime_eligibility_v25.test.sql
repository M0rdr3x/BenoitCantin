begin;

create extension if not exists pgtap with schema extensions;
set local search_path=public,extensions;

select plan(4);

select ok(
  exists(
    select 1 from pg_policies
    where schemaname='realtime' and tablename='messages'
      and policyname='sinjira_live_realtime_read'
      and qual ilike '%has_accepted_community_rules%'
      and qual ilike '%social_is_suspended%'
      and qual ilike '%sinjira_my_age_band%'
      and qual ilike '%social_is_blocked%'
  ),
  'lecture Realtime exige règles, absence de suspension, cohorte courante et blocage owner'
);

select ok(
  exists(
    select 1 from pg_policies
    where schemaname='realtime' and tablename='messages'
      and policyname='sinjira_live_realtime_read_guard'
      and permissive='RESTRICTIVE'
      and qual ilike '%has_accepted_community_rules%'
      and qual ilike '%social_is_suspended%'
      and qual ilike '%sinjira_my_age_band%'
  ),
  'garde restrictive de lecture conserve les mêmes critères d éligibilité'
);

select ok(
  exists(
    select 1 from pg_policies
    where schemaname='realtime' and tablename='messages'
      and policyname='sinjira_live_realtime_presence_write'
      and with_check ilike '%extension%presence%'
      and with_check ilike '%has_accepted_community_rules%'
      and with_check ilike '%social_is_suspended%'
      and with_check ilike '%sinjira_my_age_band%'
  ),
  'Presence Realtime exige l éligibilité courante du membre'
);

select ok(
  exists(
    select 1 from pg_policies
    where schemaname='realtime' and tablename='messages'
      and policyname='sinjira_live_realtime_write_guard'
      and permissive='RESTRICTIVE'
      and with_check ilike '%sinjira-live:%'
      and with_check ilike '%extension%presence%'
      and with_check ilike '%has_accepted_community_rules%'
      and with_check ilike '%social_is_suspended%'
      and with_check ilike '%sinjira_my_age_band%'
  ),
  'garde restrictive d écriture interdit le maintien Realtime après perte d éligibilité'
);

select * from finish();
rollback;
