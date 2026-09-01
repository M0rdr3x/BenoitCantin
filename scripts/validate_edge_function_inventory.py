#!/usr/bin/env python3
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / "supabase" / "functions"
CONFIG = ROOT / "supabase" / "config.toml"

CANONICAL = {
    "admin-analytics", "admin-console", "admin-license-codes", "admin-reports",
    "admin-sinjira-v18", "admin-social-v20", "admin-users", "delete-player-account",
    "fracture-engine-gateway", "get-document-url", "life-story-delivery", "life-story-export",
    "redeem-license-code", "revoke-my-contributions", "security-context", "send-game-report",
    "send-player-sheet", "submit-character-questionnaire", "submit-fracture-endgame",
    "submit-game-contribution",
}

RETIRED = {
    "admin-reader", "generate-sinjira-character", "admin-literary", "validate-phone-v22",
    "guardian-create-youth-v22", "create-youth-account",
}

CUSTOM_AUTH = {
    "get-document-url": (
        "optionalUser", "project_access_rank", "doc.status!=='approved'",
        "doc.projects?.status!=='active'", "createSignedUrl", "MAX_REQUEST_BYTES", "UUID_RE",
        "externalUrlAllowed", "TextEncoder", "Cache-Control", "no-store", "Referrer-Policy",
    ),
    "send-game-report": (
        "optionalUser", "!user?.email", "to: [user.email]", "MAX_REQUEST_BYTES", "TextEncoder",
        "PAID_EXTERNAL_SERVICES_ENABLED=false", "MAX_TEMPLATE_BYTES=15*1024*1024",
        "TEMPLATE_ORIGIN='https://www.benoitcantin.com'",
        "TEMPLATE_PATH_PREFIX='/projets/sinjira/jeux/fracture-du-reseau-mere/documents/'",
        "redirect:'error'", "REPORT_TEMPLATE_TOO_LARGE", "%PDF-", "Cache-Control", "no-store",
        "Referrer-Policy",
    ),
    "life-story-delivery": (
        "token_hash", "sha256Hex", "expires_at", "max_downloads",
        "service_life_story_register_download", "req.method !== 'POST'", "requestUrl.search",
        "MAX_REQUEST_BYTES", "MAX_PDF_BYTES", "hasPdfSignature", "allowedOrigin",
        "Content-Security-Policy", "Cache-Control", "no-store",
    ),
}

JWT_SENSITIVE_GUARDS = {
    "delete-player-account": (
        "req.method !== 'POST'", "MAX_REQUEST_BYTES=1024", "readBoundedJson", "TextEncoder",
        "JSON_REQUIRED", "REQUEST_TOO_LARGE", "INVALID_JSON", "Cache-Control", "private, no-store",
        "X-Content-Type-Options", "nosniff", "Referrer-Policy", "no-referrer",
        "privacy_service_can_delete_user", "MFA_REQUIRED", "OWNER_OR_ADMIN_DELETE_BLOCKED",
        "CONFIRM_PHRASE='SUPPRIMER MON COMPTE'",
    ),
    "revoke-my-contributions": (
        "req.method !== 'POST'", "MAX_REQUEST_BYTES=2048", "readBoundedJson", "TextEncoder",
        "JSON_REQUIRED", "REQUEST_TOO_LARGE", "INVALID_JSON", "UUID_RE", "body.all===true",
        "AMBIGUOUS_SCOPE", "SESSION_REQUIRED", "revokeAll ? null : sessionId",
        "Cache-Control", "private, no-store", "X-Content-Type-Options", "nosniff",
        "Referrer-Policy", "no-referrer",
    ),
    "submit-game-contribution": (
        "req.method!=='POST'", "MAX_REQUEST_BYTES=2048", "readBoundedJson", "TextEncoder",
        "JSON_REQUIRED", "REQUEST_TOO_LARGE", "INVALID_JSON", "UUID_RE", "INVALID_SESSION",
        "p_user_id:user.id", "select('id,game_slug,play_mode,human_player_count,effective_player_count,player_count,duration_minutes')",
        "submitted:true", "Cache-Control", "private, no-store", "X-Content-Type-Options",
        "nosniff", "Referrer-Policy", "no-referrer",
    ),
    "submit-fracture-endgame": (
        "req.method!=='POST'", "MAX_REQUEST_BYTES=2048", "readBoundedJson", "TextEncoder",
        "JSON_REQUIRED", "REQUEST_TOO_LARGE", "INVALID_JSON", "PARTY_CODE_RE=/^[A-Z0-9-]{10}$/",
        "record_sinjira_fracture_endgame_contribution", "p_user_id:user.id", "p_session_id:session.id",
        "p_party_id:party.id", "submitted:true", "PAID_EXTERNAL_SERVICES_ENABLED=false",
        "Cache-Control", "private, no-store", "X-Content-Type-Options", "nosniff",
        "Referrer-Policy", "no-referrer",
    ),
}

TEXT_SUFFIXES = {".ts", ".js", ".json", ".toml", ".md", ".html"}


def text_files(path: Path):
    if not path.exists():
        return
    for file in sorted(path.rglob("*")):
        if file.is_file() and file.suffix in TEXT_SUFFIXES:
            yield file


def read_tree_text(path: Path) -> str:
    return "\n".join(file.read_text("utf-8", errors="ignore") for file in text_files(path) or [])


def find_edge_calls(paths: list[Path], slug: str) -> list[str]:
    escaped = re.escape(slug)
    patterns = (
        re.compile(rf"functions\s*\.\s*invoke\s*\(\s*['\"]{escaped}['\"]"),
        re.compile(rf"/functions/v1/{escaped}(?:['\"/?#]|$)"),
        re.compile(rf"functions/{escaped}/index\.(?:ts|js)"),
    )
    hits: list[str] = []
    for root in paths:
        for file in text_files(root) or []:
            text = file.read_text("utf-8", errors="ignore")
            if any(pattern.search(text) for pattern in patterns):
                hits.append(str(file.relative_to(ROOT)))
    return sorted(set(hits))


def main() -> int:
    errors: list[str] = []
    if not FUNCTIONS.is_dir():
        print("ECHEC inventaire Edge Functions: dossier supabase/functions absent.")
        return 1

    actual = {path.name for path in FUNCTIONS.iterdir() if path.is_dir() and path.name != "_shared"}
    missing = sorted(CANONICAL - actual)
    extra = sorted(actual - CANONICAL)
    if missing:
        errors.append("Fonctions canoniques absentes du dépôt: " + ", ".join(missing))
    if extra:
        errors.append("Fonctions non canoniques présentes dans le dépôt: " + ", ".join(extra))

    if not CONFIG.exists():
        errors.append("supabase/config.toml absent.")
        config = {}
    else:
        config = tomllib.loads(CONFIG.read_text("utf-8"))

    function_config = config.get("functions", {}) if isinstance(config, dict) else {}
    configured = set(function_config.keys()) if isinstance(function_config, dict) else set()
    if configured != CANONICAL:
        if CANONICAL - configured:
            errors.append("Fonctions canoniques absentes de config.toml: " + ", ".join(sorted(CANONICAL - configured)))
        if configured - CANONICAL:
            errors.append("Fonctions non canoniques encore configurées: " + ", ".join(sorted(configured - CANONICAL)))

    for slug in sorted(CANONICAL):
        cfg = function_config.get(slug, {}) if isinstance(function_config, dict) else {}
        verify = cfg.get("verify_jwt") if isinstance(cfg, dict) else None
        expected = slug not in CUSTOM_AUTH
        if verify is not expected:
            errors.append(f"{slug}: verify_jwt={verify!r}, attendu {expected!r}.")
        entry = FUNCTIONS / slug / "index.ts"
        if not entry.exists():
            errors.append(f"{slug}: index.ts absent.")

    for slug, markers in CUSTOM_AUTH.items():
        source = read_tree_text(FUNCTIONS / slug)
        for marker in markers:
            if marker not in source:
                errors.append(f"{slug}: garde-fou custom auth/access manquant: {marker}.")

    for slug, markers in JWT_SENSITIVE_GUARDS.items():
        source = read_tree_text(FUNCTIONS / slug)
        for marker in markers:
            if marker not in source:
                errors.append(f"{slug}: garde-fou HTTP/destructif manquant: {marker}.")
        if "await req.json()" in source or "await req.json (" in source:
            errors.append(f"{slug}: lecture JSON directe non bornée interdite.")

    contribution_source = read_tree_text(FUNCTIONS / "submit-game-contribution")
    if "contribution_id" in contribution_source:
        errors.append("submit-game-contribution: un UUID interne de contribution ne doit pas sortir vers le client.")
    if ".select('*')" in contribution_source:
        errors.append("submit-game-contribution: sélection SQL large interdite depuis V24.5.53.")

    fracture_source = read_tree_text(FUNCTIONS / "submit-fracture-endgame")
    for forbidden in (
        ".from('internal_gameplay_contributions').insert",
        '.from("internal_gameplay_contributions").insert',
        ".from('internal_contribution_ownership').insert",
        '.from("internal_contribution_ownership").insert',
        ".from('contribution_receipts').insert",
        '.from("contribution_receipts").insert',
    ):
        if forbidden in fracture_source:
            errors.append("submit-fracture-endgame: écriture directe interdite; utiliser la RPC transactionnelle V24.5.54.")
    if ".select('*')" in fracture_source:
        errors.append("submit-fracture-endgame: sélection SQL large interdite depuis V24.5.54.")

    delivery_source = read_tree_text(FUNCTIONS / "life-story-delivery")
    if "searchParams.get('token')" in delivery_source or 'searchParams.get("token")' in delivery_source:
        errors.append("life-story-delivery: le jeton ne doit jamais être lu depuis l URL.")
    if "req.method !== 'GET'" in delivery_source:
        errors.append("life-story-delivery: le mode GET direct est interdit depuis V24.5.50.")

    export_source = read_tree_text(FUNCTIONS / "life-story-export")
    for marker in (
        "requiredAdmin", "admin_life_story_get_export", "source_boundary", "DELIVERY_PAGE",
        "histoire-de-vie/remise.html", "#${raw}", "service_life_story_mark_export_generated",
        "service_life_story_mark_export_purged",
    ):
        if marker not in export_source:
            errors.append(f"life-story-export: contrat posthume manquant: {marker}.")
    if "?token=" in export_source:
        errors.append("life-story-export: les liens de remise ne doivent plus placer le jeton dans la query string.")
    if "reader_characters" in export_source or "registry_account_links" in export_source or "characters')." in export_source:
        errors.append("life-story-export ne doit pas interroger le Registre ou les personnages.")

    searchable_roots = [ROOT / "assets", ROOT / "compte", ROOT / "projets", ROOT / "admin", ROOT / "supabase" / "functions"]
    for slug in sorted(RETIRED):
        hits = find_edge_calls(searchable_roots, slug)
        if hits:
            errors.append(f"Appel à une Edge Function retirée: {slug} — " + ", ".join(hits))

    if errors:
        print(f"ECHEC inventaire Edge Functions: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print("OK inventaire Edge Functions: 20 fonctions canoniques, JWT/custom auth cohérents, actions sensibles bornées/no-store, contributions jeu sans UUID exposé, Fracture via RPC transactionnelle révocable, modèle PDF Fracture borné, remise posthume POST sans jeton URL et aucun ancien appel Edge référencé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
