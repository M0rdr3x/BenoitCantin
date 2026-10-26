#!/usr/bin/env python3
"""Refuser les vecteurs de compromission courants sur TOUS les workflows GitHub."""
from __future__ import annotations
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
SHA_ACTION = re.compile(r"^(?:[A-Za-z0-9_.-]+/){1,3}[A-Za-z0-9_.-]+@[a-fA-F0-9]{40}$")
ACTION_LINE = re.compile(r"(?m)^\s*(?:-\s*)?uses:\s*([^\s#]+)")
UNSAFE_TRIGGERS = re.compile(r"\b(?:pull_request_target|workflow_run)\s*:")
CURL_PIPE = re.compile(r"\b(?:curl|wget)\b[^\n]{0,240}\|\s*(?:bash|sh)\b")
SHELL_INTERPOLATION = re.compile(
    r"\$\{\{\s*github\.event\.pull_request\.(?:title|body|head\.ref)\s*\}\}"
)
CREDENTIAL_PERSIST = re.compile(
    r"""(?mi)^[ \t]*(?:-[ \t]*)?persist-credentials:[ \t]*(?:true|'true'|"true")[ \t]*(?:\#.*)?$"""
)

def validate_workflow(source: str) -> list[str]:
    clean = "\n".join(
        line for line in source.splitlines()
        if not line.lstrip().startswith("#")
    )
    problems: list[str] = []
    for match in ACTION_LINE.finditer(clean):
        action = match.group(1).strip("'\"")
        if not action.startswith("./") and not SHA_ACTION.fullmatch(action):
            problems.append("action non épinglée à un SHA immuable")
    if UNSAFE_TRIGGERS.search(clean) or re.search(
        r"\bon:\s*\[[^\]]*(?:pull_request_target|workflow_run)", clean
    ):
        problems.append("déclencheur GitHub privilégié interdit")
    if re.search(r"(?m)^\s*permissions:\s*write-all\s*$", clean):
        problems.append("jeton GitHub avec permission write-all")
    if CREDENTIAL_PERSIST.search(clean):
        problems.append("credentials Git persistants")
    if CURL_PIPE.search(clean):
        problems.append("script distant exécuté directement dans un shell")
    if SHELL_INTERPOLATION.search(clean):
        problems.append("donnée PR non fiable interpolée dans un shell")
    return problems

def self_test() -> None:
    good = (
        "on:\n  pull_request:\npermissions:\n  contents: read\njobs:\n"
        "  test:\n    steps:\n"
        "      - uses: actions/checkout@" + "a" * 40 + "\n"
        "      - uses: ./.github/actions/local\n"
    )
    assert not validate_workflow(good)
    changes = (
        ("actions/checkout@" + "a" * 40, "actions/checkout@v4"),
        ("  pull_request:", "  pull_request_target:"),
        ("  pull_request:", "  workflow_run:"),
        ("  contents: read", "  permissions: write-all"),
        ("      - uses:", "      - persist-credentials: true\n      - uses:"),
        ("      - uses:", "      - persist-credentials: 'true'\n      - uses:"),
        ("      - uses:", '      - persist-credentials: "true" # refuse aussi les commentaires YAML\n      - uses:'),
        ("      - uses:", "      - persist-credentials: true # commentaires YAML\n      - uses:"),
        ("      - uses:", "      - run: curl https://example.invalid/setup.sh | bash\n      - uses:"),
        ("      - uses:", "      - run: echo $" + "{{ github.event.pull_request.title }}\n      - uses:"),
    )
    for before, after in changes:
        bad = good.replace(before, after, 1)
        assert bad != good and validate_workflow(bad), before
    assert validate_workflow("on: [pull_request_target]\n")
    assert not validate_workflow(good + "      - persist-credentials: false\n")
    assert not validate_workflow(good + "      - persist-credentials: 'false'\n")
    assert not validate_workflow(
        good + "\n# uses: actions/unpinned@main\n# pull_request_target:\n"
    )
    print("OK Actions : 11 mutations négatives rejetées, y compris credentials YAML cités.")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    paths = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
    if not paths:
        print("ECHEC : aucun workflow à contrôler")
        return 1
    errors: list[str] = []
    for path in paths:
        if path.is_symlink() or not path.is_file():
            errors.append(path.name + ": chemin non fiable")
            continue
        try:
            source = path.read_text("utf-8")
        except (OSError, UnicodeError):
            errors.append(path.name + ": workflow non lisible")
            continue
        for problem in validate_workflow(source):
            errors.append(path.name + ": " + problem)
    if errors:
        for error in errors:
            print("ECHEC sécurité workflow : " + error)
        return 1
    print(f"OK : {len(paths)} workflows contrôlés : actions figées, aucune"
          " élévation PR ou injection shell détectée.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
