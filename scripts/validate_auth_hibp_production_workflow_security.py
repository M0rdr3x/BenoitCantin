#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-v25-auth-password-hardening.yml"

CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
TOKEN_REF = "SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}"
MAIN_GUARD = 'test "$GITHUB_REF" = "refs/heads/main"'
CONFIRM_GUARD = 'test "$AUTH_CONFIRMATION" = "ENABLE-SINJIRA-V25-LEAKED-PASSWORD-PROTECTION"'
ORG_ENDPOINT = "$SUPABASE_MANAGEMENT_API/organizations/$SUPABASE_ORGANIZATION_SLUG"
AUTH_ENDPOINT = "$SUPABASE_MANAGEMENT_API/projects/$SUPABASE_PROJECT_REF/config/auth"
ADVISOR_ENDPOINT = "$SUPABASE_MANAGEMENT_API/projects/$SUPABASE_PROJECT_REF/advisors/security"
PATCH_PAYLOAD = '--data \'{"password_hibp_enabled":true}\' \\'


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
        "timeout-minutes: 10",
        "environment: production",
        "SUPABASE_PROJECT_REF: gpvivleexywljowcqkru",
        "SUPABASE_ORGANIZATION_SLUG: glaxqwyumblfqmzusqbt",
        MAIN_GUARD,
        CONFIRM_GUARD,
        f"uses: {CHECKOUT}",
        "ref: main",
        "persist-credentials: false",
        f"uses: {SETUP_PYTHON}",
        "python-version: '3.12.14'",
        "check-latest: false",
        "python3 scripts/validate_auth_password_hardening_workflow.py",
        'eligible = {"pro", "team", "enterprise"}',
        "if plan not in eligible:",
        "Activation HIBP bloquée avant PATCH",
        "password_min_length",
        "minimum < 12",
        'stable.pop("password_hibp_enabled", None)',
        "auth-config-before.sha256",
        "after_digest != before_digest",
        "Aucun rollback automatique n'est tenté",
        "Seul password_hibp_enabled a été autorisé à passer à true.",
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
        "supabase db ",
        "supabase migration",
        "supabase functions",
        "supabase secrets",
        "service_role",
        "SERVICE_ROLE",
        "--linked",
        "--no-verify-jwt",
        "continue-on-error:",
        "set -x",
        "database/migrations",
        "database/query",
        "/auth/v1/admin/users",
        "auth.users",
        "password_required_characters\":",
        "password_min_length\":",
        "organizations/$SUPABASE_ORGANIZATION_SLUG/billing",
        "organizations/$SUPABASE_ORGANIZATION_SLUG/subscription",
    ):
        if forbidden in text:
            out.append(f"capacité interdite détectée: {forbidden}")

    for method in ("POST", "PUT", "DELETE"):
        if f"--request {method}" in text or f"-X {method}" in text:
            out.append(f"méthode Management API interdite: {method}")
    if text.count("--request PATCH") != 1:
        out.append("un unique PATCH Management API est autorisé")

    data_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("--data")]
    if data_lines != [PATCH_PAYLOAD]:
        out.append(f"payload PATCH inattendu: {data_lines}")

    if text.count(ORG_ENDPOINT) != 1:
        out.append("un unique GET organisation/plan est attendu")
    if text.count(AUTH_ENDPOINT) != 3:
        out.append("/config/auth doit apparaître exactement pour GET avant, PATCH, GET après")
    if text.count(ADVISOR_ENDPOINT) != 1:
        out.append("un unique endpoint Security Advisor est attendu")

    secret_refs = set(re.findall(r"secrets\.([A-Z0-9_]+)", text))
    if secret_refs != {"SUPABASE_ACCESS_TOKEN"}:
        out.append(f"secrets GitHub inattendus: {sorted(secret_refs)}")

    token_lines = [line for line in text.splitlines() if "secrets.SUPABASE_ACCESS_TOKEN" in line]
    if len(token_lines) != 6:
        out.append("SUPABASE_ACCESS_TOKEN doit être référencé exactement dans six env d'étape")
    for line in token_lines:
        if not re.fullmatch(r" {10}SUPABASE_ACCESS_TOKEN: \$\{\{ secrets\.SUPABASE_ACCESS_TOKEN \}\}", line):
            out.append(f"secret production hors env d'étape: {line.strip()}")

    blocks = step_blocks(text)
    checkout_blocks = [block for _, block in blocks if "uses: actions/checkout@" in block]
    if len(checkout_blocks) != 1:
        out.append("exactement un checkout est attendu")
    else:
        checkout = checkout_blocks[0]
        if "ref: main" not in checkout or "persist-credentials: false" not in checkout:
            out.append("checkout production doit forcer main sans credentials persistés")
        if "secrets." in checkout or "SUPABASE_ACCESS_TOKEN:" in checkout:
            out.append("aucun secret production ne doit être exposé à checkout")

    python_blocks = [block for _, block in blocks if "uses: actions/setup-python@" in block]
    if len(python_blocks) != 1:
        out.append("exactement un setup-python est attendu")
    elif "secrets." in python_blocks[0] or "SUPABASE_ACCESS_TOKEN:" in python_blocks[0]:
        out.append("aucun secret production ne doit être exposé à setup-python")

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
    org_at = text.find(ORG_ENDPOINT)
    auth_at = text.find(AUTH_ENDPOINT)
    patch_at = text.find("--request PATCH")
    advisor_at = text.find(ADVISOR_ENDPOINT)
    if min(confirm_at, org_at, auth_at, patch_at, advisor_at) < 0 or not confirm_at < org_at < auth_at < patch_at < advisor_at:
        out.append("ordre obligatoire: confirmation → plan → GET Auth → PATCH HIBP → Advisor")

    setup_python_at = text.find(f"uses: {SETUP_PYTHON}")
    static_check_at = text.find("python3 scripts/validate_auth_password_hardening_workflow.py")
    if setup_python_at < 0 or static_check_at < 0 or setup_python_at > static_check_at:
        out.append("setup-python doit précéder le validateur statique Auth")

    if text.count('stable.pop("password_hibp_enabled", None)') != 2:
        out.append("empreinte avant/après hors HIBP obligatoire exactement deux fois")

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
        ("timeout élargi", text.replace("    timeout-minutes: 10", "    timeout-minutes: 60", 1)),
        ("token job-level", text.replace("          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}", "      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}", 1)),
        ("secret additionnel", text + "\n# ${{ secrets.SUPABASE_DB_PASSWORD }}\n"),
        ("POST", text.replace("--request PATCH", "--request POST", 1)),
        ("PUT", text.replace("--request PATCH", "--request PUT", 1)),
        ("DELETE", text.replace("--request PATCH", "--request DELETE", 1)),
        ("second PATCH", text + "\n# --request PATCH\n"),
        ("payload élargi", text.replace('{"password_hibp_enabled":true}', '{"password_hibp_enabled":true,"password_min_length":8}', 1)),
        ("endpoint Auth changé", text.replace(AUTH_ENDPOINT, "$SUPABASE_MANAGEMENT_API/projects/$SUPABASE_PROJECT_REF/database/query", 1)),
        ("endpoint Advisor changé", text.replace(ADVISOR_ENDPOINT, "$SUPABASE_MANAGEMENT_API/projects/$SUPABASE_PROJECT_REF/advisors/performance", 1)),
        ("plan Free autorisé", text.replace('{"pro", "team", "enterprise"}', '{"free", "pro", "team", "enterprise"}', 1)),
        ("refus plan retiré", text.replace("if plan not in eligible:", "if False:", 1)),
        ("seuil 12 retiré", text.replace("minimum < 12", "minimum < 8", 1)),
        ("validateur retiré", text.replace("python3 scripts/validate_auth_password_hardening_workflow.py", "python3 -V", 1)),
        ("db password", text + "\n# SUPABASE_DB_PASSWORD\n"),
        ("db push", text + "\n# supabase db push --linked\n"),
        ("deploy", text + "\n# supabase functions deploy auth\n"),
        ("secret write", text + "\n# supabase secrets set X=Y\n"),
        ("migration repair", text + "\n# supabase migration repair\n"),
        ("service role", text + "\n# service_role\n"),
        ("continue on error", text + "\n    continue-on-error: true\n"),
        ("shell trace", text.replace("set -euo pipefail", "set -x", 1)),
        ("empreinte retirée", text.replace('stable.pop("password_hibp_enabled", None)', "pass", 1)),
        ("rollback aveugle", text.replace("Aucun rollback automatique n'est tenté", "Rollback automatique autorisé", 1)),
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
                "OK CI HIBP production: lancement manuel main-only, runtime/actions immuables, "
                "token borné, plan Pro+ requis et PATCH unique limité à password_hibp_enabled=true."
            )
    except ValueError as exc:
        print(f"ECHEC CI HIBP production: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
