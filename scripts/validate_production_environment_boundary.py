#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"

EXPECTED_ENVIRONMENTS = {
    ("deploy-github-pages-isolated.yml", "deploy"): "github-pages",
    ("supabase-production-preflight.yml", "apply-production"): "production",
    ("sinjira-v25-auth-password-hardening.yml", "enable-leaked-password-protection"): "production",
    ("sinjira-v25-production-deploy.yml", "verify-v25-consciousness-vault"): "production",
    ("sinjira-v25-employment-production.yml", "verify-employment-v25"): "production",
    ("sinjira-v25-personal-ai-production-readiness.yml", "verify-personal-ai-v25"): "production",
}

WRITE_ALLOWLIST = {
    ("deploy-github-pages-isolated.yml", "deploy"),
    ("supabase-production-preflight.yml", "apply-production"),
    ("sinjira-v25-auth-password-hardening.yml", "enable-leaked-password-protection"),
}

MANUAL_WRITE_JOB_MARKERS = {
    ("deploy-github-pages-isolated.yml", "deploy"): (
        "github.ref == 'refs/heads/main'",
        "inputs.confirm_containment == 'CONTAIN'",
        "inputs.acknowledge_header_gap == 'ACK_HEADER_GAP'",
    ),
    ("supabase-production-preflight.yml", "apply-production"): (
        "github.event_name == 'workflow_dispatch'",
        "inputs.apply == true",
        "inputs.confirmation == 'APPLY-SUPABASE-PRODUCTION'",
        "github.ref == 'refs/heads/main'",
    ),
    ("sinjira-v25-auth-password-hardening.yml", "enable-leaked-password-protection"): (
        'test "$GITHUB_REF" = "refs/heads/main"',
        "ENABLE-SINJIRA-V25-LEAKED-PASSWORD-PROTECTION",
    ),
}

STRICTLY_MANUAL_WORKFLOWS = {
    "deploy-github-pages-isolated.yml",
    "sinjira-v25-auth-password-hardening.yml",
}


def job_blocks(text: str) -> dict[str, str]:
    jobs_match = re.search(r"(?m)^jobs:\s*$", text)
    if not jobs_match:
        return {}
    body = text[jobs_match.end():]
    matches = list(re.finditer(r"(?m)^  ([A-Za-z0-9_-]+):\s*$", body))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        blocks[match.group(1)] = body[match.start():end]
    return blocks


def job_environment(block: str) -> str | None:
    scalar = re.search(r"(?m)^    environment:\s*([A-Za-z0-9_-]+)\s*$", block)
    if scalar:
        return scalar.group(1)
    mapping = re.search(
        r"(?m)^    environment:\s*$[\s\S]*?^      name:\s*([A-Za-z0-9_-]+)\s*$",
        block,
    )
    return mapping.group(1) if mapping else None


def write_signals(block: str) -> list[str]:
    signals: list[str] = []
    active_lines = [
        line for line in block.splitlines()
        if not line.lstrip().startswith("#")
    ]
    active = "\n".join(active_lines)

    if re.search(r"(?m)^\s*pages:\s*write\s*$", active):
        signals.append("pages:write")
    if "uses: actions/deploy-pages@" in active:
        signals.append("deploy-pages")
    if "supabase functions deploy" in active:
        signals.append("supabase-functions-deploy")
    if "supabase secrets set" in active:
        signals.append("supabase-secrets-set")
    if "supabase migration repair" in active:
        signals.append("supabase-migration-repair")
    for line in active_lines:
        if "supabase db push" in line and "--dry-run" not in line:
            signals.append("supabase-db-push")
            break
    if (
        re.search(r"--request\s+(?:PATCH|POST|PUT|DELETE)\b", active)
        and ("api.supabase.com" in active or "$SUPABASE_MANAGEMENT_API" in active)
    ):
        signals.append("mutating-supabase-management-request")
    return sorted(set(signals))



def trigger_block(text: str) -> str:
    jobs_match = re.search(r"(?m)^jobs:\s*$", text)
    return text[: jobs_match.start()] if jobs_match else text


def validate_manual_write_boundary(
    filename: str,
    workflow_text: str,
    job_name: str,
    block: str,
) -> list[str]:
    errors: list[str] = []
    triggers = trigger_block(workflow_text)
    pair = (filename, job_name)

    if "workflow_dispatch:" not in triggers:
        errors.append(f"{filename}/{job_name}: workflow_dispatch obligatoire pour toute écriture distante")

    if filename in STRICTLY_MANUAL_WORKFLOWS:
        for automatic in ("push:", "pull_request:", "schedule:"):
            if re.search(rf"(?m)^  {re.escape(automatic)}\s*$", triggers):
                errors.append(
                    f"{filename}/{job_name}: déclencheur automatique interdit pour ce workflow: {automatic[:-1]}"
                )

    for marker in MANUAL_WRITE_JOB_MARKERS.get(pair, ()):
        if marker not in block:
            errors.append(f"{filename}/{job_name}: garde manuelle absente: {marker}")
    return errors

def validate_workflows(texts: dict[str, str]) -> list[str]:
    errors: list[str] = []
    parsed: dict[str, dict[str, str]] = {}

    for filename, text in texts.items():
        parsed[filename] = job_blocks(text)

    for (filename, job_name), expected_environment in EXPECTED_ENVIRONMENTS.items():
        jobs = parsed.get(filename)
        if jobs is None:
            errors.append(f"{filename}: workflow attendu absent de l’inventaire")
            continue
        block = jobs.get(job_name)
        if block is None:
            errors.append(f"{filename}: job attendu absent: {job_name}")
            continue
        observed = job_environment(block)
        if observed != expected_environment:
            errors.append(
                f"{filename}/{job_name}: environment={observed!r}, attendu={expected_environment!r}"
            )

    for filename, jobs in parsed.items():
        for job_name, block in jobs.items():
            observed = job_environment(block)
            if observed == "github-pages" and (filename, job_name) != (
                "deploy-github-pages-isolated.yml",
                "deploy",
            ):
                errors.append(f"{filename}/{job_name}: environment github-pages réservé au confinement Pages")

            signals = write_signals(block)
            if not signals:
                continue
            pair = (filename, job_name)
            if pair not in WRITE_ALLOWLIST:
                errors.append(
                    f"{filename}/{job_name}: écriture distante non inventoriée: {', '.join(signals)}"
                )
                continue
            expected_environment = EXPECTED_ENVIRONMENTS[pair]
            if observed != expected_environment:
                errors.append(
                    f"{filename}/{job_name}: écriture distante hors environment {expected_environment}"
                )
            errors.extend(
                validate_manual_write_boundary(filename, texts[filename], job_name, block)
            )

    return errors


def repository_texts() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8", errors="strict")
        for path in sorted(WORKFLOW_DIR.glob("*.yml"))
    }


def self_test() -> None:
    fixtures = {
        "deploy-github-pages-isolated.yml": """on:
  workflow_dispatch:
jobs:
  deploy:
    if: github.ref == 'refs/heads/main' && inputs.confirm_containment == 'CONTAIN' && inputs.acknowledge_header_gap == 'ACK_HEADER_GAP'
    permissions:
      pages: write
    environment:
      name: github-pages
    steps:
      - uses: actions/deploy-pages@0123456789012345678901234567890123456789
""",
        "supabase-production-preflight.yml": """on:
  push:
  pull_request:
  workflow_dispatch:
jobs:
  apply-production:
    if: github.event_name == 'workflow_dispatch' && inputs.apply == true && inputs.confirmation == 'APPLY-SUPABASE-PRODUCTION' && github.ref == 'refs/heads/main'
    environment: production
    steps:
      - run: supabase db push --linked --password "$DB"
""",
        "sinjira-v25-auth-password-hardening.yml": """on:
  workflow_dispatch:
jobs:
  enable-leaked-password-protection:
    environment: production
    steps:
      - run: |
          test "$GITHUB_REF" = "refs/heads/main"
          test "$AUTH_CONFIRMATION" = "ENABLE-SINJIRA-V25-LEAKED-PASSWORD-PROTECTION"
          curl --request PATCH "$SUPABASE_MANAGEMENT_API/projects/x/config/auth"
""",
        "sinjira-v25-production-deploy.yml": """jobs:
  verify-v25-consciousness-vault:
    environment: production
    steps:
      - run: echo verify
""",
        "sinjira-v25-employment-production.yml": """jobs:
  verify-employment-v25:
    environment: production
    steps:
      - run: echo verify
""",
        "sinjira-v25-personal-ai-production-readiness.yml": """jobs:
  verify-personal-ai-v25:
    environment: production
    steps:
      - run: echo verify
""",
    }
    if validate_workflows(fixtures):
        raise SystemExit("ERREUR auto-test environments: inventaire valide refusé.")

    mutations = {
        "production retiré": (
            "supabase-production-preflight.yml",
            fixtures["supabase-production-preflight.yml"].replace(
                "environment: production", "environment: staging", 1
            ),
        ),
        "Pages environment retiré": (
            "deploy-github-pages-isolated.yml",
            fixtures["deploy-github-pages-isolated.yml"].replace(
                "name: github-pages", "name: staging", 1
            ),
        ),
        "écriture inconnue": (
            "untracked-production.yml",
            """jobs:
  mutate:
    environment: production
    steps:
      - run: supabase functions deploy dangerous --project-ref x
""",
        ),
        "PATCH Management API inconnu": (
            "untracked-auth.yml",
            """jobs:
  mutate:
    environment: production
    steps:
      - run: curl --request PATCH "$SUPABASE_MANAGEMENT_API/projects/x/config/auth"
""",
        ),
        "workflow_dispatch Supabase retiré": (
            "supabase-production-preflight.yml",
            fixtures["supabase-production-preflight.yml"].replace("  workflow_dispatch:\n", "", 1),
        ),
        "confirmation Supabase retirée": (
            "supabase-production-preflight.yml",
            fixtures["supabase-production-preflight.yml"].replace(
                " && inputs.confirmation == 'APPLY-SUPABASE-PRODUCTION'", "", 1
            ),
        ),
        "Pages rendu automatique": (
            "deploy-github-pages-isolated.yml",
            fixtures["deploy-github-pages-isolated.yml"].replace(
                "  workflow_dispatch:\n", "  push:\n", 1
            ),
        ),
        "garde main HIBP retirée": (
            "sinjira-v25-auth-password-hardening.yml",
            fixtures["sinjira-v25-auth-password-hardening.yml"].replace(
                '          test "$GITHUB_REF" = "refs/heads/main"\n', "", 1
            ),
        ),
    }

    local_only = """jobs:
  local-test:
    steps:
      - run: |
          API_URL="http://127.0.0.1:54321"
          curl --request POST "$API_URL/auth/v1/signup"
"""
    if write_signals(job_blocks(local_only)["local-test"]):
        raise SystemExit("ERREUR auto-test environments: POST Supabase local classé comme écriture production.")

    for name, (filename, mutated) in mutations.items():
        case = dict(fixtures)
        case[filename] = mutated
        if not validate_workflows(case):
            raise SystemExit(f"ERREUR auto-test environments: affaiblissement non détecté: {name}")

    print(
        "OK auto-test environments production: jobs sensibles inventoriés, "
        "exception github-pages bornée, écritures inconnues refusées et déclenchements manuels verrouillés."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    errors = validate_workflows(repository_texts())
    if errors:
        print(f"ECHEC frontière Environments production: {len(errors)} problème(s).")
        for error in errors:
            print("- " + error)
        return 1

    print("OK frontière Environments production.")
    print("- écritures Supabase reconnues: environment production")
    print("- vérifications production ciblées: environment production")
    print("- publication Pages isolée: exception environment github-pages bornée")
    print("- toute nouvelle écriture distante reconnue hors inventaire est refusée")
    print("- toute écriture distante reconnue exige workflow_dispatch et ses gardes manuelles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
