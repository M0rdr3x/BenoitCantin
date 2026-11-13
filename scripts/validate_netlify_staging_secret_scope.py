#!/usr/bin/env python3
"""Fail closed if Netlify staging secrets escape their three approved steps.

Only inspects GitHub workflow source; no real credentials, deployment or network.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/deploy-netlify-staging.yml"
SECRETS = ("NETLIFY_AUTH_TOKEN", "NETLIFY_SITE_ID")
APPROVED_STEPS = (
    "Verrouiller ref, SHA, site et secrets",
    "Déployer le preview staging sans promotion",
    "Déployer le production-candidate sans promotion",
)
STEP_LINE = re.compile(r"^      - name: ([^\n]+)$")
EXPRESSION = re.compile(r"\$\{\{\s*secrets\.(NETLIFY_AUTH_TOKEN|NETLIFY_SITE_ID)\s*\}\}")
ASSIGNMENT = re.compile(r"^\s*(NETLIFY_AUTH_TOKEN|NETLIFY_SITE_ID)\s*:")


def inspect(source: str) -> list[str]:
    errors: list[str] = []
    counts = {(step, secret): 0 for step in APPROVED_STEPS for secret in SECRETS}
    current_step: str | None = None
    in_step_env = False
    for number, line in enumerate(source.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        step = STEP_LINE.fullmatch(line)
        if step:
            current_step = step.group(1)
            in_step_env = False
        elif line.strip():
            if indent < 6:
                current_step = None
                in_step_env = False
            elif indent == 8:
                in_step_env = line.strip() == "env:"
            elif indent == 6:
                current_step = None
                in_step_env = False
        references = EXPRESSION.findall(line)
        assignment = ASSIGNMENT.match(line)
        if not (references or assignment):
            continue
        if assignment:
            secret = assignment.group(1)
            expected = "          " + secret + ": ${{ secrets." + secret + " }}"
            safe = (
                current_step in APPROVED_STEPS
                and in_step_env
                and line.rstrip() == expected
                and len(references) == 1
                and references[0] == secret
            )
            if safe:
                counts[(current_step, secret)] += 1
            else:
                errors.append(f"ligne {number}: affectation {secret} hors de son env de step approuvé")
        elif references:
            errors.append(f"ligne {number}: interpolation de secret Netlify hors env approuvé")
    for (step, secret), count in counts.items():
        if count != 1:
            errors.append(f"{step}: {secret} doit apparaître exactement une fois (observé: {count})")
    for number, line in enumerate(source.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        if re.search(r"\bsecrets\s*\[\s*['\"](?:NETLIFY_AUTH_TOKEN|NETLIFY_SITE_ID)['\"]\s*\]", line):
            errors.append(f"ligne {number}: accès dynamique au secret Netlify interdit")
    return errors


def self_test(source: str) -> None:
    if errors := inspect(source):
        raise AssertionError("le workflow de référence ne respecte pas le contrat: " + "; ".join(errors))
    token = "          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}\n"
    site = "          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}\n"
    mutants = {
        "job-level exposure": source.replace(
            "    env:\n", "    env:\n      NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}\n", 1
        ),
        "setup-node exposure": source.replace(
            "      - name: Configurer Node\n",
            "      - name: Configurer Node\n        env:\n" + token, 1,
        ),
        "shell interpolation": source.replace(
            "          set -euo pipefail\n",
            "          echo '${{ secrets.NETLIFY_AUTH_TOKEN }}'\n          set -euo pipefail\n", 1,
        ),
        "replaced token binding": source.replace(
            token, "          NETLIFY_AUTH_TOKEN: ${{ inputs.token }}\n", 1
        ),
        "removed site binding": source.replace(site, "", 1),
        "token bracket lookup": source.replace(
            "          set -euo pipefail\n",
            "          echo '${{ secrets[\"NETLIFY_AUTH_TOKEN\"] }}'\n          set -euo pipefail\n", 1,
        ),
    }
    for label, mutant in mutants.items():
        if mutant == source or not inspect(mutant):
            raise AssertionError(f"mutation non détectée: {label}")
    print(f"OK: contrat d'isolation et {len(mutants)} mutations adversariales vérifiées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    source = WORKFLOW.read_text(encoding="utf-8")
    if args.self_test:
        self_test(source)
        return 0
    errors = inspect(source)
    for error in errors:
        print("ERREUR:", error)
    if errors:
        return 1
    print("OK: jeton et identifiant Netlify limités aux trois étapes autorisées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
