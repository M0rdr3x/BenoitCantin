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

# Ces deux fonctions ont volontairement verify_jwt=false. Elles doivent donc
# conserver leurs garde-fous applicatifs spécifiques dans leur code.
CUSTOM_AUTH = {
    "get-document-url": (
        "optionalUser",
        "document_requires_account",
    ),
    "send-game-report": (
        "requiredUser",
        "user.email",
    ),
}


def read_tree_text(path: Path) -> str:
    parts: list[str] = []
    if not path.exists():
        return ""
    for file in sorted(path.rglob("*")):
        if file.is_file() and file.suffix in {".ts", ".js", ".json", ".toml", ".md", ".html"}:
            parts.append(file.read_text("utf-8", errors="ignore"))
    return "\n".join(parts)


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
            errors.append(
                f"{slug}: verify_jwt={verify!r}, attendu {expected!r}."
            )

        entry = FUNCTIONS / slug / "index.ts"
        if not entry.exists():
            errors.append(f"{slug}: index.ts absent.")

    # Les fonctions sans vérification JWT plateforme doivent prouver leurs
    # protections applicatives dans leur source canonique.
    for slug, markers in CUSTOM_AUTH.items():
        source = read_tree_text(FUNCTIONS / slug)
        for marker in markers:
            if marker not in source:
                errors.append(
                    f"{slug}: garde-fou custom auth/access manquant: {marker}."
                )

    # Aucune route/frontend canonique ne doit réintroduire les anciens slugs.
    searchable_roots = [
        ROOT / "assets",
        ROOT / "compte",
        ROOT / "projets",
        ROOT / "admin",
        ROOT / "supabase" / "functions",
    ]
    public_source = "\n".join(read_tree_text(root) for root in searchable_roots)
    for slug in sorted(RETIRED):
        if slug in public_source:
            errors.append(f"Référence à une Edge Function retirée: {slug}.")

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
