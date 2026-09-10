#!/usr/bin/env python3
"""Contrat fail-closed du workflow CI AAL2 confidentialité/sécurité admin."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

WORKFLOW = Path('.github/workflows/sinjira-admin-privacy-safety-aal2-v24-5-14.yml')
CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
ALLOWED_USES = {CHECKOUT, SETUP_PYTHON}
SELF_TEST = 'python scripts/validate_admin_aal2_workflow_security.py --self-test'
SELF_CHECK = 'python scripts/validate_admin_aal2_workflow_security.py'
SELF_TEST_LINE = f'        run: {SELF_TEST}'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}'

TRIGGER_PATHS = (
    "'supabase/migrations/20260824013042_sinjira_v24_5_14_admin_privacy_safety_aal2_hardening.sql'",
    "'supabase/production-migration-ledger.txt'",
    "'scripts/validate_admin_privacy_safety_aal2_v24_5_14.py'",
    "'scripts/validate_admin_aal2_workflow_security.py'",
    "'scripts/validate_site.py'",
    "'scripts/validate_supabase.py'",
    "'scripts/validate_production_migration_ledger.py'",
    "'scripts/validate_production_schema_manifest.py'",
    "'scripts/validate_free_only_mode.py'",
    "'ADMIN_PRIVACY_SAFETY_AAL2_V24_5_14.md'",
    "'.github/workflows/sinjira-admin-privacy-safety-aal2-v24-5-14.yml'",
)

CHECKS = (
    'python scripts/validate_admin_privacy_safety_aal2_v24_5_14.py',
    'python scripts/validate_site.py',
    'python scripts/validate_supabase.py',
    'python scripts/validate_production_migration_ledger.py',
    'python scripts/validate_production_schema_manifest.py',
    'python scripts/validate_free_only_mode.py',
)

FORBIDDEN_ACTIVE = (
    'ubuntu-latest',
    'contents: write',
    'persist-credentials: true',
    '${{ secrets.',
    'SUPABASE_ACCESS_TOKEN',
    'SUPABASE_DB_PASSWORD',
    'SERVICE_ROLE',
    'service_role',
    'environment: production',
    'api.supabase.com',
    'gpvivleexywljowcqkru',
    'supabase db push',
    'supabase link',
    'supabase functions deploy',
    'supabase functions list',
    'supabase secrets set',
    'supabase migration repair',
    '--linked',
    '--no-verify-jwt',
    'continue-on-error:',
    'set -x',
    'curl ',
    'wget ',
    'gh api',
    'git push',
    'GITHUB_TOKEN:',
    'GH_TOKEN:',
    'http://',
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


def active_text(text: str) -> str:
    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))


def exact_line_count(text: str, line: str) -> int:
    return text.splitlines().count(line)


def trigger_keys(on_block: str) -> set[str]:
    keys: set[str] = set()
    for line in on_block.splitlines()[1:]:
        match = re.match(r'^  ([A-Za-z0-9_-]+):(?:\s|$)', line)
        if match:
            keys.add(match.group(1))
    return keys


def mutate_section(text: str, start: str, end: str, old: str, new: str) -> str:
    current = section(text, start, end)
    if old not in current:
        return text
    return text.replace(current, current.replace(old, new, 1), 1)


def validate_text(text: str) -> None:
    on = section(text, 'on:\n', '\npermissions:')
    if trigger_keys(on) != {'pull_request', 'push', 'workflow_dispatch'}:
        fail('déclencheurs autorisés exactement: pull_request + push + workflow_dispatch')

    pr = section(text, '  pull_request:', '  push:')
    push = section(text, '  push:', '  workflow_dispatch:')
    for trigger_name, trigger in (('pull_request', pr), ('push', push)):
        if exact_line_count(trigger, '    branches: [main]') != 1:
            fail(f'{trigger_name} doit rester borné exactement à main')
        for path in TRIGGER_PATHS:
            if f'      - {path}' not in trigger:
                fail(f'chemin critique absent de {trigger_name}: {path}')

    required_exact = (
        '    runs-on: ubuntu-24.04',
        '    timeout-minutes: 10',
        '          persist-credentials: false',
        "          python-version: '3.12.14'",
        '          check-latest: false',
        SELF_TEST_LINE,
        SELF_CHECK_LINE,
    )
    if 'permissions:\n  contents: read' not in text:
        fail('permissions contents: read absentes')
    for line in required_exact:
        if exact_line_count(text, line) != 1:
            fail(f'ligne exacte obligatoire absente ou dupliquée: {line.strip()}')

    uses = re.findall(r'(?m)^\s*(?:-\s*)?uses:\s*([^\s#]+)', text)
    unexpected = [target for target in uses if target not in ALLOWED_USES]
    if unexpected:
        fail('action réutilisable non autorisée/non épinglée: ' + ', '.join(unexpected))
    if uses.count(CHECKOUT) != 1 or uses.count(SETUP_PYTHON) != 1:
        fail('checkout et setup-python doivent chacun apparaître exactement une fois')

    active = active_text(text)
    for marker in FORBIDDEN_ACTIVE:
        if marker in active:
            fail(f'capacité distante/secret/affaiblissement interdit dans la CI AAL2: {marker}')

    for check in CHECKS:
        line = f'        run: {check}'
        if exact_line_count(text, line) != 1:
            fail(f'contrôle AAL2 absent ou dupliqué: {check}')

    self_test_at = text.index(SELF_TEST_LINE + '\n')
    self_check_at = text.index(SELF_CHECK_LINE + '\n')
    check_positions = [text.index(f'        run: {check}\n') for check in CHECKS]
    if not self_test_at < self_check_at < min(check_positions):
        fail('ordre obligatoire: auto-test du garde → garde réel → validations AAL2')
    if check_positions != sorted(check_positions):
        fail('ordre des validations AAL2 modifié')


def mutations(text: str):
    yield 'trigger supplémentaire', text.replace('  workflow_dispatch:\n', '  pull_request_target:\n  workflow_dispatch:\n', 1)
    yield 'PR main retirée', text.replace('  pull_request:\n    branches: [main]\n', '  pull_request:\n    branches: [develop]\n', 1)
    yield 'push main retiré', text.replace('  push:\n    branches: [main]\n', '  push:\n    branches: [develop]\n', 1)
    yield 'workflow_dispatch retiré', text.replace('  workflow_dispatch:\n', '', 1)
    yield 'path garde PR retiré', mutate_section(text, '  pull_request:', '  push:', "      - 'scripts/validate_admin_aal2_workflow_security.py'\n", '')
    yield 'path garde push retiré', mutate_section(text, '  push:', '  workflow_dispatch:', "      - 'scripts/validate_admin_aal2_workflow_security.py'\n", '')
    yield 'path migration PR retiré', mutate_section(text, '  pull_request:', '  push:', f"      - {TRIGGER_PATHS[0]}\n", '')
    yield 'path migration push retiré', mutate_section(text, '  push:', '  workflow_dispatch:', f"      - {TRIGGER_PATHS[0]}\n", '')
    yield 'runner mobile', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)
    yield 'timeout élargi', text.replace('timeout-minutes: 10', 'timeout-minutes: 60', 1)
    yield 'checkout mobile', text.replace(CHECKOUT, 'actions/checkout@v6', 1)
    yield 'setup-python mobile', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)
    yield 'action inconnue compacte', text.replace('    steps:\n', '    steps:\n      - uses: owner/action@v1\n', 1)
    yield 'action inconnue nommée', text.replace('    steps:\n', '    steps:\n      - name: Action inconnue\n        uses: owner/action@deadbeef\n', 1)
    yield 'credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)
    yield 'Python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)
    yield 'Python latest', text.replace('check-latest: false', 'check-latest: true', 1)
    yield 'permission écriture', text.replace('contents: read', 'contents: write', 1)
    yield 'secret GitHub', text.replace('    steps:\n', '    env:\n      BAD: ${{ secrets.BAD }}\n    steps:\n', 1)
    yield 'token Supabase', text.replace('    steps:\n', '    env:\n      SUPABASE_ACCESS_TOKEN: x\n    steps:\n', 1)
    yield 'service role', text.replace('    steps:\n', '    env:\n      SERVICE_ROLE_KEY: x\n    steps:\n', 1)
    yield 'environment production', text.replace('    timeout-minutes: 10\n', '    timeout-minutes: 10\n    environment: production\n', 1)
    yield 'endpoint production', text.replace('        run: ' + CHECKS[0], '        run: echo api.supabase.com\n      - run: ' + CHECKS[0], 1)
    yield 'project production', text.replace('        run: ' + CHECKS[0], '        run: echo gpvivleexywljowcqkru\n      - run: ' + CHECKS[0], 1)
    yield 'db push', text.replace('        run: ' + CHECKS[0], '        run: supabase db push --linked\n      - run: ' + CHECKS[0], 1)
    yield 'functions deploy', text.replace('        run: ' + CHECKS[0], '        run: supabase functions deploy x\n      - run: ' + CHECKS[0], 1)
    yield 'JWT bypass', text.replace('        run: ' + CHECKS[0], '        run: echo --no-verify-jwt\n      - run: ' + CHECKS[0], 1)
    yield 'curl réseau', text.replace('        run: ' + CHECKS[0], '        run: curl https://example.invalid\n      - run: ' + CHECKS[0], 1)
    yield 'wget réseau', text.replace('        run: ' + CHECKS[0], '        run: wget https://example.invalid\n      - run: ' + CHECKS[0], 1)
    yield 'gh api', text.replace('        run: ' + CHECKS[0], '        run: gh api /repos/x/y\n      - run: ' + CHECKS[0], 1)
    yield 'git push', text.replace('        run: ' + CHECKS[0], '        run: git push origin main\n      - run: ' + CHECKS[0], 1)
    yield 'continue-on-error', text.replace('    timeout-minutes: 10\n', '    timeout-minutes: 10\n    continue-on-error: true\n', 1)
    yield 'set -x', text.replace('        run: ' + CHECKS[0], '        run: set -x\n      - run: ' + CHECKS[0], 1)
    yield 'auto-test retiré', text.replace(SELF_TEST_LINE + '\n', '        run: python -V\n', 1)
    yield 'garde réel retiré', text.replace(SELF_CHECK_LINE + '\n', '        run: python -V\n', 1)
    for index, check in enumerate(CHECKS, start=1):
        yield f'contrôle {index} retiré', text.replace(f'        run: {check}\n', '        run: python -V\n', 1)


def self_test(text: str) -> None:
    validate_text(text)

    benign_comments = text + (
        '\n# environment: production\n'
        '# SUPABASE_ACCESS_TOKEN\n'
        '# supabase db push --linked\n'
        '# --no-verify-jwt\n'
        '# curl https://example.invalid\n'
    )
    validate_text(benign_comments)

    missed: list[str] = []
    total = 0
    for label, mutated in mutations(text):
        total += 1
        if mutated == text:
            missed.append(f'{label} (mutation sans effet)')
            continue
        try:
            validate_text(mutated)
        except ValueError:
            continue
        missed.append(label)
    if missed:
        fail('mutations non détectées: ' + ', '.join(missed))
    print(f'OK: {total}/{total} mutations critiques détectées; commentaires inertes acceptés')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    text = WORKFLOW.read_text(encoding='utf-8')
    try:
        if args.self_test:
            self_test(text)
        else:
            validate_text(text)
            print(
                'OK CI AAL2 admin: PR+push main+manuel exacts, runner/actions/Python épinglés, '
                'permissions read-only et aucune capacité production/réseau explicite.'
            )
    except ValueError as exc:
        raise SystemExit(f'ERREUR: {exc}') from exc


if __name__ == '__main__':
    main()
