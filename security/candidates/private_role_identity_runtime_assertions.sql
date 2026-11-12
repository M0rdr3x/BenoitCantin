-- Assertions pgTAP LOCAL uniquement, assemblées avant ROLLBACK du candidat #843.
-- UUID et courriels entièrement fictifs; aucune donnée hébergée utilisée.
-- Refus d'exécution autonome : le générateur ajoute ce marqueur uniquement
-- à l'intérieur de sa transaction BEGIN ... ROLLBACK locale.
DO $test_gate$
BEGIN
  IF current_setting('application_name', true) <> 'sinjira-local-rls-pgtap' THEN
    RAISE EXCEPTION 'SINJIRA_PGTAP_LOCAL_ASSEMBLY_REQUIRED';
  END IF;
END
$test_gate$;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path = public, extensions;
-- Les migrations locales ne reproduisent pas encore les GRANT SELECT de
-- la production (constat catalogue live : anon=true et authenticated=true).
-- La simulation de la politique RLS est uniquement DANS BEGIN/ROLLBACK.
-- Cette permission ne sera JAMAIS appliquée sur Supabase distant.
GRANT SELECT ON public.projects TO anon, authenticated;

-- La reconstruction locale ne reflète pas encore l'ensemble des politiques
-- réellement déployées. Test ciblé sous un SNAPSHOT transactionnel des deux
-- politiques de lecture projets, vérifiées dans pg_catalog.pg_policies live.
-- Aucune stratégie d'accès n'est ajoutée aux autres tables ni à production.
DO $local_policy_snapshot$
DECLARE v_policy record;
BEGIN
  FOR v_policy IN
    SELECT policyname
    FROM pg_catalog.pg_policies
    WHERE schemaname='public' AND tablename='projects' AND cmd='SELECT'
  LOOP
    EXECUTE format('DROP POLICY %I ON public.projects',v_policy.policyname);
  END LOOP;
END
$local_policy_snapshot$;

CREATE POLICY projects_public_read ON public.projects FOR SELECT TO anon
USING (status<>'draft' AND visibility='public');

CREATE POLICY projects_authenticated_read ON public.projects FOR SELECT TO authenticated
USING (
  public.is_sinjira_admin((SELECT auth.uid()))
  OR (
    status<>'draft'
    AND (
      visibility IN ('public','account')
      OR private.project_access_rank(id,(SELECT auth.uid())) >= 20
    )
  )
);
SELECT plan(28);

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
('33333333-3333-4333-8333-333333333333','authenticated','authenticated',
  (SELECT (regexp_match(
    pg_catalog.pg_get_functiondef('public.enforce_sinjira_single_admin()'::regprocedure),
    $pattern$lower\('([^']+)'\)$pattern$))[1]),'{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"Homme","sex":"male"}'::jsonb,now(),now());
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


-- Vérifications réelles des POLITIQUES RLS, pas seulement des helpers.
SELECT is(
 pg_temp.sinjira_check_as('anon',NULL,'anon',
 $test$SELECT count(*)::text FROM public.projects WHERE slug LIKE 'local-security-rank-%'$test$),
 '1','RLS projects interdit les projets non publics aux visiteurs'
);
SELECT is(
 pg_temp.sinjira_check_as('authenticated','11111111-1111-4111-8111-111111111111','authenticated',
 $test$SELECT count(*)::text FROM public.projects WHERE slug LIKE 'local-security-rank-%'$test$),
 '3','RLS projects conserve les projets autorisés du testeur A'
);
SELECT is(
 pg_temp.sinjira_check_as('authenticated','22222222-2222-4222-8222-222222222222','authenticated',
 $test$SELECT count(*)::text FROM public.projects WHERE slug LIKE 'local-security-rank-%'$test$),
 '3','RLS projects conserve les projets autorisés du joueur B'
);
SELECT is(
 pg_temp.sinjira_check_as('authenticated','33333333-3333-4333-8333-333333333333','authenticated',
 $test$SELECT count(*)::text FROM public.projects WHERE slug LIKE 'local-security-rank-%'$test$),
 '4','RLS projects conserve la lecture administrateur propriétaire'
);
SELECT * FROM finish();
