#!/usr/bin/env python3
"""Security contract for the SINJIRA V25 local security-risk workflow."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-security-risk-v25.yml'

CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_CLI_SHA = '3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
PYTHON_VERSION = '3.12.14'
SUPABASE_VERSION = '2.111.0'

TRIGGERS = (
    "      - 'supabase/migrations/**'",
    "      - 'supabase/tests/security_risk_model_v25.test.sql'",
    "      - 'supabase/config.toml'",
    "      - 'scripts/validate_security_risk_workflow_security.py'",
    "      - '.github/workflows/sinjira-security-risk-v25.yml'",
)

SELF_TEST_RUN = 'run: python scripts/validate_security_risk_workflow_security.py --self-test'
CONTRACT_RUN = 'run: python scripts/validate_security_risk_workflow_security.py'
DB_START_COMMAND = 'supabase db start'
PGTAP_COMMAND = 'supabase test db supabase/tests/security_risk_model_v25.test.sql --local'
STOP_RUN = 'run: supabase stop --no-backup || true'


def fail(message: str) -> None:
    raise SystemExit(f'ERREUR risk-model CI: {message}')


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
        'timeout-minutes: 20',
        f'uses: actions/checkout@{CHECKOUT_SHA}',
        'persist-credentials: false',
        f'uses: actions/setup-python@{SETUP_PYTHON_SHA}',
        f"python-version: '{PYTHON_VERSION}'",
        f'uses: supabase/setup-cli@{SETUP_CLI_SHA}',
        f'version: {SUPABASE_VERSION}',
    )
    for needle in required:
        if needle not in text:
            fail(f'élément obligatoire absent: {needle}')

    for trigger in TRIGGERS:
        if text.count(trigger) != 2:
            fail(f'déclenchement PR + push requis exactement deux fois: {trigger}')

    for command in (SELF_TEST_RUN, CONTRACT_RUN, DB_START_COMMAND, PGTAP_COMMAND, STOP_RUN):
        require_exact_line(text, command)

    forbidden = (
        'ubuntu-latest',
        'actions/checkout@v',
        'actions/setup-python@v',
        'supabase/setup-cli@v',
        "python-version: '3.12'",
        'persist-credentials: true',
        'github-token:',
        '${{ github.token }}',
        'SUPABASE_ACCESS_TOKEN',
        'SUPABASE_DB_PASSWORD',
        'supabase db push',
        'supabase migration repair',
        'supabase functions deploy',
        'supabase secrets set',
        'supabase link',
        '--linked',
        '--no-verify-jwt',
        'continue-on-error:',
    )
    for needle in forbidden:
        if needle in text:
            fail(f'élément mutable, distant ou dangereux détecté: {needle}')

    if re.search(r'\$\{\{\s*secrets\.', text):
        fail('aucun secret GitHub ne doit être référencé')
    if re.search(r'^\s*environment\s*:', text, flags=re.MULTILINE):
        fail('un workflow de risque strictement local ne doit cibler aucun environment GitHub')
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
        f'supabase/setup-cli@{SETUP_CLI_SHA}',
    }
    if len(uses_targets) != 3 or set(uses_targets) != expected_actions:
        fail(f'ensemble inattendu d’actions réutilisables: {uses_targets}')
    for target in uses_targets:
        if '@' not in target or not re.fullmatch(r'[0-9a-f]{40}', target.rsplit('@', 1)[1]):
            fail(f'référence action non immuable: {target}')

    self_test_index = exact_line_index(text, SELF_TEST_RUN)
    contract_index = exact_line_index(text, CONTRACT_RUN)
    setup_cli_index = exact_line_index(text, f'uses: supabase/setup-cli@{SETUP_CLI_SHA}')
    db_start_index = exact_line_index(text, DB_START_COMMAND)
    pgtap_index = exact_line_index(text, PGTAP_COMMAND)
    stop_index = exact_line_index(text, STOP_RUN)
    if not (self_test_index < contract_index < setup_cli_index < db_start_index < pgtap_index < stop_index):
        fail('ordre fail-closed attendu: auto-test, garde CI, CLI épinglée, base locale, pgTAP, arrêt')


def self_test(text: str) -> None:
    # Le baseline doit être valide avant de tester les mutations, sinon un garde
    # cassé pourrait "détecter" toutes les mutations pour la mauvaise raison.
    validate_text(text)

    insertion_anchor = '      - name: Démarrer PostgreSQL Supabase local et appliquer les migrations\n'
    mutations = {
        'checkout mutable': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mutable': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'setup-cli mutable': text.replace(f'supabase/setup-cli@{SETUP_CLI_SHA}', 'supabase/setup-cli@v2', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'runner mutable': text.replace('ubuntu-24.04', 'ubuntu-latest', 1),
        'Python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'CLI mutable': text.replace(f'version: {SUPABASE_VERSION}', 'version: latest', 1),
        'github token explicite': text.replace(
            '          version: 2.111.0\n',
            '          version: 2.111.0\n          github-token: ${{ github.token }}\n',
            1,
        ),
        'secret GitHub': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\nenv:\n  BAD: ${{ secrets.BAD }}',
            1,
        ),
        'permission contents write': text.replace('contents: read', 'contents: write', 1),
        'permission additionnelle write': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\n  issues: write',
            1,
        ),
        'environment production': text.replace(
            '    runs-on: ubuntu-24.04',
            '    environment: production\n    runs-on: ubuntu-24.04',
            1,
        ),
        'continue-on-error': text.replace(
            insertion_anchor,
            '      - name: Mauvais contournement\n        continue-on-error: true\n        run: echo bad\n\n' + insertion_anchor,
            1,
        ),
        'trace shell': text.replace('          set -euo pipefail', '          set -x', 1),
        'db push distant': text.replace(
            insertion_anchor,
            '      - name: Mauvaise écriture distante\n        run: supabase db push --linked\n\n' + insertion_anchor,
            1,
        ),
        'migration repair distante': text.replace(
            insertion_anchor,
            '      - name: Mauvaise réparation distante\n        run: supabase migration repair --linked 20260910150000\n\n' + insertion_anchor,
            1,
        ),
        'functions deploy distant': text.replace(
            insertion_anchor,
            '      - name: Mauvais déploiement distant\n        run: supabase functions deploy security-risk\n\n' + insertion_anchor,
            1,
        ),
        'secrets set distant': text.replace(
            insertion_anchor,
            '      - name: Mauvaise écriture secret\n        run: supabase secrets set BAD=value\n\n' + insertion_anchor,
            1,
        ),
        'supabase link distant': text.replace(
            insertion_anchor,
            '      - name: Mauvais lien distant\n        run: supabase link --project-ref bad\n\n' + insertion_anchor,
            1,
        ),
        'bypass JWT': text.replace(
            insertion_anchor,
            '      - name: Mauvais bypass JWT\n        run: supabase functions serve --no-verify-jwt\n\n' + insertion_anchor,
            1,
        ),
        'curl inattendu': text.replace(
            insertion_anchor,
            '      - name: Mauvais réseau\n        run: curl https://example.invalid\n\n' + insertion_anchor,
            1,
        ),
        'wget inattendu': text.replace(
            insertion_anchor,
            '      - name: Mauvais réseau\n        run: wget https://example.invalid\n\n' + insertion_anchor,
            1,
        ),
        'gh api inattendu': text.replace(
            insertion_anchor,
            '      - name: Mauvaise API GitHub\n        run: gh api repos/x/y\n\n' + insertion_anchor,
            1,
        ),
        'git push inattendu': text.replace(
            insertion_anchor,
            '      - name: Mauvaise écriture Git\n        run: git push origin HEAD\n\n' + insertion_anchor,
            1,
        ),
        'pip install inattendu': text.replace(
            insertion_anchor,
            '      - name: Mauvaise dépendance\n        run: pip install bad\n\n' + insertion_anchor,
            1,
        ),
        'npm inattendu': text.replace(
            insertion_anchor,
            '      - name: Mauvaise dépendance\n        run: npm install bad\n\n' + insertion_anchor,
            1,
        ),
        'docker push inattendu': text.replace(
            insertion_anchor,
            '      - name: Mauvaise publication\n        run: docker push example.invalid/x\n\n' + insertion_anchor,
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
        'déclencheur migrations retiré': text.replace(TRIGGERS[0] + '\n', '', 1),
        'déclencheur test retiré': text.replace(TRIGGERS[1] + '\n', '', 1),
        'déclencheur config retiré': text.replace(TRIGGERS[2] + '\n', '', 1),
        'déclencheur garde retiré': text.replace(TRIGGERS[3] + '\n', '', 1),
        'déclencheur workflow retiré': text.replace(TRIGGERS[4] + '\n', '', 1),
        'auto-test retiré': text.replace(
            '      - name: Auto-tester le contrat CI du moteur de risque\n'
            f'        {SELF_TEST_RUN}\n\n',
            '',
            1,
        ),
        'contrat CI retiré': text.replace(
            '      - name: Vérifier le contrat CI du moteur de risque\n'
            f'        {CONTRACT_RUN}\n\n',
            '',
            1,
        ),
        'démarrage local retiré': text.replace('          supabase db start\n', '', 1),
        'pgTAP retiré': text.replace(f'          {PGTAP_COMMAND}\n', '', 1),
        'arrêt local retiré': text.replace(f'        {STOP_RUN}\n', '', 1),
        'timeout relâché': text.replace('timeout-minutes: 20', 'timeout-minutes: 30', 1),
    }

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
        fail(f'workflow absent: {WORKFLOW.relative_to(ROOT)}')

    text = WORKFLOW.read_text(encoding='utf-8', errors='strict')
    if args.self_test:
        self_test(text)
    else:
        validate_text(text)
        print(
            'OK sécurité risk-model CI: Python et actions immuables, '
            'Supabase local uniquement, PR/push main, aucune capacité production.'
        )


if __name__ == '__main__':
    main()
