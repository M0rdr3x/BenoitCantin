begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;
select plan(1);
select is((
  select sum(n)::int from (
    select count(*)::int n from pg_policies where lower(coalesce(qual,'')||' '||coalesce(with_check,'')) like '%sinjira_rls_internal.is_fracture_party_member%'
    union all select count(*)::int from pg_policies where lower(coalesce(qual,'')||' '||coalesce(with_check,'')) like '%sinjira_rls_internal.moderation_content_visible%'
    union all select count(*)::int from pg_policies where lower(coalesce(qual,'')||' '||coalesce(with_check,'')) like '%sinjira_rls_internal.sinjira_can_social_interact%'
    union all select count(*)::int from pg_policies where lower(coalesce(qual,'')||' '||coalesce(with_check,'')) like '%sinjira_rls_internal.sinjira_content_allowed%'
    union all select count(*)::int from pg_policies where lower(coalesce(qual,'')||' '||coalesce(with_check,'')) like '%sinjira_rls_internal.sinjira_cycle_allowed%'
    union all select count(*)::int from pg_policies where lower(coalesce(qual,'')||' '||coalesce(with_check,'')) like '%sinjira_rls_internal.sinjira_mfa_access_allowed%'
    union all select count(*)::int from pg_policies where lower(coalesce(qual,'')||' '||coalesce(with_check,'')) like '%sinjira_rls_internal.sinjira_my_age_band%'
    union all select count(*)::int from pg_policies where lower(coalesce(qual,'')||' '||coalesce(with_check,'')) like '%sinjira_rls_internal.social_is_blocked%'
    union all select count(*)::int from pg_policies where lower(coalesce(qual,'')||' '||coalesce(with_check,'')) like '%sinjira_rls_internal.social_is_suspended%'
  ) refs
),81,'81 dépendances helper-politique RLS conservées');
select * from finish();
rollback;
