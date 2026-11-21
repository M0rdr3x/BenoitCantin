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
# Les clés YAML entre guillemets et les variantes "uses :" doivent rester
# soumises aux contrôles d'intégrité, jamais ignorées silencieusement.
ACTION_LINE = re.compile(r"^\s*(?:-\s*)?['\"]?uses['\"]?\s*:\s*(.*?)\s*$")
FLOW_USES_LINE = re.compile(r"^\s*-\s*\{.*['\"]?uses['\"]?\s*:")
ROOT_PERMISSIONS_LINE = re.compile(r"^(?:permissions|['\"]permissions['\"])\s*:\s*(.*)$")
ANY_WRITE_ALL = re.compile(
    r"(?m)^\s*['\"]?permissions['\"]?\s*:\s*['\"]?write-all['\"]?(?:\s*(?:#.*)?)?$"
)
IMMUTABLE_ACTION = re.compile(r"^[^@\s]+@[a-f0-9]{40}$")
IMMUTABLE_DOCKER = re.compile(r"^docker://[^@\s]+@sha256:[a-f0-9]{64}$")



def has_privileged_pr_trigger(source: str) -> bool:
    """Refuser pull_request_target dans les formes YAML bloc, liste et inline.

    On n'interprète que l'événement racine `on` : les exemples dans les
    commentaires et les commandes shell ne doivent pas produire de faux positifs.
    """
    lines = source.splitlines()
    event = re.compile(r"(?<![\w])['\"]?pull_request_target['\"]?(?![\w])")
    for index, line in enumerate(lines):
        root = re.match(r"^(?:on|['\"]on['\"])\s*:\s*(.*)$", line)
        if not root:
            continue
        if event.search(root.group(1).split("#", 1)[0]):
            return True
        for child in lines[index + 1:]:
            if child.strip() and not child[0].isspace() and not child.lstrip().startswith("#"):
                break
            candidate = child.strip().split("#", 1)[0].strip()
            if re.fullmatch(r"['\"]?pull_request_target['\"]?\s*:\s*.*", candidate):
                return True
            if re.fullmatch(r"-\s*['\"]?pull_request_target['\"]?", candidate):
                return True
    return False


def inspect_workflow(name: str, source: str) -> list[str]:
    errors: list[str] = []
    # Une permission déclarée dans UN job ne fixe pas les droits par défaut
    # des autres jobs. Exiger exactement une déclaration en racine YAML.
    root_permissions = [
        match for line in source.splitlines()
        if (match := ROOT_PERMISSIONS_LINE.match(line))
    ]
    if len(root_permissions) != 1:
        errors.append(f"{name}: déclaration de permissions globale unique obligatoire")
    if has_privileged_pr_trigger(source):
        errors.append(f"{name}: déclencheur privilégié pull_request_target interdit")
    if ANY_WRITE_ALL.search(source):
        errors.append(f"{name}: permissions write-all interdites")
    for lineno, raw in enumerate(source.splitlines(), 1):
        if FLOW_USES_LINE.match(raw):
            # Les mappings YAML compacts ne passent pas l'analyse des actions;
            # rejeter plutôt que laisser une action mutable non examinée.
            errors.append(f"{name}:{lineno}: uses en mapping YAML compact interdit")
            continue
        match = ACTION_LINE.match(raw)
        if not match:
            continue
        action = match.group(1).split(" #", 1)[0].strip()
        if len(action) >= 2 and action[0] in ("'", '"') and action[-1] == action[0]:
            action = action[1:-1]
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
        "permission limitée à un seul job":
            good.replace("permissions:\n  contents: read\n", "").replace(
                "    steps:\n", "    permissions:\n      contents: read\n    steps:\n"
            ),
        "permissions write-all locales":
            good.replace("    steps:\n", "    permissions: write-all\n    steps:\n"),
        "uses YAML à clé espacée et version mobile":
            good.replace("uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
                         "uses : actions/checkout@v6"),
        "uses YAML entre guillemets et version mobile":
            good.replace("uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
                         "'uses': 'actions/checkout@v6'"),
        "uses YAML mapping compact":
            good.replace("- uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
                         "- {name: Injection, uses: actions/checkout@v6}"),

    }
    for label, altered in mutants.items():
        if not inspect_workflow(label, altered):
            raise SystemExit(f"Auto-test défectueux : {label}")
    for bad_event in (
        "on: pull_request_target\n",
        "on : pull_request_target\n",
        "on: [push, pull_request_target]\n",
        "on: {push: {}, pull_request_target: {}}\n",
        "on:\n  'pull_request_target':\n",
        "on:\n  - pull_request_target\n",
    ):
        mutant = good.replace("on:\n  pull_request:\n", bad_event)
        if not inspect_workflow("événement alternatif", mutant):
            raise SystemExit("Auto-test défectueux : variante pull_request_target")
    # Des formes YAML valides et épinglées ne doivent jamais être rejetées.
    for variation in (
        good.replace("uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
                     "uses : actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"),
        good.replace("uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
                     '"uses": "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"'),
        good.replace("permissions:\n  contents: read", "'permissions':\n  contents: read"),
    ):
        assert inspect_workflow("variante épinglée", variation) == []
    safe_comment = good.replace("  pull_request:", "  # pull_request_target interdit\n  pull_request:")
    if inspect_workflow("commentaire inoffensif", safe_comment):
        raise SystemExit("Auto-test défectueux : faux positif commentaire")
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
