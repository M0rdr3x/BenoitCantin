begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(12);
select ok(to_regprocedure('private.sinjira_child_sensitive_write_guard()') is not null,'garde serveur child des mutations sensibles existe');
select ok(to_regprocedure('private.sinjira_child_research_consent_guard()') is not null,'garde consentement recherche child existe');
select ok(exists(select 1 from pg_trigger where tgname='sinjira_child_sensitive_write_guard' and tgrelid='public.employment_profiles'::regclass and not tgisinternal),'Emploi porte la garde child');
select ok(exists(select 1 from pg_trigger where tgname='sinjira_child_sensitive_write_guard' and tgrelid='public.market_listings'::regclass and not tgisinternal),'Marché porte la garde child');
select ok(exists(select 1 from pg_trigger where tgname='sinjira_child_sensitive_write_guard' and tgrelid='public.access_requests'::regclass and not tgisinternal),'demandes testeur portent la garde child');
select ok(exists(select 1 from pg_trigger where tgname='sinjira_child_sensitive_write_guard' and tgrelid='public.product_preorders'::regclass and not tgisinternal),'précommandes portent la garde child');
select ok((select qual ilike '%sinjira_age_band%' from pg_policies where schemaname='public' and tablename='documents' and policyname='approved documents visible by access'),'documents privés tiennent compte de la bande âge');
select ok((select with_check ilike '%sinjira_age_band%' from pg_policies where schemaname='public' and tablename='playtest_participants' and policyname='participants own apply'),'playtests refusent child côté RLS');
select is(
  (select count(*) from pg_policies where schemaname='public' and tablename='playtests' and cmd='SELECT'),
  1::bigint,
  'une seule politique SELECT Playtests reste active pour éviter un OR permissif'
);
select ok(
  (select qual ilike '%sinjira_age_band%' from pg_policies where schemaname='public' and tablename='playtests' and policyname='playtests_read_authorized'),
  'la politique SELECT Playtests canonique exclut explicitement child'
);
select is(
  (select count(*) from pg_policies where schemaname='public' and tablename='playtest_participants' and cmd='SELECT'),
  1::bigint,
  'une seule politique SELECT participations Playtests reste active'
);
select ok(
  (select qual ilike '%sinjira_age_band%' from pg_policies where schemaname='public' and tablename='playtest_participants' and policyname='playtest_participants_read_authorized'),
  'la lecture des participations Playtests exclut explicitement child'
);
select * from finish();
rollback;
