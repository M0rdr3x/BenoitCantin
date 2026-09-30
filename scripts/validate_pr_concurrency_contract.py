#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

READ_ONLY_PR_WORKFLOWS = (
    ".github/workflows/sinjira-mobile-native-route-dispatch-v25.yml",
    ".github/workflows/sinjira-personal-ai-functional-v25.yml",
    ".github/workflows/sinjira-employment-v25.yml",
    ".github/workflows/sinjira-secret-guard.yml",
    ".github/workflows/nova-a1.yml",
    ".github/workflows/sinjira-mobile-native.yml",
    ".github/workflows/site-personality-v25.yml",
    ".github/workflows/validate-site.yml",
    ".github/workflows/sinjira-public-navigation-v25.yml",
    ".github/workflows/public-seo-v25.yml",
    ".github/workflows/e2e-site.yml",
)

EXPECTED_CONCURRENCY = """concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
"""

FORBIDDEN_ACTIVE = (
    "contents: write",
    "environment: production",
    "${{ secrets.",
    "SUPABASE_ACCESS_TOKEN",
    "SUPABASE_DB_PASSWORD",
    "SERVICE_ROLE_KEY",
    "supabase db push",
    "supabase functions deploy",
    "supabase secrets set",
    "supabase migration repair",
    "supabase link",
    "--linked",
    "gh api",
    "git push",
)


def active_text(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("#"))


def validate_text(path: str, text: str) -> list[str]:
    errors: list[str] = []
    active = active_text(text)

    if "pull_request:" not in text:
        errors.append(f"{path}: déclencheur pull_request absent")
    if "permissions:\n  contents: read" not in text:
        errors.append(f"{path}: permissions.contents doit rester read")
    if text.count(EXPECTED_CONCURRENCY) != 1:
        errors.append(f"{path}: bloc concurrency PR exact absent ou dupliqué")
    if "cancel-in-progress: true" in active:
        errors.append(f"{path}: annulation inconditionnelle interdite; seuls les runs PR peuvent être annulés")
    if "pull_request_target:" in active:
        errors.append(f"{path}: pull_request_target interdit dans ce groupe read-only")

    found = [marker for marker in FORBIDDEN_ACTIVE if marker in active]
    if found:
        errors.append(f"{path}: capacité d'écriture/production incompatible avec le groupe read-only: {found}")

    return errors


def validate_repo() -> list[str]:
    errors: list[str] = []
    for rel in READ_ONLY_PR_WORKFLOWS:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"{rel}: workflow absent")
            continue
        errors.extend(validate_text(rel, path.read_text(encoding="utf-8", errors="strict")))
    return errors


def self_test() -> None:
    fixture = f"""name: fixture

on:
  pull_request:
  push:
    branches: [ main ]

permissions:
  contents: read

{EXPECTED_CONCURRENCY}
jobs:
  validate:
    runs-on: ubuntu-24.04
    steps:
      - run: python3 -V
"""
    if validate_text("fixture.yml", fixture):
        raise SystemExit("ECHEC auto-test concurrence PR: fixture valide rejetée")

    mutations = {
        "bloc retiré": fixture.replace(EXPECTED_CONCURRENCY + "\n", "", 1),
        "annulation globale": fixture.replace(
            "cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
            "cancel-in-progress: true",
            1,
        ),
        "groupe non borné à la PR": fixture.replace(
            "group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}",
            "group: ${{ github.workflow }}",
            1,
        ),
        "permissions write": fixture.replace("contents: read", "contents: write", 1),
        "secret ajouté": fixture.replace(
            "    steps:\n",
            "    env:\n      TOKEN: ${{ secrets.TEST_TOKEN }}\n    steps:\n",
            1,
        ),
        "production ajoutée": fixture.replace(
            "    runs-on: ubuntu-24.04",
            "    runs-on: ubuntu-24.04\n    environment: production",
            1,
        ),
        "push Git ajouté": fixture.replace(
            "      - run: python3 -V",
            "      - run: git push origin HEAD:main",
            1,
        ),
        "pull_request_target ajouté": fixture.replace(
            "  pull_request:\n",
            "  pull_request:\n  pull_request_target:\n",
            1,
        ),
    }

    missed: list[str] = []
    for name, mutated in mutations.items():
        if mutated == fixture:
            missed.append(f"{name} (mutation inactive)")
            continue
        if not validate_text("fixture.yml", mutated):
            missed.append(name)

    if missed:
        raise SystemExit("ECHEC auto-test concurrence PR: mutations non détectées: " + ", ".join(missed))

    print(f"OK auto-tests concurrence PR: {len(mutations)}/{len(mutations)} affaiblissements détectés.")


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        self_test()

    errors = validate_repo()
    if errors:
        for error in errors:
            print(f"ERREUR concurrence PR: {error}", file=sys.stderr)
        return 1

    print(
        "OK concurrence PR: 11 workflows read-only bornés par workflow/PR; "
        "annulation limitée aux pull requests, push/main et dispatch préservés."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
