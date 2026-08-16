#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "gpvivleexywljowcqkru"
MIGRATIONS = ROOT / "supabase" / "migrations"
FUNCTIONS = ROOT / "supabase" / "functions"
CONFIG = ROOT / "supabase" / "config.toml"
FRONTEND_CONFIG = ROOT / "assets" / "js" / "sinjira-supabase-config.js"
WORKFLOW = ROOT / ".github" / "workflows" / "supabase-production-preflight.yml"

DEFAULT_EDGE_ENV = {
    "SUPABASE_URL",
    "SUPABASE_DB_URL",
    "SUPABASE_PUBLISHABLE_KEYS",
    "SUPABASE_SECRET_KEYS",
    "SUPABASE_JWKS",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SB_REGION",
    "SB_EXECUTION_ID",
    "DENO_DEPLOYMENT_ID",
}


def read(path: Path) -> str:
    return path.read_text("utf-8", errors="ignore")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not MIGRATIONS.exists():
        errors.append("Dossier supabase/migrations absent.")
        migrations = []
    else:
        migrations = sorted(MIGRATIONS.glob("*.sql"))

    versions: list[str] = []
    migration_re = re.compile(r"^(\d{14})_([a-z0-9_]+)\.sql$")
    for path in migrations:
        match = migration_re.match(path.name)
        if not match:
            errors.append(
                f"Migration mal nommée: {path.name}. Format requis: YYYYMMDDHHMMSS_nom.sql"
            )
            continue
        versions.append(match.group(1))

    duplicate_versions = sorted({v for v in versions if versions.count(v) > 1})
    if duplicate_versions:
        errors.append("Versions de migration dupliquées: " + ", ".join(duplicate_versions))
    if versions != sorted(versions):
        errors.append("Les migrations ne sont pas ordonnées chronologiquement par leur timestamp.")

    sql = "\n".join(read(path) for path in migrations)
    for required in (
        "get_sinjira_server_version",
        "fracture_engine_health",
        "fracture_engine_get_state",
        "is_sinjira_admin",
        "ensure_sinjira_owner_character",
        "has_sinjira_product",
    ):
        if required.lower() not in sql.lower():
            errors.append(f"RPC critique absente des migrations: {required}")

    config_text = read(CONFIG) if CONFIG.exists() else ""
    if f'project_id = "{PROJECT_ID}"' not in config_text:
        errors.append("supabase/config.toml ne pointe pas vers le projet de production attendu.")

    frontend = read(FRONTEND_CONFIG) if FRONTEND_CONFIG.exists() else ""
    if f"https://{PROJECT_ID}.supabase.co" not in frontend:
        errors.append("La configuration navigateur ne pointe pas vers le bon projet Supabase.")
    if "sb_publishable_" not in frontend:
        errors.append("La configuration navigateur doit utiliser une clé Supabase publiable moderne.")
    if "service_role" in frontend.lower() or "SUPABASE_SECRET_KEYS" in frontend:
        errors.append("Une clé serveur Supabase ne doit jamais apparaître dans la configuration navigateur.")

    workflow = read(WORKFLOW) if WORKFLOW.exists() else ""
    for required in ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD", PROJECT_ID):
        if required not in workflow:
            errors.append(f"Workflow Supabase incomplet: {required} absent.")

    function_dirs = sorted(
        p.name for p in FUNCTIONS.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    ) if FUNCTIONS.exists() else []
    configured_functions = sorted(set(re.findall(r"^\[functions\.([^\]]+)\]", config_text, re.M)))
    missing_config = sorted(set(function_dirs) - set(configured_functions))
    stale_config = sorted(set(configured_functions) - set(function_dirs))
    if missing_config:
        errors.append("Edge Functions sans configuration config.toml: " + ", ".join(missing_config))
    if stale_config:
        errors.append("Entrées config.toml sans dossier Edge Function: " + ", ".join(stale_config))

    custom_env: set[str] = set()
    if FUNCTIONS.exists():
        env_re = re.compile(r"Deno\.env\.get\(['\"]([A-Z0-9_]+)['\"]\)")
        for path in FUNCTIONS.rglob("*.ts"):
            custom_env.update(env_re.findall(read(path)))
    custom_env -= DEFAULT_EDGE_ENV

    tracked_env = [
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file() and p.name.startswith(".env") and ".git" not in p.parts
    ]
    if tracked_env:
        errors.append("Fichier(s) .env suivi(s) dans le dépôt: " + ", ".join(tracked_env))

    print(
        f"Validation Supabase: {len(migrations)} migrations, "
        f"{len(function_dirs)} Edge Functions, {len(custom_env)} variable(s) personnalisée(s)."
    )
    if custom_env:
        print("Variables Edge personnalisées détectées: " + ", ".join(sorted(custom_env)))
    for warning in warnings:
        print("AVERTISSEMENT: " + warning)

    if errors:
        print(f"ECHEC Supabase: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print("OK: structure Supabase cohérente pour le déploiement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
