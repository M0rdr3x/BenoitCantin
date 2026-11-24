-- Prévol exclusivement en lecture seule. Ne lit que le catalogue PostgreSQL.
-- Exécuter sur la cible prévue AVANT de préparer une migration, jamais comme migration.
-- Toute ligne autre que MATCH_ORIGINAL est un NO-GO : revue et réconciliation requises.
BEGIN TRANSACTION READ ONLY;
WITH expected(name, definition_sha256) AS (
  VALUES
    ('security_after_password_recovery', '1ced27350a3f05818e3bfebb03ebd5791fc9a5e0e566505a0d4c99ce79596a3a'),
    ('security_compromise_account', '264a472bdd9f23df25aa9d26adaf00601e2a6a49f852c86bdb4253f3d16d8394'),
    ('security_report_lost_device', 'a8e31f1f9c68a6d4ec06fe78f52ebc81823b69d47f1e67bf227175c93b6b28f4'),
    ('security_resolve_connection_challenge', 'ca24404955fb7ee9a3c0f75e6171beb0e7000f00841e256070802b0d31c09f07'),
    ('security_resolve_connection_challenge_mfa', '41717bb023f0415f8a986e7cf7b5f704e587e4d8877d39a3bc715f2fe0f35c10'),
    ('security_revoke_device', 'fcdf34e4f92a076cd3e8237a6ec17b4d9a784ed6ae116305a8595a7ab5340bbd'),
    ('security_set_device_trust', '9993426ee89dff625687c09a529776d1b9f3809412f3affa3945b26a83179c84'),
    ('security_update_settings', 'c11672c4df85e1a1ee3bb9e26b7bdfe46a2fd6776aa5f8062bc8dad5ba3a9dc2')
), actual AS (
  SELECT p.proname::text AS name,
         pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
           pg_catalog.regexp_replace(pg_catalog.pg_get_functiondef(p.oid),
             '^[[:space:]]+|[[:space:]]+$','','g'), 'UTF8')), 'hex') AS definition_sha256,
         position('private.security_require_current_auth_session'
           in pg_catalog.pg_get_functiondef(p.oid)) > 0 AS guard_present
  FROM pg_catalog.pg_proc p
  JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'sinjira_security_internal'
    AND p.proname::text IN (SELECT name FROM expected)
)
SELECT e.name,
       CASE
         WHEN count(a.name) = 0 THEN 'MISSING'
         WHEN count(a.name) <> 1 THEN 'AMBIGUOUS_OVERLOAD'
         WHEN bool_or(a.guard_present) THEN 'GUARD_ALREADY_PRESENT_REVIEW'
         WHEN bool_and(a.definition_sha256 = e.definition_sha256) THEN 'MATCH_ORIGINAL'
         ELSE 'DEFINITION_DRIFT'
       END AS status
FROM expected e
LEFT JOIN actual a ON a.name = e.name
GROUP BY e.name
ORDER BY e.name;
ROLLBACK;
