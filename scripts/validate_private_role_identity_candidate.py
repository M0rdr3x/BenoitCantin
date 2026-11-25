#!/usr/bin/env python3
"""Valider sans BD un candidat SQL SECURITY DEFINER toujours rollback-only.

Ce garde statique n'est PAS une preuve de compatibilité des politiques RLS.
Il empêche cependant que le candidat sorte du périmètre de revue, perde
la liaison au JWT ou soit appliqué par une simple exécution accidentelle.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "security/candidates/private_admin_project_access_identity.sql"

EXPECTED_FUNCTIONS = {
    "private.is_sinjira_admin": (
        "p_user_id = auth.uid()",
        "p_user_id IS NOT NULL",
        "public.internal_admin_users",
    ),
    "private.project_access_rank": (
        "p_user_id IS NOT DISTINCT FROM auth.uid()",
        "private.is_sinjira_admin(p_user_id)",
        "public.project_access",
        "public.projects",
    ),
}
JWT_SERVICE_GUARD = "COALESCE((auth.jwt() ->> 'role') = 'service_role', false)"


def without_line_comments(source: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in source.splitlines())


def inspect_sql(source: str) -> list[str]:
    errors: list[str] = []
    sql = without_line_comments(source).strip()
    if not re.match(r"^BEGIN\s*;", sql, flags=re.I) or len(
        re.findall(r"(?im)^\s*BEGIN\s*;", sql)
    ) != 1:
        errors.append("Transaction explicite BEGIN unique obligatoire")
    if not re.search(r"ROLLBACK\s*;\s*$", sql, flags=re.I) or len(
        re.findall(r"(?im)^\s*ROLLBACK\s*;", sql)
    ) != 1:
        errors.append("ROLLBACK unique et final obligatoire : candidat non déployable")
    if re.search(
        r"\b(?:COMMIT|GRANT|REVOKE|INSERT|UPDATE|DELETE|TRUNCATE|DROP|ALTER|COPY|"
        r"SAVEPOINT|RELEASE|EXECUTE|CALL|SET\s+ROLE|START\s+TRANSACTION)\b",
        sql, flags=re.I
    ):
        errors.append("Commande de publication, de droits, dynamique ou destructrice interdite")
    chunks = re.split(r"(?i)\bCREATE OR REPLACE FUNCTION\s+", sql)
    if len(chunks) != 3:
        errors.append("Exactement deux fonctions privées doivent être remplacées")
        return errors

    for body, (name, markers) in zip(chunks[1:], EXPECTED_FUNCTIONS.items()):
        if not body.lower().lstrip().startswith(name.lower() + "("):
            errors.append("Fonction ou ordre inattendu : " + name)
        if "LANGUAGE sql" not in body:
            errors.append("LANGUAGE sql attendu : " + name)
        if "SECURITY DEFINER" not in body:
            errors.append("SECURITY DEFINER historique absent : " + name)
        if "SET search_path = ''" not in body:
            errors.append("search_path hermétique absent : " + name)
        if JWT_SERVICE_GUARD not in body:
            errors.append("Exception service_role basée sur JWT signé absente : " + name)
        for marker in markers:
            if marker not in body:
                errors.append("Garde d'identité ou requête historique absent : " + name + " / " + marker)
        if "DEFAULT auth.uid()" not in body.split("AS $function$", 1)[0]:
            errors.append("Signature avec défaut auth.uid perdue : " + name)
    return errors


PREFLIGHT = ROOT / "security/candidates/preflight_private_identity_catalog_read_only.sql"
# Exactitude du texte complet : aucun retrait de commentaires ni interprétation
# des littéraux SQL. Toute modification exige une nouvelle revue.
EXPECTED_PREFLIGHT = """-- Catalogue uniquement ; aucune lecture de données utilisateurs.
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
"""

def inspect_preflight(source: str) -> list[str]:
    if source != EXPECTED_PREFLIGHT:
        return ["Prévol catalogue différent de la requête lecture seule approuvée"]
    return []

def self_test_preflight(source: str) -> None:
    assert not inspect_preflight(source)
    mutations = (
        ("BEGIN TRANSACTION READ ONLY;", "BEGIN;"),
        ("ROLLBACK;", "COMMIT;"),
        ("count(a.name) <> 1", "count(a.name) < 1"),
        ("NOT bool_and(a.expected_acl)", "false"),
        ("a.definition_sha256 = e.definition_sha256", "true"),
        ("n.nspname = 'private'", "n.nspname = 'public'"),
        ("ROLLBACK;", "SELECT 1;\nROLLBACK;"),
        ("-- Catalogue uniquement", "-- Catalogue modifié"),
    )
    for before, after in mutations:
        assert before in source
        assert inspect_preflight(source.replace(before, after, 1)), before
    print("OK : 8 mutations du prévol catalogue refusées.")

def self_test(source: str) -> None:
    assert not inspect_sql(source), inspect_sql(source)
    mutations = (
        ("retirer rollback", "ROLLBACK;", "COMMIT;"),
        ("usurper admin", "OR p_user_id = auth.uid()", "OR TRUE"),
        ("usurper projet", "OR p_user_id IS NOT DISTINCT FROM auth.uid()", "OR TRUE"),
        ("retirer contrôle de recherche", "SET search_path = ''", "SET search_path = public"),
        ("ajouter privilège", "ROLLBACK;", "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA private TO anon;\nROLLBACK;"),
        ("retirer JWT", JWT_SERVICE_GUARD, "TRUE"),
        ("démarrer une deuxième transaction", "ROLLBACK;", "BEGIN;\nROLLBACK;"),
        ("terminer une transaction trop tôt", "CREATE OR REPLACE FUNCTION private.project_access_rank",
         "ROLLBACK;\nCREATE OR REPLACE FUNCTION private.project_access_rank"),
        ("ajouter une écriture", "ROLLBACK;", "UPDATE public.projects SET status='active';\nROLLBACK;"),
    )
    for name, original, changed in mutations:
        assert original in source, "Fixture absente : " + name
        mutant = source.replace(original, changed, 1)
        assert inspect_sql(mutant), "La mutation dangereuse est passée : " + name
    print("OK : 9 mutations SQL refusées, aucune application de migration.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not CANDIDATE.is_file() or CANDIDATE.is_symlink():
        print("ECHEC : candidat SQL absent ou lien symbolique")
        return 1
    try:
        source = CANDIDATE.read_text("utf-8", errors="strict")
    except (OSError, UnicodeError):
        print("ECHEC : candidat SQL illisible")
        return 1
    if len(source) > 50_000:
        print("ECHEC : candidat SQL anormalement volumineux")
        return 1
    if not PREFLIGHT.is_file() or PREFLIGHT.is_symlink():
        print("ECHEC : prévol catalogue absent ou lien symbolique")
        return 1
    try:
        preflight = PREFLIGHT.read_bytes().decode("utf-8", errors="strict")
    except (OSError, UnicodeError):
        print("ECHEC : prévol catalogue illisible")
        return 1
    if len(preflight) > 20_000 or inspect_preflight(preflight):
        print("ECHEC : prévol catalogue non conforme")
        return 1
    if args.self_test:
        self_test_preflight(preflight)
        self_test(source)
        return 0
    errors = inspect_sql(source)
    if errors:
        for error in errors:
            print("ECHEC : " + error)
        return 1
    print("OK : deux fonctions privées liées à l'identité JWT, rollback final, aucun déploiement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
