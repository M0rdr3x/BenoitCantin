#!/usr/bin/env python3
"""Refuser les nouvelles migrations SQL qui exposent un objet API par défaut.

Le catalogue PostgreSQL de production attribue encore des privilèges
automatiques élevés aux rôles anon/authenticated sur de futurs objets.
Ce scanner de prévention est statique et n'interroge jamais une base.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase" / "migrations"
MAX_BYTES = 2 * 1024 * 1024
SHA_RE = re.compile(r"^[a-fA-F0-9]{40}$")

CREATE_TABLE = re.compile(
    r"\bCREATE\s+(?:UNLOGGED\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
    r'(?P<name>(?:"?[\w]+"?\.)?"?[\w]+"?)\s*\(', re.I
)
CREATE_FUNCTION = re.compile(
    r"\bCREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+"
    r'(?P<name>(?:"?[\w]+"?\.)?"?[\w]+"?)\s*\(', re.I
)


def strip_comments(sql: str) -> str:
    # Retirer les commentaires SQL simples; les commentaires bloc sont
    # également pris en charge. Ne remplace pas un parseur SQL complet.
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


def has_revoke(sql: str, kind: str, qualified_name: str) -> bool:
    escaped = re.escape(qualified_name)
    # Postgres permet REVOKE ALL et REVOKE ALL PRIVILEGES; les trois rôles
    # publics doivent être explicitement révoqués (ordre indifférent).
    pattern = re.compile(
        rf"\bREVOKE\s+ALL(?:\s+PRIVILEGES)?\s+ON\s+"
        rf"(?:{kind}\s+)?{escaped}"
        rf"(?:\s*\([^;]*?\))?\s+FROM\s+(?P<roles>[^;]+);",
        re.I | re.S,
    )
    for found in pattern.finditer(sql):
        roles = {token.strip().strip('"').lower() for token in found.group("roles").split(",")}
        if {"public", "anon", "authenticated"} <= roles and "service_role" not in roles:
            return True
    return False


def inspect_sql(source: str) -> list[str]:
    errors: list[str] = []
    sql = strip_comments(source).replace('"', "")
    for match in CREATE_TABLE.finditer(sql):
        name = match.group("name").lower()
        if "." not in name:
            errors.append(f"CREATE TABLE sans schéma explicite : {name}")
            continue
        if not name.startswith("public."):
            # Cette garde est propre à l'API publique. Les schémas
            # internes sont contrôlés par leurs contrats séparés.
            continue
        rls = rf"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?{re.escape(name)}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY\b"
        if not re.search(rls, sql, re.I):
            errors.append(f"RLS non activée dans la même migration : {name}")
        if not has_revoke(sql, "TABLE", name):
            errors.append(f"REVOKE ALL des rôles publics absent sur la table : {name}")

    for match in CREATE_FUNCTION.finditer(sql):
        name = match.group("name").lower()
        if "." not in name:
            errors.append(f"CREATE FUNCTION sans schéma explicite : {name}")
            continue
        if not name.startswith("public."):
            continue
        if not has_revoke(sql, "FUNCTION", name):
            errors.append(f"REVOKE ALL des rôles publics absent sur la fonction : {name}")
    return errors


def changed_migrations(base_ref: str) -> list[Path]:
    if not SHA_RE.fullmatch(base_ref):
        raise ValueError("Base Git invalide : SHA hexadécimal de 40 caractères requis")
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=AM", base_ref, "HEAD", "--", "supabase/migrations/"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError("Impossible de déterminer les migrations modifiées")
    files: list[Path] = []
    for line in result.stdout.splitlines():
        rel = Path(line)
        if rel.parent.as_posix() != "supabase/migrations" or rel.suffix != ".sql":
            raise ValueError("Chemin migration inattendu dans le diff Git")
        file = (ROOT / rel)
        if not file.is_file() or file.is_symlink():
            raise ValueError("Migration absente ou lien symbolique")
        files.append(file)
    return files


def self_test() -> None:
    table = (
        "CREATE TABLE public.example (id uuid primary key);\n"
        "ALTER TABLE public.example ENABLE ROW LEVEL SECURITY;\n"
        "REVOKE ALL ON TABLE public.example FROM anon, authenticated, PUBLIC;\n"
    )
    function = (
        "CREATE OR REPLACE FUNCTION public.example() RETURNS boolean "
        "LANGUAGE SQL AS $$ SELECT true $$;\n"
        "REVOKE ALL ON FUNCTION public.example() FROM authenticated, PUBLIC, anon;\n"
    )
    assert inspect_sql(table + function) == []
    mutants = (
        table.replace("ENABLE ROW LEVEL SECURITY", "DISABLE ROW LEVEL SECURITY"),
        table.replace("REVOKE ALL ON TABLE", "GRANT ALL ON TABLE"),
        table.replace("anon, authenticated, PUBLIC", "anon"),
        table.replace("PUBLIC;", "PUBLIC, service_role;"),
        table.replace("public.example", "example"),
        function.replace("REVOKE ALL ON FUNCTION", "GRANT EXECUTE ON FUNCTION"),
        function.replace("authenticated, PUBLIC, anon", "authenticated"),
    )
    for candidate in mutants:
        assert inspect_sql(candidate), "Une migration dangereuse n'a pas été rejetée"
    assert not inspect_sql("-- CREATE TABLE public.fake();\n" + table)
    print(f"OK : {len(mutants)} mutations SQL refusées et deux objets explicites acceptés.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base-ref")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.base_ref:
        parser.error("--base-ref requis pour la vérification Git")
    try:
        paths = changed_migrations(args.base_ref)
    except (ValueError, RuntimeError) as exc:
        print("ECHEC : " + str(exc))
        return 1
    errors = []
    for path in paths:
        if path.stat().st_size > MAX_BYTES:
            errors.append(path.name + " : fichier SQL trop volumineux")
            continue
        try:
            sql = path.read_text("utf-8", errors="strict")
        except (OSError, UnicodeError):
            errors.append(path.name + " : SQL illisible")
            continue
        errors.extend(f"{path.name} : {msg}" for msg in inspect_sql(sql))
    if errors:
        for error in errors:
            print("ECHEC : " + error)
        return 1
    print(f"OK : {len(paths)} migrations ajoutées/modifiées; aucun CREATE public non borné détecté.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
