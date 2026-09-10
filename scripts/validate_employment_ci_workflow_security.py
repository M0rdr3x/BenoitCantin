#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-employment-v25.yml"

CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
SETUP_CLI = "supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf"
SELF_TEST = "python3 scripts/validate_employment_ci_workflow_security.py --self-test"
SELF_CHECK = "python3 scripts/validate_employment_ci_workflow_security.py"
ALLOWED_USES = {CHECKOUT, SETUP_PYTHON, SETUP_CLI}

CRITICAL_PATHS = (
    "'compte/emploi.html'",
    "'compte/index.html'",
    "'assets/js/sinjira-employment-v25.js'",
    "'supabase/migrations/**employment**.sql'",
    "'supabase/tests/employment_v25.test.sql'",
    "'scripts/smoke_employment_auth_local.py'",
    "'scripts/validate_employment_v25.py'",
    "'scripts/validate_employment_ci_workflow_security.py'",
    "'scripts/validate_employment_production_deploy_workflow.py'",
    "'scripts/validate_production_schema_manifest.py'",
    "'docs/sinjira-v25-employment-production-readiness.md'",
    "'docs/sinjira-v25-employment-production-deployment-2026-09-05.md'",
    "'.github/workflows/sinjira-employment-v25.yml'",
    "'.github/workflows/sinjira-v25-employment-production.yml'",
)


def fail(message: str) -> None:
    raise ValueError(message)


def block(text: str, start: str, end: str) -> str:
    begin = text.find(start)
    if begin < 0:
        fail(f"section absente: {start.strip()}")
    finish = text.find(end, begin + len(start))
    if finish < 0:
        fail(f"fin de section absente: {end.strip()}")
    return text[begin:finish]


def active_text(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))


def exact_line_count(text: str, line: str) -> int:
    return text.splitlines().count(line)


def trigger_keys(on_block: str) -> set[str]:
    keys: set[str] = set()
    for line in on_block.splitlines()[1:]:
        match = re.match(r"^  ([A-Za-z0-9_-]+):(?:\s|$)", line)
        if match:
            keys.add(match.group(1))
    return keys


def mutate_block(text: str, start: str, end: str, old: str, new: str) -> str:
    section = block(text, start, end)
    if old not in section:
        return text
    return text.replace(section, section.replace(old, new, 1), 1)


def validate(text: str) -> None:
    on = block(text, "on:\n", "\npermissions:")
    if trigger_keys(on) != {"pull_request", "push", "workflow_dispatch"}:
        fail("déclencheurs autorisés exactement: pull_request + push + workflow_dispatch")

    pr = block(text, "  pull_request:", "  push:")
    push = block(text, "  push:", "  workflow_dispatch:")
    for trigger_name, trigger in (("pull_request", pr), ("push", push)):
        if "    branches: [main]" not in trigger:
            fail(f"{trigger_name} doit rester borné à main")
        for path in CRITICAL_PATHS:
            if f"      - {path}" not in trigger:
                fail(f"path critique absent de {trigger_name}: {path}")

    required = (
        "name: SINJIRA V25 — Emploi",
        "permissions:\n  contents: read",
        "  employment-contract:",
        "    runs-on: ubuntu-24.04",
        "    timeout-minutes: 25",
        f"uses: {CHECKOUT}",
        "          persist-credentials: false",
        f"uses: {SETUP_PYTHON}",
        "          python-version: '3.12.14'",
        "          check-latest: false",
        f"uses: {SETUP_CLI}",
        "          version: 2.111.0",
        f"run: {SELF_TEST}",
        f"run: {SELF_CHECK}",
        "python3 scripts/validate_employment_v25.py",
        "python3 scripts/validate_employment_production_deploy_workflow.py",
        "run: python3 scripts/validate_production_schema_manifest.py",
        "run: supabase start",
        "run: supabase test db supabase/tests/employment_v25.test.sql --local",
        'status_env="$(supabase status -o env)"',
        'SINJIRA_LOCAL_API_URL="$API_URL"',
        'SINJIRA_LOCAL_ANON_KEY="$ANON_KEY"',
        "python3 scripts/smoke_employment_auth_local.py",
        "if: always()",
        "run: supabase stop --no-backup || true",
    )
    for marker in required:
        if marker not in text:
            fail(f"marqueur obligatoire absent: {marker}")

    active = active_text(text)
    forbidden = (
        "ubuntu-latest",
        "contents: write",
        "persist-credentials: true",
        "environment: production",
        "${{ secrets.",
        "SUPABASE_ACCESS_TOKEN",
        "SUPABASE_DB_PASSWORD",
        "SERVICE_ROLE",
        "service_role",
        "gpvivleexywljowcqkru",
        "api.supabase.com",
        "supabase link",
        "supabase db push",
        "supabase functions deploy",
        "supabase functions list",
        "supabase secrets set",
        "supabase migration repair",
        "supabase db reset --linked",
        "--linked",
        "--no-verify-jwt",
        "continue-on-error:",
        "set -x",
        "curl ",
        "wget ",
        "gh api",
        "git push",
        "${{ github.token }}",
        "GITHUB_TOKEN:",
        "GH_TOKEN:",
    )
    for marker in forbidden:
        if marker in active:
            fail(f"capacité distante/affaiblissement interdit dans la CI locale: {marker}")

    if text.count("    runs-on:") != 1:
        fail("exactement un job est autorisé dans le workflow Emploi local")
    if exact_line_count(text, "    runs-on: ubuntu-24.04") != 1:
        fail("le job Emploi doit utiliser exactement ubuntu-24.04")
    if exact_line_count(text, "          persist-credentials: false") != 1:
        fail("checkout doit désactiver les credentials exactement une fois")

    uses = re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", text)
    unexpected = [value for value in uses if value not in ALLOWED_USES]
    if unexpected:
        fail("action réutilisable non autorisée/non épinglée: " + ", ".join(unexpected))
    if uses.count(CHECKOUT) != 1 or uses.count(SETUP_PYTHON) != 1 or uses.count(SETUP_CLI) != 1:
        fail("checkout, setup-python et setup-cli doivent chacun apparaître exactement une fois")

    if text.count(SELF_TEST) != 1 or text.count(SELF_CHECK) != 2:
        # SELF_CHECK est aussi un préfixe de SELF_TEST; ce contrôle protège les deux lignes attendues.
        fail("auto-test et vérification du garde Emploi doivent chacun rester uniques")
    self_test_line = f"        run: {SELF_TEST}\n"
    self_check_line = f"        run: {SELF_CHECK}\n"
    if self_test_line not in text or self_check_line not in text:
        fail("lignes exactes auto-test/garde Emploi absentes")
    if text.index(self_test_line) > text.index(self_check_line):
        fail("l'auto-test du garde Emploi doit précéder sa vérification réelle")

    validators_at = text.find("Valider le contrat Emploi V25")
    start_at = text.find("Démarrer Supabase local complet")
    test_at = text.find("Tester Emploi avec pgTAP")
    smoke_at = text.find("Tester Auth et isolation RLS Emploi par HTTP")
    stop_at = text.find("Arrêter Supabase local")
    if min(validators_at, start_at, test_at, smoke_at, stop_at) < 0:
        fail("chaîne locale Emploi incomplète")
    if not validators_at < start_at < test_at < smoke_at < stop_at:
        fail("ordre local obligatoire: contrats → start → pgTAP → smoke HTTP → stop")

    if active.count("supabase start") != 1:
        fail("supabase start local doit apparaître exactement une fois")
    if active.count("supabase test db supabase/tests/employment_v25.test.sql --local") != 1:
        fail("les 31 pgTAP Emploi doivent s'exécuter exactement une fois avec --local")
    if active.count("supabase status -o env") != 1:
        fail("le smoke doit dériver exactement une fois les paramètres de la pile locale")
    if active.count("supabase stop --no-backup || true") != 1:
        fail("l'arrêt Supabase local sans backup doit apparaître exactement une fois")
    if "supabase db start" in active:
        fail("supabase db start seul est insuffisant pour Auth/PostgREST")


def mutations(text: str):
    yield "push main retiré", text.replace("  push:\n    branches: [main]\n", "  push:\n    branches: [develop]\n", 1)
    yield "PR main retirée", text.replace("  pull_request:\n    branches: [main]\n", "  pull_request:\n    branches: [develop]\n", 1)
    yield "trigger supplémentaire", text.replace("  workflow_dispatch:\n", "  pull_request_target:\n  workflow_dispatch:\n", 1)
    yield "path garde PR retiré", mutate_block(
        text, "  pull_request:", "  push:",
        "      - 'scripts/validate_employment_ci_workflow_security.py'\n", "",
    )
    yield "path garde push retiré", mutate_block(
        text, "  push:", "  workflow_dispatch:",
        "      - 'scripts/validate_employment_ci_workflow_security.py'\n", "",
    )
    yield "workflow_dispatch retiré", text.replace("  workflow_dispatch:\n", "", 1)
    yield "runner mutable", text.replace("runs-on: ubuntu-24.04", "runs-on: ubuntu-latest", 1)
    yield "checkout mutable", text.replace(CHECKOUT, "actions/checkout@v6", 1)
    yield "python mutable", text.replace(SETUP_PYTHON, "actions/setup-python@v6", 1)
    yield "cli mutable", text.replace(SETUP_CLI, "supabase/setup-cli@v2", 1)
    yield "python large", text.replace("python-version: '3.12.14'", "python-version: '3.x'", 1)
    yield "python latest", text.replace("check-latest: false", "check-latest: true", 1)
    yield "cli latest", text.replace("version: 2.111.0", "version: latest", 1)
    yield "credentials persistés", text.replace("persist-credentials: false", "persist-credentials: true", 1)
    yield "permissions écriture", text.replace("contents: read", "contents: write", 1)
    yield "environment production", text.replace("    timeout-minutes: 25", "    timeout-minutes: 25\n    environment: production", 1)
    yield "secret production", text.replace("    steps:\n", "    env:\n      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n    steps:\n", 1)
    yield "service role", text.replace("run: supabase start", "run: echo SERVICE_ROLE_KEY\n      - run: supabase start", 1)
    yield "project production", text.replace("run: supabase start", "run: echo gpvivleexywljowcqkru\n      - run: supabase start", 1)
    yield "endpoint production", text.replace("run: supabase start", "run: echo api.supabase.com\n      - run: supabase start", 1)
    yield "supabase link", text.replace("run: supabase start", "run: supabase link --project-ref demo\n      - run: supabase start", 1)
    yield "db push", text.replace("run: supabase start", "run: supabase db push --linked\n      - run: supabase start", 1)
    yield "functions deploy", text.replace("run: supabase start", "run: supabase functions deploy employment\n      - run: supabase start", 1)
    yield "functions list", text.replace("run: supabase start", "run: supabase functions list --project-ref demo\n      - run: supabase start", 1)
    yield "secrets set", text.replace("run: supabase start", "run: supabase secrets set X=Y\n      - run: supabase start", 1)
    yield "migration repair", text.replace("run: supabase start", "run: supabase migration repair 1 --status applied\n      - run: supabase start", 1)
    yield "jwt bypass", text.replace("run: supabase start", "run: echo --no-verify-jwt\n      - run: supabase start", 1)
    yield "curl réseau", text.replace("run: supabase start", "run: curl https://example.com\n      - run: supabase start", 1)
    yield "wget réseau", text.replace("run: supabase start", "run: wget https://example.com\n      - run: supabase start", 1)
    yield "gh api", text.replace("run: supabase start", "run: gh api /repos/x/y\n      - run: supabase start", 1)
    yield "git push", text.replace("run: supabase start", "run: git push origin main\n      - run: supabase start", 1)
    yield "continue on error", text.replace("    timeout-minutes: 25", "    timeout-minutes: 25\n    continue-on-error: true", 1)
    yield "shell trace", text.replace("set -euo pipefail", "set -x", 1)
    yield "action inconnue", text.replace("    steps:\n", "    steps:\n      - uses: owner/action@v1\n", 1)
    yield "auto-test retiré", text.replace(f"        run: {SELF_TEST}\n", "        run: python3 -V\n", 1)
    yield "garde réel retiré", text.replace(f"        run: {SELF_CHECK}\n", "        run: python3 -V\n", 1)
    yield "validateur métier retiré", text.replace("python3 scripts/validate_employment_v25.py", "python3 -V", 1)
    yield "validateur production retiré", text.replace("python3 scripts/validate_employment_production_deploy_workflow.py", "python3 -V", 1)
    yield "manifest retiré", text.replace("run: python3 scripts/validate_production_schema_manifest.py", "run: python3 -V", 1)
    yield "db start réduit", text.replace("run: supabase start", "run: supabase db start", 1)
    yield "pgTAP sans local", text.replace("employment_v25.test.sql --local", "employment_v25.test.sql", 1)
    yield "smoke retiré", text.replace("python3 scripts/smoke_employment_auth_local.py", "python3 -V", 1)
    yield "API locale retirée", text.replace('SINJIRA_LOCAL_API_URL="$API_URL"', 'SINJIRA_LOCAL_API_URL="https://example.com"', 1)
    yield "anon locale retirée", text.replace('SINJIRA_LOCAL_ANON_KEY="$ANON_KEY"', 'SINJIRA_LOCAL_ANON_KEY="x"', 1)
    yield "stop always retiré", text.replace("        if: always()", "        if: success()", 1)
    yield "stop retiré", text.replace("run: supabase stop --no-backup || true", "run: echo stop", 1)


def self_test(text: str) -> None:
    validate(text)
    missed: list[str] = []
    total = 0
    for name, mutated in mutations(text):
        total += 1
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
    print(f"OK: {total}/{total} mutations critiques détectées")


def main() -> int:
    if not WORKFLOW.is_file():
        print(f"ECHEC CI Emploi: workflow absent: {WORKFLOW.relative_to(ROOT)}", file=sys.stderr)
        return 1
    text = WORKFLOW.read_text(encoding="utf-8")
    try:
        if "--self-test" in sys.argv[1:]:
            self_test(text)
        else:
            validate(text)
            print(
                "OK CI Emploi V25: PR+push main, runner/actions/runtimes épinglés, permissions read-only, "
                "aucun secret ni endpoint production et chaîne Supabase strictement locale."
            )
    except ValueError as exc:
        print(f"ECHEC CI Emploi V25: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
