-- Catalogue uniquement ; aucune lecture de données utilisateurs.
-- Toute ligne autre que MATCH_ORIGINAL ou un nombre différent de deux lignes = NO-GO.
-- Ne jamais utiliser comme migration. Les droits historiques sont comparés, pas approuvés.
BEGIN TRANSACTION READ ONLY;
WITH expected(name, signature, definition_sha256) AS (
  VALUES
    ('is_sinjira_admin', 'p_user_id uuid', '5e3df1425976db0252e8c3b544929f60038d02581f4226d684819c7c4a347c06'),
    ('project_access_rank', 'p_project_id uuid, p_user_id uuid', 'efc5da4d75817740e4e3ab12d84124fd4638c32d0d4df75b8496d07bfa08d4a3')
), actual AS (
  SELECT p.proname::text AS name,
         pg_catalog.pg_get_function_identity_arguments(p.oid) AS signature,
         pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
           pg_catalog.regexp_replace(pg_catalog.pg_get_functiondef(p.oid),
             '^[[:space:]]+|[[:space:]]+$','','g'), 'UTF8')), 'hex') AS definition_sha256,
         p.prosecdef AND pg_catalog.pg_get_userbyid(p.proowner) = 'postgres'
           AND pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE')
           AND pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE')
           AND pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE') AS expected_acl
  FROM pg_catalog.pg_proc p
  JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'private' AND p.proname::text IN (SELECT name FROM expected)
)
SELECT e.name,
       CASE
         WHEN count(a.name) = 0 THEN 'MISSING'
         WHEN count(a.name) <> 1 THEN 'AMBIGUOUS_OVERLOAD'
         WHEN NOT bool_and(a.signature = e.signature) THEN 'SIGNATURE_DRIFT'
         WHEN NOT bool_and(a.expected_acl) THEN 'PRIVILEGE_DRIFT'
         WHEN bool_and(a.definition_sha256 = e.definition_sha256) THEN 'MATCH_ORIGINAL'
         ELSE 'DEFINITION_DRIFT'
       END AS status
FROM expected e LEFT JOIN actual a ON a.name = e.name
GROUP BY e.name ORDER BY e.name;
ROLLBACK;
