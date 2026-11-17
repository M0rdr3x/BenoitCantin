#!/usr/bin/env python3
"""Reject direct interpolation of untrusted GitHub event strings into Actions shell scripts.

Dependency-free, read-only, and intentionally conservative. This does not replace
GitHub branch protection, a YAML parser, or independent code review. Bind untrusted
strings through a step environment variable and quote the variable in the shell.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / '.github' / 'workflows'
RUN_KEY = re.compile(r"^(?P<indent>[ \t]*)(?:-\s+)?(?:run|['\"]run['\"])\s*:\s*(?P<value>.*)$")
EXPRESSION = re.compile(r'\$\{\{(.*?)\}\}', re.DOTALL)
UNTRUSTED = re.compile(
    r'\b(?:github\.(?:head_ref|ref_name)\b'
    r'|github\.event\.(?:'
    r'pull_request\.(?:title|body|head\.(?:ref|label))'
    r'|issue\.(?:title|body)'
    r'|comment\.body|review\.body'
    r'|discussion\.(?:title|body)'
    r'|workflow_run\.head_branch'
    r'|release\.(?:name|body)'
    r'|inputs(?:\.[a-zA-Z_][\w-]*)?'
    r'|client_payload(?:\.[a-zA-Z_][\w-]*)*'
    r')\b'
    r'|\binputs\.[a-zA-Z_][\w-]*\b)',
    re.IGNORECASE,
)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(' \t'))


def inspect_workflow(name: str, source: str) -> list[str]:
    """Find dangerous event string expressions inside YAML run scalar values."""
    lines = source.splitlines()
    errors: list[str] = []
    for index, line in enumerate(lines):
        if line.lstrip().startswith('#'):
            continue
        match = RUN_KEY.match(line)
        if not match:
            continue
        scalar = match.group('value')
        snippet = scalar
        if re.match(r'^(?:&[\w-]+\s+)?[|>][-+0-9]*(?:\s*(?:#.*)?)?$', scalar):
            block = []
            for child in lines[index + 1:]:
                if child.strip() and _indent(child) <= _indent(line):
                    break
                if not child.lstrip().startswith('#'):
                    block.append(child)
            snippet = '\n'.join(block)
        elif scalar.lstrip().startswith('*'):
            # Aliases obscure the source of the run command and evade inspection.
            errors.append(f'{name}:{index + 1}: alias YAML interdit dans run')
            continue
        for expression in EXPRESSION.finditer(snippet):
            if UNTRUSTED.search(expression.group(1)):
                errors.append(
                    f'{name}:{index + 1}: interpolation directe de données GitHub non fiables dans run'
                )
    return errors


def self_test() -> None:
    good = (
        'name: Test\n'
        'on: pull_request\n'
        'permissions:\n  contents: read\n'
        'jobs:\n  check:\n    runs-on: ubuntu-24.04\n'
        '    steps:\n'
        '      - name: Script sûr\n'
        '        env:\n          PR_TITLE: ${{ github.event.pull_request.title }}\n'
        '        run: printf "%s\\n" "$PR_TITLE"\n'
    )
    assert inspect_workflow('safe.yml', good) == [], 'env isolation should be accepted'
    assert inspect_workflow('safe.yml', good + '        # run: echo ${{ github.head_ref }}\n') == []
    assert inspect_workflow('safe.yml', good + '        run: echo ${{ github.event.pull_request.number }}\n') == []
    mutants = {
        'PR title inline': '        run: echo "${{ github.event.pull_request.title }}"\n',
        'PR body block': '        run: |\n          echo "${{ github.event.pull_request.body }}"\n',
        'PR branch folded': '        run: >-\n          printf "%s" "${{ github.head_ref }}"\n',
        'issue body quoted run key': '        "run": echo "${{ github.event.issue.body }}"\n',
        'comment body expression': '        run: echo "${{ format(\'x{0}\', github.event.comment.body) }}"\n',
        'workflow dispatch input': '        run: echo "${{ inputs.deploy_target }}"\n',
        'event input alias': '        run: echo "${{ github.event.inputs.confirmation }}"\n',
        'event input object': '        run: echo "${{ toJSON(github.event.inputs) }}"\n',
        'repository dispatch payload': '        run: echo "${{ github.event.client_payload.command }}"\n',
        'repository dispatch payload object': '        run: echo "${{ toJSON(github.event.client_payload) }}"\n',
        'release note': '        run: echo "${{ github.event.release.body }}"\n',
        'ref name': '        run: echo "${{ github.ref_name }}"\n',
        'YAML alias': '        run: *unsafe-script\n',
    }
    for label, mutant in mutants.items():
        if not inspect_workflow(label, good + mutant):
            raise AssertionError(f'failed to reject: {label}')
    print('OK: malicious shell interpolation is rejected and env isolation is accepted.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not WORKFLOWS.is_dir():
        print('ECHEC: répertoire des workflows absent')
        return 1
    paths = sorted((*WORKFLOWS.glob('*.yml'), *WORKFLOWS.glob('*.yaml')))
    if len(paths) < 100:
        print('ECHEC: inventaire de workflows incomplet')
        return 1
    errors: list[str] = []
    for path in paths:
        try:
            source = path.read_text(encoding='utf-8', errors='strict')
        except (OSError, UnicodeError):
            errors.append(f'{path.name}: fichier illisible')
            continue
        errors.extend(inspect_workflow(path.name, source))
    for error in errors:
        print('ECHEC: ' + error)
    if errors:
        return 1
    print(f'OK: {len(paths)} workflows inspectés; aucune interpolation shell non fiable détectée.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
