#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase" / "migrations"
FRONTEND = ROOT / "assets" / "js" / "sinjira-fracture-engine.js"
VERSION = "24.4.19"
SENSITIVE_ACL_VERSION = "24.4.36"
SENSITIVE_ACL_MIGRATION = MIGRATIONS / "20260817012809_sinjira_v24_4_36_sensitive_acl_hardening.sql"

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


def latest_function(all_sql: str, name: str) -> str:
    """Return the latest CREATE/REPLACE definition for a public function."""
    pattern = re.compile(
        rf"create\s+(?:or\s+replace\s+)?function\s+public\.{re.escape(name)}\s*"
        rf"\([^)]*\).*?(?P<tag>\$[A-Za-z0-9_]*\$).*?(?P=tag)\s*;",
        flags=re.I | re.S,
    )
    matches = [m.group(0) for m in pattern.finditer(all_sql)]
    return matches[-1] if matches else ""


def require_latest_function_contract(
    errors: list[str], all_sql: str, name: str, markers: tuple[str, ...]
) -> None:
    definition = latest_function(all_sql, name)
    if not definition:
        fail(errors, f"Fonction de sécurité introuvable: {name}.")
        return
    normalized = compact(definition)
    if "securitydefiner" not in normalized:
        fail(errors, f"{name}: SECURITY DEFINER attendu par le contrat actuel.")
    if "setsearch_path=public,auth" not in normalized:
        fail(errors, f"{name}: search_path explicite public,auth absent.")
    for marker in markers:
        if compact(marker) not in normalized:
            fail(errors, f"{name}: garde d'autorisation manquante: {marker}.")


def require_latest_invoker_role_contract(
    errors: list[str], all_sql: str, name: str, markers: tuple[str, ...]
) -> None:
    definition = latest_function(all_sql, name)
    if not definition:
        fail(errors, f"Fonction de rôle introuvable: {name}.")
        return
    normalized = compact(definition)
    if "securityinvoker" not in normalized:
        fail(errors, f"{name}: SECURITY INVOKER attendu depuis V24.4.56.")
    if "securitydefiner" in normalized:
        fail(errors, f"{name}: SECURITY DEFINER ne doit plus être utilisé depuis V24.4.56.")
    if "setsearch_path=public,auth,pg_temp" not in normalized:
        fail(errors, f"{name}: search_path explicite public,auth,pg_temp absent.")
    for marker in markers:
        if compact(marker) not in normalized:
            fail(errors, f"{name}: garde de rôle manquante: {marker}.")


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

    # V24.4.36 : réduire aussi les privilèges SQL de tables privées qui étaient déjà
    # protégées par RLS. La défense ne dépend plus uniquement de l'absence de policy anon.
    if not SENSITIVE_ACL_MIGRATION.exists():
        fail(errors, f"Migration ACL sensible absente: {SENSITIVE_ACL_MIGRATION.name}.")
    else:
        acl = compact(SENSITIVE_ACL_MIGRATION.read_text("utf-8", errors="ignore"))
        acl_markers = (
            "revokeallprivilegesontablepublic.guardian_linksfrompublic,anon;",
            "grantsel ectontablepublic.guardian_linkstoauthenticated;".replace(" ", ""),
            "revokeallprivilegesontablepublic.guardian_signup_invitesfrompublic,anon;",
            "revokeinsert,update,delete,truncate,references,triggerontablepublic.guardian_signup_invitesfromauthenticated;",
            "grantselectontablepublic.guardian_signup_invitestoauthenticated;",
            "revokeallprivilegesontablepublic.private_family_linksfrompublic,anon;",
            "grantselect,insert,update,deleteontablepublic.private_family_linkstoauthenticated;",
            "revokeallprivilegesontablepublic.social_real_messagesfrompublic,anon;",
            "grantselect,insertontablepublic.social_real_messagestoauthenticated;",
            "revokeallprivilegesontablepublic.social_character_messagesfrompublic,anon;",
            "grantselect,insertontablepublic.social_character_messagestoauthenticated;",
            f"'version','{SENSITIVE_ACL_VERSION}'",
            "revokeallonfunctionpublic.sinjira_sensitive_acl_health()frompublic,anon,authenticated;",
            "grantexecuteonfunctionpublic.sinjira_sensitive_acl_health()toservice_role;",
        )
        for marker in acl_markers:
            if marker not in acl:
                fail(errors, f"Contrat ACL sensible {SENSITIVE_ACL_VERSION} incomplet: {marker}.")
        health = latest_function(all_sql, "sinjira_sensitive_acl_health")
        health_compact = compact(health)
        if not health:
            fail(errors, "sinjira_sensitive_acl_health() introuvable.")
        else:
            for marker in (
                "securitydefiner",
                "setsearch_path=public",
                "guardian_signup_invites_auth_read_only",
                "social_real_messages_auth_minimal",
                "social_character_messages_auth_minimal",
            ):
                if compact(marker) not in health_compact:
                    fail(errors, f"Diagnostic ACL sensible incomplet: {marker}.")

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
    # elle évite d'ouvrir les tables de modération. Le schéma canonique utilise le
    # statut unique (pending/approved/...) plutôt que des colonnes is_hidden/is_reported.
    # Le contrat exige donc: roman identifiable, commentaires activés, statut approved
    # et limite dure afin de contenir la surface publique et le coût de la requête.
    comment = latest_function(all_sql, "list_sinjira_novel_comments")
    if not comment:
        fail(errors, "RPC publique de commentaires introuvable.")
    else:
        comment_normalized = compact(comment)
        for marker in (
            "c.status='approved'",
            "n.comments_enabled=true",
            "n.slug=trim(p_novel_slug)",
            "limit250",
        ):
            if compact(marker) not in comment_normalized:
                fail(errors, f"Garde publique manquante dans list_sinjira_novel_comments: {marker}.")

    # V24.4.56 : les vérifications de rôle utilisent désormais SECURITY INVOKER + RLS self-only.
    # Le navigateur ne lit que sa propre ligne internal_admin_users; service_role conserve
    # le chemin serveur nécessaire aux Edge Functions.
    require_latest_invoker_role_contract(
        errors, all_sql, "is_sinjira_admin",
        ("p_user_id=(select auth.uid())", "auth.jwt()->>'role'", "'service_role'", "internal_admin_users"),
    )
    require_latest_invoker_role_contract(
        errors, all_sql, "is_sinjira_owner",
        ("p_user_id=(select auth.uid())", "auth.jwt()->>'role'", "'service_role'", "a.role='owner'"),
    )
    require_latest_function_contract(
        errors, all_sql, "social_is_suspended",
        ("p_user_id=auth.uid()", "auth.jwt()->>'role'", "'service_role'", "else false"),
    )
    require_latest_function_contract(
        errors, all_sql, "social_is_blocked",
        ("auth.uid()<>a", "auth.uid()<>b", "then false", "'service_role'"),
    )
    require_latest_function_contract(
        errors, all_sql, "is_fracture_party_member",
        ("p_user_id=auth.uid()", "auth.jwt()->>'role'", "'service_role'", "else false"),
    )
    require_latest_function_contract(
        errors, all_sql, "sinjira_cycle_allowed",
        ("p_user_id<>auth.uid()", "then false", "auth.jwt()->>'role'", "'service_role'"),
    )
    require_latest_function_contract(
        errors, all_sql, "sinjira_can_social_interact",
        ("auth.uid()<>p_a", "auth.uid()<>p_b", "then false", "'service_role'"),
    )
    require_latest_function_contract(
        errors, all_sql, "sinjira_content_allowed",
        ("p_user_id<>auth.uid()", "return false", "auth.jwt()->>'role'", "'service_role'"),
    )
    require_latest_function_contract(
        errors, all_sql, "sinjira_mfa_access_allowed",
        ("p_user_id<>auth.uid()", "return false", "auth.jwt()->>'aal'", "'aal2'"),
    )

    if errors:
        print(f"ECHEC contrat sécurité: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK contrat sécurité: tables internes scellées, ACL sensibles minimales, état brut Fracture réservé au serveur, "
        f"état joueur assaini, rôles owner/admin SECURITY INVOKER + RLS self-only, autres self-scopes privilégiés contrôlés et diagnostics {VERSION}/{SENSITIVE_ACL_VERSION} protégés."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
