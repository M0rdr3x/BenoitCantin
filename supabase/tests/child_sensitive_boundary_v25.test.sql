begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(8);
select ok(to_regprocedure('private.sinjira_child_sensitive_write_guard()') is not null,'garde serveur child des mutations sensibles existe');
select ok(to_regprocedure('private.sinjira_child_research_consent_guard()') is not null,'garde consentement recherche child existe');
select ok(exists(select 1 from pg_trigger where tgname='sinjira_child_sensitive_write_guard' and tgrelid='public.employment_profiles'::regclass and not tgisinternal),'Emploi porte la garde child');
select ok(exists(select 1 from pg_trigger where tgname='sinjira_child_sensitive_write_guard' and tgrelid='public.market_listings'::regclass and not tgisinternal),'Marché porte la garde child');
select ok(exists(select 1 from pg_trigger where tgname='sinjira_child_sensitive_write_guard' and tgrelid='public.access_requests'::regclass and not tgisinternal),'demandes testeur portent la garde child');
select ok(exists(select 1 from pg_trigger where tgname='sinjira_child_sensitive_write_guard' and tgrelid='public.product_preorders'::regclass and not tgisinternal),'précommandes portent la garde child');
select ok((select qual ilike '%sinjira_age_band%' from pg_policies where schemaname='public' and tablename='documents' and policyname='approved documents visible by access'),'documents privés tiennent compte de la bande âge');
select ok((select with_check ilike '%sinjira_age_band%' from pg_policies where schemaname='public' and tablename='playtest_participants' and policyname='participants own apply'),'playtests refusent child côté RLS');
select * from finish();
rollback;
