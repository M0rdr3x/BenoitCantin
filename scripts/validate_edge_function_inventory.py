#!/usr/bin/env python3
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / "supabase" / "functions"
CONFIG = ROOT / "supabase" / "config.toml"

CANONICAL = {
    "admin-analytics",
    "admin-console",
    "admin-license-codes",
    "admin-reports",
    "admin-sinjira-v18",
    "admin-social-v20",
    "admin-users",
    "delete-player-account",
    "fracture-engine-gateway",
    "get-document-url",
    "redeem-license-code",
    "revoke-my-contributions",
    "send-game-report",
    "send-player-sheet",
    "submit-character-questionnaire",
    "submit-fracture-endgame",
    "submit-game-contribution",
}

RETIRED = {
    "admin-reader",
    "generate-sinjira-character",
    "admin-literary",
    "validate-phone-v22",
    "guardian-create-youth-v22",
    "create-youth-account",
}

CUSTOM_AUTH = {
    "get-document-url": (
        "optionalUser",
        "project_access_rank",
        "doc.status!=='approved'",
        "createSignedUrl",
    ),
    "send-game-report": (
        "optionalUser",
        "!user?.email",
        "to: [user.email]",
        "MAX_REQUEST_BYTES",
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
    return "\n".join(
        file.read_text("utf-8", errors="ignore")
        for file in text_files(path) or []
    )


def find_references(paths: list[Path], needle: str) -> list[str]:
    hits: list[str] = []
    for root in paths:
        for file in text_files(root) or []:
            if needle in file.read_text("utf-8", errors="ignore"):
                hits.append(str(file.relative_to(ROOT)))
    return sorted(set(hits))


def main() -> int:
    errors: list[str] = []

    if not FUNCTIONS.is_dir():
        print("ECHEC inventaire Edge Functions: dossier supabase/functions absent.")
        return 1

    actual = {
        path.name
        for path in FUNCTIONS.iterdir()
        if path.is_dir() and path.name != "_shared"
    }

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
            errors.append(
                "Fonctions canoniques absentes de config.toml: "
                + ", ".join(sorted(CANONICAL - configured))
            )
        if configured - CANONICAL:
            errors.append(
                "Fonctions non canoniques encore configurées: "
                + ", ".join(sorted(configured - CANONICAL))
            )

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

    searchable_roots = [
        ROOT / "assets",
        ROOT / "compte",
        ROOT / "projets",
        ROOT / "admin",
        ROOT / "supabase" / "functions",
    ]
    for slug in sorted(RETIRED):
        hits = find_references(searchable_roots, slug)
        if hits:
            errors.append(
                f"Référence à une Edge Function retirée: {slug} — " + ", ".join(hits)
            )

    if errors:
        print(f"ECHEC inventaire Edge Functions: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK inventaire Edge Functions: 17 fonctions canoniques, configuration JWT cohérente, "
        "garde-fous des 2 fonctions publiques vérifiés et aucun ancien slug référencé."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
