#!/usr/bin/env python3
"""Contrat statique des actions CI : références immuables et droits minimaux.

Scanner local de fichiers YAML, sans exécuter de code GitHub, sans réseau
et sans secrets. Ce contrôle complète les protections serveur de main.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
ACTION_LINE = re.compile(r"^\s*(?:-\s*)?uses:\s*(\S+)")
IMMUTABLE_ACTION = re.compile(r"^[^@\s]+@[a-f0-9]{40}$")
IMMUTABLE_DOCKER = re.compile(r"^docker://[^@\s]+@sha256:[a-f0-9]{64}$")


def inspect_workflow(name: str, source: str) -> list[str]:
    errors: list[str] = []
    if not re.search(r"^\s*permissions\s*:", source, flags=re.MULTILINE):
        errors.append(f"{name}: permissions explicites manquantes")
    if re.search(r"^\s*pull_request_target\s*:", source, flags=re.MULTILINE):
        errors.append(f"{name}: déclencheur privilégié pull_request_target interdit")
    if re.search(r"^\s*permissions\s*:\s*write-all\b", source, flags=re.MULTILINE):
        errors.append(f"{name}: permissions write-all interdites")
    for lineno, raw in enumerate(source.splitlines(), 1):
        match = ACTION_LINE.match(raw)
        if not match:
            continue
        action = match.group(1)
        if action.startswith("./"):
            continue
        if action.startswith("docker://"):
            safe = bool(IMMUTABLE_DOCKER.fullmatch(action))
        else:
            safe = bool(IMMUTABLE_ACTION.fullmatch(action))
        if not safe:
            errors.append(f"{name}:{lineno}: action non épinglée à un commit : {action}")
    return errors


def self_test() -> None:
    good = (
        "name: Test\n"
        "on:\n  pull_request:\n"
        "permissions:\n  contents: read\n"
        "jobs:\n  verify:\n    steps:\n"
        "      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803\n"
        "      - uses: ./.github/actions/local-safe\n"
    )
    assert inspect_workflow("safe.yml", good) == []
    mutants = {
        "étiquette mobile": good.replace("@d23441a48e516b6c34aea4fa41551a30e30af803", "@v6"),
        "branche mobile": good.replace("@d23441a48e516b6c34aea4fa41551a30e30af803", "@main"),
        "permission implicite": good.replace("permissions:\n  contents: read\n", ""),
        "droits larges": good.replace("permissions:\n  contents: read", "permissions: write-all"),
        "déclencheur privilégié": good.replace("  pull_request:", "  pull_request_target:"),
    }
    for label, altered in mutants.items():
        if not inspect_workflow(label, altered):
            raise SystemExit(f"Auto-test défectueux : {label}")
    print("OK: les mutations de sécurité CI sont refusées.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not WORKFLOWS.is_dir():
        print("ÉCHEC: répertoire workflows manquant")
        return 1
    paths = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    if len(paths) < 100:
        print("ÉCHEC: inventaire workflows anormalement incomplet")
        return 1
    findings = []
    for path in paths:
        try:
            source = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeError, OSError):
            findings.append(f"{path.name}: fichier YAML illisible")
            continue
        findings.extend(inspect_workflow(path.name, source))
    if findings:
        print(f"ÉCHEC: {len(findings)} anomalie(s) dans {len(paths)} workflows :")
        for item in findings:
            print("- " + item)
        return 1
    print(f"OK: {len(paths)} workflows analysés; actions épinglées, déclencheurs et permissions contrôlés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
