#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

PENDING_CONCURRENCY_NORMALIZATION = {
    ".github/workflows/sinjira-child-community-v25.yml",
    ".github/workflows/sinjira-child-signup-browser-v25.yml",
    ".github/workflows/sinjira-child-signup-v25.yml",
    ".github/workflows/sinjira-junior-guardian-revocation-v25.yml",
}

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
    ".github/workflows/recovery-drill.yml",
    ".github/workflows/sinjira-a1-integration-rehearsal.yml",
    ".github/workflows/sinjira-a1-publication-isolation.yml",
    ".github/workflows/sinjira-account-content-hub-v25.yml",
    ".github/workflows/sinjira-account-life-story-a1.yml",
    ".github/workflows/sinjira-literature-browser-v25.yml",
    ".github/workflows/sinjira-livre-i-private-delivery.yml",
    ".github/workflows/sinjira-private-novel-catalog-v25.yml",
    ".github/workflows/sinjira-security-context-response-v25.yml",
    ".github/workflows/sinjira-v25-release-review-snapshot.yml",
    ".github/workflows/validate-ai-transparency.yml",
    ".github/workflows/validate-community-v24-4-79.yml",
    ".github/workflows/validate-dating-v24-4-75.yml",
    ".github/workflows/sinjira-life-story-user-rpc-v24-5-13.yml",
    ".github/workflows/sinjira-mobile-native-life-story-hub-v25.yml",
    ".github/workflows/validate-preorders-v24-5-3.yml",
    ".github/workflows/sinjira-preorder-admin-rpc-v24-5-8.yml",
    ".github/workflows/sinjira-native-push-producer-boundary-v25.yml",
    ".github/workflows/sinjira-device-challenge-client-boundary-v25.yml",
    ".github/workflows/sinjira-user-rights-convergence-v24-5-28.yml",
    ".github/workflows/sinjira-conscience-vault-functional-v25.yml",
    ".github/workflows/sinjira-mobile-safe-share-v25.yml",
    ".github/workflows/sinjira-mobile-native-dating-hub-v25.yml",
    ".github/workflows/sinjira-private-profile-v24-5-23.yml",
    ".github/workflows/sinjira-mobile-native-hub-destinations-v25.yml",
    ".github/workflows/sinjira-live-social-activation-gate-v25.yml",
    ".github/workflows/sinjira-rls-helper-rpc-v24-5-22.yml",
    ".github/workflows/sinjira-security-risk-v25.yml",
    ".github/workflows/sinjira-security-travel-client-visibility-v25.yml",
    ".github/workflows/sinjira-security-travel-consent-v25.yml",
    ".github/workflows/sinjira-security-travel-data-minimization-v25.yml",
    ".github/workflows/sinjira-security-travel-retention-v25.yml",
    ".github/workflows/sinjira-security-travel-self-only-v25.yml",
    ".github/workflows/sinjira-security-travel-visibility-v25.yml",
    ".github/workflows/sinjira-security-v24-4-99.yml",
    ".github/workflows/sinjira-sensitive-aal2-v25.yml",
    ".github/workflows/sinjira-social-home-v25.yml",
    ".github/workflows/sinjira-social-user-rpc-v24-5-15.yml",
    ".github/workflows/validate-global-safety-v24-4-83.yml",
    ".github/workflows/validate-life-story-v24-5-2.yml",
    ".github/workflows/validate-moderation-v24-4-90.yml",
    ".github/workflows/validate-safety-v24-4-82.yml",
    ".github/workflows/sinjira-consciousness-vault-v25.yml",
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

    workflows_dir = ROOT / ".github" / "workflows"
    for workflow in sorted((*workflows_dir.glob("*.yml"), *workflows_dir.glob("*.yaml"))):
        text = workflow.read_text(encoding="utf-8", errors="strict")
        active = active_text(text)
        rel = workflow.relative_to(ROOT).as_posix()
        if (
            "pull_request:" in active
            and "cancel-in-progress: true" in active
            and rel not in PENDING_CONCURRENCY_NORMALIZATION
        ):
            errors.append(
                f"{rel}: cancel-in-progress=true interdit; annulation PR conditionnelle requise"
            )
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
        "OK concurrence PR: 54 workflows read-only bornés par workflow/PR; "
        f"{len(PENDING_CONCURRENCY_NORMALIZATION)} exceptions legacy suivies; "
        "annulation limitée aux pull requests, push/main et dispatch préservés."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
