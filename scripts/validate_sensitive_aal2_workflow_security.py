#!/usr/bin/env python3
"""Security contract for the sensitive AAL2 local smoke workflow."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

WORKFLOW = Path('.github/workflows/sinjira-sensitive-aal2-v25.yml')
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SUPABASE_SETUP_SHA = '3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
PYTHON_VERSION = '3.12.14'
SUPABASE_VERSION = '2.111.0'
CONTRACT_TRIGGER = "      - 'scripts/validate_sensitive_aal2_workflow_security.py'"
SMOKE_TRIGGER = "      - 'scripts/smoke_sensitive_aal2_local.py'"
SMOKE_VALIDATOR_TRIGGER = "      - 'scripts/validate_sensitive_aal2_smoke.py'"
AUTH_TRIGGER = "      - 'supabase/functions/_shared/auth.ts'"
SECURITY_MIGRATION_TRIGGER = "      - 'supabase/migrations/**security**.sql'"
SELF_TEST_RUN = 'run: python scripts/validate_sensitive_aal2_workflow_security.py --self-test'
CONTRACT_RUN = 'run: python scripts/validate_sensitive_aal2_workflow_security.py'
SMOKE_CONTRACT_RUN = 'run: python3 scripts/validate_sensitive_aal2_smoke.py'
SUPABASE_START_RUN = 'run: supabase start'
SUPABASE_STOP_RUN = 'run: supabase stop --no-backup || true'
HTTP_SMOKE_COMMAND = 'python3 scripts/smoke_sensitive_aal2_local.py'


def fail(message: str) -> None:
    raise SystemExit(f'ERREUR: {message}')


def require_exact_line(text: str, expected: str) -> None:
    lines = [line.strip() for line in text.splitlines()]
    if lines.count(expected) != 1:
        fail(f'ligne exacte obligatoire absente ou dupliquée: {expected}')


def validate_text(text: str) -> None:
    required = [
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
        f'uses: supabase/setup-cli@{SUPABASE_SETUP_SHA}',
        f'version: {SUPABASE_VERSION}',
        HTTP_SMOKE_COMMAND,
    ]
    for needle in required:
        if needle not in text:
            fail(f'élément obligatoire absent: {needle}')

    for trigger, label in (
        (CONTRACT_TRIGGER, 'contrat CI'),
        (SMOKE_TRIGGER, 'smoke AAL2'),
        (SMOKE_VALIDATOR_TRIGGER, 'validateur smoke AAL2'),
        (AUTH_TRIGGER, 'frontière auth Edge'),
        (SECURITY_MIGRATION_TRIGGER, 'migrations sécurité'),
    ):
        if text.count(trigger) != 2:
            fail(f'{label}: déclenchement PR + push requis exactement deux fois')

    for command in (
        SELF_TEST_RUN,
        CONTRACT_RUN,
        SMOKE_CONTRACT_RUN,
        SUPABASE_START_RUN,
        SUPABASE_STOP_RUN,
    ):
        require_exact_line(text, command)

    if [line.strip() for line in text.splitlines()].count(HTTP_SMOKE_COMMAND) != 1:
        fail('la commande HTTP AAL2 doit apparaître exactement une fois')

    forbidden = [
        'ubuntu-latest',
        'actions/checkout@v',
        'actions/setup-python@v',
        'supabase/setup-cli@v',
        "python-version: '3.12'",
        'persist-credentials: true',
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
        '${{ github.token }}',
    ]
    for needle in forbidden:
        if needle in text:
            fail(f'élément mutable, distant ou dangereux détecté: {needle}')

    if re.search(r'^\s*environment\s*:', text, flags=re.MULTILINE):
        fail('un workflow AAL2 strictement local ne doit cibler aucun environment GitHub')
    if re.search(r'\$\{\{\s*secrets\.', text):
        fail('le workflow ne doit référencer aucun secret GitHub')
    if re.search(r'^\s*[A-Za-z0-9_-]+:\s*write\s*$', text, flags=re.MULTILINE):
        fail('permission GitHub en écriture détectée')
    if re.search(r'^\s*set\s+-[A-Za-z]*x[A-Za-z]*\b', text, flags=re.MULTILINE):
        fail('trace shell set -x interdite: elle peut exposer des données sensibles')

    network_patterns = (
        r'(^|[\s|;&])curl(?:\s|$)',
        r'(^|[\s|;&])wget(?:\s|$)',
        r'(^|[\s|;&])gh\s+api(?:\s|$)',
        r'(^|[\s|;&])git\s+push(?:\s|$)',
    )
    for pattern in network_patterns:
        if re.search(pattern, text, flags=re.MULTILINE):
            fail(f'primitive réseau inattendue détectée: {pattern}')

    uses_targets = re.findall(r'^\s*-?\s*uses:\s+(\S+)\s*$', text, flags=re.MULTILINE)
    expected_actions = {
        f'actions/checkout@{CHECKOUT_SHA}',
        f'actions/setup-python@{SETUP_PYTHON_SHA}',
        f'supabase/setup-cli@{SUPABASE_SETUP_SHA}',
    }
    if len(uses_targets) != 3 or set(uses_targets) != expected_actions:
        fail(f'ensemble inattendu d’actions réutilisables: {uses_targets}')
    for target in uses_targets:
        if '@' not in target or not re.fullmatch(r'[0-9a-f]{40}', target.rsplit('@', 1)[1]):
            fail(f'référence action non immuable: {target}')

    static_guard_index = text.index(CONTRACT_RUN)
    smoke_contract_index = text.index(SMOKE_CONTRACT_RUN)
    supabase_start_index = text.index(SUPABASE_START_RUN)
    http_smoke_index = text.index(HTTP_SMOKE_COMMAND)
    supabase_stop_index = text.index(SUPABASE_STOP_RUN)
    if not (static_guard_index < smoke_contract_index < supabase_start_index < http_smoke_index < supabase_stop_index):
        fail('ordre fail-closed attendu: garde CI, contrat smoke, Supabase local, smoke HTTP, arrêt local')


def self_test(text: str) -> None:
    mutations = {
        'checkout mutable': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mutable': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'setup-cli mutable': text.replace(f'supabase/setup-cli@{SUPABASE_SETUP_SHA}', 'supabase/setup-cli@v2', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'runner mutable': text.replace('ubuntu-24.04', 'ubuntu-latest', 1),
        'Python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'CLI mutable': text.replace(f'version: {SUPABASE_VERSION}', 'version: latest', 1),
        'secret GitHub': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\nenv:\n  BAD: ${{ secrets.BAD }}',
            1,
        ),
        'github token': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\nenv:\n  BAD_TOKEN: ${{ github.token }}',
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
            '      - name: Vérifier le contrat du smoke AAL2\n',
            '      - name: Vérifier le contrat du smoke AAL2\n        continue-on-error: true\n',
            1,
        ),
        'trace shell': text.replace('          set -euo pipefail', '          set -x', 1),
        'db push distant': text.replace(
            '      - name: Démarrer Supabase local complet\n',
            '      - name: Mauvaise opération distante\n        run: supabase db push --linked\n\n      - name: Démarrer Supabase local complet\n',
            1,
        ),
        'migration repair distante': text.replace(
            '      - name: Démarrer Supabase local complet\n',
            '      - name: Mauvaise réparation distante\n        run: supabase migration repair --linked 20260910150000\n\n      - name: Démarrer Supabase local complet\n',
            1,
        ),
        'functions deploy distant': text.replace(
            '      - name: Démarrer Supabase local complet\n',
            '      - name: Mauvais déploiement distant\n        run: supabase functions deploy personal-ai\n\n      - name: Démarrer Supabase local complet\n',
            1,
        ),
        'supabase link distant': text.replace(
            '      - name: Démarrer Supabase local complet\n',
            '      - name: Mauvais lien distant\n        run: supabase link --project-ref bad\n\n      - name: Démarrer Supabase local complet\n',
            1,
        ),
        'bypass JWT': text.replace(
            '      - name: Démarrer Supabase local complet\n',
            '      - name: Mauvais bypass JWT\n        run: supabase functions serve --no-verify-jwt\n\n      - name: Démarrer Supabase local complet\n',
            1,
        ),
        'curl inattendu': text.replace(
            '      - name: Démarrer Supabase local complet\n',
            '      - name: Mauvais réseau\n        run: curl https://example.invalid\n\n      - name: Démarrer Supabase local complet\n',
            1,
        ),
        'wget inattendu': text.replace(
            '      - name: Démarrer Supabase local complet\n',
            '      - name: Mauvais réseau\n        run: wget https://example.invalid\n\n      - name: Démarrer Supabase local complet\n',
            1,
        ),
        'gh api inattendu': text.replace(
            '      - name: Démarrer Supabase local complet\n',
            '      - name: Mauvaise API GitHub\n        run: gh api repos/x/y\n\n      - name: Démarrer Supabase local complet\n',
            1,
        ),
        'git push inattendu': text.replace(
            '      - name: Démarrer Supabase local complet\n',
            '      - name: Mauvaise écriture Git\n        run: git push origin HEAD\n\n      - name: Démarrer Supabase local complet\n',
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
        'déclencheur contrat retiré': text.replace(CONTRACT_TRIGGER + '\n', '', 1),
        'déclencheur smoke retiré': text.replace(SMOKE_TRIGGER + '\n', '', 1),
        'déclencheur validateur smoke retiré': text.replace(SMOKE_VALIDATOR_TRIGGER + '\n', '', 1),
        'déclencheur auth retiré': text.replace(AUTH_TRIGGER + '\n', '', 1),
        'déclencheur migration sécurité retiré': text.replace(SECURITY_MIGRATION_TRIGGER + '\n', '', 1),
        'auto-test retiré': text.replace(
            '      - name: Auto-tester le contrat CI AAL2 sensible\n'
            f'        {SELF_TEST_RUN}\n\n',
            '',
            1,
        ),
        'contrat CI retiré': text.replace(
            '      - name: Vérifier le contrat CI AAL2 sensible\n'
            f'        {CONTRACT_RUN}\n\n',
            '',
            1,
        ),
        'contrat smoke retiré': text.replace(f'        {SMOKE_CONTRACT_RUN}\n', '', 1),
        'Supabase local retiré': text.replace(f'        {SUPABASE_START_RUN}\n', '', 1),
        'smoke AAL2 retiré': text.replace(f'            {HTTP_SMOKE_COMMAND}\n', '', 1),
        'arrêt local retiré': text.replace(f'        {SUPABASE_STOP_RUN}\n', '', 1),
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
    text = WORKFLOW.read_text(encoding='utf-8')
    if args.self_test:
        self_test(text)
    else:
        validate_text(text)
        print('OK: contrat CI smoke AAL2 sensible respecté')


if __name__ == '__main__':
    main()
