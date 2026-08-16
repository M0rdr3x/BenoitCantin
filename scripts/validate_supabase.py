#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "gpvivleexywljowcqkru"
EXPECTED_SERVER_VERSION = "24.4.11"
SUPABASE_JS_VERSION = "2.112.3"
MIGRATIONS = ROOT / "supabase" / "migrations"
FUNCTIONS = ROOT / "supabase" / "functions"
CONFIG = ROOT / "supabase" / "config.toml"
FRONTEND_CONFIG = ROOT / "assets" / "js" / "sinjira-supabase-config.js"
FRONTEND_CLIENT = ROOT / "assets" / "js" / "sinjira-supabase.js"
WORKFLOW = ROOT / ".github" / "workflows" / "supabase-production-preflight.yml"
CORS = FUNCTIONS / "_shared" / "cors.ts"
SHARED_AUTH = FUNCTIONS / "_shared" / "auth.ts"
PUBLIC_CHARACTER = FUNCTIONS / "submit-character-questionnaire" / "index.ts"
ADMIN_CHARACTER = FUNCTIONS / "admin-sinjira-v18" / "index.ts"
ADMIN_SOCIAL = FUNCTIONS / "admin-social-v20" / "index.ts"
SOCIAL_INTEGRITY = MIGRATIONS / "20260816130000_sinjira_v24_4_11_social_report_integrity.sql"

DEFAULT_EDGE_ENV = {
    "SUPABASE_URL", "SUPABASE_DB_URL", "SUPABASE_PUBLISHABLE_KEYS",
    "SUPABASE_SECRET_KEYS", "SUPABASE_JWKS", "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY", "SB_REGION", "SB_EXECUTION_ID",
    "DENO_DEPLOYMENT_ID",
}
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
    table_rx = re.compile(r"\bcreate\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?([a-z_][a-z0-9_]*)", re.I)
    view_rx = re.compile(r"\bcreate\s+(?:or\s+replace\s+)?(?:materialized\s+)?view\s+(?:public\.)?([a-z_][a-z0-9_]*)", re.I)
    return {m.lower() for m in table_rx.findall(sql)}, {m.lower() for m in view_rx.findall(sql)}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    migrations = sorted(MIGRATIONS.glob("*.sql")) if MIGRATIONS.exists() else []
    if not migrations:
        errors.append("Dossier supabase/migrations absent ou vide.")

    versions: list[str] = []
    migration_re = re.compile(r"^(\d{14})_([a-z0-9_]+)\.sql$")
    for path in migrations:
        match = migration_re.match(path.name)
        if not match:
            errors.append(f"Migration mal nommée: {path.name}. Format requis: YYYYMMDDHHMMSS_nom.sql")
            continue
        versions.append(match.group(1))
    duplicate_versions = sorted({v for v in versions if versions.count(v) > 1})
    if duplicate_versions:
        errors.append("Versions de migration dupliquées: " + ", ".join(duplicate_versions))
    if versions != sorted(versions):
        errors.append("Les migrations ne sont pas ordonnées chronologiquement par leur timestamp.")

    sql = "\n".join(read(path) for path in migrations)
    sql_lower = sql.lower()
    required_rpcs = {
        "get_sinjira_server_version", "fracture_engine_health", "fracture_engine_get_state",
        "fracture_engine_start", "fracture_engine_submit_keep", "fracture_engine_pick",
        "fracture_engine_submit_report", "fracture_engine_submit_accusation",
        "create_fracture_party", "join_fracture_party", "is_sinjira_admin",
        "ensure_sinjira_owner_character", "has_sinjira_product",
    }
    for required in sorted(required_rpcs):
        if required.lower() not in sql_lower:
            errors.append(f"RPC critique absente des migrations: {required}")
    if f"select '{EXPECTED_SERVER_VERSION}'::text" not in sql_lower:
        errors.append(f"Marqueur serveur attendu {EXPECTED_SERVER_VERSION} absent des migrations.")
    if "create or replace function public.canonicalize_social_report" not in sql_lower:
        errors.append("La canonicalisation serveur des signalements sociaux V24.4.11 est absente.")
    if "before insert on public.social_reports" not in sql_lower:
        errors.append("Le trigger BEFORE INSERT des signalements sociaux est absent.")

    social_sql = read(SOCIAL_INTEGRITY) if SOCIAL_INTEGRITY.exists() else ""
    social_lower = social_sql.lower()
    if "create table if not exists public.social_report_targets" not in social_lower:
        errors.append("La table privée social_report_targets est absente de la migration V24.4.11.")
    if "after insert on public.social_reports" not in social_lower or "persist_social_report_target" not in social_lower:
        errors.append("Le mapping serveur privé des cibles de signalement n'est pas persisté après insertion.")
    if "alter table public.social_report_targets enable row level security" not in social_lower:
        errors.append("RLS absent sur social_report_targets.")
    if "revoke all on public.social_report_targets from public,anon,authenticated" not in social_lower:
        errors.append("social_report_targets doit être inaccessible aux rôles navigateur.")
    # Le snapshot d'un signalement narratif est lisible par son déclarant. Il ne doit donc
    # jamais embarquer l'UUID du compte réel derrière le personnage.
    char_section = social_sql.split("elsif new.network='character'", 1)[1] if "elsif new.network='character'" in social_sql else ""
    char_section = char_section.split("return new;", 1)[0]
    if re.search(r"new\.snapshot\s*:=\s*jsonb_build_object\([^;]*?'(?:user_id|sender_user_id|recipient_user_id)'", char_section, re.I | re.S):
        errors.append("Un snapshot de réseau personnage expose encore un UUID de compte réel.")

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

    browser_client = read(FRONTEND_CLIENT) if FRONTEND_CLIENT.exists() else ""
    expected_browser_import = f"@supabase/supabase-js@{SUPABASE_JS_VERSION}/+esm"
    if expected_browser_import not in browser_client:
        errors.append(f"Le client navigateur Supabase doit être épinglé exactement sur {SUPABASE_JS_VERSION}.")
    shared_auth = read(SHARED_AUTH) if SHARED_AUTH.exists() else ""
    if f"npm:@supabase/supabase-js@{SUPABASE_JS_VERSION}" not in shared_auth:
        errors.append(f"Le client Supabase des Edge Functions doit être épinglé exactement sur {SUPABASE_JS_VERSION}.")

    workflow = read(WORKFLOW) if WORKFLOW.exists() else ""
    for required in ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD", PROJECT_ID):
        if required not in workflow:
            errors.append(f"Workflow Supabase incomplet: {required} absent.")
    if "migration repair" in workflow.lower():
        errors.append("Le workflow de production ne doit jamais réparer automatiquement l'historique des migrations.")
    if "db push --linked --dry-run" not in workflow:
        errors.append("Le workflow de production doit effectuer un dry-run avant application.")
    if "db lint --linked --schema public --level error --fail-on error" not in workflow:
        errors.append("Le workflow doit exécuter le lint SQL distant avant/après migrations.")
    if 'SINJIRA_CHARACTER_AI_ENABLED=false' not in workflow:
        errors.append("Le workflow de production doit maintenir explicitement l'IA de personnage désactivée.")

    function_dirs = sorted(p.name for p in FUNCTIONS.iterdir() if p.is_dir() and not p.name.startswith("_")) if FUNCTIONS.exists() else []
    configured_functions = sorted(set(re.findall(r"^\[functions\.([^\]]+)\]", config_text, re.M)))
    missing_config = sorted(set(function_dirs) - set(configured_functions))
    stale_config = sorted(set(configured_functions) - set(function_dirs))
    if missing_config:
        errors.append("Edge Functions sans configuration config.toml: " + ", ".join(missing_config))
    if stale_config:
        errors.append("Entrées config.toml sans dossier Edge Function: " + ", ".join(stale_config))

    false_jwt = {name for name, value in re.findall(r"\[functions\.([^\]]+)\]\s*\n\s*verify_jwt\s*=\s*(true|false)", config_text, re.I) if value.lower() == "false"}
    unexpected_false = sorted(false_jwt - ALLOWED_VERIFY_JWT_FALSE)
    missing_false = sorted(ALLOWED_VERIFY_JWT_FALSE - false_jwt)
    if unexpected_false:
        errors.append("Edge Functions verify_jwt=false non autorisées: " + ", ".join(unexpected_false))
    if missing_false:
        warnings.append("Fonctions attendues avec authentification interne différentes de la configuration: " + ", ".join(missing_false))

    sources = source_files()
    source_text = "\n".join(read(path) for path in sources)

    # Dépendances Supabase : aucune plage flottante @2 n'est acceptée.
    floating_patterns = [
        r"@supabase/supabase-js@2(?:/|['\"])",
        r"@supabase/supabase-js@\^2",
        r"@supabase/supabase-js@~2",
    ]
    for path in sources:
        text = read(path)
        rel = path.relative_to(ROOT).as_posix()
        if any(re.search(pattern, text) for pattern in floating_patterns):
            errors.append(f"Dépendance Supabase JS flottante dans {rel}.")
        if path.suffix.lower() == ".ts" and path != SHARED_AUTH:
            if re.search(r"\bcreateClient\s*\(", text) or "SUPABASE_SERVICE_ROLE_KEY" in text or "SUPABASE_SECRET_KEYS" in text:
                errors.append(f"Edge Function contournant _shared/auth.ts: {rel}")

    # IA de personnage : clé seule insuffisante. Le flag doit rester opt-in explicite.
    for path in (PUBLIC_CHARACTER, ADMIN_CHARACTER):
        text = read(path) if path.exists() else ""
        rel = path.relative_to(ROOT).as_posix()
        if "SINJIRA_CHARACTER_AI_ENABLED" not in text or "characterAiEnabled" not in text:
            errors.append(f"Garde-fou IA serveur absent dans {rel}")
        if "OPENAI_API_KEY" in text and "CHARACTER_AI_DISABLED" not in text:
            errors.append(f"IA potentiellement activable sans refus explicite dans {rel}")

    admin_social = read(ADMIN_SOCIAL) if ADMIN_SOCIAL.exists() else ""
    if "authoritativeTargetUser" not in admin_social:
        errors.append("La modération sociale ne résout pas la cible depuis les tables autoritaires.")
    if "social_report_targets" not in admin_social:
        errors.append("La modération sociale n'utilise pas le mapping privé de cible V24.4.11.")
    if re.search(r"snap\.(?:user_id|sender_user_id|character_id|sender_character_id)", admin_social):
        errors.append("La modération sociale fait encore confiance au snapshot fourni par le signalement.")
    for action in ("resolve_social_report", "remove_reported_content", "suspend_reported_user"):
        if action not in admin_social:
            errors.append(f"Audit de modération manquant: {action}")

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

    defined_rpcs = {name.lower() for name in re.findall(r"\bcreate\s+(?:or\s+replace\s+)?function\s+(?:public\.)?([a-z_][a-z0-9_]*)\s*\(", sql, re.I)}
    called_rpcs = {name.lower() for name in re.findall(r"\.rpc\(\s*['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]", source_text)}
    missing_rpcs = sorted(called_rpcs - defined_rpcs)
    if missing_rpcs:
        errors.append("RPC appelées par le code mais absentes des migrations: " + ", ".join(missing_rpcs))

    invoked_edges = set(re.findall(r"\.functions\.invoke\(\s*['\"]([a-zA-Z0-9_-]+)['\"]", source_text))
    missing_edges = sorted(invoked_edges - set(function_dirs))
    if missing_edges:
        errors.append("Edge Functions invoquées mais absentes du dépôt: " + ", ".join(missing_edges))

    rls_enabled = {name.lower() for name in re.findall(r"\balter\s+table\s+(?:if\s+exists\s+)?(?:public\.)?([a-z_][a-z0-9_]*)\s+enable\s+row\s+level\s+security", sql, re.I)}
    missing_rls = sorted(tables - rls_enabled)
    if missing_rls:
        errors.append("Tables applicatives sans activation RLS détectée: " + ", ".join(missing_rls))

    function_blocks = re.findall(r"(create\s+(?:or\s+replace\s+)?function\s+.*?\$\$;)", sql, re.I | re.S)
    insecure_definers: list[str] = []
    for block in function_blocks:
        if "security definer" not in block.lower() or "set search_path" in block.lower():
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

    tracked_env = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.name.startswith(".env") and ".git" not in p.parts]
    if tracked_env:
        errors.append("Fichier(s) .env suivi(s) dans le dépôt: " + ", ".join(tracked_env))

    print(f"Validation Supabase profonde: {len(migrations)} migrations, {len(tables)} tables, {len(defined_rpcs)} RPC, {len(function_dirs)} Edge Functions.")
    print(f"Contrats code: {len(database_calls)} relation(s), {len(called_rpcs)} RPC appelée(s), {len(invoked_edges)} Edge Function(s) invoquée(s).")
    print(f"Client Supabase JS épinglé: {SUPABASE_JS_VERSION}.")
    if custom_env:
        print("Variables Edge personnalisées détectées: " + ", ".join(sorted(custom_env)))
    for warning in warnings:
        print("AVERTISSEMENT: " + warning)
    if errors:
        print(f"ECHEC Supabase: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1
    print("OK: structure, contrats, dépendances et garde-fous Supabase cohérents pour le déploiement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
