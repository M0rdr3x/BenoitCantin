#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RETIRED = (
    "admin-reader",
    "generate-sinjira-character",
    "admin-literary",
    "validate-phone-v22",
    "guardian-create-youth-v22",
    "create-youth-account",
)


def require(source: str, marker: str, label: str, errors: list[str]):
    if marker not in source:
        errors.append(f"{label}: garde-fou absent: {marker}")


def main() -> int:
    errors = []
    site_js = (ROOT / "assets" / "js" / "site.js").read_text("utf-8", errors="ignore")
    for marker in (
        "RUNTIME_VERSION = '24.4.21'",
        "randomUUID",
        "window.addEventListener('error'",
        "window.addEventListener('unhandledrejection'",
        "sessionStorage",
        "runtime-errors",
        "requestId",
    ):
        require(site_js, marker, "assets/js/site.js", errors)
    if "fetch(" in site_js.split("RUNTIME_VERSION = '24.4.21'", 1)[-1]:
        errors.append("assets/js/site.js: le collecteur d’erreurs ne doit pas transmettre automatiquement les erreurs.")

    questionnaire = (ROOT / "supabase" / "functions" / "submit-character-questionnaire" / "index.ts").read_text("utf-8", errors="ignore")
    for marker in ("requiredUser(req)", "req.method!=='POST'", "length>500000", "413"):
        require(questionnaire, marker, "submit-character-questionnaire", errors)

    report = (ROOT / "supabase" / "functions" / "send-game-report" / "index.ts").read_text("utf-8", errors="ignore")
    for marker in ("MAX_REQUEST_BYTES", "optionalUser", "!user?.email", "to: [user.email]"):
        require(report, marker, "send-game-report", errors)

    gateway = (ROOT / "supabase" / "functions" / "fracture-engine-gateway" / "index.ts").read_text("utf-8", errors="ignore")
    for marker in (
        "MAX_BODY_BYTES",
        "ALLOWED_ACTIONS",
        "PARTY_RE",
        "Authorization",
        "client.auth.getUser",
        "actionError",
    ):
        require(gateway, marker, "fracture-engine-gateway", errors)

    search_roots = [ROOT / "assets", ROOT / "compte", ROOT / "projets", ROOT / "admin"]
    for slug in RETIRED:
        needle1 = f"functions.invoke('{slug}'"
        needle2 = f'functions.invoke("{slug}"'
        needle3 = f"/functions/v1/{slug}"
        for base in search_roots:
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in {".js", ".ts", ".html"}:
                    continue
                text = path.read_text("utf-8", errors="ignore")
                if needle1 in text or needle2 in text or needle3 in text:
                    errors.append(f"{path.relative_to(ROOT)}: appel runtime retiré encore présent: {slug}")

    if errors:
        print(f"ECHEC résilience runtime: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1
    print("OK résilience: erreurs navigateur minimisées localement, limites de requête/auth vérifiées et anciens endpoints absents du runtime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
