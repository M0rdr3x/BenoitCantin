#!/usr/bin/env python3
"""Contrat strict du garde Pages, sans réseau ni paquet YAML tiers.

Le validateur contrôle la position des lignes YAML réellement exécutables.
Les commandes commentées, affichées ou sautées ne constituent pas une preuve.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/pages-cutover-preflight.yml"

EXPECTED_IF = (
    "    if: >-\n"
    "      github.repository == 'M0rdr3x/BenoitCantin' &&\n"
    "      github.event_name == 'pull_request' &&\n"
    "      github.event.pull_request.draft == false\n"
)


def active_yaml(source: str) -> str:
    """Ignorer les commentaires YAML, pas les blocs à exécuter."""
    return "\n".join(
        line for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ) + "\n"


def failures(workflow: str) -> list[str]:
    issues: list[str] = []
    source = active_yaml(workflow)
    header = source.split("\njobs:\n", 1)[0]
    if "  pull_request:\n    branches: [main]\n" not in header:
        issues.append("La garde doit couvrir toutes les PR vers main")
    if re.search(r"(?m)^    paths(?:-ignore)?:", header):
        issues.append("Un filtre de chemins rendrait le required check absent")
    if "    types: [opened, synchronize, reopened, ready_for_review]\n" not in header:
        issues.append("L'événement ready_for_review ou synchronize n'est plus couvert")
    if source.count("  pages-source-promotion-gate:\n") != 1:
        issues.append("Le job de promotion doit être présent une seule fois")
        return issues
    gate = source.split("\n  pages-source-promotion-gate:\n", 1)[1]
    gate = re.split(r"\n  [a-zA-Z][a-zA-Z0-9_-]*:\n", gate, maxsplit=1)[0]
    if source.count("\njobs:\n") != 1 or source.count("\non:\n") > 1:
        issues.append("Structure YAML des événements/jobs ambiguë")
    if gate.count("    steps:\n") != 1:
        issues.append("Une seule liste d'étapes de promotion est autorisée")
    if len(re.findall(r"(?m)^        run:", gate)) != 2:
        issues.append("Les deux commandes de sécurité doivent être les seules commandes du job")

    # Condition exacte, sans contournement par OR, false ou événement différent.
    conditions = re.findall(r"(?m)^    if:.*(?:\n {6}.*)*", gate)
    if len(conditions) != 1 or conditions[0].rstrip() != EXPECTED_IF.rstrip():
        issues.append("Condition du job promotion modifiée ou contournée")

    permissions = re.search(
        r"(?m)^    permissions:\n((?: {6}[^\n]*\n)+)", gate
    )
    if gate.count("    permissions:\n") != 1 or permissions is None:
        issues.append("Permissions du job promotion absentes ou dupliquées")
    elif set(permissions.group(1).splitlines()) != {
        "      contents: read", "      pages: read"
    }:
        issues.append("Les permissions de promotion doivent être uniquement read-only")

    required_lines = (
        "        uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
        "          persist-credentials: false",
        "        run: python3 scripts/report_pages_cutover_status.py --self-test",
        "        run: python3 scripts/report_pages_cutover_status.py --require-source",
        "          GH_PAGES_READ_TOKEN: " + "$" + "{{ github.token }}",
    )
    for line in required_lines:
        if gate.splitlines().count(line) != 1:
            issues.append(
                "Étape de promotion manquante, dupliquée ou non exécutable : "
                + line.strip()
            )
    if re.search(r"(?m)^        if:\s*", gate):
        issues.append("Une étape de la garde pourrait être ignorée")
    if re.search(r"(?m)^\s+continue-on-error:\s*", gate):
        issues.append("Un échec de la garde ne doit pas être ignoré")
    if re.search(r"(?m)^\s+run:\s*(?:echo |true\s*$|exit 0\s*$)", gate):
        issues.append("Étape factice dans la garde de promotion")
    if "|| true" in gate or "exit 0" in gate:
        issues.append("Le refus pourrait être neutralisé par une sortie à zéro")
    if re.search(r"(?m)^\s+(?:pages|contents): write\s*$", gate):
        issues.append("La garde ne peut jamais obtenir de droit d'écriture")
    return issues


def self_test() -> None:
    source = WORKFLOW.read_text("utf-8")
    assert not failures(source), failures(source)
    replacements = {
        "filtre paths": (
            "  workflow_dispatch:",
            "    paths: ['docs/**']\n  workflow_dispatch:",
        ),
        "suppression job": (
            "  pages-source-promotion-gate:\n", "  job-neutralise:\n"
        ),
        "ignorer erreur": (
            "        run: python3 scripts/report_pages_cutover_status.py --require-source",
            "        continue-on-error: true\n"
            "        run: python3 scripts/report_pages_cutover_status.py --require-source",
        ),
        "ne plus refuser": (
            "run: python3 scripts/report_pages_cutover_status.py --require-source",
            "run: python3 scripts/report_pages_cutover_status.py --report",
        ),
        "brouillon inversé": (
            "github.event.pull_request.draft == false",
            "github.event.pull_request.draft == true",
        ),
        "autotest neutralisé": (
            "        run: python3 scripts/report_pages_cutover_status.py --self-test",
            "        run: echo PRET",
        ),
        "écriture": (
            "  pages-source-promotion-gate:\n",
            "  pages-source-promotion-gate:\n"
            "    permissions:\n      pages: write\n",
        ),
        "condition toujours vraie": (
            "github.event.pull_request.draft == false",
            "github.event.pull_request.draft == false || true",
        ),
        "job désactivé": (
            "    if: >-\n      github.repository == 'M0rdr3x/BenoitCantin' &&",
            "    if: false &&\n      github.repository == 'M0rdr3x/BenoitCantin' &&",
        ),
        "commande en commentaire": (
            "        run: python3 scripts/report_pages_cutover_status.py --require-source",
            "        # run: python3 scripts/report_pages_cutover_status.py --require-source",
        ),
        "commande affichée": (
            "        run: python3 scripts/report_pages_cutover_status.py --require-source",
            "        run: echo python3 scripts/report_pages_cutover_status.py --require-source",
        ),
        "étape sautée": (
            "        run: python3 scripts/report_pages_cutover_status.py --require-source",
            "        if: false\n"
            "        run: python3 scripts/report_pages_cutover_status.py --require-source",
        ),
        "jeton Pages supprimé": (
            "          GH_PAGES_READ_TOKEN: " + "$" + "{{ github.token }}",
            "          GH_PAGES_READ_TOKEN: ''",
        ),
        "permission cachée": (
            "      pages: read\n", "      pages: read\n      issues: write\n"
        ),
        "workflow ciblant docs": (
            "    branches: [main]", "    branches: [docs]"
        ),
        "commandes dupliquées": (
            "        run: python3 scripts/report_pages_cutover_status.py --require-source",
            "        run: python3 scripts/report_pages_cutover_status.py --require-source\n"
            "        run: echo IGNORE",
        ),
        "étapes dupliquées": (
            "    steps:\n", "    steps:\n    steps:\n"
        ),
        "double garde": (
            "  pages-source-promotion-gate:\n",
            "  pages-source-promotion-gate:\n  pages-source-promotion-gate:\n",
        ),
    }
    for label, (before, after) in replacements.items():
        assert before in source, f"Mutation inactive : {label}"
        changed = source.replace(before, after, 1)
        assert failures(changed), f"Régression acceptée : {label}"
    print(
        f"OK garde promotion : contrôles structurels, "
        f"{len(replacements)} mutations refusées"
    )


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
    for issue in errors:
        print("ECHEC garde de promotion : " + issue)
    if errors:
        return 1
    print("OK garde de promotion : condition et étapes effectives, sans publication")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
