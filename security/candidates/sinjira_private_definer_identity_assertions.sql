-- Assertions pgTAP pour Supabase LOCAL ; le script de generation ajoute ROLLBACK.
-- Utilisateurs, emails et projets entierement fictifs, aucune production.
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path = public, extensions;
SELECT plan(22);

INSERT INTO auth.users(id,aud,role,email,raw_user_meta_data,created_at,updated_at) VALUES
 ('11111111-1111-4111-8111-111111111111','authenticated','authenticated','candidate-alice@example.invalid',
  '{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"female"}'::jsonb,now(),now()),
 ('22222222-2222-4222-8222-222222222222','authenticated','authenticated','candidate-bob@example.invalid',
  '{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"female"}'::jsonb,now(),now()),
 ('33333333-3333-4333-8333-333333333333','authenticated','authenticated','candidate-charlie@example.invalid',
  '{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"female"}'::jsonb,now(),now());

INSERT INTO public.projects(id,slug,name,status,visibility) VALUES
 ('44444444-4444-4444-8444-444444444444','candidate-identity-public-20261121','Public synthétique','active','public'),
 ('55555555-5555-4555-8555-555555555555','candidate-identity-account-20261121','Compte synthétique','active','account'),
 ('66666666-6666-4666-8666-666666666666','candidate-identity-restricted-20261121','Privé synthétique','active','restricted');

INSERT INTO public.internal_admin_users(user_id,role)
VALUES ('22222222-2222-4222-8222-222222222222','admin');
INSERT INTO public.project_access(user_id,project_id,access_level)
VALUES ('11111111-1111-4111-8111-111111111111',
        '66666666-6666-4666-8666-666666666666','player');

SELECT set_config('request.jwt.claim.sub','',true);
SELECT set_config('request.jwt.claims','{"role":"anon"}',true);
SET LOCAL ROLE anon;
SELECT is(private.is_sinjira_admin('22222222-2222-4222-8222-222222222222'),false,'anon ne peut interroger un administrateur');
SELECT is(private.project_access_rank('44444444-4444-4444-8444-444444444444',NULL),1,'anon voit toujours le projet public');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666',NULL),0,'anon ne voit pas un projet prive');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666','22222222-2222-4222-8222-222222222222'),0,'anon ne peut sonder le rang admin');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666','11111111-1111-4111-8111-111111111111'),0,'anon ne peut sonder le rang utilisateur');
RESET ROLE;

SELECT set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
SELECT set_config('request.jwt.claims','{"role":"authenticated","sub":"11111111-1111-4111-8111-111111111111"}',true);
SET LOCAL ROLE authenticated;
SELECT is(private.is_sinjira_admin('22222222-2222-4222-8222-222222222222'),false,'Alice ne peut sonder les droits admin de Bob');
SELECT is(private.is_sinjira_admin('11111111-1111-4111-8111-111111111111'),false,'Alice non administratrice');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666','22222222-2222-4222-8222-222222222222'),0,'Alice ne peut sonder le rang de Bob');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666','11111111-1111-4111-8111-111111111111'),20,'Alice conserve son acces player');
SELECT is(private.project_access_rank('44444444-4444-4444-8444-444444444444','11111111-1111-4111-8111-111111111111'),10,'Alice conserve le rang public');
SELECT is(private.project_access_rank('55555555-5555-4555-8555-555555555555','11111111-1111-4111-8111-111111111111'),10,'Alice conserve le rang compte');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666',NULL),0,'Alice ne peut interroger une identite nulle');
RESET ROLE;

SELECT set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',true);
SELECT set_config('request.jwt.claims','{"role":"authenticated","sub":"22222222-2222-4222-8222-222222222222"}',true);
SET LOCAL ROLE authenticated;
SELECT is(private.is_sinjira_admin('22222222-2222-4222-8222-222222222222'),true,'Bob peut consulter son propre rang admin');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666','22222222-2222-4222-8222-222222222222'),100,'Bob conserve son propre rang admin');
SELECT is(private.project_access_rank('44444444-4444-4444-8444-444444444444','22222222-2222-4222-8222-222222222222'),100,'Bob conserve ses droits admin sur un projet public');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666','11111111-1111-4111-8111-111111111111'),0,'Bob ne peut sonder le rang d Alice');
RESET ROLE;

SELECT set_config('request.jwt.claim.sub','33333333-3333-4333-8333-333333333333',true);
SELECT set_config('request.jwt.claims','{"role":"authenticated","sub":"33333333-3333-4333-8333-333333333333"}',true);
SET LOCAL ROLE authenticated;
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666','33333333-3333-4333-8333-333333333333'),0,'Charlie ne possede aucun droit de projet prive');
RESET ROLE;

SELECT set_config('request.jwt.claim.sub','',true);
SELECT set_config('request.jwt.claims','{"role":"service_role"}',true);
SET LOCAL ROLE service_role;
SELECT is(private.is_sinjira_admin('22222222-2222-4222-8222-222222222222'),true,'service_role conserve la lecture admin');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666','22222222-2222-4222-8222-222222222222'),100,'service_role conserve la lecture admin de Bob');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666','11111111-1111-4111-8111-111111111111'),20,'service_role conserve la lecture du droit player d Alice');
RESET ROLE;

SELECT set_config('request.jwt.claim.sub','',true);
SELECT set_config('request.jwt.claims','{}',true);
SET LOCAL ROLE anon;
SELECT is(private.is_sinjira_admin('22222222-2222-4222-8222-222222222222'),false,'JWT sans identite : admin non divulgue');
SELECT is(private.project_access_rank('66666666-6666-4666-8666-666666666666','22222222-2222-4222-8222-222222222222'),0,'JWT sans identite : rang du tiers refuse');
RESET ROLE;

SELECT * FROM finish();
