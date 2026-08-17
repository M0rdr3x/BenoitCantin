#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = [
    ROOT / ".github/workflows/validate-site.yml",
    ROOT / ".github/workflows/e2e-site.yml",
    ROOT / ".github/workflows/recovery-drill.yml",
    ROOT / ".github/workflows/validate-production-ledger.yml",
]

errors = []
required_types = "types: [opened, synchronize, reopened, ready_for_review]"
draft_gate = "github.event_name != 'pull_request' || github.event.pull_request.draft == false"

for workflow in WORKFLOWS:
    if not workflow.exists():
        errors.append(f"workflow absent: {workflow.relative_to(ROOT)}")
        continue
    text = workflow.read_text(encoding="utf-8")
    rel = workflow.relative_to(ROOT)
    if "pull_request:" not in text:
        errors.append(f"{rel}: déclencheur pull_request absent")
    if required_types not in text:
        errors.append(f"{rel}: types pull_request incomplets; ready_for_review doit être explicite")
    if draft_gate not in text:
        errors.append(f"{rel}: garde PR brouillon absent")

# Les pushes sur main restent obligatoires pour valider le code réellement déployé.
for workflow in (WORKFLOWS[0], WORKFLOWS[1], WORKFLOWS[2], WORKFLOWS[3]):
    if workflow.exists():
        text = workflow.read_text(encoding="utf-8")
        if "push:" not in text or "branches: [ main ]" not in text:
            errors.append(f"{workflow.relative_to(ROOT)}: validation push main absente")

if errors:
    print(f"ECHEC contrat CI brouillon: {len(errors)} problème(s).")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print(
    "OK CI V24.4.47: les PR brouillon ne lancent pas les validations coûteuses, "
    "ready_for_review les réactive et les pushes main restent contrôlés."
)
