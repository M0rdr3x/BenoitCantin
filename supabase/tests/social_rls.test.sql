begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, extensions;

select plan(14);

-- Toutes les tables sociales critiques conservent RLS.
select ok((select relrowsecurity from pg_class where oid='public.social_character_posts'::regclass), 'RLS actif: social_character_posts');
select ok((select relrowsecurity from pg_class where oid='public.social_real_posts'::regclass), 'RLS actif: social_real_posts');
select ok((select relrowsecurity from pg_class where oid='public.social_character_messages'::regclass), 'RLS actif: social_character_messages');
select ok((select relrowsecurity from pg_class where oid='public.social_real_messages'::regclass), 'RLS actif: social_real_messages');

-- La cohorte paramétrée est interne; le navigateur ne peut demander que sa propre cohorte.
select ok(not has_function_privilege('anon', 'public.sinjira_age_band(uuid)', 'EXECUTE'), 'anon ne peut pas interroger sinjira_age_band(uuid)');
select ok(not has_function_privilege('authenticated', 'public.sinjira_age_band(uuid)', 'EXECUTE'), 'authenticated ne peut pas interroger la cohorte arbitraire');
select ok(has_function_privilege('service_role', 'public.sinjira_age_band(uuid)', 'EXECUTE'), 'service_role garde sinjira_age_band(uuid)');
select ok(has_function_privilege('authenticated', 'public.sinjira_my_age_band()', 'EXECUTE'), 'authenticated peut lire uniquement sa propre cohorte');

-- Le diagnostic propriétaire reste strictement serveur.
select ok(not has_function_privilege('anon', 'public.sinjira_owner_social_health()', 'EXECUTE'), 'anon ne peut pas appeler owner social health');
select ok(not has_function_privilege('authenticated', 'public.sinjira_owner_social_health()', 'EXECUTE'), 'authenticated ne peut pas appeler owner social health');
select ok(has_function_privilege('service_role', 'public.sinjira_owner_social_health()', 'EXECUTE'), 'service_role peut appeler owner social health');

-- Les rôles API n'ont jamais besoin des privilèges structurels contournant la logique ligne-par-ligne.
select is((select count(*) from information_schema.role_table_grants where table_schema='public' and grantee='anon' and privilege_type in ('TRUNCATE','TRIGGER','REFERENCES')), 0::bigint, 'anon: aucun privilège structurel public');
select is((select count(*) from information_schema.role_table_grants where table_schema='public' and grantee='authenticated' and privilege_type in ('TRUNCATE','TRIGGER','REFERENCES')), 0::bigint, 'authenticated: aucun privilège structurel public');

-- Les politiques de publication doivent rester explicites et non permissives.
select ok(
  exists(
    select 1 from pg_policies
    where schemaname='public' and tablename='social_character_posts' and policyname='char_posts_insert'
      and cmd='INSERT'
      and with_check ilike '%sinjira_my_age_band%'
      and with_check ilike '%has_accepted_community_rules%'
      and with_check ilike '%social_is_suspended%'
  ),
  'char_posts_insert conserve cohorte + règles + suspension'
);

select * from finish();
rollback;
