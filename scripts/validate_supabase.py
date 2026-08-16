#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "gpvivleexywljowcqkru"
EXPECTED_SERVER_VERSION = "24.4.11"
MIGRATIONS = ROOT / "supabase" / "migrations"
FUNCTIONS = ROOT / "supabase" / "functions"
CONFIG = ROOT / "supabase" / "config.toml"
FRONTEND_CONFIG = ROOT / "assets" / "js" / "sinjira-supabase-config.js"
WORKFLOW = ROOT / ".github" / "workflows" / "supabase-production-preflight.yml"
CORS = FUNCTIONS / "_shared" / "cors.ts"

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

# Ces deux fonctions ont volontairement verify_jwt=false : elles effectuent leur propre
# contrôle. send-game-report autorise seulement la génération PDF anonyme; le courriel
# exige un utilisateur authentifié. get-document-url vérifie lui-même le niveau d'accès.
ALLOWED_VERIFY_JWT_FALSE = {"send-game-report", "get-document-url"}


def read(path: Path) -> str:
    return path.read_text("utf-8", errors="ignore")


def source_files() -> list[Path]:
    paths: list[Path] = []
    for root in (ROOT / "assets" / "js", FUNCTIONS):
        if root.exists():
            paths.extend(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".js", ".ts"})
    return paths


def find_created_relations(sql: str) -> tuple[set[str], set[str]]:
    table_rx = re.compile(
        r"\bcreate\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?([a-z_][a-z0-9_]*)",
        re.I,
    )
    view_rx = re.compile(
        r"\bcreate\s+(?:or\s+replace\s+)?(?:materialized\s+)?view\s+(?:public\.)?([a-z_][a-z0-9_]*)",
        re.I,
    )
    return {m.lower() for m in table_rx.findall(sql)}, {m.lower() for m in view_rx.findall(sql)}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not MIGRATIONS.exists():
        errors.append("Dossier supabase/migrations absent.")
        migrations: list[Path] = []
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

    sql_parts = [read(path) for path in migrations]
    sql = "\n".join(sql_parts)
    sql_lower = sql.lower()

    required_rpcs = {
        "get_sinjira_server_version",
        "get_sinjira_runtime_health",
        "fracture_engine_health",
        "fracture_engine_get_state",
        "fracture_engine_start",
        "fracture_engine_submit_keep",
        "fracture_engine_pick",
        "fracture_engine_submit_report",
        "fracture_engine_submit_accusation",
        "create_fracture_party",
        "join_fracture_party",
        "is_sinjira_admin",
        "ensure_sinjira_owner_character",
        "has_sinjira_product",
    }
    for required in sorted(required_rpcs):
        if required.lower() not in sql_lower:
            errors.append(f"RPC critique absente des migrations: {required}")

    if f"select '{EXPECTED_SERVER_VERSION}'::text" not in sql_lower:
        errors.append(f"Marqueur serveur attendu {EXPECTED_SERVER_VERSION} absent des migrations.")

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
    if "migration repair" in workflow.lower():
        errors.append("Le workflow de production ne doit jamais réparer automatiquement l'historique des migrations.")
    if "db push --linked --dry-run" not in workflow:
        errors.append("Le workflow de production doit effectuer un dry-run avant application.")
    if "inputs.apply == true" not in workflow:
        errors.append("Le workflow de production doit exiger un lancement manuel explicite avec apply=true pour toute écriture.")
    if "ÉTAT PRODUCTION" not in workflow:
        warnings.append("Le workflow devrait résumer explicitement si la production a été modifiée ou seulement prévisualisée.")

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

    false_jwt = set()
    for name, value in re.findall(
        r"\[functions\.([^\]]+)\]\s*\n\s*verify_jwt\s*=\s*(true|false)",
        config_text,
        re.I,
    ):
        if value.lower() == "false":
            false_jwt.add(name)
    unexpected_false = sorted(false_jwt - ALLOWED_VERIFY_JWT_FALSE)
    missing_false = sorted(ALLOWED_VERIFY_JWT_FALSE - false_jwt)
    if unexpected_false:
        errors.append("Edge Functions verify_jwt=false non autorisées: " + ", ".join(unexpected_false))
    if missing_false:
        warnings.append("Fonctions attendues avec authentification interne différentes de la configuration: " + ", ".join(missing_false))

    sources = source_files()
    source_text = "\n".join(read(path) for path in sources)

    custom_env: set[str] = set()
    env_re = re.compile(r"Deno\.env\.get\(['\"]([A-Z0-9_]+)['\"]\)")
    for path in sources:
        if path.suffix.lower() == ".ts":
            custom_env.update(env_re.findall(read(path)))
    custom_env -= DEFAULT_EDGE_ENV

    tables, views = find_created_relations(sql)
    defined_relations = tables | views
    storage_buckets = set(re.findall(r"\.storage\.from\(\s*['\"]([a-zA-Z0-9_-]+)['\"]", source_text))
    from_calls = set(re.findall(r"\.from\(\s*['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]", source_text))
    database_calls = {name.lower() for name in from_calls if name not in storage_buckets}
    missing_relations = sorted(database_calls - defined_relations)
    if missing_relations:
        errors.append("Relations Supabase utilisées par le code mais absentes des migrations: " + ", ".join(missing_relations))

    defined_rpcs = set(re.findall(
        r"\bcreate\s+(?:or\s+replace\s+)?function\s+(?:public\.)?([a-z_][a-z0-9_]*)\s*\(",
        sql,
        re.I,
    ))
    defined_rpcs = {name.lower() for name in defined_rpcs}
    called_rpcs = {name.lower() for name in re.findall(r"\.rpc\(\s*['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]", source_text)}
    missing_rpcs = sorted(called_rpcs - defined_rpcs)
    if missing_rpcs:
        errors.append("RPC appelées par le code mais absentes des migrations: " + ", ".join(missing_rpcs))

    invoked_edges = set(re.findall(r"\.functions\.invoke\(\s*['\"]([a-zA-Z0-9_-]+)['\"]", source_text))
    missing_edges = sorted(invoked_edges - set(function_dirs))
    if missing_edges:
        errors.append("Edge Functions invoquées mais absentes du dépôt: " + ", ".join(missing_edges))

    rls_enabled = set(re.findall(
        r"\balter\s+table\s+(?:if\s+exists\s+)?(?:public\.)?([a-z_][a-z0-9_]*)\s+enable\s+row\s+level\s+security",
        sql,
        re.I,
    ))
    rls_enabled = {name.lower() for name in rls_enabled}
    missing_rls = sorted(tables - rls_enabled)
    if missing_rls:
        errors.append("Tables applicatives sans activation RLS détectée: " + ", ".join(missing_rls))

    function_blocks = re.findall(
        r"(create\s+(?:or\s+replace\s+)?function\s+.*?\$\$;)",
        sql,
        re.I | re.S,
    )
    insecure_definers: list[str] = []
    for block in function_blocks:
        if "security definer" not in block.lower():
            continue
        if "set search_path" in block.lower():
            continue
        match = re.search(r"function\s+(?:public\.)?([a-z_][a-z0-9_]*)", block, re.I)
        insecure_definers.append(match.group(1) if match else "fonction_inconnue")
    if insecure_definers:
        errors.append("SECURITY DEFINER sans SET search_path explicite: " + ", ".join(sorted(set(insecure_definers))))

    if CORS.exists():
        cors_text = read(CORS)
        if "https://www.benoitcantin.com" not in cors_text:
            errors.append("CORS Edge Functions: origine de production SINJIRA absente.")
        if "Access-Control-Allow-Origin': '*'" in cors_text or 'Access-Control-Allow-Origin": "*"' in cors_text:
            errors.append("CORS Edge Functions trop permissif: origine * détectée.")
    else:
        errors.append("Fichier CORS partagé des Edge Functions absent.")

    tracked_env = [
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file() and p.name.startswith(".env") and ".git" not in p.parts
    ]
    if tracked_env:
        errors.append("Fichier(s) .env suivi(s) dans le dépôt: " + ", ".join(tracked_env))

    print(
        f"Validation Supabase profonde: {len(migrations)} migrations, "
        f"{len(tables)} tables, {len(defined_rpcs)} RPC, {len(function_dirs)} Edge Functions."
    )
    print(
        f"Contrats code: {len(database_calls)} relation(s), {len(called_rpcs)} RPC appelée(s), "
        f"{len(invoked_edges)} Edge Function(s) invoquée(s)."
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

    print("OK: structure, contrats et garde-fous Supabase cohérents pour le déploiement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
