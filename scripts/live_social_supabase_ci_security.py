#!/usr/bin/env python3
"""Invariants CI communs aux workflows Supabase locaux de En direct V25.

Ce module garde ces workflows strictement locaux et en lecture seule vis-a-vis
GitHub/Supabase hébergé. Il ne valide pas la logique métier propre à chaque
workflow; les validateurs spécialisés restent responsables de leurs preuves.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_CLI = 'supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
PYTHON_VERSION = "python-version: '3.12.14'"
SUPABASE_CLI_VERSION = 'version: 2.111.0'
START = 'run: supabase start'
STOP = 'run: supabase stop --no-backup || true'

FORBIDDEN = (
    '${{ secrets.',
    '${{ github.token',
    'GITHUB_TOKEN',
    'GH_TOKEN',
    'SUPABASE_ACCESS_TOKEN',
    'SUPABASE_DB_PASSWORD',
    'environment: production',
    'supabase db push',
    'db push',
    '--linked',
    'supabase link',
    'functions deploy',
    'migration repair',
    'inputs.apply',
    '--no-verify-jwt',
    'continue-on-error:',
    'set -x',
    'curl ',
    'wget ',
    'gh api',
    'git push',
)


def fail(message: str) -> None:
    raise ValueError(message)


def section(text: str, start: str, end: str) -> str:
    begin = text.find(start)
    if begin < 0:
        fail(f'section absente: {start.strip()}')
    finish = text.find(end, begin + len(start))
    if finish < 0:
        fail(f'fin de section absente: {end.strip()}')
    return text[begin:finish]


def validate_baseline(text: str, *, timeout_minutes: int, trigger_paths: Iterable[str]) -> None:
    if 'permissions:\n  contents: read' not in text:
        fail('permissions contents: read absentes')
    if re.search(r'^\s*permissions:\s*write-all\s*$', text, flags=re.MULTILINE):
        fail('permissions write-all interdites')
    if re.search(r'^\s*[A-Za-z0-9_-]+:\s*write\s*$', text, flags=re.MULTILINE):
        fail('permission GitHub en écriture détectée')

    if 'runs-on: ubuntu-24.04' not in text or 'ubuntu-latest' in text:
        fail('runner Ubuntu non figé à 24.04')
    if f'timeout-minutes: {timeout_minutes}' not in text:
        fail(f'timeout {timeout_minutes} minutes absent')

    for action in (CHECKOUT, SETUP_PYTHON, SETUP_CLI):
        if action not in text:
            fail(f'action épinglée absente: {action}')
    uses_targets = re.findall(r'^\s*-?\s*uses:\s+(\S+)\s*$', text, flags=re.MULTILINE)
    if len(uses_targets) != 3:
        fail(f'nombre inattendu d’actions réutilisables: {len(uses_targets)}')
    for target in uses_targets:
        if '@' not in target or not re.fullmatch(r'[0-9a-f]{40}', target.rsplit('@', 1)[1]):
            fail(f'référence action non immuable: {target}')

    if 'persist-credentials: false' not in text:
        fail('credentials Git persistés')
    if PYTHON_VERSION not in text:
        fail('Python 3.12.14 non figé')
    if SUPABASE_CLI_VERSION not in text:
        fail('Supabase CLI 2.111.0 non figé')

    pr = section(text, '  pull_request:', '  push:')
    push = section(text, '  push:', '  workflow_dispatch:')
    if 'branches: [main]' not in pr or 'branches: [main]' not in push:
        fail('couverture main PR/push incomplète')
    if '  workflow_dispatch:' not in text:
        fail('workflow_dispatch absent')
    for marker in trigger_paths:
        if marker not in pr:
            fail(f'chemin PR manquant: {marker}')
        if marker not in push:
            fail(f'chemin push main manquant: {marker}')

    if START not in text or 'supabase db start' in text:
        fail('pile Supabase locale complète non garantie')
    if text.count(START) != 1:
        fail('supabase start doit être unique')
    if 'if: always()' not in text or STOP not in text:
        fail('arrêt Supabase local always absent')
    if text.count(STOP) != 1:
        fail('arrêt Supabase local doit être unique')
    if text.index(START) >= text.index(STOP):
        fail('arrêt Supabase placé avant le démarrage')

    for marker in FORBIDDEN:
        if marker in text:
            fail(f'capacité CI interdite: {marker}')


def remove_section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    finish = text.index(end, begin + len(start))
    return text[:begin] + text[finish:]


def generic_mutations(text: str):
    yield 'checkout mutable', text.replace(CHECKOUT, 'actions/checkout@v6', 1)
    yield 'setup-python mutable', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)
    yield 'setup-cli mutable', text.replace(SETUP_CLI, 'supabase/setup-cli@v2', 1)
    yield 'credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)
    yield 'runner latest', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)
    yield 'Python large', text.replace(PYTHON_VERSION, "python-version: '3.12'", 1)
    yield 'CLI dérive', text.replace(SUPABASE_CLI_VERSION, 'version: latest', 1)
    yield 'permission contents write', text.replace('contents: read', 'contents: write', 1)
    yield 'permissions write-all', text.replace('permissions:\n  contents: read', 'permissions: write-all', 1)
    yield 'secret GitHub', text + '\nenv:\n  BAD: ${{ secrets.BAD }}\n'
    yield 'token GitHub explicite', text + '\nenv:\n  GITHUB_TOKEN: ${{ github.token }}\n'
    yield 'secret Supabase', text + '\nenv:\n  SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n'
    yield 'environnement production', text.replace('jobs:\n', 'jobs:\n  # environment: production\n', 1)
    yield 'db push distant', text + '\n# supabase db push --linked\n'
    yield 'liaison Supabase', text + '\n# supabase link --project-ref bad\n'
    yield 'déploiement fonction', text + '\n# supabase functions deploy bad\n'
    yield 'réparation migration', text + '\n# supabase migration repair 20260101000000\n'
    yield 'JWT désactivé', text + '\n# --no-verify-jwt\n'
    yield 'continue-on-error', text + '\n# continue-on-error: true\n'
    yield 'trace shell', text + '\n# set -x\n'
    yield 'curl réseau', text + '\n# curl https://example.invalid\n'
    yield 'wget réseau', text + '\n# wget https://example.invalid\n'
    yield 'gh api', text + '\n# gh api repos/example/example\n'
    yield 'git push', text + '\n# git push origin main\n'
    yield 'push main retiré', remove_section(text, '  push:', '  workflow_dispatch:')
    yield 'pull request retiré', remove_section(text, '  pull_request:', '  push:')
    yield 'workflow dispatch retiré', text.replace('  workflow_dispatch:\n', '', 1)
    yield 'start distant/altéré', text.replace(START, 'run: supabase db start', 1)
    yield 'arrêt non always', text.replace('if: always()', 'if: success()', 1)
    yield 'arrêt retiré', text.replace(STOP, 'run: echo stop-retire', 1)


def self_test(
    text: str,
    validate: Callable[[str], None],
    extra_mutations: Iterable[tuple[str, str]],
    *,
    label: str,
) -> None:
    validate(text)
    all_mutations = list(generic_mutations(text)) + list(extra_mutations)
    detected = 0
    for name, mutated in all_mutations:
        if mutated == text:
            raise SystemExit(f'ECHEC auto-test CI {label}: mutation sans effet: {name}')
        try:
            validate(mutated)
        except ValueError:
            detected += 1
        else:
            raise SystemExit(f'ECHEC auto-test CI {label}: mutation non détectée: {name}')
    print(f'OK: {detected}/{len(all_mutations)} mutations critiques détectées')
