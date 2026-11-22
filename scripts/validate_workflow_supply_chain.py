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



# Une action checkout persiste le jeton GitHub par défaut. Les workflows
# qui exécutent du code fourni par une PR ne doivent jamais le conserver.
CHECKOUT_ACTION = re.compile(r"^actions/checkout@[a-f0-9]{40}$")
STEP_START = re.compile(
    r"^(?P<indent> *)-\s+(?:name|id|uses|if|run|shell|env|with|timeout-minutes|working-directory)\s*:"
)
WITH_LINE = re.compile(r"^(?P<indent> *)with\s*:\s*(?:#.*)?$")
PERSIST_LINE = re.compile(
    r"^(?P<indent> *)persist-credentials\s*:\s*(?P<value>[^#\n]*?)(?:\s+#.*)?$"
)


def checkout_token_findings(name: str, source: str) -> list[str]:
    """Inspecter le bloc STEP exact, pas un 'false' dans un autre step.

    L'option checkout doit être sous 'with:' à la bonne indentation.
    Les valeurs d'un 'run: |', commentaires, doublons et steps voisins
    ne peuvent pas satisfaire la règle de sécurité.
    """
    errors: list[str] = []
    lines = source.splitlines()
    for i, raw in enumerate(lines):
        m = ACTION_LINE.match(raw)
        if not m or not CHECKOUT_ACTION.fullmatch(m.group(1)):
            continue
        use_indent = len(raw) - len(raw.lstrip(" "))
        start = None
        step_indent = None
        for j in range(i, -1, -1):
            a = STEP_START.match(lines[j])
            if a and len(a.group("indent")) <= use_indent:
                start = j
                step_indent = len(a.group("indent"))
                break
        if start is None or step_indent is None:
            errors.append(f"{name}:{i+1}: checkout hors étape YAML identifiable")
            continue
        end = len(lines)
        for j in range(start + 1, len(lines)):
            line = lines[j]
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            if indent <= step_indent:
                end = j
                break

        with_indent = step_indent + 2
        field_indent = step_indent + 4
        w = [
            j for j in range(start, end)
            if (a := WITH_LINE.match(lines[j])) and len(a.group("indent")) == with_indent
        ]
        if len(w) != 1:
            errors.append(f"{name}:{i+1}: checkout sans bloc with unique")
            continue
        fields = []
        within_with = False
        for j in range(w[0] + 1, end):
            line = lines[j]
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            if indent <= with_indent:
                break
            a = PERSIST_LINE.match(line)
            if a and indent == field_indent:
                fields.append(a.group("value").strip().strip("'\""))
        if len(fields) != 1 or fields[0] != "false":
            errors.append(
                f"{name}:{i+1}: checkout doit déclarer un unique "
                "with.persist-credentials: false (jeton non persistant)"
            )
    return errors



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
    if not re.search(r"^\s*permissions\s*:", source, flags=re.MULTILINE):
        errors.append(f"{name}: permissions explicites manquantes")
    if has_privileged_pr_trigger(source):
        errors.append(f"{name}: déclencheur privilégié pull_request_target interdit")
    errors.extend(checkout_token_findings(name, source))
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
        "        with:\n"
        "          persist-credentials: false\n"
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
    checkout_mutants = {
        "checkout sans with": good.replace("        with:\\n          persist-credentials: false\\n", ""),
        "checkout token true": good.replace("persist-credentials: false", "persist-credentials: true"),
        "checkout champ incorrect": good.replace("persist-credentials: false", "persist_credentials: false"),
        "checkout commentaire": good.replace("persist-credentials: false", "# persist-credentials: false"),
        "checkout champ au mauvais niveau": good.replace("          persist-credentials: false", "        persist-credentials: false"),
        "checkout champ dans run": good.replace("        with:\\n          persist-credentials: false", "        run: |\\n          persist-credentials: false"),
        "checkout false au step suivant": good.replace(
            "        with:\\n          persist-credentials: false\\n      - uses: ./.github/actions/local-safe",
            "      - uses: ./.github/actions/local-safe\\n        with:\\n          persist-credentials: false"
        ),
        "checkout doublon true et false": good.replace(
            "          persist-credentials: false",
            "          persist-credentials: false\\n          persist-credentials: true"
        ),
        "checkout env au lieu de with": good.replace(
            "        with:\\n          persist-credentials: false",
            "        env:\\n          persist-credentials: false"
        ),
    }
    for label, altered in checkout_mutants.items():
        found = checkout_token_findings(label, altered)
        if not found:
            raise SystemExit(f"Auto-test credentials défectueux : {label}")
    assert checkout_token_findings("checkout correct", good) == []
    print(f"OK : {len(checkout_mutants)} mutations de jeton checkout détectées.")
    for bad_event in (
        "on: pull_request_target\n",
        "on: [push, pull_request_target]\n",
        "on: {push: {}, pull_request_target: {}}\n",
        "on:\n  'pull_request_target':\n",
        "on:\n  - pull_request_target\n",
    ):
        mutant = good.replace("on:\n  pull_request:\n", bad_event)
        if not inspect_workflow("événement alternatif", mutant):
            raise SystemExit("Auto-test défectueux : variante pull_request_target")
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
