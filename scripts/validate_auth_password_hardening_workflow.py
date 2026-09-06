#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-v25-auth-password-hardening.yml"
STATUS = ROOT / "docs" / "sinjira-v25-hosted-auth-password-security.md"
CONFIG = ROOT / "supabase" / "config.toml"


def fail(message: str) -> None:
    print(f"ECHEC: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> int:
    for path in (WORKFLOW, STATUS, CONFIG):
        require(path.is_file(), f"fichier absent: {path.relative_to(ROOT)}")
    text = WORKFLOW.read_text(encoding="utf-8")
    status = STATUS.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")

    # Déclenchement et cible production strictement bornés.
    require("workflow_dispatch:" in text, "workflow_dispatch obligatoire")
    forbidden_triggers = ["pull_request:", "push:", "schedule:", "repository_dispatch:"]
    for trigger in forbidden_triggers:
        require(trigger not in text, f"déclencheur interdit: {trigger}")
    require(
        'ENABLE-SINJIRA-V25-LEAKED-PASSWORD-PROTECTION' in text,
        "confirmation exacte HIBP absente",
    )
    require("environment: production" in text, "environment production obligatoire")
    require(
        "SUPABASE_PROJECT_REF: gpvivleexywljowcqkru" in text,
        "project ref production inattendu",
    )
    require(
        "SUPABASE_ORGANIZATION_SLUG: glaxqwyumblfqmzusqbt" in text,
        "organization slug production inattendu",
    )
    require(
        "SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}" in text,
        "le workflow doit utiliser uniquement le PAT Management API de l'environnement production",
    )

    secret_refs = set(re.findall(r"secrets\.([A-Z0-9_]+)", text))
    require(
        secret_refs == {"SUPABASE_ACCESS_TOKEN"},
        f"secrets GitHub inattendus: {sorted(secret_refs)}",
    )

    # Surface Management API autorisée: organisation en lecture, Auth config et Security Advisor.
    organization_endpoint = "$SUPABASE_MANAGEMENT_API/organizations/$SUPABASE_ORGANIZATION_SLUG"
    auth_endpoint = "$SUPABASE_MANAGEMENT_API/projects/$SUPABASE_PROJECT_REF/config/auth"
    advisor_endpoint = "$SUPABASE_MANAGEMENT_API/projects/$SUPABASE_PROJECT_REF/advisors/security"
    require(organization_endpoint in text, "préflight organisation/plan obligatoire")
    require(auth_endpoint in text, "endpoint /config/auth obligatoire")
    require(advisor_endpoint in text, "postflight Security Advisor obligatoire")
    require(text.count("--request PATCH") == 1, "un unique PATCH Management API est autorisé")
    for method in ("POST", "PUT", "DELETE"):
        require(f"--request {method}" not in text, f"méthode Management API interdite: {method}")

    # L'éligibilité Pro+ doit être testée avant toute lecture/écriture Auth.
    require(
        'eligible = {"pro", "team", "enterprise"}' in text,
        "allowlist des plans éligibles Pro/Team/Enterprise absente",
    )
    require("if plan not in eligible:" in text, "refus explicite des plans non éligibles absent")
    require(
        "Activation HIBP bloquée avant PATCH" in text,
        "diagnostic de blocage avant PATCH absent",
    )
    organization_pos = text.index(organization_endpoint)
    auth_pos = text.index(auth_endpoint)
    patch_pos = text.index("--request PATCH")
    require(organization_pos < auth_pos < patch_pos, "l'ordre plan -> Auth GET -> PATCH doit rester strict")

    # Le corps du PATCH est volontairement minuscule: un seul booléen, rien d'autre.
    data_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("--data")]
    require(
        data_lines == ['--data \'{"password_hibp_enabled":true}\' \\'],
        f"payload PATCH inattendu: {data_lines}",
    )
    require(text.count("password_hibp_enabled") >= 4, "contrôles HIBP avant/après insuffisants")
    require("password_min_length" in text, "précondition password_min_length absente")
    require("minimum < 12" in text, "seuil minimum de 12 caractères non vérifié")

    # Aucune autre famille d'opérations de production ne doit pouvoir apparaître ici.
    forbidden_fragments = [
        "supabase db ",
        "supabase migration",
        "database/migrations",
        "database/query",
        "functions deploy",
        "functions/deploy",
        "supabase functions deploy",
        "service_role",
        "SERVICE_ROLE",
        "auth.users",
        "/auth/v1/admin/users",
        "external_google_",
        "external_apple_",
        "external_facebook_",
        "external_github_",
        "security_captcha_secret",
        "smtp_",
        "twilio_",
        "password_required_characters\":",
        "password_min_length\":",
        "organizations/$SUPABASE_ORGANIZATION_SLUG/billing",
        "organizations/$SUPABASE_ORGANIZATION_SLUG/subscription",
    ]
    for fragment in forbidden_fragments:
        require(fragment not in text, f"surface interdite détectée: {fragment}")

    # Le workflow doit comparer l'état complet hors HIBP pour détecter tout changement concurrent/inattendu.
    require(
        text.count('stable.pop("password_hibp_enabled", None)') == 2,
        "empreinte avant/après de la configuration hors HIBP obligatoire",
    )
    require("auth-config-before.sha256" in text, "empreinte préflight absente")
    require("after_digest != before_digest" in text, "comparaison postflight absente")
    require(
        "Aucun rollback automatique n'est tenté" in text,
        "le workflow doit refuser un rollback Auth aveugle en cas de concurrence",
    )

    # Le dépôt doit refléter honnêtement l'état hébergé observé, sans le transformer en contrat permanent.
    require("Dernière vérification : 2026-09-06." in status, "date de vérification hébergée absente")
    require("Plan observé le 2026-09-06 : **Free**" in status, "plan Free observé non documenté")
    require("auth_leaked_password_protection" in status, "WARN Advisor HIBP non documenté")
    require("n'est donc **pas activée** en production" in status, "état HIBP réel ambigu")
    require("Cette page est un état daté" in status, "le plan observé ne doit pas être traité comme permanent")
    require("password_hibp_enabled" in status, "champ Management API HIBP non documenté")
    require("PATCH /v1/projects/{ref}/config/auth" in status, "route Management API HIBP non documentée")
    require("ne doit jamais être modifié avec une migration SQL" in status, "interdiction du contournement SQL absente")
    require("workflow prêt, activation hébergée bloquée par le plan actuel" in status,
            "formulation de statut bornée absente")
    require("https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection" in status,
            "référence Supabase sur la protection HIBP absente")

    # La protection disponible dans le dépôt reste au minimum de 12 caractères.
    require("minimum_password_length = 12" in config, "minimum local Auth de 12 caractères absent")
    require("[auth.mfa.totp]" in config and "enroll_enabled = true" in config and "verify_enabled = true" in config,
            "le contrat AAL2 local doit rester actif")

    print(
        "OK workflow Auth V25: manuel, plan Pro+ requis avant Auth, PATCH HIBP seul, état Free/WARN documenté et minimum local 12 conservé."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
