#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-v25-personal-ai-production-readiness.yml"
CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
SETUP_CLI = "supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf"


def errors(text: str) -> list[str]:
    out: list[str] = []
    required = (
        "workflow_dispatch:",
        "permissions:\n  contents: read",
        "runs-on: ubuntu-24.04",
        "timeout-minutes: 20",
        "environment: production",
        'test "$GITHUB_REF" = "refs/heads/main"',
        'test "$VERIFY_CONFIRMATION" = "VERIFY-SINJIRA-V25-PERSONAL-AI"',
        "SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}",
        f"uses: {CHECKOUT}",
        "ref: main",
        "persist-credentials: false",
        f"uses: {SETUP_PYTHON}",
        "python-version: '3.12.14'",
        "check-latest: false",
        "python3 scripts/validate_personal_ai_v25.py",
        "python3 scripts/validate_personal_ai_production_readiness.py",
        "python3 scripts/validate_production_schema_manifest.py",
        '"$SUPABASE_MANAGEMENT_API/projects/$SUPABASE_PROJECT_REF/database/migrations"',
        "--header \"Authorization: Bearer $SUPABASE_ACCESS_TOKEN\"",
        f"uses: {SETUP_CLI}",
        "version: 2.111.0",
        "run: supabase db start",
        "run: supabase test db supabase/tests/personal_ai_v25.test.sql --local",
        "if: always()",
        "run: supabase stop --no-backup || true",
    )
    for marker in required:
        if marker not in text:
            out.append(f"marqueur obligatoire absent: {marker}")

    for forbidden in (
        "pull_request:",
        "push:",
        "schedule:",
        "repository_dispatch:",
        "contents: write",
        "persist-credentials: true",
        "ubuntu-latest",
        "actions/checkout@v",
        "actions/setup-python@v",
        "supabase/setup-cli@v",
        "supabase link",
        "supabase db push",
        "supabase functions deploy",
        "supabase secrets set",
        "supabase migration repair",
        "--linked",
        "--no-verify-jwt",
        "service_role",
        "SERVICE_ROLE",
        "curl -X POST",
        "curl --request POST",
        "curl -X PUT",
        "curl --request PUT",
        "curl -X PATCH",
        "curl --request PATCH",
        "curl -X DELETE",
        "curl --request DELETE",
        "continue-on-error: true",
        "set -x",
    ):
        if forbidden in text:
            out.append(f"capacité interdite détectée: {forbidden}")

    token_lines = [line for line in text.splitlines() if "secrets.SUPABASE_ACCESS_TOKEN" in line]
    if len(token_lines) != 2:
        out.append("SUPABASE_ACCESS_TOKEN doit être référencé exactement dans deux env d'étape")
    if any(not line.startswith("          SUPABASE_ACCESS_TOKEN:") for line in token_lines):
        out.append("SUPABASE_ACCESS_TOKEN doit rester borné aux env d'étape")

    main_pos = text.find('test "$GITHUB_REF" = "refs/heads/main"')
    token_pos = text.find("secrets.SUPABASE_ACCESS_TOKEN")
    if main_pos < 0 or token_pos < 0 or main_pos > token_pos:
        out.append("le refus hors main doit précéder le premier accès au secret")

    if text.count("curl --fail-with-body --silent --show-error") != 1:
        out.append("un seul appel curl distant en lecture est attendu")
    if text.count("/database/migrations") != 1:
        out.append("l'appel distant doit rester borné à l'historique des migrations")
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
        ("python large", text.replace("python-version: '3.12.14'", "python-version: '3.x'", 1)),
        ("cli mutable", text.replace(SETUP_CLI, "supabase/setup-cli@v2", 1)),
        ("cli large", text.replace("version: 2.111.0", "version: latest", 1)),
        ("git write", text.replace("contents: read", "contents: write", 1)),
        ("credentials", text.replace("persist-credentials: false", "persist-credentials: true", 1)),
        ("push trigger", text.replace("  workflow_dispatch:", "  push:\n    branches: [main]\n  workflow_dispatch:", 1)),
        ("remove main guard", text.replace('test "$GITHUB_REF" = "refs/heads/main"', "true", 1)),
        ("remove confirmation", text.replace('test "$VERIFY_CONFIRMATION" = "VERIFY-SINJIRA-V25-PERSONAL-AI"', "true", 1)),
        ("linked", text + "\n# supabase db push --linked\n"),
        ("deploy", text + "\n# supabase functions deploy personal-ai\n"),
        ("secret write", text + "\n# supabase secrets set X=Y\n"),
        ("repair", text + "\n# supabase migration repair\n"),
        ("jwt bypass", text + "\n# --no-verify-jwt\n"),
        ("service role", text + "\n# service_role\n"),
        ("remote POST", text.replace("curl --fail-with-body --silent --show-error", "curl -X POST --fail-with-body --silent --show-error", 1)),
        ("remove local flag", text.replace("personal_ai_v25.test.sql --local", "personal_ai_v25.test.sql", 1)),
        ("remove stop", text.replace("run: supabase stop --no-backup || true", "run: echo stop", 1)),
        ("remove always", text.replace("if: always()", "if: success()", 1)),
        ("remove validator ai", text.replace("python3 scripts/validate_personal_ai_v25.py", "python3 -V", 1)),
        ("remove readiness", text.replace("python3 scripts/validate_personal_ai_production_readiness.py", "python3 -V", 1)),
        ("remove manifest", text.replace("python3 scripts/validate_production_schema_manifest.py", "python3 -V", 1)),
        ("change endpoint", text.replace("/database/migrations", "/database/query", 1)),
        ("continue on error", text + "\n    continue-on-error: true\n"),
        ("shell trace", text.replace("set -euo pipefail", "set -x", 1)),
    ]
    missed: list[str] = []
    for name, mutated in mutations:
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
        if "--self-test" in sys.argv:
            validate(text)
            self_test(text)
        else:
            validate(text)
            print("OK CI production-readiness Mon IA: lancement manuel main-only, runtimes/actions immuables, secret borné, lecture distante migrations uniquement et tests Supabase strictement locaux.")
    except ValueError as exc:
        print(f"ECHEC CI production-readiness Mon IA: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
