#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-consciousness-vault-v25.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_CLI = 'supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
ALLOWED_USES = {CHECKOUT, SETUP_PYTHON, SETUP_CLI}

SELF_TEST = 'python3 scripts/validate_consciousness_vault_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_consciousness_vault_workflow_security.py'
PROD_SELF_TEST = 'python3 scripts/validate_v25_production_verification_workflow_security.py --self-test'
PROD_SELF_CHECK = 'python3 scripts/validate_v25_production_verification_workflow_security.py'

SELF_TEST_LINE = f'        run: {SELF_TEST}'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}'
PROD_SELF_TEST_LINE = f'        run: {PROD_SELF_TEST}'
PROD_SELF_CHECK_LINE = f'        run: {PROD_SELF_CHECK}'

TRIGGER_PATHS = (
    "'supabase/migrations/**'",
    "'supabase/tests/personal_consciousness_vault_v25.test.sql'",
    "'supabase/functions/conscience-vault/**'",
    "'supabase/functions/_shared/auth.ts'",
    "'supabase/config.toml'",
    "'compte/registre-personnel.html'",
    "'compte/index.html'",
    "'compte/histoire-de-vie.html'",
    "'assets/js/sinjira-consciousness-vault-v25.js'",
    "'assets/css/sinjira-consciousness-vault-v25.css'",
    "'assets/js/sinjira-security-center-v24-4-98.js'",
    "'scripts/validate_conscience_vault_edge_v25.py'",
    "'scripts/validate_conscience_vault_web_v25.py'",
    "'scripts/validate_edge_function_inventory.py'",
    "'scripts/validate_production_schema_manifest.py'",
    "'scripts/validate_v25_production_deploy_workflow.py'",
    "'scripts/validate_v25_production_verification_workflow_security.py'",
    "'scripts/validate_consciousness_vault_workflow_security.py'",
    "'.github/workflows/sinjira-consciousness-vault-v25.yml'",
    "'.github/workflows/sinjira-v25-production-deploy.yml'",
)

STATIC_CHECKS = (
    'python3 scripts/validate_conscience_vault_edge_v25.py',
    'python3 scripts/validate_conscience_vault_web_v25.py',
    'python3 scripts/validate_edge_function_inventory.py',
    'python3 scripts/validate_production_schema_manifest.py',
    'python3 scripts/validate_v25_production_deploy_workflow.py',
)

PGTAP = 'supabase test db supabase/tests/personal_consciousness_vault_v25.test.sql --local'
DB_START = 'supabase db start'
STOP = 'run: supabase stop --no-backup || true'

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
    'gpvivleexywljowcqkru',
    'api.supabase.com',
    'supabase db push',
    'supabase link',
    'supabase functions deploy',
    'supabase functions list',
    'supabase secrets set',
    'supabase migration repair',
    'supabase db reset --linked',
    '--linked',
    '--no-verify-jwt',
    'inputs.apply',
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

    if 'permissions:\n  contents: read' not in text:
        fail('permissions contents: read absentes')
    if exact_line_count(text, '    runs-on: ubuntu-24.04') != 1:
        fail('runner Coffre doit être exactement ubuntu-24.04')
    if exact_line_count(text, '    timeout-minutes: 20') != 1:
        fail('timeout Coffre doit être exactement 20 minutes')
    if exact_line_count(text, '          persist-credentials: false') != 1:
        fail('checkout doit désactiver les credentials exactement une fois')
    if exact_line_count(text, "          python-version: '3.12.14'") != 1:
        fail('Python doit être exactement 3.12.14')
    if exact_line_count(text, '          check-latest: false') != 1:
        fail('setup-python doit rester fail-closed avec check-latest: false')
    if exact_line_count(text, '          version: 2.111.0') != 1:
        fail('Supabase CLI doit être exactement 2.111.0')
    if exact_line_count(text, '          github-token: ${{ github.token }}') != 1:
        fail('setup-cli doit utiliser uniquement le github.token borné du job')

    active = active_text(text)
    for marker in FORBIDDEN_ACTIVE:
        if marker in active:
            fail(f'capacité distante/secret/affaiblissement interdit dans la CI locale: {marker}')

    uses = re.findall(r'(?m)^\s*(?:-\s*)?uses:\s*([^\s#]+)', text)
    unexpected = [value for value in uses if value not in ALLOWED_USES]
    if unexpected:
        fail('action réutilisable non autorisée/non épinglée: ' + ', '.join(unexpected))
    if uses.count(CHECKOUT) != 1 or uses.count(SETUP_PYTHON) != 1 or uses.count(SETUP_CLI) != 1:
        fail('checkout, setup-python et setup-cli doivent chacun apparaître exactement une fois')

    pr = section(text, '  pull_request:', '  push:')
    push = section(text, '  push:', '  workflow_dispatch:')
    for trigger_name, trigger in (('pull_request', pr), ('push', push)):
        if exact_line_count(trigger, '    branches: [main]') != 1:
            fail(f'{trigger_name} doit rester borné exactement à main')
        for marker in TRIGGER_PATHS:
            if f'      - {marker}' not in trigger:
                fail(f'chemin critique non couvert par {trigger_name}: {marker}')

    for line, label in (
        (SELF_TEST_LINE, 'auto-test du garde local'),
        (SELF_CHECK_LINE, 'garde local réel'),
        (PROD_SELF_TEST_LINE, 'auto-test du garde production'),
        (PROD_SELF_CHECK_LINE, 'garde production réel'),
    ):
        if exact_line_count(text, line) != 1:
            fail(f'{label} absent ou dupliqué')

    for marker in STATIC_CHECKS:
        if text.count(marker) != 1:
            fail(f'validateur statique absent ou dupliqué: {marker}')

    if active.count(DB_START) != 1:
        fail('démarrage PostgreSQL Supabase local doit apparaître exactement une fois')
    if active.count(PGTAP) != 1:
        fail('preuve 32 pgTAP locale doit apparaître exactement une fois')
    if exact_line_count(text, '        if: always()') != 1 or exact_line_count(text, f'        {STOP}') != 1:
        fail('arrêt Supabase local always doit rester exact et unique')

    self_test_index = text.index(SELF_TEST_LINE)
    self_check_index = text.index(SELF_CHECK_LINE)
    prod_self_test_index = text.index(PROD_SELF_TEST_LINE)
    prod_self_check_index = text.index(PROD_SELF_CHECK_LINE)
    static_indexes = [text.index(marker) for marker in STATIC_CHECKS]
    cli_index = text.index(f'uses: {SETUP_CLI}')
    start_index = text.index(DB_START)
    test_index = text.index(PGTAP)
    stop_index = text.index(STOP)
    if not (
        self_test_index < self_check_index < prod_self_test_index < prod_self_check_index
        < min(static_indexes) <= max(static_indexes) < cli_index < start_index < test_index < stop_index
    ):
        fail('ordre obligatoire: auto-test local → garde local → auto-test prod → garde prod → statique → CLI → db start → pgTAP → stop')


def mutations(text: str):
    yield 'trigger supplémentaire', text.replace('  workflow_dispatch:\n', '  pull_request_target:\n  workflow_dispatch:\n', 1)
    yield 'PR main retirée', text.replace('  pull_request:\n    branches: [main]\n', '  pull_request:\n    branches: [develop]\n', 1)
    yield 'push main retiré', text.replace('  push:\n    branches: [main]\n', '  push:\n    branches: [develop]\n', 1)
    yield 'path garde PR retiré', mutate_section(text, '  pull_request:', '  push:', "      - 'scripts/validate_consciousness_vault_workflow_security.py'\n", '')
    yield 'path garde push retiré', mutate_section(text, '  push:', '  workflow_dispatch:', "      - 'scripts/validate_consciousness_vault_workflow_security.py'\n", '')
    yield 'path garde production PR retiré', mutate_section(text, '  pull_request:', '  push:', "      - 'scripts/validate_v25_production_verification_workflow_security.py'\n", '')
    yield 'path garde production push retiré', mutate_section(text, '  push:', '  workflow_dispatch:', "      - 'scripts/validate_v25_production_verification_workflow_security.py'\n", '')
    yield 'workflow production PR retiré', mutate_section(text, '  pull_request:', '  push:', "      - '.github/workflows/sinjira-v25-production-deploy.yml'\n", '')
    yield 'workflow production push retiré', mutate_section(text, '  push:', '  workflow_dispatch:', "      - '.github/workflows/sinjira-v25-production-deploy.yml'\n", '')
    yield 'checkout mobile', text.replace(CHECKOUT, 'actions/checkout@v6', 1)
    yield 'setup-python mobile', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)
    yield 'setup-cli mobile', text.replace(SETUP_CLI, 'supabase/setup-cli@v2', 1)
    yield 'action inconnue compacte', text.replace('    steps:\n', '    steps:\n      - uses: owner/action@v1\n', 1)
    yield 'action inconnue nommée', text.replace('    steps:\n', '    steps:\n      - name: Action inconnue\n        uses: owner/action@deadbeef\n', 1)
    yield 'credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)
    yield 'runner latest', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)
    yield 'python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)
    yield 'python latest', text.replace('check-latest: false', 'check-latest: true', 1)
    yield 'permissions écriture', text.replace('contents: read', 'contents: write', 1)
    yield 'cli dérive', text.replace('version: 2.111.0', 'version: latest', 1)
    yield 'github token remplacé', text.replace('github-token: ${{ github.token }}', 'github-token: ${{ secrets.GITHUB_TOKEN }}', 1)
    yield 'secret Supabase actif', text.replace('    steps:\n', '    env:\n      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n    steps:\n', 1)
    yield 'service role actif', text.replace('    steps:\n', '    env:\n      SERVICE_ROLE_KEY: x\n    steps:\n', 1)
    yield 'environnement production actif', text.replace('    timeout-minutes: 20\n', '    timeout-minutes: 20\n    environment: production\n', 1)
    yield 'project ref production actif', text.replace('          supabase db start\n', '          echo gpvivleexywljowcqkru\n          supabase db start\n', 1)
    yield 'endpoint production actif', text.replace('          supabase db start\n', '          echo api.supabase.com\n          supabase db start\n', 1)
    yield 'db push distant', text.replace('          supabase db start\n', '          supabase db push --linked\n          supabase db start\n', 1)
    yield 'link distant', text.replace('          supabase db start\n', '          supabase link --project-ref demo\n          supabase db start\n', 1)
    yield 'functions deploy', text.replace('          supabase db start\n', '          supabase functions deploy conscience-vault\n          supabase db start\n', 1)
    yield 'functions list', text.replace('          supabase db start\n', '          supabase functions list --project-ref demo\n          supabase db start\n', 1)
    yield 'secrets set', text.replace('          supabase db start\n', '          supabase secrets set X=Y\n          supabase db start\n', 1)
    yield 'migration repair', text.replace('          supabase db start\n', '          supabase migration repair 1 --status applied\n          supabase db start\n', 1)
    yield 'JWT désactivé actif', text.replace('          supabase db start\n', '          echo --no-verify-jwt\n          supabase db start\n', 1)
    yield 'curl réseau', text.replace('          supabase db start\n', '          curl https://example.invalid\n          supabase db start\n', 1)
    yield 'wget réseau', text.replace('          supabase db start\n', '          wget https://example.invalid\n          supabase db start\n', 1)
    yield 'gh api', text.replace('          supabase db start\n', '          gh api /repos/x/y\n          supabase db start\n', 1)
    yield 'git push', text.replace('          supabase db start\n', '          git push origin main\n          supabase db start\n', 1)
    yield 'continue on error', text.replace('    timeout-minutes: 20\n', '    timeout-minutes: 20\n    continue-on-error: true\n', 1)
    yield 'shell trace', text.replace('set -euo pipefail', 'set -x', 1)
    yield 'auto-test local retiré', text.replace(SELF_TEST_LINE + '\n', '        run: echo auto-test-local-retire\n', 1)
    yield 'garde local retiré', text.replace(SELF_CHECK_LINE + '\n', '        run: echo garde-local-retire\n', 1)
    yield 'auto-test prod retiré', text.replace(PROD_SELF_TEST_LINE + '\n', '        run: echo auto-test-prod-retire\n', 1)
    yield 'garde prod retiré', text.replace(PROD_SELF_CHECK_LINE + '\n', '        run: echo garde-prod-retire\n', 1)
    yield 'validateur edge retiré', text.replace(STATIC_CHECKS[0], 'echo edge-validator-retire', 1)
    yield 'validateur web retiré', text.replace(STATIC_CHECKS[1], 'echo web-validator-retire', 1)
    yield 'validateur inventaire retiré', text.replace(STATIC_CHECKS[2], 'echo inventory-validator-retire', 1)
    yield 'manifest retiré', text.replace(STATIC_CHECKS[3], 'echo manifest-validator-retire', 1)
    yield 'validateur production historique retiré', text.replace(STATIC_CHECKS[4], 'echo production-validator-retire', 1)
    yield 'db start retiré', text.replace(DB_START, 'echo db-start-retire', 1)
    yield 'pgTAP sans local', text.replace(PGTAP, PGTAP.replace(' --local', ''), 1)
    yield 'pgTAP retiré', text.replace(PGTAP, 'echo pgtap-retire', 1)
    yield 'arrêt non always', text.replace('        if: always()', '        if: success()', 1)
    yield 'arrêt retiré', text.replace('        ' + STOP, '        run: echo stop-retire', 1)


def self_test(text: str) -> None:
    validate_text(text)

    # Les commentaires sont inertes : le garde doit raisonner sur les capacités actives,
    # pas produire de faux positifs à partir de documentation ou d'exemples commentés.
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
    for name, mutated in mutations(text):
        total += 1
        if mutated == text:
            missed.append(f'{name} (mutation sans effet)')
            continue
        try:
            validate_text(mutated)
        except ValueError:
            continue
        missed.append(name)
    if missed:
        raise ValueError('mutations non détectées: ' + ', '.join(missed))
    print(f'OK: {total}/{total} mutations critiques détectées; commentaires inertes acceptés')


def main() -> int:
    if not WORKFLOW.is_file():
        print('ECHEC CI Coffre des consciences: workflow absent', file=sys.stderr)
        return 1
    text = WORKFLOW.read_text('utf-8')
    try:
        if '--self-test' in sys.argv[1:]:
            self_test(text)
        else:
            validate_text(text)
            print(
                'OK CI Coffre V25: déclencheurs exacts PR+push main+manuel, actions/runtimes épinglés, '
                'permissions read-only, aucune capacité production active et chaîne PostgreSQL/pgTAP strictement locale.'
            )
    except ValueError as exc:
        print(f'ECHEC CI Coffre des consciences V25: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())