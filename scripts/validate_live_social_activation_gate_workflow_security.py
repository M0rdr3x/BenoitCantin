#!/usr/bin/env python3
"""Fail-closed CI security contract for the V25 Live Social activation gate."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

WORKFLOW = Path('.github/workflows/sinjira-live-social-activation-gate-v25.yml')
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
PYTHON_VERSION = '3.12.14'

TRIGGERS = (
    "      - 'supabase/production-migration-ledger.txt'",
    "      - 'supabase/migrations/**'",
    "      - 'scripts/validate_production_migration_ledger.py'",
    "      - 'scripts/validate_production_schema_manifest.py'",
    "      - 'scripts/validate_live_social_activation_gate_v25.py'",
    "      - 'scripts/test_live_social_activation_gate_v25.py'",
    "      - 'scripts/validate_live_social_activation_gate_workflow_security.py'",
    "      - 'assets/js/**/*.js'",
    "      - 'assets/css/**/*.css'",
    "      - '**/*.html'",
    "      - '.github/workflows/sinjira-live-social-activation-gate-v25.yml'",
)

SELF_TEST_RUN = 'run: python scripts/validate_live_social_activation_gate_workflow_security.py --self-test'
CONTRACT_RUN = 'run: python scripts/validate_live_social_activation_gate_workflow_security.py'
STATE_TEST_RUN = 'run: python scripts/test_live_social_activation_gate_v25.py'
GATE_RUN = 'run: python scripts/validate_live_social_activation_gate_v25.py'
LEDGER_RUN = 'run: python scripts/validate_production_migration_ledger.py'
MANIFEST_RUN = 'run: python scripts/validate_production_schema_manifest.py'


def fail(message: str) -> None:
    raise SystemExit(f'ERREUR activation-gate CI: {message}')


def stripped_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines()]


def require_exact_line(text: str, expected: str) -> None:
    count = stripped_lines(text).count(expected)
    if count != 1:
        fail(f'ligne exacte obligatoire absente ou dupliquée ({count}): {expected}')


def exact_line_index(text: str, expected: str) -> int:
    lines = stripped_lines(text)
    if lines.count(expected) != 1:
        fail(f'ligne exacte obligatoire absente ou dupliquée pour ordre: {expected}')
    return lines.index(expected)


def validate_text(text: str) -> None:
    required = (
        'permissions:\n  contents: read',
        'pull_request:\n    branches: [main]',
        'push:\n    branches: [main]',
        'workflow_dispatch:',
        'runs-on: ubuntu-24.04',
        'timeout-minutes: 10',
        f'uses: actions/checkout@{CHECKOUT_SHA}',
        'fetch-depth: 0',
        'persist-credentials: false',
        f'uses: actions/setup-python@{SETUP_PYTHON_SHA}',
        f"python-version: '{PYTHON_VERSION}'",
    )
    for needle in required:
        if needle not in text:
            fail(f'élément obligatoire absent: {needle}')

    for trigger in TRIGGERS:
        if text.count(trigger) != 2:
            fail(f'déclenchement PR + push requis exactement deux fois: {trigger}')

    commands = (
        SELF_TEST_RUN,
        CONTRACT_RUN,
        STATE_TEST_RUN,
        GATE_RUN,
        LEDGER_RUN,
        MANIFEST_RUN,
    )
    for command in commands:
        require_exact_line(text, command)

    forbidden = (
        'ubuntu-latest',
        'actions/checkout@v',
        'actions/setup-python@v',
        "python-version: '3.12'",
        'persist-credentials: true',
        'SUPABASE_ACCESS_TOKEN',
        'SUPABASE_DB_PASSWORD',
        'github-token:',
        '${{ github.token }}',
        'supabase db push',
        'supabase migration repair',
        'supabase functions deploy',
        'supabase secrets set',
        'supabase link',
        '--linked',
        '--no-verify-jwt',
        'continue-on-error:',
        'inputs.apply',
    )
    for needle in forbidden:
        if needle in text:
            fail(f'élément mutable, distant ou dangereux détecté: {needle}')

    if re.search(r'\$\{\{\s*secrets\.', text):
        fail('aucun secret GitHub ne doit être référencé')
    if re.search(r'^\s*environment\s*:', text, flags=re.MULTILINE):
        fail('le garde dark launch ne doit cibler aucun environment GitHub')
    if re.search(r'^\s*[A-Za-z0-9_-]+:\s*write\s*$', text, flags=re.MULTILINE):
        fail('permission GitHub en écriture détectée')
    if re.search(r'^\s*set\s+-[A-Za-z]*x[A-Za-z]*\b', text, flags=re.MULTILINE):
        fail('trace shell set -x interdite')

    network_or_write_patterns = (
        r'(^|[\s|;&])curl(?:\s|$)',
        r'(^|[\s|;&])wget(?:\s|$)',
        r'(^|[\s|;&])gh\s+api(?:\s|$)',
        r'(^|[\s|;&])git\s+push(?:\s|$)',
        r'(^|[\s|;&])pip\s+install(?:\s|$)',
        r'(^|[\s|;&])python(?:3)?\s+-m\s+pip\s+install(?:\s|$)',
        r'(^|[\s|;&])npm(?:\s|$)',
        r'(^|[\s|;&])npx(?:\s|$)',
        r'(^|[\s|;&])docker\s+login(?:\s|$)',
        r'(^|[\s|;&])docker\s+push(?:\s|$)',
    )
    for pattern in network_or_write_patterns:
        if re.search(pattern, text, flags=re.MULTILINE):
            fail(f'primitive réseau, dépendance ou écriture inattendue détectée: {pattern}')

    uses_targets = re.findall(r'^\s*-?\s*uses:\s+(\S+)\s*$', text, flags=re.MULTILINE)
    expected_actions = {
        f'actions/checkout@{CHECKOUT_SHA}',
        f'actions/setup-python@{SETUP_PYTHON_SHA}',
    }
    if len(uses_targets) != 2 or set(uses_targets) != expected_actions:
        fail(f'ensemble inattendu d’actions réutilisables: {uses_targets}')
    for target in uses_targets:
        if '@' not in target or not re.fullmatch(r'[0-9a-f]{40}', target.rsplit('@', 1)[1]):
            fail(f'référence action non immuable: {target}')

    ordered = tuple(exact_line_index(text, command) for command in commands)
    if tuple(sorted(ordered)) != ordered:
        fail('ordre fail-closed attendu: auto-test, garde CI, tests états, garde activation, ledger, manifeste')


def self_test(text: str) -> None:
    # Un baseline invalide doit faire échouer le self-test avant toute mutation.
    validate_text(text)

    anchor = '      - name: Tester les états du garde En direct\n'
    mutations = {
        'checkout mutable': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mutable': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'historique Git tronqué': text.replace('fetch-depth: 0', 'fetch-depth: 1', 1),
        'runner mutable': text.replace('ubuntu-24.04', 'ubuntu-latest', 1),
        'Python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'permission contents write': text.replace('contents: read', 'contents: write', 1),
        'permission additionnelle write': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\n  issues: write',
            1,
        ),
        'secret GitHub': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\nenv:\n  BAD: ${{ secrets.BAD }}',
            1,
        ),
        'github token explicite': text.replace(
            anchor,
            '      - name: Mauvais token\n        env:\n          TOKEN: ${{ github.token }}\n        run: echo bad\n\n' + anchor,
            1,
        ),
        'environment production': text.replace(
            '    runs-on: ubuntu-24.04',
            '    environment: production\n    runs-on: ubuntu-24.04',
            1,
        ),
        'continue-on-error': text.replace(
            anchor,
            '      - name: Mauvais contournement\n        continue-on-error: true\n        run: echo bad\n\n' + anchor,
            1,
        ),
        'trace shell': text.replace(
            anchor,
            '      - name: Mauvaise trace\n        run: set -x\n\n' + anchor,
            1,
        ),
        'db push distant': text.replace(
            anchor,
            '      - name: Mauvaise écriture distante\n        run: supabase db push --linked\n\n' + anchor,
            1,
        ),
        'migration repair distante': text.replace(
            anchor,
            '      - name: Mauvaise réparation distante\n        run: supabase migration repair --linked 20260910150000\n\n' + anchor,
            1,
        ),
        'functions deploy distant': text.replace(
            anchor,
            '      - name: Mauvais déploiement distant\n        run: supabase functions deploy live-social\n\n' + anchor,
            1,
        ),
        'secrets set distant': text.replace(
            anchor,
            '      - name: Mauvaise écriture secret\n        run: supabase secrets set BAD=value\n\n' + anchor,
            1,
        ),
        'supabase link distant': text.replace(
            anchor,
            '      - name: Mauvais lien distant\n        run: supabase link --project-ref bad\n\n' + anchor,
            1,
        ),
        'bypass JWT': text.replace(
            anchor,
            '      - name: Mauvais bypass JWT\n        run: supabase functions serve --no-verify-jwt\n\n' + anchor,
            1,
        ),
        'curl inattendu': text.replace(
            anchor,
            '      - name: Mauvais réseau\n        run: curl https://example.invalid\n\n' + anchor,
            1,
        ),
        'wget inattendu': text.replace(
            anchor,
            '      - name: Mauvais réseau\n        run: wget https://example.invalid\n\n' + anchor,
            1,
        ),
        'gh api inattendu': text.replace(
            anchor,
            '      - name: Mauvaise API GitHub\n        run: gh api repos/x/y\n\n' + anchor,
            1,
        ),
        'git push inattendu': text.replace(
            anchor,
            '      - name: Mauvaise écriture Git\n        run: git push origin HEAD\n\n' + anchor,
            1,
        ),
        'pip install inattendu': text.replace(
            anchor,
            '      - name: Mauvaise dépendance\n        run: pip install bad\n\n' + anchor,
            1,
        ),
        'npm inattendu': text.replace(
            anchor,
            '      - name: Mauvaise dépendance\n        run: npm install bad\n\n' + anchor,
            1,
        ),
        'docker push inattendu': text.replace(
            anchor,
            '      - name: Mauvaise publication\n        run: docker push example.invalid/x\n\n' + anchor,
            1,
        ),
        'action supplémentaire': text.replace(
            '      - name: Configurer Python\n',
            '      - name: Action inattendue\n        uses: owner/action@0123456789012345678901234567890123456789\n\n      - name: Configurer Python\n',
            1,
        ),
        'pull_request retiré': text.replace('  pull_request:\n    branches: [main]\n', '', 1),
        'push main retiré': text.replace('  push:\n    branches: [main]\n', '', 1),
        'workflow_dispatch retiré': text.replace('  workflow_dispatch:\n', '', 1),
        'auto-test retiré': text.replace(
            '      - name: Auto-tester le contrat CI garde activation En direct\n'
            f'        {SELF_TEST_RUN}\n\n',
            '',
            1,
        ),
        'contrat CI retiré': text.replace(
            '      - name: Vérifier le contrat CI garde activation En direct\n'
            f'        {CONTRACT_RUN}\n\n',
            '',
            1,
        ),
        'tests états retirés': text.replace(f'        {STATE_TEST_RUN}\n', '', 1),
        'garde activation retiré': text.replace(f'        {GATE_RUN}\n', '', 1),
        'ledger retiré': text.replace(f'        {LEDGER_RUN}\n', '', 1),
        'manifeste retiré': text.replace(f'        {MANIFEST_RUN}', '', 1),
        'timeout relâché': text.replace('timeout-minutes: 10', 'timeout-minutes: 30', 1),
    }

    for index, trigger in enumerate(TRIGGERS, 1):
        mutations[f'déclencheur {index} retiré'] = text.replace(trigger + '\n', '', 1)

    for label, mutated in mutations.items():
        if mutated == text:
            fail(f'auto-test invalide, mutation sans effet: {label}')
        try:
            validate_text(mutated)
        except (SystemExit, ValueError):
            continue
        fail(f'auto-test non détecté: {label}')

    print(f'OK: {len(mutations)}/{len(mutations)} mutations critiques détectées')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()

    if not WORKFLOW.is_file():
        fail(f'workflow absent: {WORKFLOW}')

    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        self_test(text)
    else:
        validate_text(text)
        print(
            'OK contrat CI garde activation En direct V25: actions et runtime immuables, '
            'tests dark launch obligatoires, aucune capacité production ou écriture distante.'
        )


if __name__ == '__main__':
    main()
