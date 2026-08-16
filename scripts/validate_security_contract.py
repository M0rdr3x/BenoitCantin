#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase" / "migrations"
FRONTEND = ROOT / "assets" / "js" / "sinjira-fracture-engine.js"
VERSION = "24.4.19"

SEALED_TABLES = (
    "character_generation_runs",
    "fracture_engine_actions",
    "fracture_engine_cards",
    "fracture_engine_events",
    "fracture_engine_games",
    "fracture_engine_rounds",
    "fracture_engine_seats",
    "fracture_engine_votes",
    "internal_admin_users",
    "internal_contribution_ownership",
    "internal_gameplay_contributions",
    "sinjira_canon_context",
    "sinjira_security_settings",
    "social_suspensions",
)


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    files = sorted(MIGRATIONS.glob("*.sql"))
    if not files:
        print("ECHEC contrat sécurité: aucune migration Supabase.")
        return 1

    all_sql = "\n".join(path.read_text("utf-8", errors="ignore") for path in files)
    normalized = compact(all_sql)

    if f"'security_version','{VERSION}'" not in normalized:
        fail(errors, f"Diagnostic de sécurité {VERSION} introuvable.")

    if "functionpublic.sinjira_security_contract_health()" not in normalized:
        fail(errors, "sinjira_security_contract_health() introuvable.")

    for table in SEALED_TABLES:
        marker = f"revokeallprivilegesontablepublic.{table}frompublic,anon,authenticated;"
        if marker not in normalized:
            fail(errors, f"Table interne non verrouillée explicitement: {table}.")

    raw_revoke = (
        "revokeallonfunctionpublic._fracture_engine_get_state_raw(text)"
        "frompublic,anon,authenticated;"
    )
    if raw_revoke not in normalized:
        fail(errors, "L'état brut Fracture n'est pas explicitement révoqué à PUBLIC/anon/authenticated.")

    if (
        "grantexecuteonfunctionpublic._fracture_engine_get_state_raw(text)"
        "toservice_role;"
    ) not in normalized:
        fail(errors, "L'état brut Fracture n'est pas explicitement réservé au service_role.")

    health_revoke = (
        "revokeallonfunctionpublic.sinjira_security_contract_health()"
        "frompublic,anon,authenticated;"
    )
    if health_revoke not in normalized:
        fail(errors, "Le diagnostic du contrat de sécurité est exposé à un rôle navigateur.")

    if FRONTEND.exists():
        frontend = FRONTEND.read_text("utf-8", errors="ignore")
        if "fracture-engine-gateway" not in frontend:
            fail(errors, "Le client Fracture n'utilise plus la passerelle serveur.")
        if "fracture_engine_get_state_safe" not in frontend:
            fail(errors, "Le client Fracture n'utilise plus l'état assaini.")
        if "_fracture_engine_get_state_raw" in frontend:
            fail(errors, "Le client Fracture référence l'état brut interne.")
    else:
        fail(errors, "Client Fracture introuvable.")

    # La liste publique des commentaires est volontairement une RPC SECURITY DEFINER:
    # elle évite d'ouvrir les tables de modération. Le contrat exige que la définition
    # canonique continue de ne retourner que le contenu approuvé et non masqué/signalé.
    comment_defs = re.findall(
        r"create\s+(?:or\s+replace\s+)?function\s+public\.list_sinjira_novel_comments\s*\([^)]*\).*?\$\$.*?\$\$\s*;",
        all_sql,
        flags=re.I | re.S,
    )
    if not comment_defs:
        fail(errors, "RPC publique de commentaires introuvable.")
    else:
        comment = compact(comment_defs[-1])
        for marker in ("c.status='approved'", "c.is_hidden=false", "c.is_reported=false"):
            if compact(marker) not in comment:
                fail(errors, f"Filtre de modération manquant dans list_sinjira_novel_comments: {marker}.")

    if errors:
        print(f"ECHEC contrat sécurité: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK contrat sécurité: tables internes scellées, état brut Fracture réservé au serveur, "
        f"état joueur assaini et diagnostic {VERSION} protégé."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
