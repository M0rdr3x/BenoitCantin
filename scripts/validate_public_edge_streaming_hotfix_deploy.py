#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/deploy-public-edge-streaming-hotfix.yml"

EXPECTED_SLUGS = {
    "get-document-url",
    "send-game-report",
    "life-story-delivery",
}
CONFIRMATION = "DEPLOY-PUBLIC-EDGE-STREAMING-HOTFIX"
PROJECT_REF = "gpvivleexywljowcqkru"


def trigger_block(text: str) -> str:
    start = text.find("on:\n")
    end = text.find("\npermissions:", start)
    if start < 0 or end < 0:
        return ""
    return text[start:end]


def validate_text(text: str) -> list[str]:
    errors: list[str] = []
    triggers = trigger_block(text)
    if not triggers:
        errors.append("Bloc on:/permissions introuvable.")
    else:
        if "workflow_dispatch:" not in triggers:
            errors.append("Le workflow doit rester workflow_dispatch uniquement.")
        for forbidden in ("\npush:", "\npull_request:", "\nschedule:", "\nworkflow_run:"):
            if forbidden in triggers:
                errors.append(f"Trigger automatique interdit: {forbidden.strip()}")

    required_markers = (
        "default: false",
        "type: boolean",
        "expected_sha:",
        f"EXPECTED_CONFIRMATION: {CONFIRMATION}",
        "permissions:\n  contents: read",
        "cancel-in-progress: false",
        "environment: production",
        f"PROJECT_REF: {PROJECT_REF}",
        "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
        "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
        "supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf",
        "version: 2.111.0",
        "persist-credentials: false",
        'test "$APPLY_REQUESTED" = "true"',
        'test "$EXPECTED_SHA_INPUT" = "$GITHUB_SHA"',
        'test "$CONFIRMATION_INPUT" = "$EXPECTED_CONFIRMATION"',
        'test "$GITHUB_REF" = "refs/heads/main"',
        "python3 scripts/validate_public_edge_streaming_hotfix_deploy.py --self-test",
        "python3 scripts/validate_public_edge_streaming_hotfix_deploy.py",
        "python3 scripts/validate_get_document_url_security.py",
        "python3 scripts/validate_send_game_report_security.py",
        "python3 scripts/validate_life_story_delivery_v24_5_50.py",
        "python3 scripts/validate_edge_function_inventory.py",
        "python3 scripts/validate_edge_response_privacy_v24_5_48.py",
        "supabase functions list --project-ref",
        "application/json-patch+json",
        'test "$status" = "415"',
    )
    for marker in required_markers:
        if marker not in text:
            errors.append(f"Marqueur production requis absent: {marker}")

    if text.count("environment: production") != 1:
        errors.append("Exactement un job doit traverser Environment production.")
    if text.count("persist-credentials: false") != 2:
        errors.append("Les deux checkouts doivent désactiver les credentials persistés.")
    if text.count('test "$APPLY_REQUESTED" = "true"') != 2:
        errors.append("apply=true doit être revalidé avant et après Environment.")
    if text.count('test "$EXPECTED_SHA_INPUT" = "$GITHUB_SHA"') != 2:
        errors.append("Le SHA exact doit être revalidé avant et après Environment.")
    if text.count('test "$CONFIRMATION_INPUT" = "$EXPECTED_CONFIRMATION"') != 2:
        errors.append("La confirmation exacte doit être revalidée avant et après Environment.")
    if text.count('test "$GITHUB_REF" = "refs/heads/main"') != 2:
        errors.append("La branche main doit être revalidée avant et après Environment.")

    deploys = re.findall(
        r"^\s*supabase functions deploy ([a-z0-9-]+) --project-ref \"\$PROJECT_REF\" --no-verify-jwt\s*$",
        text,
        flags=re.MULTILINE,
    )
    if len(deploys) != 3 or set(deploys) != EXPECTED_SLUGS:
        errors.append(
            "Le workflow doit déployer exactement les trois slugs approuvés avec --no-verify-jwt."
        )
    if text.count("--no-verify-jwt") != 3:
        errors.append("--no-verify-jwt doit apparaître exactement sur les trois deploys.")
    if text.count("python3 scripts/validate_edge_response_privacy_v24_5_48.py") != 2:
        errors.append("Le contrat confidentialité Edge doit être revalidé avant et après Environment.")

    lower = text.lower()
    for pattern, label in (
        (r"\bsupabase\s+db\b", "commande base de données"),
        (r"\bsupabase\s+migration\b", "commande migration"),
        (r"\bsupabase\s+secrets\b", "mutation de secrets"),
        (r"\bsupabase\s+functions\s+delete\b", "suppression Edge"),
        (r"\bsupabase\s+link\b", "liaison implicite de projet"),
    ):
        if re.search(pattern, lower):
            errors.append(f"Mutation hors périmètre interdite: {label}.")

    for marker in (
        "contents: write",
        "actions: write",
        "deployments: write",
        "id-token: write",
        "continue-on-error:",
        "persist-credentials: true",
        "cancel-in-progress: true",
        "set -x",
    ):
        if marker in text:
            errors.append(f"Affaiblissement CI interdit: {marker}")

    preflight_start = text.find("  preflight:")
    deploy_start = text.find("\n  deploy:")
    if preflight_start < 0 or deploy_start < 0 or deploy_start <= preflight_start:
        errors.append("Séparation preflight/deploy introuvable.")
    else:
        preflight = text[preflight_start:deploy_start]
        deploy = text[deploy_start:]
        if "secrets.SUPABASE_ACCESS_TOKEN" in preflight:
            errors.append("Le secret Supabase ne doit jamais entrer dans le job préflight.")
        if "environment: production" in preflight:
            errors.append("Le préflight non mutant ne doit pas traverser Environment production.")
        if "secrets.SUPABASE_ACCESS_TOKEN" not in deploy:
            errors.append("Le job deploy doit recevoir le token uniquement après Environment.")

    if text.count("Content-Type: application/json-patch+json") != 1:
        errors.append("Le postflight réseau doit tester exactement une fois le media type non exact.")
    if "for slug in get-document-url send-game-report life-story-delivery; do" not in text:
        errors.append("Le postflight doit parcourir exactement les trois slugs.")

    return errors


def self_test(text: str) -> None:
    clean = validate_text(text)
    if clean:
        raise SystemExit("ERREUR auto-test workflow hotfix: cas sain refusé: " + " | ".join(clean))

    mutations = {
        "trigger push": text.replace("  workflow_dispatch:", "  push:", 1),
        "confirmation affaiblie": text.replace(
            f"EXPECTED_CONFIRMATION: {CONFIRMATION}",
            "EXPECTED_CONFIRMATION: DEPLOY",
            1,
        ),
        "Environment retiré": text.replace("    environment: production\n", "", 1),
        "main retiré": text.replace(
            '          test "$GITHUB_REF" = "refs/heads/main" || {',
            '          test -n "$GITHUB_REF" || {',
            1,
        ),
        "slug élargi": text.replace(
            "supabase functions deploy send-game-report --project-ref \"$PROJECT_REF\" --no-verify-jwt",
            "supabase functions deploy admin-users --project-ref \"$PROJECT_REF\" --no-verify-jwt",
            1,
        ),
        "JWT flag retiré": text.replace(
            "supabase functions deploy get-document-url --project-ref \"$PROJECT_REF\" --no-verify-jwt",
            "supabase functions deploy get-document-url --project-ref \"$PROJECT_REF\"",
            1,
        ),
        "DB mutation ajoutée": text.replace(
            "supabase functions deploy life-story-delivery --project-ref \"$PROJECT_REF\" --no-verify-jwt",
            "supabase functions deploy life-story-delivery --project-ref \"$PROJECT_REF\" --no-verify-jwt\n          supabase db push --project-ref \"$PROJECT_REF\"",
            1,
        ),
        "secret au préflight": text.replace(
            "      - name: Calculer les empreintes source à déployer",
            "      - name: Secret interdit\n        env:\n          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n        run: echo interdit\n\n      - name: Calculer les empreintes source à déployer",
            1,
        ),
        "credentials checkout": text.replace("persist-credentials: false", "persist-credentials: true", 1),
        "contrat confidentialité post-Environment retiré": text.replace(
            "          python3 scripts/validate_edge_response_privacy_v24_5_48.py\n",
            "",
            1,
        ),
        "postflight 415 retiré": text.replace('test "$status" = "415"', 'test -n "$status"', 1),
        "MIME postflight retiré": text.replace("Content-Type: application/json-patch+json", "Content-Type: application/json", 1),
    }
    for label, mutated in mutations.items():
        if mutated == text:
            raise SystemExit(f"ERREUR auto-test workflow hotfix: mutation sans effet: {label}")
        if not validate_text(mutated):
            raise SystemExit(f"ERREUR auto-test workflow hotfix: affaiblissement non détecté: {label}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valide le workflow manuel de déploiement des trois Edge Functions publiques."
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        text = WORKFLOW.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        print(f"ECHEC workflow hotfix Edge: {exc}")
        return 1

    if args.self_test:
        self_test(text)
        print("OK auto-test workflow hotfix Edge public.")
        return 0

    errors = validate_text(text)
    if errors:
        print(f"ECHEC workflow hotfix Edge: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print(
        "OK workflow hotfix Edge: workflow_dispatch uniquement, main+SHA+confirmation+apply revalidés, "
        "Environment production, secret post-frontière, 3 slugs exacts, aucune DB/migration et postflight HTTP 415."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
