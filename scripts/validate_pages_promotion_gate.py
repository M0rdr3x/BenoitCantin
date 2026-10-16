#!/usr/bin/env python3
"""Prouver que le workflow Pages ne perd pas son garde de promotion.

Contrôle hors ligne des mutations négatives; aucun réseau, aucun déploiement.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/pages-cutover-preflight.yml"


def failures(workflow: str) -> list[str]:
    issues: list[str] = []
    if "  pull_request:\n    branches: [main]\n" not in workflow:
        issues.append("La garde doit couvrir toutes les PR vers main")
    head = workflow.split("\n  workflow_dispatch:", 1)[0]
    if "\n    paths:" in head or "\n    paths-ignore:" in head:
        issues.append("Un filtre de chemins rendrait le required check absent")
    if "types: [opened, synchronize, reopened, ready_for_review]" not in head:
        issues.append("L'événement ready_for_review ou synchronize n'est plus couvert")
    if "  pages-source-promotion-gate:\n" not in workflow:
        issues.append("Job promotion manquant")
        return issues
    gate = workflow.split("\n  pages-source-promotion-gate:\n", 1)[1]
    required = (
        "github.event_name == 'pull_request'",
        "github.event.pull_request.draft == false",
        "github.repository == 'M0rdr3x/BenoitCantin'",
        "run: python3 scripts/report_pages_cutover_status.py --require-source",
        "run: python3 scripts/report_pages_cutover_status.py --self-test",
        "pages: read",
        "contents: read",
        "persist-credentials: false",
    )
    for marker in required:
        if marker not in gate:
            issues.append(f"Garde de promotion incomplète : {marker}")
    if "continue-on-error: true" in gate:
        issues.append("Garde désactivée par continue-on-error")
    if "|| true" in gate or "exit 0" in gate:
        issues.append("Le refus pourrait être neutralisé par une sortie à zéro")
    if "pages: write" in gate or "contents: write" in gate:
        issues.append("Une permission d'écriture est incompatible avec ce diagnostic")
    return issues


def self_test() -> None:
    source = WORKFLOW.read_text("utf-8")
    assert not failures(source), failures(source)
    tests = {
        "filtre paths": source.replace(
            "  workflow_dispatch:", "  pull_request:\n    paths: ['docs/**']\n  workflow_dispatch:", 1
        ),
        "suppression job": source.replace("  pages-source-promotion-gate:\n", "  job-neutralise:\n", 1),
        "ignorer erreur": source.replace(
            "        run: python3 scripts/report_pages_cutover_status.py --require-source",
            "        continue-on-error: true\n        run: python3 scripts/report_pages_cutover_status.py --require-source", 1
        ),
        "ne plus refuser": source.replace(
            "run: python3 scripts/report_pages_cutover_status.py --require-source",
            "run: python3 scripts/report_pages_cutover_status.py --report", 1
        ),
        "PR brouillon non distinguée": source.replace(
            "github.event.pull_request.draft == false",
            "github.event.pull_request.draft == true", 1
        ),
        "source non testée": source.replace(
            "run: python3 scripts/report_pages_cutover_status.py --self-test",
            "run: echo PRET", 1
        ),
        "écriture": source.replace(
            "  pages-source-promotion-gate:\n", "  pages-source-promotion-gate:\n    permissions:\n      pages: write\n", 1
        ),
    }
    for label, changed in tests.items():
        assert changed != source, f"Mutation inactive : {label}"
        assert failures(changed), f"Régression acceptée : {label}"
    print("OK garde promotion : toutes PR, fail-closed, 7 mutations refusées")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = failures(WORKFLOW.read_text("utf-8"))
    for item in errors:
        print("ECHEC garde de promotion : " + item)
    if errors:
        return 1
    print("OK garde de promotion : statut prêt pour revue surveillé")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
