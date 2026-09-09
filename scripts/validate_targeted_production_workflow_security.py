#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"

CHECKOUT_SHA = "d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_CLI_SHA = "3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf"
TOKEN_REF = "SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}"
MAIN_REF_GUARD = 'test "$GITHUB_REF" = "refs/heads/main"'

TARGETS = {
    "sinjira-v25-production-deploy.yml": True,
    "sinjira-v25-employment-production.yml": False,
    "sinjira-v25-personal-ai-production-readiness.yml": True,
    "sinjira-v25-auth-password-hardening.yml": False,
}


def step_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^      - name: (.+)$", text))
    blocks: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((match.group(1).strip(), text[match.start():end]))
    return blocks


def validate_text(filename: str, text: str) -> list[str]:
    errors: list[str] = []

    if "environment: production" not in text:
        errors.append(f"{filename}: environment production obligatoire")
    if "workflow_dispatch:" not in text:
        errors.append(f"{filename}: workflow_dispatch obligatoire")

    for forbidden in ("pull_request:", "push:", "schedule:", "repository_dispatch:"):
        if forbidden in text:
            errors.append(f"{filename}: déclencheur production interdit: {forbidden}")

    if MAIN_REF_GUARD not in text:
        errors.append(f"{filename}: lancement hors main non refusé avant accès aux secrets")

    checkout_use = f"uses: actions/checkout@{CHECKOUT_SHA}"
    if checkout_use not in text:
        errors.append(f"{filename}: actions/checkout doit être épinglé au SHA vérifié {CHECKOUT_SHA}")

    blocks = step_blocks(text)
    checkout_blocks = [block for _, block in blocks if checkout_use in block or "uses: actions/checkout@" in block]
    if len(checkout_blocks) != 1:
        errors.append(f"{filename}: exactement un checkout est attendu")
    else:
        checkout = checkout_blocks[0]
        if "ref: main" not in checkout:
            errors.append(f"{filename}: checkout production doit forcer ref: main")
        if "persist-credentials: false" not in checkout:
            errors.append(f"{filename}: checkout production doit désactiver persist-credentials")
        if "secrets." in checkout or "SUPABASE_ACCESS_TOKEN:" in checkout:
            errors.append(f"{filename}: aucun secret production ne doit être exposé à checkout")

    if re.search(r"(?m)^ {6}SUPABASE_ACCESS_TOKEN:\s*\$\{\{ secrets\.SUPABASE_ACCESS_TOKEN \}\}$", text):
        errors.append(f"{filename}: SUPABASE_ACCESS_TOKEN interdit au niveau du job")

    secret_lines = [line for line in text.splitlines() if "secrets.SUPABASE_ACCESS_TOKEN" in line]
    if not secret_lines:
        errors.append(f"{filename}: référence step-scoped à SUPABASE_ACCESS_TOKEN absente")
    for line in secret_lines:
        if not re.fullmatch(r" {10}SUPABASE_ACCESS_TOKEN: \$\{\{ secrets\.SUPABASE_ACCESS_TOKEN \}\}", line):
            errors.append(f"{filename}: secret production hors env d'étape: {line.strip()}")

    for name, block in blocks:
        if "$SUPABASE_ACCESS_TOKEN" in block and TOKEN_REF not in block:
            errors.append(f"{filename}: étape utilisant le token sans env borné: {name}")
        if "uses:" in block and ("secrets.SUPABASE_ACCESS_TOKEN" in block or "SUPABASE_ACCESS_TOKEN:" in block):
            errors.append(f"{filename}: secret production exposé à une action réutilisable: {name}")

    if TARGETS.get(filename):
        expected = f"uses: supabase/setup-cli@{SETUP_CLI_SHA}"
        if expected not in text:
            errors.append(f"{filename}: supabase/setup-cli doit être épinglé au SHA vérifié {SETUP_CLI_SHA}")
        for name, block in blocks:
            if "uses: supabase/setup-cli@" in block and ("secrets." in block or "SUPABASE_ACCESS_TOKEN:" in block):
                errors.append(f"{filename}: aucun secret production ne doit être exposé à setup-cli: {name}")

    return errors


def validate_repository() -> list[str]:
    errors: list[str] = []
    for filename in TARGETS:
        path = WORKFLOW_DIR / filename
        if not path.is_file():
            errors.append(f"Workflow production ciblé absent: {filename}")
            continue
        errors.extend(validate_text(filename, path.read_text(encoding="utf-8")))
    return errors


def main() -> int:
    errors = validate_repository()
    if errors:
        print("Contrat sécurité workflows production ciblés: ÉCHEC")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Contrat sécurité workflows production ciblés: OK")
    print("- lancement manuel depuis main uniquement")
    print("- checkout main sans credentials et épinglé au SHA vérifié")
    print("- SUPABASE_ACCESS_TOKEN borné uniquement aux étapes shell qui l'utilisent")
    print("- aucun secret production exposé à checkout ou setup-cli")
    print("- setup-cli épinglé dans les workflows qui l'utilisent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
