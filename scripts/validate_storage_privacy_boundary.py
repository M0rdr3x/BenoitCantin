#!/usr/bin/env python3
"""Frontière de confidentialité SINJIRA Storage : SQL historique + état distant.

N'inclut ni noms d'objets, ni identifiants de comptes, ni contenu de fichiers.
Les contrôles CI ne nécessitent aucun jeton Supabase. L'état distant est validé
uniquement depuis un JSON issu d'une requête en lecture seule, hors des PR.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase/migrations"
PRIVATE = frozenset({
    "sinjira-private-documents",
    "sinjira-life-story-exports",
    "sinjira-character-sources",
    "sinjira-character-submissions",
})
PUBLIC = frozenset({"sinjira-avatars"})
ALL_EXPECTED = PRIVATE | PUBLIC
# Écart documenté en production : bucket privé effectivement présent et borné
# par RLS, mais absent du dépôt de migrations (voir issue de sécurité #716).
# Exception de TRAÇABILITÉ uniquement, jamais autorisation de le rendre public.
PRODUCTION_ONLY_BUCKETS = frozenset({"sinjira-character-submissions"})

# Une seule ligne, aucun nom d'objet; le serveur répond uniquement par booléens.
QUERY = """
SELECT
  (SELECT count(*) = 4
   FROM storage.buckets
   WHERE id IN (
     'sinjira-private-documents','sinjira-life-story-exports',
     'sinjira-character-sources','sinjira-character-submissions'
   ) AND NOT public) AS private_buckets_safe,
  (SELECT count(*) = 1
   FROM storage.buckets
   WHERE id = 'sinjira-avatars' AND public) AS avatars_public_only,
  (SELECT count(*) = 0
   FROM storage.buckets
   WHERE id LIKE 'sinjira-%'
     AND public
     AND id <> 'sinjira-avatars') AS no_unreviewed_public_bucket,
  (SELECT c.relrowsecurity
   FROM pg_catalog.pg_class c
   JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'storage' AND c.relname = 'objects'
   AND c.relkind IN ('r','p')) AS object_rls_on
""".strip()

EXPECTED_FLAGS = frozenset({
    "private_buckets_safe", "avatars_public_only",
    "no_unreviewed_public_bucket", "object_rls_on",
})


def validate_snapshot(data: object) -> list[str]:
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        return ["Réponse de sécurité Storage invalide ou absente"]
    row = data[0]
    if set(row) != EXPECTED_FLAGS:
        return ["Colonnes d'audit Storage inattendues"]
    return [f"Frontière Storage non confirmée : {key}"
            for key in sorted(EXPECTED_FLAGS) if row[key] is not True]


def strip_sql_comments(sql: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def migration_errors(files: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if not files:
        return ["Aucune migration SQL à inspecter."]
    corpus = "\n".join(strip_sql_comments(content) for content in files.values())
    for bucket in sorted(ALL_EXPECTED - PRODUCTION_ONLY_BUCKETS):
        if "'" + bucket + "'" not in corpus:
            errors.append(f"Bucket SINJIRA historique absent : {bucket}")
    statements = re.findall(
        r"(?is)\b(?:insert\s+into|update)\s+storage\.buckets\b[^;]*;",
        corpus,
    )
    for statement in statements:
        normalized = re.sub(r"\s+", "", statement.lower())
        # Échec conservateur si une même écriture manipule une zone privée et
        # publie une quelconque ligne; séparer les écritures pour audit humain.
        if any("'" + bucket + "'" in statement.lower() for bucket in PRIVATE):
            if re.search(r"\bpublic\s*=\s*true\b", statement, re.I) or re.search(
                r",\s*true\s*[,)]", statement, re.I
            ):
                errors.append("Une migration rend potentiellement public un bucket privé.")
        # Refuser les nouveaux buckets SINJIRA publics par défaut, sauf avatars.
        if "storage.buckets" in statement.lower() and re.search(r"\bpublic\s*=\s*true\b", statement, re.I):
            if "sinjira-avatars" not in statement.lower():
                errors.append("Publication Storage sans allowlist avatars.")
        if "storage.buckets" in statement.lower() and re.search(r"'sinjira-[^']+'", statement, re.I):
            # Tout ajout explicite d'un nouveau bucket avec un booléen public
            # dans VALUES doit avoir une revue, et non être déployé implicitement.
            ids = set(re.findall(r"'(sinjira-[a-z0-9-]+)'", statement.lower()))
            if ids - ALL_EXPECTED:
                errors.append("Nouvel identifiant bucket SINJIRA non revu : " + ", ".join(sorted(ids - ALL_EXPECTED)))
    return sorted(set(errors))


def repository_errors(root: Path = ROOT) -> list[str]:
    if not (root / "supabase/migrations").is_dir():
        return ["Répertoire de migrations absent"]
    files = {}
    for path in sorted((root / "supabase/migrations").glob("*.sql")):
        if path.is_symlink():
            return ["Migration SQL symbolique refusée"]
        try:
            files[path.name] = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            return ["Migration SQL illisible"]
    return migration_errors(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-repository", action="store_true")
    group.add_argument("--check-snapshot", type=Path)
    group.add_argument("--write-query", type=Path)
    args = parser.parse_args()
    if args.write_query:
        args.write_query.write_text(json.dumps({"query": QUERY}) + "\n", encoding="utf-8")
        print("PASS: SQL de vérification Storage en lecture seule préparé.")
        return 0
    if args.check_repository:
        errors = repository_errors()
    else:
        try:
            payload = json.loads(args.check_snapshot.read_text(encoding="utf-8"))
            errors = validate_snapshot(payload)
        except (OSError, UnicodeError, ValueError):
            errors = ["Réponse distante Storage non interprétable"]
    if errors:
        for error in errors:
            print("NO_GO: " + error, file=sys.stderr)
        return 1
    print("PASS: confidentialité des buckets SINJIRA vérifiée (périmètre du contrôle).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
