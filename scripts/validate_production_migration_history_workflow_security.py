#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sinjira-production-migration-history-guard-v25.yml"

CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
RUNNER = "    runs-on: ubuntu-24.04"
PYTHON_VERSION = "          python-version: '3.12.14'"
SELF_TEST_RUN = "        run: python3 scripts/validate_production_migration_history_workflow_security.py --self-test"
SELF_CHECK_RUN = "        run: python3 scripts/validate_production_migration_history_workflow_security.py"
LEDGER_CHECK = "python scripts/validate_production_migration_ledger.py"
TRIGGER_PATH = "      - 'scripts/validate_production_migration_history_workflow_security.py'"


def validate_text(text: str) -> list[str]:
    errors: list[str] = []

    if "permissions:\n  contents: read\n" not in text:
        errors.append("Le workflow doit conserver permissions.contents en lecture seule.")
    if "contents: write" in text:
        errors.append("contents: write est interdit pour le garde de migrations production.")

    if text.count(RUNNER) != 1:
        errors.append("Le job doit utiliser exactement ubuntu-24.04.")
    if "ubuntu-latest" in text:
        errors.append("ubuntu-latest est interdit sur cette frontière production.")

    if f"uses: {CHECKOUT}" not in text:
        errors.append("actions/checkout doit être épinglée au SHA vérifié.")
    if f"uses: {SETUP_PYTHON}" not in text:
        errors.append("actions/setup-python doit être épinglée au SHA vérifié.")
    if "actions/checkout@v" in text or "actions/setup-python@v" in text:
        errors.append("Les tags d'actions GitHub mutables sont interdits.")

    if "          persist-credentials: false" not in text:
        errors.append("Checkout doit utiliser persist-credentials: false.")
    if "          fetch-depth: 0" not in text:
        errors.append("Le garde doit conserver fetch-depth: 0 pour comparer l'historique Git.")

    if text.count(PYTHON_VERSION) != 1:
        errors.append("Python doit être figé exactement à 3.12.14.")

    if text.count(TRIGGER_PATH) < 2:
        errors.append("Le validateur sécurité doit déclencher les contrôles sur push et pull_request.")

    self_test_at = text.find(SELF_TEST_RUN)
    self_check_at = text.find(SELF_CHECK_RUN + "\n")
    ledger_step_at = text.find("      - name: Verrouiller les migrations historiques")
    if self_test_at < 0:
        errors.append("L'auto-test mutationnel du garde sécurité est absent.")
    if self_check_at < 0:
        errors.append("La validation du workflow est absente.")
    if ledger_step_at < 0:
        errors.append("L'étape historique de verrouillage des migrations est absente.")
    if min(self_test_at, self_check_at, ledger_step_at) >= 0 and not self_test_at < self_check_at < ledger_step_at:
        errors.append("L'ordre doit rester auto-test sécurité → validation sécurité → verrouillage historique.")

    required_fragments = (
        'if [ "${{ github.event_name }}" = "pull_request" ]; then',
        'echo "ref=${{ github.event.pull_request.base.sha }}" >> "$GITHUB_OUTPUT"',
        'before="${{ github.event.before }}"',
        'BASE_REF="${{ steps.migration_base.outputs.ref }}"',
        'python scripts/validate_production_migration_ledger.py --base-ref "$BASE_REF"',
        LEDGER_CHECK,
    )
    for fragment in required_fragments:
        if fragment not in text:
            errors.append(f"Contrat historique indispensable absent: {fragment}")

    for forbidden in ("continue-on-error:", "set -x", "curl |", "wget |"):
        if forbidden in text:
            errors.append(f"Construction interdite dans le garde production: {forbidden}")

    return errors


def self_test(valid: str) -> int:
    mutations = [
        ("runner flottant", valid.replace("ubuntu-24.04", "ubuntu-latest", 1)),
        ("Python flottant", valid.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)),
        ("checkout mutable", valid.replace(CHECKOUT, "actions/checkout@v6", 1)),
        ("setup-python mutable", valid.replace(SETUP_PYTHON, "actions/setup-python@v6", 1)),
        ("credentials checkout", valid.replace("persist-credentials: false", "persist-credentials: true", 1)),
        ("historique superficiel", valid.replace("fetch-depth: 0", "fetch-depth: 1", 1)),
        ("permission écriture", valid.replace("contents: read", "contents: write", 1)),
        ("auto-test retiré", valid.replace(SELF_TEST_RUN, "        run: echo self-test-retire", 1)),
        ("validation retirée", valid.replace(SELF_CHECK_RUN + "\n", "        run: echo validation-retire\n", 1)),
        ("base PR retirée", valid.replace('echo "ref=${{ github.event.pull_request.base.sha }}" >> "$GITHUB_OUTPUT"', "echo ref= >> \"$GITHUB_OUTPUT\"", 1)),
        ("base push retirée", valid.replace('before="${{ github.event.before }}"', 'before=""', 1)),
        ("base-ref ledger retiré", valid.replace('python scripts/validate_production_migration_ledger.py --base-ref "$BASE_REF"', LEDGER_CHECK, 1)),
        ("continue-on-error", valid.replace("    timeout-minutes: 5", "    timeout-minutes: 5\n    continue-on-error: true", 1)),
    ]

    failures: list[str] = []
    for name, mutated in mutations:
        if mutated == valid:
            failures.append(f"mutation inopérante: {name}")
            continue
        if not validate_text(mutated):
            failures.append(f"mutation dangereuse acceptée: {name}")

    if failures:
        print("Auto-test du garde historique migrations: ÉCHEC")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Auto-test du garde historique migrations: OK ({len(mutations)}/{len(mutations)} mutations rejetées)")
    return 0


def main() -> int:
    if not WORKFLOW.is_file():
        print(f"Workflow introuvable: {WORKFLOW}")
        return 2

    text = WORKFLOW.read_text(encoding="utf-8")
    if "--self-test" in sys.argv[1:]:
        return self_test(text)

    errors = validate_text(text)
    if errors:
        print("Contrat sécurité du garde historique migrations production: ÉCHEC")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Contrat sécurité du garde historique migrations production: OK")
    print("- runner Ubuntu 24.04 et Python 3.12.14 figés")
    print("- actions réutilisables épinglées par SHA et checkout sans credentials persistés")
    print("- historique Git complet conservé pour les comparaisons de migrations")
    print("- auto-test mutationnel exécuté avant le verrouillage du ledger")
    return 0


if __name__ == "__main__":
    sys.exit(main())
