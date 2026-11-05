#!/usr/bin/env python3
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / "supabase" / "functions"
CONFIG = ROOT / "supabase" / "config.toml"

CANONICAL = {
    "admin-analytics", "admin-console", "admin-license-codes", "admin-reports",
    "admin-sinjira-v18", "admin-social-v20", "admin-users", "conscience-vault",
    "delete-player-account", "fracture-engine-gateway", "get-document-url",
    "get-novel-file-url", "get-private-book-url", "life-story-delivery", "life-story-export", "personal-ai",
    "redeem-license-code", "revoke-my-contributions", "security-context", "send-game-report",
    "send-player-sheet", "submit-character-questionnaire", "submit-fracture-endgame",
    "submit-game-contribution", "nova-civic-poll",
}

RETIRED = {
    "admin-reader", "generate-sinjira-character", "admin-literary", "validate-phone-v22",
    "guardian-create-youth-v22", "create-youth-account",
}

CUSTOM_AUTH = {
    "nova-civic-poll": (
        "NOVA_POLL_ENABLED", "NOVA_POLL_APPROVED_VERSION", "NOVA_POLL_TURNSTILE_SECRET",
        "NOVA_POLL_TURNSTILE_SITE_KEY", "NOVA_POLL_HMAC_KEY",
        "MAX_BODY_BYTES", "readLimitedJson", "confirmCaptcha",
        "hashToken", "ORIGINS", "nova_poll_public_counts",
        "nova_poll_publication_state", "MIN_PUBLIC_BALLOTS",
        "if(!isOpen()) return respond(503",
        "Cache-Control", "no-store", "Referrer-Policy",
    ),
    "get-document-url": (
        "optionalUser", "project_access_rank", "doc.status!=='approved'",
        "doc.projects?.status!=='active'", "createSignedUrl", "MAX_REQUEST_BYTES", "UUID_RE",
        "externalUrlAllowed", "readLimitedUtf8Body", "Cache-Control", "no-store", "Referrer-Policy",
    ),
    "send-game-report": (
        "optionalUser", "!user?.email", "to: [user.email]", "MAX_REQUEST_BYTES", "readLimitedUtf8Body",
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
    "conscience-vault": (
        "req.method !== 'POST'", "MAX_REQUEST_BYTES", "readBoundedJson", "req.body.getReader()",
        "REQUEST_TOO_LARGE", "INVALID_JSON", "requiredVaultUser", "service_conscience_evaluate_access",
        "CLIENT_IDENTITY_FORBIDDEN", "trusted_device_confirmation", "Cache-Control", "private, no-store",
        "X-Content-Type-Options", "nosniff", "Referrer-Policy", "no-referrer",
    ),
    "personal-ai": (
        "req.method !== 'POST'", "MAX_REQUEST_BYTES", "readBoundedJson", "req.body.getReader()",
        "REQUEST_TOO_LARGE", "INVALID_JSON", "requiredPersonalAiUser", "service_personal_ai_evaluate_access",
        "CLIENT_IDENTITY_FORBIDDEN", "ai_private", "Cache-Control", "private, no-store",
        "X-Content-Type-Options", "nosniff", "Referrer-Policy", "no-referrer",
        "conversation_enabled", "source_retrieval_enabled",
    ),
    "get-novel-file-url": (
        "req.method==='OPTIONS'", "req.method!=='POST'", "MAX_REQUEST_BYTES=2048",
        "readBoundedJson", "req.body.getReader()", "REQUEST_TOO_LARGE", "INVALID_JSON",
        "requiredUser(req)", "sinjira_novels", "is_sinjira_owner", "is_sinjira_admin",
        "user_entitlements", "file_ready", "createSignedUrl", "expires_in:600",
        "Cache-Control", "private, no-store", "X-Content-Type-Options", "nosniff",
        "Referrer-Policy", "no-referrer",
    ),
    "get-private-book-url": (
        "req.method!=='POST'", "requiredUser(req)", "user_entitlements",
        ".eq('user_id',user.id)", ".eq('product_id',product.id)",
        "SINJIRA_LIVRE_I_PRIVATE_DELIVERY_ENABLED", "SINJIRA_LIVRE_I_PRIVATE_BUCKET",
        "SINJIRA_LIVRE_I_PRIVATE_PATH", "SIGNED_URL_SECONDS=300", "createSignedUrl",
        "Cache-Control", "private, no-store", "X-Content-Type-Options", "nosniff",
        "Referrer-Policy", "no-referrer",
    ),
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
}

TEXT_SUFFIXES = {".ts", ".js", ".json", ".toml", ".md", ".html"}
MAX_SOURCE_BYTES = 2 * 1024 * 1024


class UnsafeSource(Exception):
    """Une source contrôlée ne peut être vérifiée de façon fiable."""


def read_security_text(file: Path) -> str:
    """Fail-closed : aucun lien symbolique, octet NUL ou décodage permissif."""
    if file.is_symlink():
        raise UnsafeSource(f"{file}: lien symbolique interdit")
    try:
        size = file.stat().st_size
        if size > MAX_SOURCE_BYTES:
            raise UnsafeSource(f"{file}: fichier source trop volumineux")
        data = file.read_bytes()
    except OSError as exc:
        raise UnsafeSource(f"{file}: source inaccessible ({type(exc).__name__})") from exc
    if len(data) > MAX_SOURCE_BYTES:
        raise UnsafeSource(f"{file}: fichier source trop volumineux")
    if b"\x00" in data:
        raise UnsafeSource(f"{file}: octet NUL dans une source texte")
    try:
        return data.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise UnsafeSource(f"{file}: UTF-8 invalide") from exc



def text_files(path: Path):
    if not path.exists():
        return
    for file in sorted(path.rglob("*")):
        if file.is_file() and file.suffix in TEXT_SUFFIXES:
            yield file


def read_tree_text(path: Path) -> str:
    return "\n".join(read_security_text(file) for file in text_files(path) or [])


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
            text = read_security_text(file)
            if any(pattern.search(text) for pattern in patterns):
                hits.append(str(file.relative_to(ROOT)))
    return sorted(set(hits))


def main() -> int:
    errors: list[str] = []
    if not FUNCTIONS.is_dir():
        print("ECHEC inventaire Edge Functions: dossier supabase/functions absent.")
        return 1

    if FUNCTIONS.is_symlink():
        errors.append("Le répertoire des fonctions Edge est un lien symbolique.")
    for entry in FUNCTIONS.rglob("*"):
        if entry.is_symlink():
            errors.append(f"Lien symbolique interdit dans les fonctions Edge: {entry.relative_to(ROOT)}")
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
        if CONFIG.is_symlink():
            raise UnsafeSource("supabase/config.toml: lien symbolique interdit")
        config = tomllib.loads(read_security_text(CONFIG))

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

    # Enforce the actual shared streaming implementation; old inline byte
    # encoder markers are no longer applicable to these three public routes.
    limited_reader = FUNCTIONS / "_shared" / "limited-body.mjs"
    if not limited_reader.is_file():
        errors.append("Lecteur HTTP borné partagé manquant.")
    else:
        helper = read_security_text(limited_reader)
        for marker in (
            "req.body.getReader()",
            "byteCount += value.byteLength",
            "byteCount > maxBytes",
            "new TextDecoder('utf-8', { fatal: true })",
            "reader.cancel()",
        ):
            if marker not in helper:
                errors.append(f"Lecteur HTTP borné partagé: contrôle manquant {marker}.")
    for slug in ("get-document-url", "send-game-report", "life-story-delivery"):
        entry = FUNCTIONS / slug / "index.ts"
        if entry.is_file():
            source = read_security_text(entry)
            if "readLimitedUtf8Body" not in source or "limited-body.mjs" not in source:
                errors.append(f"{slug}: utilisation du lecteur HTTP partagé absente.")
            if "await req.text()" in source or "await req.json()" in source:
                errors.append(f"{slug}: lecture directe d'un corps non borné interdite.")

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

    book_source = read_tree_text(FUNCTIONS / "get-private-book-url")
    for forbidden in ("external_url", "getPublicUrl("):
        if forbidden in book_source:
            errors.append(f"get-private-book-url: repli public interdit: {forbidden}.")

    vault_source = read_tree_text(FUNCTIONS / "conscience-vault")
    if "service.rpc('security_evaluate_context'" in vault_source or 'service.rpc("security_evaluate_context"' in vault_source:
        errors.append("conscience-vault: l Edge doit passer par service_conscience_evaluate_access pour conserver les challenges entre retries.")

    ai_source = read_tree_text(FUNCTIONS / "personal-ai")
    if "service.rpc('security_evaluate_context'" in ai_source or 'service.rpc("security_evaluate_context"' in ai_source:
        errors.append("personal-ai: l Edge doit passer par service_personal_ai_evaluate_access pour conserver le scope ai_private et les challenges.")
    for forbidden in ("conscience_entries", "service_conscience_", "life_story_entries", "employment_profiles", "employment_applications"):
        if forbidden in ai_source:
            errors.append(f"personal-ai: lecture directe de source interdite dans la fondation V25: {forbidden}.")

    contribution_source = read_tree_text(FUNCTIONS / "submit-game-contribution")
    if "contribution_id" in contribution_source:
        errors.append("submit-game-contribution: un UUID interne de contribution ne doit pas sortir vers le client.")
    if ".select('*')" in contribution_source:
        errors.append("submit-game-contribution: sélection SQL large interdite depuis V24.5.53.")

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

    print("OK inventaire Edge Functions: 25 fonctions canoniques, JWT/custom auth cohérents, portes Livre I entitlement privées, actions sensibles bornées/no-store, coffre et Mon IA derrière continuité de challenge serveur, aucune lecture directe des sources privées par Mon IA, UUID contribution non exposé, modèle PDF Fracture borné à l’origine approuvée, remise posthume POST sans jeton URL et aucun ancien appel Edge référencé.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UnsafeSource as exc:
        print(f"ECHEC inventaire Edge Functions: lecture de source non fiable: {exc}")
        raise SystemExit(1) from None
