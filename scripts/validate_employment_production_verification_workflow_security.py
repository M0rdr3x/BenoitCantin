#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-v25-employment-production.yml"

CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
TOKEN_REF = "SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}"
MAIN_GUARD = 'test "$GITHUB_REF" = "refs/heads/main"'
CONFIRM_GUARD = 'test "$VERIFY_CONFIRMATION" = "VERIFY-SINJIRA-V25-EMPLOYMENT"'
ENDPOINT = "/projects/$SUPABASE_PROJECT_REF/database/migrations"


def trigger_block(text: str) -> str:
    start = text.find("on:\n")
    end = text.find("\npermissions:", start + 1)
    return "" if start < 0 or end < 0 else text[start:end]


def step_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^      - name: (.+)$", text))
    blocks: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((match.group(1).strip(), text[match.start():end]))
    return blocks


def errors(text: str) -> list[str]:
    out: list[str] = []

    triggers = trigger_block(text)
    if not triggers or "  workflow_dispatch:" not in triggers:
        out.append("workflow_dispatch manuel obligatoire")
    for forbidden_trigger in ("  pull_request:", "  push:", "  schedule:", "  repository_dispatch:"):
        if forbidden_trigger in triggers:
            out.append(f"déclencheur production interdit: {forbidden_trigger.strip()}")

    required = (
        "permissions:\n  contents: read",
        "runs-on: ubuntu-24.04",
        "timeout-minutes: 15",
        "environment: production",
        MAIN_GUARD,
        CONFIRM_GUARD,
        f"uses: {CHECKOUT}",
        "ref: main",
        "persist-credentials: false",
        f"uses: {SETUP_PYTHON}",
        "python-version: '3.12.14'",
        "check-latest: false",
        "python3 scripts/validate_employment_v25.py",
        "python3 scripts/validate_employment_production_deploy_workflow.py",
        "python3 scripts/validate_production_schema_manifest.py",
        ENDPOINT,
        "curl --fail-with-body --silent --show-error",
        'Authorization: Bearer $SUPABASE_ACCESS_TOKEN',
        "if observed != employment:",
        "if len(matches) != 1:",
        "Vérification Emploi V25 terminée en lecture seule.",
        "Aucune migration, aucune Edge Function et aucun secret n'ont été modifiés",
        "Emploi reste séparé du Registre personnel",
    )
    for marker in required:
        if marker not in text:
            out.append(f"marqueur obligatoire absent: {marker}")

    for forbidden in (
        "ubuntu-latest",
        "contents: write",
        "persist-credentials: true",
        "actions/checkout@v",
        "actions/setup-python@v",
        "SUPABASE_DB_PASSWORD",
        "supabase/setup-cli@",
        "supabase link",
        "supabase db push",
        "supabase migration repair",
        "supabase functions deploy",
        "supabase secrets set",
        "service_role",
        "SERVICE_ROLE",
        "--linked",
        "--no-verify-jwt",
        "continue-on-error:",
        "set -x",
        "curl -X POST",
        "curl --request POST",
        "curl -X PUT",
        "curl --request PUT",
        "curl -X PATCH",
        "curl --request PATCH",
        "curl -X DELETE",
        "curl --request DELETE",
        "--data ",
        "--data=",
        "--data-binary",
        "--form ",
    ):
        if forbidden in text:
            out.append(f"capacité interdite détectée: {forbidden}")

    blocks = step_blocks(text)
    checkout_blocks = [block for _, block in blocks if "uses: actions/checkout@" in block]
    if len(checkout_blocks) != 1:
        out.append("exactement un checkout est attendu")
    elif "secrets." in checkout_blocks[0] or "SUPABASE_ACCESS_TOKEN:" in checkout_blocks[0]:
        out.append("aucun secret production ne doit être exposé à checkout")

    python_blocks = [block for _, block in blocks if "uses: actions/setup-python@" in block]
    if len(python_blocks) != 1:
        out.append("exactement un setup-python est attendu")
    elif "secrets." in python_blocks[0] or "SUPABASE_ACCESS_TOKEN:" in python_blocks[0]:
        out.append("aucun secret production ne doit être exposé à setup-python")

    token_lines = [line for line in text.splitlines() if "secrets.SUPABASE_ACCESS_TOKEN" in line]
    if len(token_lines) != 2:
        out.append("SUPABASE_ACCESS_TOKEN doit être référencé exactement dans deux env d'étape")
    for line in token_lines:
        if not re.fullmatch(r" {10}SUPABASE_ACCESS_TOKEN: \$\{\{ secrets\.SUPABASE_ACCESS_TOKEN \}\}", line):
            out.append(f"secret production hors env d'étape: {line.strip()}")

    for name, block in blocks:
        if "$SUPABASE_ACCESS_TOKEN" in block and TOKEN_REF not in block:
            out.append(f"étape utilisant le token sans env borné: {name}")
        if "uses:" in block and ("secrets.SUPABASE_ACCESS_TOKEN" in block or "SUPABASE_ACCESS_TOKEN:" in block):
            out.append(f"secret production exposé à une action réutilisable: {name}")

    main_at = text.find(MAIN_GUARD)
    token_at = text.find("secrets.SUPABASE_ACCESS_TOKEN")
    if main_at < 0 or token_at < 0 or main_at > token_at:
        out.append("le refus hors main doit précéder le premier accès au secret")

    confirm_at = text.find(CONFIRM_GUARD)
    history_at = text.find("Vérifier l'historique Emploi en lecture seule")
    if confirm_at < 0 or history_at < 0 or confirm_at > history_at:
        out.append("la confirmation explicite doit précéder la lecture distante")

    if text.count("curl --fail-with-body --silent --show-error") != 1:
        out.append("une seule commande curl distante en lecture est autorisée")
    if text.count(ENDPOINT) != 1:
        out.append("l'appel distant doit rester borné à un seul endpoint migrations")

    contracts_at = text.find("Vérifier les contrats Emploi")
    history_at = text.find("Vérifier l'historique Emploi en lecture seule")
    summary_at = text.find("Résumé lecture seule")
    if min(contracts_at, history_at, summary_at) < 0 or not contracts_at < history_at < summary_at:
        out.append("ordre obligatoire: contrats locaux → historique distant → résumé lecture seule")

    return out


def validate(text: str) -> None:
    found = errors(text)
    if found:
        raise ValueError("; ".join(found))


def self_test(text: str) -> None:
    mutations = [
        ("runner mutable", text.replace("runs-on: ubuntu-24.04", "runs-on: ubuntu-latest", 1)),
        ("checkout mutable", text.replace(CHECKOUT, "actions/checkout@v6", 1)),
        ("python mutable", text.replace(SETUP_PYTHON, "actions/setup-python@v6", 1)),
        ("python large", text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)),
        ("python latest", text.replace("check-latest: false", "check-latest: true", 1)),
        ("git write", text.replace("contents: read", "contents: write", 1)),
        ("credentials persistés", text.replace("persist-credentials: false", "persist-credentials: true", 1)),
        ("push trigger", text.replace("  workflow_dispatch:", "  push:\n    branches: [main]\n  workflow_dispatch:", 1)),
        ("main guard retiré", text.replace(MAIN_GUARD, "true", 1)),
        ("confirmation retirée", text.replace(CONFIRM_GUARD, "true", 1)),
        ("checkout autre ref", text.replace("          ref: main", "          ref: develop", 1)),
        ("environnement retiré", text.replace("    environment: production", "    environment: staging", 1)),
        ("timeout retiré", text.replace("    timeout-minutes: 15", "    timeout-minutes: 60", 1)),
        ("token job-level", text.replace("          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}", "      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}", 1)),
        ("remote POST", text.replace("curl --fail-with-body --silent --show-error", "curl -X POST --fail-with-body --silent --show-error", 1)),
        ("remote data", text.replace("--header 'Accept: application/json'", "--data '{}'") ),
        ("endpoint changé", text.replace(ENDPOINT, "/projects/$SUPABASE_PROJECT_REF/database/query", 1)),
        ("second curl", text + "\n# curl --fail-with-body --silent --show-error https://example.invalid\n"),
        ("db password", text + "\n# SUPABASE_DB_PASSWORD\n"),
        ("db push", text + "\n# supabase db push --linked\n"),
        ("deploy", text + "\n# supabase functions deploy employment\n"),
        ("secret write", text + "\n# supabase secrets set X=Y\n"),
        ("migration repair", text + "\n# supabase migration repair\n"),
        ("service role", text + "\n# service_role\n"),
        ("continue on error", text + "\n    continue-on-error: true\n"),
        ("shell trace", text.replace("set -euo pipefail", "set -x", 1)),
        ("validateur emploi retiré", text.replace("python3 scripts/validate_employment_v25.py", "python3 -V", 1)),
        ("validateur workflow retiré", text.replace("python3 scripts/validate_employment_production_deploy_workflow.py", "python3 -V", 1)),
        ("manifest retiré", text.replace("python3 scripts/validate_production_schema_manifest.py", "python3 -V", 1)),
        ("résumé retiré", text.replace("Vérification Emploi V25 terminée en lecture seule.", "Vérification terminée.", 1)),
    ]

    missed: list[str] = []
    for name, mutated in mutations:
        if mutated == text:
            missed.append(f"{name} (mutation sans effet)")
            continue
        try:
            validate(mutated)
        except ValueError:
            continue
        missed.append(name)
    if missed:
        raise ValueError("mutations non détectées: " + ", ".join(missed))
    print(f"OK: {len(mutations)}/{len(mutations)} mutations critiques détectées")


def main() -> int:
    if not WORKFLOW.is_file():
        print(f"ECHEC: workflow absent: {WORKFLOW.relative_to(ROOT)}", file=sys.stderr)
        return 1
    text = WORKFLOW.read_text(encoding="utf-8")
    try:
        validate(text)
        if "--self-test" in sys.argv:
            self_test(text)
        else:
            print(
                "OK CI production Emploi: lancement manuel main-only, runner/Python/actions immuables, "
                "jeton borné à deux étapes et une seule lecture distante de l'historique des migrations."
            )
    except ValueError as exc:
        print(f"ECHEC CI production Emploi: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
