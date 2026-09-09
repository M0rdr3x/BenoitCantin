#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-consciousness-vault-v25.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_CLI = 'supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
SELF_TEST = 'python3 scripts/validate_consciousness_vault_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_consciousness_vault_workflow_security.py'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}\n'

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

FORBIDDEN = (
    '${{ secrets.',
    'SUPABASE_ACCESS_TOKEN',
    'SUPABASE_DB_PASSWORD',
    'environment: production',
    'supabase db push',
    'db push',
    '--linked',
    'supabase link',
    'functions deploy',
    'secrets set',
    'migration repair',
    'inputs.apply',
    '--no-verify-jwt',
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


def validate_text(text: str) -> None:
    if 'permissions:\n  contents: read' not in text:
        fail('permissions read absentes')
    if 'runs-on: ubuntu-24.04' not in text or 'ubuntu-latest' in text:
        fail('runner non figé')
    if 'timeout-minutes: 20' not in text:
        fail('timeout 20 absent')

    for action in (CHECKOUT, SETUP_PYTHON, SETUP_CLI):
        if action not in text:
            fail(f'action épinglée absente: {action}')
    if text.count('uses:') != 3:
        fail('nombre d actions externe inattendu')
    for mutable in ('actions/checkout@v', 'actions/setup-python@v', 'supabase/setup-cli@v'):
        if mutable in text:
            fail(f'action mobile interdite: {mutable}')

    if 'persist-credentials: false' not in text:
        fail('credentials Git persistés')
    if "python-version: '3.12.14'" not in text:
        fail('Python non figé')
    if 'version: 2.111.0' not in text:
        fail('Supabase CLI non figé')

    pr = section(text, '  pull_request:', '  push:')
    push = section(text, '  push:', '  workflow_dispatch:')
    if 'branches: [main]' not in pr or 'branches: [main]' not in push:
        fail('couverture main PR/push absente')
    for marker in TRIGGER_PATHS:
        if marker not in pr or marker not in push:
            fail(f'chemin critique non couvert PR+push: {marker}')

    if SELF_TEST not in text:
        fail('auto-test contrat absent')
    if SELF_CHECK_LINE not in text:
        fail('contrat réel absent')
    for marker in STATIC_CHECKS:
        if marker not in text:
            fail(f'validateur statique absent: {marker}')
    if DB_START not in text:
        fail('démarrage DB Supabase local absent')
    if PGTAP not in text:
        fail('preuve 32 pgTAP absente')
    if 'if: always()' not in text or STOP not in text:
        fail('arrêt Supabase always absent')

    self_index = text.index(SELF_CHECK_LINE)
    static_indexes = [text.index(marker) for marker in STATIC_CHECKS]
    start_index = text.index(DB_START)
    test_index = text.index(PGTAP)
    stop_index = text.index(STOP)
    if not self_index < min(static_indexes) <= max(static_indexes) < start_index < test_index < stop_index:
        fail('ordre contrat -> statique -> db start -> pgTAP -> stop non respecté')

    for marker in FORBIDDEN:
        if marker in text:
            fail(f'capacité distante/secret interdit: {marker}')


def remove_push(text: str) -> str:
    begin = text.index('  push:')
    end = text.index('  workflow_dispatch:', begin)
    return text[:begin] + text[end:]


def mutations(text: str):
    yield 'checkout mobile', text.replace(CHECKOUT, 'actions/checkout@v6', 1)
    yield 'setup-python mobile', text.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1)
    yield 'setup-cli mobile', text.replace(SETUP_CLI, 'supabase/setup-cli@v2', 1)
    yield 'credentials persistés', text.replace('persist-credentials: false', 'persist-credentials: true', 1)
    yield 'runner latest', text.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1)
    yield 'python large', text.replace("python-version: '3.12.14'", "python-version: '3.12'", 1)
    yield 'permissions écriture', text.replace('contents: read', 'contents: write', 1)
    yield 'cli dérive', text.replace('version: 2.111.0', 'version: latest', 1)
    yield 'secret Supabase', text + '\nenv:\n  SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n'
    yield 'db push distant', text + '\n# supabase db push --linked\n'
    yield 'environnement production', text.replace('jobs:\n', 'jobs:\n  # environment: production\n', 1)
    yield 'push main retiré', remove_push(text)
    yield 'contrat path retiré', text.replace("      - 'scripts/validate_consciousness_vault_workflow_security.py'\n", '', 2)
    yield 'workflow deploy path retiré', text.replace("      - '.github/workflows/sinjira-v25-production-deploy.yml'\n", '', 2)
    yield 'auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '        run: echo auto-test-retire\n', 1)
    yield 'contrat réel retiré', text.replace(SELF_CHECK_LINE, '        run: echo contrat-retire\n', 1)
    yield 'validateur edge retiré', text.replace(STATIC_CHECKS[0], 'echo edge-validator-retire', 1)
    yield 'validateur web retiré', text.replace(STATIC_CHECKS[1], 'echo web-validator-retire', 1)
    yield 'validateur inventaire retiré', text.replace(STATIC_CHECKS[2], 'echo inventory-validator-retire', 1)
    yield 'validateur production retiré', text.replace(STATIC_CHECKS[4], 'echo deploy-validator-retire', 1)
    yield 'db start retiré', text.replace(DB_START, 'echo db-start-retire', 1)
    yield 'pgTAP retiré', text.replace(PGTAP, 'echo pgtap-retire', 1)
    yield 'arrêt non always', text.replace('if: always()', 'if: success()', 1)
    yield 'arrêt retiré', text.replace(STOP, 'run: echo stop-retire', 1)
    yield 'JWT désactivé', text + '\n# --no-verify-jwt\n'


def self_test(text: str) -> None:
    validate_text(text)
    detected = 0
    total = 0
    for name, mutated in mutations(text):
        total += 1
        try:
            validate_text(mutated)
        except ValueError:
            detected += 1
        else:
            raise SystemExit(f'ECHEC auto-test CI Coffre des consciences: mutation non détectée: {name}')
    print(f'OK: {detected}/{total} mutations critiques détectées')


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
            print('OK: contrat CI Coffre des consciences V25 respecté')
    except ValueError as exc:
        print(f'ECHEC CI Coffre des consciences V25: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
