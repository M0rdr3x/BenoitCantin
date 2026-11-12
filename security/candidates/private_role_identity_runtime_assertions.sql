-- Assertions pgTAP LOCAL uniquement, assemblées avant ROLLBACK du candidat #843.
-- UUID et courriels entièrement fictifs; aucune donnée hébergée utilisée.
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path = public, extensions;
SELECT plan(24);

SELECT ok(has_schema_privilege('anon','private','USAGE'), 'usage private pour RLS anonyme');
SELECT ok(has_schema_privilege('authenticated','private','USAGE'), 'usage private pour RLS connecté');
SELECT ok(has_function_privilege('anon','private.project_access_rank(uuid,uuid)','EXECUTE'), 'rank disponible aux RLS anonymes');
SELECT ok(has_function_privilege('authenticated','private.project_access_rank(uuid,uuid)','EXECUTE'), 'rank disponible aux RLS connectées');
SELECT ok(has_function_privilege('authenticated','private.is_sinjira_admin(uuid)','EXECUTE'), 'helper admin disponible aux RLS connectées');
SELECT ok(has_function_privilege('service_role','private.project_access_rank(uuid,uuid)','EXECUTE'), 'rank disponible aux appels de service');

-- Fictifs : le trigger profil exige des métadonnées de majorité.
INSERT INTO auth.users(id,aud,role,email,raw_user_meta_data,created_at,updated_at)
VALUES
('11111111-1111-4111-8111-111111111111','authenticated','authenticated','local-role-0@example.invalid','{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"Homme","sex":"male"}'::jsonb,now(),now()),
('22222222-2222-4222-8222-222222222222','authenticated','authenticated','local-role-1@example.invalid','{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"Homme","sex":"male"}'::jsonb,now(),now()),
('33333333-3333-4333-8333-333333333333','authenticated','authenticated','local-role-2@example.invalid','{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"Homme","sex":"male"}'::jsonb,now(),now());
INSERT INTO public.internal_admin_users(user_id,role) VALUES ('33333333-3333-4333-8333-333333333333','admin');
INSERT INTO public.projects(id,slug,name,visibility) VALUES
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','local-security-rank-restricted','Fixture de sécurité restricted','restricted'),
('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','local-security-rank-pub','Fixture de sécurité pub','public'),
('cccccccc-cccc-4ccc-8ccc-cccccccccccc','local-security-rank-account','Fixture de sécurité account','account'),
('dddddddd-dddd-4ddd-8ddd-dddddddddddd','local-security-rank-expired','Fixture de sécurité expired','restricted');
INSERT INTO public.project_access(user_id,project_id,access_level,expires_at) VALUES
('11111111-1111-4111-8111-111111111111','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','tester',NULL),
('22222222-2222-4222-8222-222222222222','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','player',NULL),
('11111111-1111-4111-8111-111111111111','dddddddd-dddd-4ddd-8ddd-dddddddddddd','tester',now()-interval '1 hour');

-- Simulation SQL des rôles; aucune signature JWT n'est revendiquée.
-- La fonction vérifie current_user, rétablit les rôles même si erreur.
CREATE OR REPLACE FUNCTION pg_temp.sinjira_check_as(
 p_role text,p_sub text,p_jwt_role text,p_query text
) RETURNS text LANGUAGE plpgsql SECURITY INVOKER
SET search_path TO 'pg_catalog'
AS $role_test$
DECLARE v_result text;
BEGIN
 IF p_role NOT IN ('anon','authenticated','service_role') THEN
   RAISE EXCEPTION 'INVALID_TEST_DB_ROLE';
 END IF;
 PERFORM pg_catalog.set_config('request.jwt.claim.sub',coalesce(p_sub,''),true);
 PERFORM pg_catalog.set_config('request.jwt.claims',
   json_build_object('sub',p_sub,'role',p_jwt_role)::text,true);
 EXECUTE format('SET LOCAL ROLE %I',p_role);
 IF current_user <> p_role THEN RAISE EXCEPTION 'TEST_ROLE_SWITCH_FAILED'; END IF;
 EXECUTE p_query INTO v_result;
 EXECUTE 'RESET ROLE';
 RETURN v_result;
EXCEPTION WHEN OTHERS THEN
 EXECUTE 'RESET ROLE';
 RAISE;
END;
$role_test$;

SELECT is(
 pg_temp.sinjira_check_as('authenticated','33333333-3333-4333-8333-333333333333','authenticated',
 $test$SELECT private.is_sinjira_admin('33333333-3333-4333-8333-333333333333')::text$test$),
 'true','admin connecté autorisé'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','11111111-1111-4111-8111-111111111111','authenticated',
 $test$SELECT private.is_sinjira_admin('33333333-3333-4333-8333-333333333333')::text$test$),
 'false','oracle du statut admin d''un tiers interdit'
);

SELECT is(
 pg_temp.sinjira_check_as('anon',NULL,'anon',
 $test$SELECT private.is_sinjira_admin('33333333-3333-4333-8333-333333333333')::text$test$),
 'false','oracle admin anonyme interdit'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','11111111-1111-4111-8111-111111111111','authenticated',
 $test$SELECT private.is_sinjira_admin()::text$test$),
 'false','utilisateur normal non admin'
);

SELECT is(
 pg_temp.sinjira_check_as('service_role',NULL,'service_role',
 $test$SELECT private.is_sinjira_admin('33333333-3333-4333-8333-333333333333')::text$test$),
 'true','service role contrôle d''admin conservé'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','11111111-1111-4111-8111-111111111111','authenticated',
 $test$SELECT private.project_access_rank('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')::text$test$),
 '30','rang tester conservé'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','22222222-2222-4222-8222-222222222222','authenticated',
 $test$SELECT private.project_access_rank('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')::text$test$),
 '20','rang player conservé'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','11111111-1111-4111-8111-111111111111','authenticated',
 $test$SELECT private.project_access_rank('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','22222222-2222-4222-8222-222222222222')::text$test$),
 '0','rang player d''un autre compte inaccessible'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','22222222-2222-4222-8222-222222222222','authenticated',
 $test$SELECT private.project_access_rank('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','11111111-1111-4111-8111-111111111111')::text$test$),
 '0','rang tester d''un autre compte inaccessible'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','11111111-1111-4111-8111-111111111111','authenticated',
 $test$SELECT private.project_access_rank('dddddddd-dddd-4ddd-8ddd-dddddddddddd')::text$test$),
 '0','accès expiré refusé'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','11111111-1111-4111-8111-111111111111','authenticated',
 $test$SELECT private.project_access_rank('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb')::text$test$),
 '10','visibilité projet public aux comptes conservée'
);

SELECT is(
 pg_temp.sinjira_check_as('anon',NULL,'anon',
 $test$SELECT private.project_access_rank('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',NULL::uuid)::text$test$),
 '1','projet public toujours visible pour anonyme'
);

SELECT is(
 pg_temp.sinjira_check_as('anon',NULL,'anon',
 $test$SELECT private.project_access_rank('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',NULL::uuid)::text$test$),
 '0','projet privé interdit aux anonymes'
);

SELECT is(
 pg_temp.sinjira_check_as('anon',NULL,'anon',
 $test$SELECT private.project_access_rank('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','11111111-1111-4111-8111-111111111111')::text$test$),
 '0','anonyme ne peut revendiquer un autre UUID'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','11111111-1111-4111-8111-111111111111','authenticated',
 $test$SELECT private.project_access_rank('cccccccc-cccc-4ccc-8ccc-cccccccccccc')::text$test$),
 '10','visibilité projet compte conservée'
);

SELECT is(
 pg_temp.sinjira_check_as('service_role',NULL,'service_role',
 $test$SELECT private.project_access_rank('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','11111111-1111-4111-8111-111111111111')::text$test$),
 '30','service role lit rang distant pour traitements légitimes'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','33333333-3333-4333-8333-333333333333','authenticated',
 $test$SELECT private.project_access_rank('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')::text$test$),
 '100','administrateur voit son propre rang'
);

SELECT is(
 pg_temp.sinjira_check_as('authenticated','11111111-1111-4111-8111-111111111111','authenticated',
 $test$SELECT private.project_access_rank('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','33333333-3333-4333-8333-333333333333')::text$test$),
 '0','un utilisateur ne lit pas le rang admin d''un tiers'
);

SELECT * FROM finish();
