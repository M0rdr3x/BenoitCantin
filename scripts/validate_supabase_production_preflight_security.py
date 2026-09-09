#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "supabase-production-preflight.yml"

LOCAL_VALIDATE = "- name: Vérifier le dépôt Supabase"
BUILD_WORKSPACE = "- name: Construire le workspace production protégé"
INSTALL_CLI = "- name: Installer Supabase CLI"
VERIFY_CLI = "- name: Vérifier Supabase CLI"

PINNED_ACTIONS = {
    "actions/checkout": "d23441a48e516b6c34aea4fa41551a30e30af803",
    "actions/setup-python": "ece7cb06caefa5fff74198d8649806c4678c61a1",
    "supabase/setup-cli": "3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
}
SUPABASE_SETUP_CLI_SHA = PINNED_ACTIONS["supabase/setup-cli"]
SUPABASE_SETUP_CLI_USE = f"uses: supabase/setup-cli@{SUPABASE_SETUP_CLI_SHA}"
MANUAL_ONLY_GUARD = "if: ${{ github.event_name == 'workflow_dispatch' }}"
MANUAL_AUTH_GUARD = MANUAL_ONLY_GUARD
REMOTE_PREFLIGHT_GUARD = "if: ${{ github.event_name == 'workflow_dispatch' && steps.auth.outputs.ready == 'true' }}"
APPLY_GUARD = "if: ${{ github.event_name == 'workflow_dispatch' && inputs.apply == true && steps.auth.outputs.ready == 'true' }}"

REMOTE_REQUIREMENTS = {
    "Détecter les secrets de connexion Supabase": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Auditer l’inventaire Edge Functions de production": ("SUPABASE_ACCESS_TOKEN",),
    "Lier le projet de production dans le workspace protégé": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Exporter l'historique exact des migrations de production": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Auditer les fonctions SQL déjà en production": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Comparer l'historique des migrations": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Prévisualiser les migrations sans modifier la production": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Appliquer les migrations de production depuis le workspace protégé": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Auditer les fonctions SQL après migrations": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
    "Garantir les secrets Edge Functions indispensables": ("SUPABASE_ACCESS_TOKEN", "OPTIONAL_RESEND_API_KEY"),
    "Déployer toutes les Edge Functions du workspace protégé": ("SUPABASE_ACCESS_TOKEN",),
    "Vérifier les Edge Functions déployées": ("SUPABASE_ACCESS_TOKEN",),
    "Vérifier l'historique et le dry-run après déploiement": ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD"),
}

REMOTE_PREFLIGHT_STEPS = (
    "Auditer l’inventaire Edge Functions de production",
    "Lier le projet de production dans le workspace protégé",
    "Exporter l'historique exact des migrations de production",
    "Publier l'historique distant comme artefact de prévol",
    "Auditer les fonctions SQL déjà en production",
    "Comparer l'historique des migrations",
    "Prévisualiser les migrations sans modifier la production",
)

MUTATING_OR_POST_APPLY_STEPS = (
    "Appliquer les migrations de production depuis le workspace protégé",
    "Auditer les fonctions SQL après migrations",
    "Garantir les secrets Edge Functions indispensables",
    "Déployer toutes les Edge Functions du workspace protégé",
    "Vérifier les Edge Functions déployées",
    "Vérifier l'historique et le dry-run après déploiement",
)


def step_block(text: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = text.find(marker)
    if start < 0:
        return ""
    following = text.find("\n      - name: ", start + len(marker))
    return text[start:] if following < 0 else text[start:following]


def validate_text(text: str) -> list[str]:
    errors: list[str] = []

    steps_at = text.find("    steps:\n")
    job_env_at = text.find("    env:\n")
    if steps_at < 0:
        errors.append("Bloc jobs.sync.steps introuvable.")
        return errors

    if 0 <= job_env_at < steps_at:
        job_env = text[job_env_at:steps_at]
        for secret in ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD", "OPTIONAL_RESEND_API_KEY", "secrets."):
            if secret in job_env:
                errors.append(f"Secret interdit au niveau jobs.sync.env: {secret}")

    for action, sha in PINNED_ACTIONS.items():
        expected = f"uses: {action}@{sha}"
        if expected not in text:
            errors.append(
                f"L'action {action} doit être épinglée au SHA vérifié {sha}, "
                "jamais à une branche ou un tag mobile."
            )

    positions = {
        "validation locale": text.find(LOCAL_VALIDATE),
        "workspace protégé": text.find(BUILD_WORKSPACE),
        "installation CLI": text.find(INSTALL_CLI),
        "vérification CLI": text.find(VERIFY_CLI),
    }
    for label, pos in positions.items():
        if pos < 0:
            errors.append(f"Étape obligatoire absente: {label}")

    if all(pos >= 0 for pos in positions.values()):
        if not positions["validation locale"] < positions["installation CLI"]:
            errors.append("La validation locale doit précéder l'installation Supabase CLI.")
        if not positions["workspace protégé"] < positions["installation CLI"]:
            errors.append("Le workspace fail-closed doit être construit avant l'installation Supabase CLI.")
        if not positions["installation CLI"] < positions["vérification CLI"]:
            errors.append("La vérification Supabase CLI doit suivre son installation.")

    local_block = step_block(text, "Vérifier le dépôt Supabase")
    for command in (
        "python scripts/validate_supabase.py",
        "python scripts/validate_edge_function_inventory.py",
        "python scripts/validate_social_rls_contract.py",
        "python scripts/validate_production_migration_ledger.py",
    ):
        if command not in local_block:
            errors.append(f"Validation locale manquante avant CLI: {command}")
    if "supabase " in local_block:
        errors.append("La validation locale pré-CLI ne doit appeler aucune commande Supabase CLI.")

    build_block = step_block(text, "Construire le workspace production protégé")
    if "python scripts/build_supabase_production_workspace.py --output .prod-workspace/supabase" not in build_block:
        errors.append("Le builder fail-closed du workspace production est absent.")

    install_cli_block = step_block(text, "Installer Supabase CLI")
    if MANUAL_ONLY_GUARD not in install_cli_block:
        errors.append("L'installation Supabase CLI doit être réservée à workflow_dispatch manuel.")
    if SUPABASE_SETUP_CLI_USE not in install_cli_block:
        errors.append(
            "L'action supabase/setup-cli doit être épinglée au SHA vérifié "
            f"{SUPABASE_SETUP_CLI_SHA}, jamais à une branche ou un tag mobile."
        )

    verify_cli_block = step_block(text, "Vérifier Supabase CLI")
    if MANUAL_ONLY_GUARD not in verify_cli_block:
        errors.append("La vérification Supabase CLI doit être réservée à workflow_dispatch manuel.")

    auth_block = step_block(text, "Détecter les secrets de connexion Supabase")
    if MANUAL_AUTH_GUARD not in auth_block:
        errors.append("Les secrets de connexion production doivent être accessibles uniquement en workflow_dispatch manuel.")

    for name in REMOTE_PREFLIGHT_STEPS:
        block = step_block(text, name)
        if not block:
            errors.append(f"Étape de préflight distant obligatoire absente: {name}")
        elif REMOTE_PREFLIGHT_GUARD not in block:
            errors.append(f"Étape distante accessible hors lancement manuel: {name}")

    for name in MUTATING_OR_POST_APPLY_STEPS:
        block = step_block(text, name)
        if not block:
            errors.append(f"Étape apply obligatoire absente: {name}")
        elif APPLY_GUARD not in block:
            errors.append(f"Étape apply sans triple garde workflow_dispatch + apply=true + auth: {name}")

    for name, required in REMOTE_REQUIREMENTS.items():
        block = step_block(text, name)
        if not block:
            errors.append(f"Étape distante obligatoire absente: {name}")
            continue
        if "\n        env:\n" not in block:
            errors.append(f"L'étape distante n'a pas d'env local: {name}")
            continue
        for key in required:
            if f"          {key}:" not in block:
                errors.append(f"Secret/env {key} non borné à l'étape: {name}")

    secret_step = step_block(text, "Garantir les secrets Edge Functions indispensables")
    if "SUPABASE_DB_PASSWORD:" in secret_step:
        errors.append("Le mot de passe DB ne doit pas être exposé à l'étape des secrets Edge Functions.")

    apply_block = step_block(text, "Appliquer les migrations de production depuis le workspace protégé")
    if "(cd .prod-workspace && supabase db push --linked --password \"$SUPABASE_DB_PASSWORD\")" not in apply_block:
        errors.append("Le db push production doit rester borné au workspace protégé.")

    secret_ref_lines = [line for line in text.splitlines() if "${{ secrets." in line]
    for line in secret_ref_lines:
        if not re.match(r"^ {10}(SUPABASE_ACCESS_TOKEN|SUPABASE_DB_PASSWORD|OPTIONAL_RESEND_API_KEY):", line):
            errors.append(f"Référence de secret hors env d'étape: {line.strip()}")

    summary = step_block(text, "ÉTAT PRODUCTION")
    for marker in (
        "🟡 PRÉVOL PR",
        "🟡 PRÉVOL SEULEMENT",
        "aucun secret production exposé au run PR",
        "aucun secret production exposé au run push",
        "🟡 PRÉVOL MANUEL SEULEMENT",
        "✅ APPLIQUÉ ET VÉRIFIÉ",
    ):
        if marker not in summary:
            errors.append(f"Résumé production sans frontière de confiance attendue: {marker}")

    return errors


def main() -> int:
    if not WORKFLOW.is_file():
        print(f"Workflow introuvable: {WORKFLOW}")
        return 2
    errors = validate_text(WORKFLOW.read_text(encoding="utf-8"))
    if errors:
        print("Contrat sécurité préflight Supabase production: ÉCHEC")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Contrat sécurité préflight Supabase production: OK")
    print("- lot/ledger/workspace vérifiés avant Supabase CLI")
    print("- aucun secret au niveau du job")
    print("- PR/push strictement locaux, sans secrets production ni Supabase CLI")
    print("- toutes les actions réutilisables du workflow production sont épinglées à des SHA vérifiés")
    print("- installation/vérification Supabase CLI réservées à workflow_dispatch")
    print("- préflight distant réservé à workflow_dispatch")
    print("- écritures protégées par workflow_dispatch + apply=true + auth")
    return 0


if __name__ == "__main__":
    sys.exit(main())
