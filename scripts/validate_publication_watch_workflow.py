#!/usr/bin/env python3
"""Empêcher la neutralisation silencieuse de la surveillance quotidienne Pages."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/publication-boundary-watch.yml"
CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
PYTHON = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
LIVE_IF = "    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'"
CONTRACT_TEST = "python3 scripts/validate_publication_live_boundary.py --self-test"
SELF_TEST = "python3 scripts/validate_publication_watch_workflow.py --self-test"
CHECK = "python3 scripts/validate_publication_watch_workflow.py --check"
LIVE = "python3 scripts/validate_publication_live_boundary.py --live"


def active(source: str) -> str:
    return "\n".join(line for line in source.splitlines()
                     if line.strip() and not line.lstrip().startswith("#")) + "\n"


def split_jobs(source: str) -> tuple[str, dict[str, str]]:
    head, sep, body = source.partition("\njobs:\n")
    if not sep or source.count("\njobs:\n") != 1:
        return "", {}
    marks = list(re.finditer(r"(?m)^  ([a-z][a-z0-9-]*):\n", body))
    found = {}
    for i, mark in enumerate(marks):
        name = mark.group(1)
        if name in found:
            return head, {}
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        found[name] = body[mark.end():end]
    return head, found


def steps(body: str) -> list[str]:
    matches = list(re.finditer(r"(?m)^      - name: [^\n]+\n", body))
    return [body[m.end():matches[i + 1].start() if i + 1 < len(matches)
                 else len(body)] for i, m in enumerate(matches)]


def failures(workflow: str) -> list[str]:
    issues: list[str] = []
    src = active(workflow)
    head, jobs = split_jobs(src)
    if not head or set(jobs) != {"contract", "live"}:
        return ["Deux jobs uniques contract et live requis, sans autre job"]

    for snippet, purpose in (
        ("\non:\n", "événements actifs"),
        ("  push:\n    branches: [main]\n", "push main"),
        ("  pull_request:\n    branches: [main]\n", "PR main"),
        ("    types: [opened, synchronize, reopened, ready_for_review]\n",
         "resynchronisation PR"),
        ("  schedule:\n    - cron: '17 11 * * *'\n", "cadence quotidienne"),
        ("  workflow_dispatch:\n", "lancement manuel"),
    ):
        if head.count(snippet) != 1:
            issues.append("Déclencheur manquant/altéré : " + purpose)
    if len(re.findall(r"(?m)^    - cron:", head)) != 1:
        issues.append("Une seule cadence est autorisée")
    if re.search(r"(?m)^    paths(?:-ignore)?:", head):
        issues.append("Filtres paths interdits pour les PR")
    if head.count("permissions:\n") != 1 or not re.search(
        r"(?m)^permissions:\n  contents: read\n(?:\n|concurrency:)", head
    ):
        issues.append("Seules les permissions contents: read sont autorisées")
    cancel = "  cancel-in-progress: " + "$" + "{{ github.event_name == 'pull_request' }}"
    if cancel not in head:
        issues.append("Les contrôles live ne doivent jamais être annulés par une PR")

    contract, live = jobs["contract"], jobs["live"]
    if re.search(r"(?m)^    if:|^    needs:", contract):
        issues.append("Le contrat doit tourner sans condition lors des PR")
    if live.splitlines().count("    needs: contract") != 1:
        issues.append("Le contrôle live doit dépendre du succès du contrat")
    if re.findall(r"(?m)^    if:.*$", live) != [LIVE_IF]:
        issues.append("Live uniquement sur schedule ou workflow_dispatch")
    for name, body, count in (("contract", contract, 5), ("live", live, 3)):
        if body.count("    steps:\n") != 1 or len(steps(body)) != 3:
            issues.append(name + ": trois étapes réelles checkout, python, commande")
            continue
        if re.search(r"(?m)^\s+(?:continue-on-error|strategy|permissions):", body):
            issues.append(name + ": permissions ou erreurs contournées")
        if re.search(r"(?m)^        if:", body):
            issues.append(name + ": étape masquée")
        if body.count("    runs-on: ubuntu-24.04\n") != 1:
            issues.append(name + ": runner modifié")
        pieces = steps(body)
        if pieces[0].splitlines().count("        uses: " + CHECKOUT) != 1 or (
            pieces[0].splitlines().count("          persist-credentials: false") != 1
        ):
            issues.append(name + ": checkout non épinglé ou credentials actifs")
        if pieces[1].splitlines().count("        uses: " + PYTHON) != 1 or (
            pieces[1].splitlines().count("          python-version: '3.12.14'") != 1
        ):
            issues.append(name + ": Python non épinglé")
        commands = [
            line.strip() for line in pieces[2].splitlines()
            if line.lstrip().startswith(("run:", "python3 ", "echo ", "exit "))
        ]
        expected = (
            ["run: |", CONTRACT_TEST, SELF_TEST, CHECK]
            if name == "contract" else ["run: " + LIVE]
        )
        if commands != expected:
            issues.append(name + ": commande exécutable incomplète/détournée")
        if re.search(r"(?m)^\s+(?:if|continue-on-error):", pieces[2]):
            issues.append(name + ": commande conditionnelle ou erreurs ignorées")
        if name == "live" and "    timeout-minutes: 10\n" not in body:
            issues.append("Le budget des 35 sondes est insuffisant")
    for forbidden in ("upload-pages-artifact@", "deploy-pages@", "pages: write",
                      "id-token: write", "curl ", "wget ", "|| true",
                      "if: false", "continue-on-error: true"):
        if forbidden in src:
            issues.append("Surveillance non strictement lecture seule : " + forbidden)
    return issues


def self_test() -> None:
    original = WORKFLOW.read_text("utf-8")
    assert not failures(original), "\n".join(failures(original))
    cases = {
        "planning effacé": ("  schedule:\n    - cron: '17 11 * * *'\n", ""),
        "planning hebdomadaire": ("'17 11 * * *'", "'17 11 * * 1'"),
        "dispatch absent": ("  workflow_dispatch:\n", ""),
        "PR désactivée": ("  pull_request:\n", "  pull_request_disabled:\n"),
        "filtre PR ajouté": ("  pull_request:\n    branches: [main]\n",
                            "  pull_request:\n    branches: [main]\n    paths: ['docs/']\n"),
        "droits write": ("  contents: read\n", "  contents: write\n"),
        "dépendance coupée": ("    needs: contract\n", "    needs: unknown\n"),
        "live en PR": (LIVE_IF, "    if: github.event_name == 'pull_request'"),
        "live désactivé": (LIVE_IF, "    if: false"),
        "condition retirée": (LIVE_IF + "\n", ""),
        "sonde remplacée": ("run: " + LIVE, "run: " + CONTRACT_TEST),
        "sonde neutralisée": ("run: " + LIVE, "run: echo INERTE"),
        "autotest absent": ("          " + CONTRACT_TEST + "\n", ""),
        "garde absent": ("          " + CHECK + "\n", ""),
        "autotest garde absent": ("          " + SELF_TEST + "\n", ""),
        "jeton conservé": ("          persist-credentials: false",
                            "          persist-credentials: true"),
        "échec ignoré": ("    needs: contract\n",
                          "    continue-on-error: true\n    needs: contract\n"),
        "publish ajouté": ("\n  live:\n", "\n  publish:\n    runs-on: ubuntu-24.04\n  live:\n"),
        "upload source": ("        run: " + LIVE, "        uses: actions/upload-pages-artifact@v3"),
        "timeout diminué": ("    timeout-minutes: 10\n", "    timeout-minutes: 1\n"),
    }
    for label, (needle, replacement) in cases.items():
        assert needle in original, "Mutation inapplicable : " + label
        assert failures(original.replace(needle, replacement, 1)), (
            "Régression acceptée : " + label
        )
    print(f"OK garde surveillance : {len(cases)} mutations dangereuses refusées")


def main() -> int:
    cli = argparse.ArgumentParser()
    mode = cli.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = cli.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = failures(WORKFLOW.read_text("utf-8"))
    for issue in errors:
        print("ECHEC : " + issue)
    if errors:
        return 1
    print("OK : planification quotidienne, sondes live réelles et permissions read-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
