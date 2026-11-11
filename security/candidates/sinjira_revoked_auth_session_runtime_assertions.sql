-- Assertions de sécurité pour le candidat P0, via une base Supabase LOCALE.
-- Le générateur les insère avant ROLLBACK : aucune donnée ne persiste.
-- Les UUID et domaines sont exclusivement fictifs.
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path = public, extensions;
SELECT plan(44);

SELECT has_function(
  'private','security_require_current_auth_session',ARRAY['uuid'],
  'le garde des sessions actives est présent'
);
SELECT ok(
  NOT has_function_privilege('anon',
    'private.security_require_current_auth_session(uuid)','EXECUTE'),
  'anon ne peut jamais appeler le garde privilégié directement'
);
SELECT ok(
  NOT has_function_privilege('authenticated',
    'private.security_require_current_auth_session(uuid)','EXECUTE'),
  'authenticated ne peut pas appeler le garde privilégié directement'
);

-- Contrôles des huit interfaces publiques réellement accessibles depuis PostgREST.
SELECT ok(
  NOT has_function_privilege('anon','public.security_after_password_recovery(text)','EXECUTE'),
  'anon refuse par le point d’entrée security_after_password_recovery'
);
SELECT ok(
  has_function_privilege('authenticated','public.security_after_password_recovery(text)','EXECUTE'),
  'authenticated a le contrat d’entrée security_after_password_recovery'
);

SELECT ok(
  NOT has_function_privilege('anon','public.security_compromise_account(text)','EXECUTE'),
  'anon refuse par le point d’entrée security_compromise_account'
);
SELECT ok(
  has_function_privilege('authenticated','public.security_compromise_account(text)','EXECUTE'),
  'authenticated a le contrat d’entrée security_compromise_account'
);

SELECT ok(
  NOT has_function_privilege('anon','public.security_report_lost_device(uuid)','EXECUTE'),
  'anon refuse par le point d’entrée security_report_lost_device'
);
SELECT ok(
  has_function_privilege('authenticated','public.security_report_lost_device(uuid)','EXECUTE'),
  'authenticated a le contrat d’entrée security_report_lost_device'
);

SELECT ok(
  NOT has_function_privilege('anon','public.security_resolve_connection_challenge(uuid,text,text)','EXECUTE'),
  'anon refuse par le point d’entrée security_resolve_connection_challenge'
);
SELECT ok(
  has_function_privilege('authenticated','public.security_resolve_connection_challenge(uuid,text,text)','EXECUTE'),
  'authenticated a le contrat d’entrée security_resolve_connection_challenge'
);

SELECT ok(
  NOT has_function_privilege('anon','public.security_resolve_connection_challenge_mfa(uuid,text)','EXECUTE'),
  'anon refuse par le point d’entrée security_resolve_connection_challenge_mfa'
);
SELECT ok(
  has_function_privilege('authenticated','public.security_resolve_connection_challenge_mfa(uuid,text)','EXECUTE'),
  'authenticated a le contrat d’entrée security_resolve_connection_challenge_mfa'
);

SELECT ok(
  NOT has_function_privilege('anon','public.security_revoke_device(uuid)','EXECUTE'),
  'anon refuse par le point d’entrée security_revoke_device'
);
SELECT ok(
  has_function_privilege('authenticated','public.security_revoke_device(uuid)','EXECUTE'),
  'authenticated a le contrat d’entrée security_revoke_device'
);

SELECT ok(
  NOT has_function_privilege('anon','public.security_set_device_trust(uuid,boolean,boolean)','EXECUTE'),
  'anon refuse par le point d’entrée security_set_device_trust'
);
SELECT ok(
  has_function_privilege('authenticated','public.security_set_device_trust(uuid,boolean,boolean)','EXECUTE'),
  'authenticated a le contrat d’entrée security_set_device_trust'
);

SELECT ok(
  NOT has_function_privilege('anon','public.security_update_settings(boolean,boolean,boolean,boolean,boolean)','EXECUTE'),
  'anon refuse par le point d’entrée security_update_settings'
);
SELECT ok(
  has_function_privilege('authenticated','public.security_update_settings(boolean,boolean,boolean,boolean,boolean)','EXECUTE'),
  'authenticated a le contrat d’entrée security_update_settings'
);

-- Deux utilisateurs fictifs : pas d'e-mail personnel ni de compte live.
INSERT INTO auth.users(id, aud, role, email, raw_user_meta_data, created_at, updated_at)
VALUES
 ('11111111-1111-4111-8111-111111111111', 'authenticated', 'authenticated',
  'rpc-fixture-a@example.invalid',
  '{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"female"}'::jsonb,
  now(),now()),
 ('22222222-2222-4222-8222-222222222222', 'authenticated', 'authenticated',
  'rpc-fixture-b@example.invalid',
  '{"birth_date":"1990-01-15","date_of_birth":"1990-01-15","gender":"female"}'::jsonb,
  now(),now());

INSERT INTO auth.sessions(id, user_id, not_after)
VALUES
 ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  '11111111-1111-4111-8111-111111111111', NULL),
 ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
  '22222222-2222-4222-8222-222222222222', NULL),
 ('cccccccc-cccc-4ccc-8ccc-cccccccccccc',
  '11111111-1111-4111-8111-111111111111', now()-interval '1 hour'),
 ('dddddddd-dddd-4ddd-8ddd-dddddddddddd',
  '11111111-1111-4111-8111-111111111111', NULL);

-- Authenticated user A, session A active.
SELECT set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
SELECT set_config('request.jwt.claims',
  '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated","session_id":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}',true);
SELECT lives_ok(
  $$SELECT private.security_require_current_auth_session('11111111-1111-4111-8111-111111111111')$$,
  'session active et propriétaire : acceptée'
);

UPDATE auth.sessions SET not_after=now()+interval '1 hour'
WHERE id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
SELECT lives_ok(
  $$SELECT private.security_require_current_auth_session('11111111-1111-4111-8111-111111111111')$$,
  'session active avec date future : acceptée'
);

-- La révocation, une autre identité ou une expiration doivent fermer l'accès.
SELECT set_config('request.jwt.claims',
  '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated","session_id":"cccccccc-cccc-4ccc-8ccc-cccccccccccc"}',true);
SELECT throws_ok(
  $$SELECT private.security_require_current_auth_session('11111111-1111-4111-8111-111111111111')$$,
  '42501','AUTH_SESSION_INVALID',
  'session dont not_after est passé : refusée'
);

SELECT set_config('request.jwt.claims',
  '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated","session_id":"bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"}',true);
SELECT throws_ok(
  $$SELECT private.security_require_current_auth_session('11111111-1111-4111-8111-111111111111')$$,
  '42501','AUTH_SESSION_INVALID',
  'session appartenant à un autre compte : refusée'
);

SELECT set_config('request.jwt.claims',
  '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated","session_id":"eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"}',true);
SELECT throws_ok(
  $$SELECT private.security_require_current_auth_session('11111111-1111-4111-8111-111111111111')$$,
  '42501','AUTH_SESSION_INVALID',
  'session absente de auth.sessions : refusée'
);

SELECT set_config('request.jwt.claims',
  '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated","session_id":"malformed"}',true);
SELECT throws_ok(
  $$SELECT private.security_require_current_auth_session('11111111-1111-4111-8111-111111111111')$$,
  '42501','AUTH_SESSION_INVALID',
  'session_id mal formé : refusé'
);

SELECT set_config('request.jwt.claims',
  '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated"}',true);
SELECT throws_ok(
  $$SELECT private.security_require_current_auth_session('11111111-1111-4111-8111-111111111111')$$,
  '42501','AUTH_SESSION_INVALID',
  'session_id absent : refusé'
);

SELECT set_config('request.jwt.claims',
  '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated","session_id":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}',true);
SELECT throws_ok(
  $$SELECT private.security_require_current_auth_session('22222222-2222-4222-8222-222222222222')$$,
  '42501','AUTH_SESSION_INVALID',
  'paramètre de compte arbitraire différent de auth.uid() : refusé'
);

-- Simulation d'un sign-out : session supprimée de la table autoritaire.
DELETE FROM auth.sessions WHERE id='dddddddd-dddd-4ddd-8ddd-dddddddddddd';
SELECT set_config('request.jwt.claims',
  '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated","session_id":"dddddddd-dddd-4ddd-8ddd-dddddddddddd"}',true);
SELECT throws_ok(
  $$SELECT private.security_require_current_auth_session('11111111-1111-4111-8111-111111111111')$$,
  '42501','AUTH_SESSION_INVALID',
  'session supprimée : refusée'
);

-- Contrôle avant toute mutation pour les huit fonctions sensibles.
-- Une session inexistante doit produire l'erreur du nouveau garde,
-- même si les paramètres RPC sont par ailleurs inoffensifs ou invalides.
SELECT set_config('request.jwt.claims',
  '{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated","session_id":"eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"}',true);
SELECT throws_ok(
  $$SELECT sinjira_security_internal.security_after_password_recovery(NULL)$$,
  '42501','AUTH_SESSION_INVALID','récupération de compte bloquée sans session'
);
SELECT throws_ok(
  $$SELECT sinjira_security_internal.security_compromise_account(NULL)$$,
  '42501','AUTH_SESSION_INVALID','compromission de compte bloquée sans session'
);
SELECT throws_ok(
  $$SELECT sinjira_security_internal.security_report_lost_device('ffffffff-ffff-4fff-8fff-ffffffffffff')$$,
  '42501','AUTH_SESSION_INVALID','appareil perdu bloqué sans session'
);
SELECT throws_ok(
  $$SELECT sinjira_security_internal.security_resolve_connection_challenge(
      'ffffffff-ffff-4fff-8fff-ffffffffffff','fixture-key','approved')$$,
  '42501','AUTH_SESSION_INVALID','confirmation de connexion bloquée sans session'
);
SELECT throws_ok(
  $$SELECT sinjira_security_internal.security_resolve_connection_challenge_mfa(
      'ffffffff-ffff-4fff-8fff-ffffffffffff','fixture-key')$$,
  '42501','AUTH_SESSION_INVALID','confirmation MFA bloquée sans session'
);
SELECT throws_ok(
  $$SELECT sinjira_security_internal.security_revoke_device('ffffffff-ffff-4fff-8fff-ffffffffffff')$$,
  '42501','AUTH_SESSION_INVALID','révocation d’appareil bloquée sans session'
);
SELECT throws_ok(
  $$SELECT sinjira_security_internal.security_set_device_trust(
      'ffffffff-ffff-4fff-8fff-ffffffffffff',true,false)$$,
  '42501','AUTH_SESSION_INVALID','attribution de confiance bloquée sans session'
);
SELECT throws_ok(
  $$SELECT sinjira_security_internal.security_update_settings(
      NULL,NULL,NULL,NULL,NULL)$$,
  '42501','AUTH_SESSION_INVALID','paramètres de sécurité bloqués sans session'
);

-- Une simulation en rôle PostgREST « authenticated » : le contrôle pgTAP
-- lui-même continue sous le rôle de test, mais la RPC est réellement exécutée
-- avec les droits DB de l'utilisateur connecté. Aucune élévation ni SQL distant.
CREATE OR REPLACE FUNCTION pg_temp.authenticated_rpc_rejects_revoked_session(p_call text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path TO 'pg_catalog'
AS $rpc_role$
DECLARE
  v_denied boolean := false;
BEGIN
  EXECUTE 'SET LOCAL ROLE authenticated';
  IF current_user <> 'authenticated' THEN
    RAISE EXCEPTION 'TEST_ROLE_SWITCH_FAILED';
  END IF;
  BEGIN
    EXECUTE p_call;
  EXCEPTION WHEN SQLSTATE '42501' THEN
    v_denied := SQLERRM = 'AUTH_SESSION_INVALID';
  END;
  EXECUTE 'RESET ROLE';
  RETURN v_denied;
EXCEPTION WHEN OTHERS THEN
  EXECUTE 'RESET ROLE';
  RAISE;
END;
$rpc_role$;

-- Garde de révocation vérifiée au travers des 8 API publiques, non directement
-- dans le schéma interne et sans privilèges postgres pendant les appels.

SELECT ok(
  pg_temp.authenticated_rpc_rejects_revoked_session(
    $call$SELECT public.security_after_password_recovery(NULL)$call$
  ),
  'session révoquée : endpoint public security_after_password_recovery refusé sous rôle authenticated'
);

SELECT ok(
  pg_temp.authenticated_rpc_rejects_revoked_session(
    $call$SELECT public.security_compromise_account(NULL)$call$
  ),
  'session révoquée : endpoint public security_compromise_account refusé sous rôle authenticated'
);

SELECT ok(
  pg_temp.authenticated_rpc_rejects_revoked_session(
    $call$SELECT public.security_report_lost_device('ffffffff-ffff-4fff-8fff-ffffffffffff')$call$
  ),
  'session révoquée : endpoint public security_report_lost_device refusé sous rôle authenticated'
);

SELECT ok(
  pg_temp.authenticated_rpc_rejects_revoked_session(
    $call$SELECT public.security_resolve_connection_challenge('ffffffff-ffff-4fff-8fff-ffffffffffff','fixture-key','approved')$call$
  ),
  'session révoquée : endpoint public security_resolve_connection_challenge refusé sous rôle authenticated'
);

SELECT ok(
  pg_temp.authenticated_rpc_rejects_revoked_session(
    $call$SELECT public.security_resolve_connection_challenge_mfa('ffffffff-ffff-4fff-8fff-ffffffffffff','fixture-key')$call$
  ),
  'session révoquée : endpoint public security_resolve_connection_challenge_mfa refusé sous rôle authenticated'
);

SELECT ok(
  pg_temp.authenticated_rpc_rejects_revoked_session(
    $call$SELECT public.security_revoke_device('ffffffff-ffff-4fff-8fff-ffffffffffff')$call$
  ),
  'session révoquée : endpoint public security_revoke_device refusé sous rôle authenticated'
);

SELECT ok(
  pg_temp.authenticated_rpc_rejects_revoked_session(
    $call$SELECT public.security_set_device_trust('ffffffff-ffff-4fff-8fff-ffffffffffff',true,false)$call$
  ),
  'session révoquée : endpoint public security_set_device_trust refusé sous rôle authenticated'
);

SELECT ok(
  pg_temp.authenticated_rpc_rejects_revoked_session(
    $call$SELECT public.security_update_settings(NULL,NULL,NULL,NULL,NULL)$call$
  ),
  'session révoquée : endpoint public security_update_settings refusé sous rôle authenticated'
);

SELECT * FROM finish();
