#!/usr/bin/env python3
"""Contrat de synthèse A1 pour la répétition d'intégration, sans promotion production."""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWED = ROOT / "supabase/production-reviewed-migration-batch.txt"
LEDGER = ROOT / "supabase/production-migration-ledger.txt"
WORKFLOW = ROOT / ".github/workflows/sinjira-a1-integration-rehearsal.yml"

TRAVEL_MIGRATIONS = (
    ("20260913030500", "sinjira_v25_travel_mode_geo_scope_hardening"),
    ("20260913230000", "sinjira_v25_travel_mode_retention_purge"),
    ("20260914223000", "sinjira_v25_travel_mode_client_visibility_boundary"),
)

REQUIRED_FILES = (
    ".github/workflows/sinjira-public-edge-auth-guard.yml",
    ".github/workflows/sinjira-security-context-response-v25.yml",
    ".github/workflows/sinjira-security-risk-v25.yml",
    ".github/workflows/sinjira-livre-i-private-delivery.yml",
    ".github/workflows/sinjira-account-life-story-a1.yml",
    ".github/workflows/sinjira-live-social-foundation-v25.yml",
    ".github/workflows/sinjira-live-social-safety-v25.yml",
    ".github/workflows/sinjira-live-social-commands-v25.yml",
    ".github/workflows/sinjira-live-social-activation-gate-v25.yml",
    "scripts/validate_edge_function_inventory.py",
    "scripts/validate_security_context_request_security.py",
    "scripts/validate_security_context_response_v25.py",
    "scripts/validate_security_travel_scope_v25.py",
    "scripts/validate_sinjira_livre_i_delivery.py",
    "scripts/validate_get_private_book_url_security.py",
    "scripts/validate_livre_i_entitlement_boundary.py",
    "scripts/validate_livre_i_entitlement_ui.py",
    "scripts/validate_livre_i_source_artifacts.py",
    "scripts/validate_delete_account_v24_5_51.py",
    "scripts/validate_life_story_export_request_security.py",
    "scripts/validate_life_story_legacy_v24_5_2.py",
    "scripts/validate_life_story_delivery_v24_5_50.py",
    "scripts/validate_live_social_foundation_workflow_security.py",
    "scripts/validate_live_social_foundation_v25.py",
    "scripts/validate_live_social_safety_workflow_security.py",
    "scripts/validate_live_social_safety_v25.py",
    "scripts/validate_live_social_share_codes_v25.py",
    "scripts/validate_live_social_commands_workflow_security.py",
    "scripts/validate_live_social_typed_commands_v25.py",
    "scripts/validate_live_social_activation_gate_workflow_security.py",
    "scripts/test_live_social_activation_gate_v25.py",
    "scripts/validate_live_social_activation_gate_v25.py",
    "supabase/functions/security-context/index.ts",
    "supabase/functions/_shared/privateBook.ts",
    "supabase/functions/get-private-book-url/index.ts",
    "supabase/functions/get-private-book-reading-url/index.ts",
    "assets/js/sinjira-private-book-reader.js",
)

REQUIRED_COMMANDS = (
    "python3 scripts/validate_a1_integration_rehearsal.py --self-test",
    "python3 scripts/validate_a1_integration_rehearsal.py",
    "python3 scripts/validate_edge_function_inventory.py",
    "python3 scripts/validate_security_context_request_security.py",
    "python3 scripts/validate_security_context_response_v25.py",
    "python3 scripts/validate_security_travel_scope_v25.py",
    "python3 scripts/validate_sinjira_livre_i_delivery.py",
    "python3 scripts/validate_get_private_book_url_security.py",
    "python3 scripts/validate_livre_i_entitlement_boundary.py",
    "python3 scripts/validate_livre_i_entitlement_ui.py",
    "python3 scripts/validate_livre_i_source_artifacts.py",
    "python3 scripts/validate_delete_account_v24_5_51.py",
    "python3 scripts/validate_life_story_export_request_security.py",
    "python3 scripts/validate_life_story_legacy_v24_5_2.py",
    "python3 scripts/validate_life_story_delivery_v24_5_50.py",
    "python3 scripts/validate_live_social_foundation_workflow_security.py --self-test",
    "python3 scripts/validate_live_social_foundation_workflow_security.py",
    "python3 scripts/validate_live_social_foundation_v25.py",
    "python3 scripts/validate_live_social_safety_workflow_security.py --self-test",
    "python3 scripts/validate_live_social_safety_workflow_security.py",
    "python3 scripts/validate_live_social_safety_v25.py",
    "python3 scripts/validate_live_social_share_codes_v25.py",
    "python3 scripts/validate_live_social_commands_workflow_security.py --self-test",
    "python3 scripts/validate_live_social_commands_workflow_security.py",
    "python3 scripts/validate_live_social_typed_commands_v25.py",
    "python3 scripts/validate_live_social_activation_gate_workflow_security.py --self-test",
    "python3 scripts/validate_live_social_activation_gate_workflow_security.py",
    "python3 scripts/test_live_social_activation_gate_v25.py",
    "python3 scripts/validate_live_social_activation_gate_v25.py",
)

REQUIRED_TRIGGERS = (
    "scripts/validate_a1_integration_rehearsal.py",
    "supabase/production-reviewed-migration-batch.txt",
    "supabase/production-migration-ledger.txt",
    ".github/workflows/sinjira-a1-integration-rehearsal.yml",
    "scripts/validate_live_social_*.py",
    "scripts/test_live_social_activation_gate_v25.py",
    "supabase/migrations/20260908*_sinjira_v25_live_social_*.sql",
    "supabase/tests/live_social_*.test.sql",
    "assets/js/sinjira-live-*.js",
    "assets/css/v25-live-*.css",
    "compte/communaute.html",
    "projets/sinjira/codex/livre-i-delivery-contract.json",
    ".github/workflows/sinjira-live-social-*.yml",
)

FORBIDDEN_WORKFLOW_COMMANDS = (
    "supabase db push",
    "supabase functions deploy",
    "supabase secrets set",
    "supabase link",
)


def fail(message: str) -> None:
    raise ValueError(message)


def has_version(text: str, version: str) -> bool:
    return any(line.strip().startswith(version + " ") for line in text.splitlines())


def normalize_workflow_line(line: str) -> str:
    value = line.strip()
    if value.startswith("run: "):
        value = value[5:].strip()
    return value


def validate_files() -> None:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            fail(f"fichier A1 requis absent: {relative}")
    for version, name in TRAVEL_MIGRATIONS:
        relative = f"supabase/migrations/{version}_{name}.sql"
        if not (ROOT / relative).is_file():
            fail(f"migration Mode Voyage requise absente: {relative}")


def validate_texts(reviewed: str, ledger: str, workflow: str) -> None:
    if "lot de migrations Supabase production explicitement revu" not in reviewed:
        fail("production-reviewed: contrat explicite de revue production absent")
    if "Ce fichier est fail-closed" not in reviewed:
        fail("production-reviewed: caractère fail-closed absent")

    for version, name in TRAVEL_MIGRATIONS:
        if has_version(reviewed, version):
            fail(f"production-reviewed: promotion implicite interdite pour {version}_{name}")
        if has_version(ledger, version):
            fail(f"ledger production: faux déploiement interdit pour {version}_{name}")
        trigger = f"- 'supabase/migrations/{version}_{name}.sql'"
        if workflow.count(trigger) != 2:
            fail(f"workflow A1: migration non surveillée en PR + push: {version}_{name}")

    if workflow.count("permissions:\n  contents: read") != 1:
        fail("workflow A1: permissions lecture seule requises")
    if "contents: write" in workflow:
        fail("workflow A1: permission contents:write interdite")

    for command in FORBIDDEN_WORKFLOW_COMMANDS:
        if command in workflow:
            fail(f"workflow A1: commande production interdite: {command}")

    workflow_lines = [normalize_workflow_line(line) for line in workflow.splitlines()]
    for command in REQUIRED_COMMANDS:
        if workflow_lines.count(command) != 1:
            fail(f"workflow A1: commande requise absente ou dupliquée: {command}")

    for relative in REQUIRED_TRIGGERS:
        trigger = f"- '{relative}'"
        if workflow.count(trigger) != 2:
            fail(f"workflow A1: déclencheur PR + push requis: {relative}")

    if "validate_production_migration_ledger.py" in workflow:
        fail("workflow A1: le garde de répétition ne doit pas transformer le préflight production en test fonctionnel")


def load() -> tuple[str, str, str]:
    return (
        REVIEWED.read_text(encoding="utf-8"),
        LEDGER.read_text(encoding="utf-8"),
        WORKFLOW.read_text(encoding="utf-8"),
    )


def self_test(values: tuple[str, str, str]) -> None:
    reviewed, ledger, workflow = values
    validate_texts(*values)
    version, name = TRAVEL_MIGRATIONS[0]
    migration_trigger = f"      - 'supabase/migrations/{version}_{name}.sql'\n"
    livre_contract_trigger = "      - 'projets/sinjira/codex/livre-i-delivery-contract.json'\n"
    mutations = {
        "promotion reviewed implicite": (
            reviewed + f"\n{version} {name} deadbeef\n",
            ledger,
            workflow,
        ),
        "faux déploiement ledger": (
            reviewed,
            ledger + f"\n{version} {name}\n",
            workflow,
        ),
        "commande de déploiement": (
            reviewed,
            ledger,
            workflow + "\n# supabase db push\n",
        ),
        "permission écriture": (
            reviewed,
            ledger,
            workflow.replace("permissions:\n  contents: read", "permissions:\n  contents: write", 1),
        ),
        "validateur Livre I retiré": (
            reviewed,
            ledger,
            workflow.replace("          python3 scripts/validate_sinjira_livre_i_delivery.py\n", "", 1),
        ),
        "validateur En direct retiré": (
            reviewed,
            ledger,
            workflow.replace("          python3 scripts/validate_live_social_activation_gate_v25.py\n", "", 1),
        ),
        "contrat Livre I non surveillé": (
            reviewed,
            ledger,
            workflow.replace(livre_contract_trigger, "", 1),
        ),
        "migration non surveillée": (
            reviewed,
            ledger,
            workflow.replace(migration_trigger, "", 1),
        ),
    }
    for label, mutated in mutations.items():
        try:
            validate_texts(*mutated)
        except ValueError:
            continue
        fail(f"auto-test non détecté: {label}")
    print(f"OK garde A1: {len(mutations)}/{len(mutations)} dérives critiques détectées")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    validate_files()
    values = load()
    if args.self_test:
        self_test(values)
    else:
        validate_texts(*values)
        print(
            "OK répétition A1: convergences critiques présentes, workflow lecture seule, "
            "aucune promotion reviewed/deployed des migrations Mode Voyage, En direct dark-launch validé."
        )


if __name__ == "__main__":
    main()
