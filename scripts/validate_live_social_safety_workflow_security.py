#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-live-social-safety-v25.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_CLI = 'supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
SELF_TEST = 'python scripts/validate_live_social_safety_workflow_security.py --self-test'
SELF_CHECK = 'python scripts/validate_live_social_safety_workflow_security.py'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}\n'

TRIGGER_PATHS = (
    "'supabase/production-migration-ledger.txt'",
    "'supabase/migrations/**'",
    "'supabase/tests/live_social_moderation_v25.test.sql'",
    "'supabase/tests/live_social_private_invites_v25.test.sql'",
    "'supabase/tests/live_social_share_codes_v25.test.sql'",
    "'supabase/tests/minor_exploitation_safety_v24_4_82.test.sql'",
    "'supabase/tests/global_safety_compliance_v24_4_83.test.sql'",
    "'supabase/tests/server_only_rls_contract_v25.test.sql'",
    "'supabase/tests/security_advisor_contract_v24_5_24.test.sql'",
    "'scripts/validate_live_social_safety_v25.py'",
    "'scripts/validate_live_social_share_codes_v25.py'",
    "'scripts/validate_live_social_foundation_v25.py'",
    "'scripts/validate_supabase.py'",
    "'scripts/validate_production_migration_ledger.py'",
    "'scripts/validate_production_schema_manifest.py'",
    "'scripts/validate_live_social_safety_workflow_security.py'",
    "'.github/workflows/sinjira-live-social-safety-v25.yml'",
)

STATIC_CHECKS = (
    'python scripts/validate_live_social_safety_v25.py',
    'python scripts/validate_live_social_share_codes_v25.py',
    'python scripts/validate_live_social_foundation_v25.py',
    'python scripts/validate_supabase.py',
    'python scripts/validate_production_migration_ledger.py',
    'python scripts/validate_production_schema_manifest.py',
)

PGTAP_CHECKS = (
    'supabase test db supabase/tests/live_social_moderation_v25.test.sql --local',
    'supabase test db supabase/tests/live_social_private_invites_v25.test.sql --local',
    'supabase test db supabase/tests/live_social_share_codes_v25.test.sql --local',
    'supabase test db supabase/tests/minor_exploitation_safety_v24_4_82.test.sql --local',
    'supabase test db supabase/tests/global_safety_compliance_v24_4_83.test.sql --local',
    'supabase test db supabase/tests/server_only_rls_contract_v25.test.sql --local',
    'supabase test db supabase/tests/security_advisor_contract_v24_5_24.test.sql --local',
)

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
        fail('permissions contents: read absentes')
    if 'runs-on: ubuntu-24.04' not in text or 'ubuntu-latest' in text:
        fail('runner Ubuntu non figé à 24.04')
    if 'timeout-minutes: 20' not in text:
        fail('timeout 20 minutes absent')

    for action in (CHECKOUT, SETUP_PYTHON, SETUP_CLI):
        if action not in text:
            fail(f'action épinglée absente: {action}')
    for mutable in ('actions/checkout@v', 'actions/setup-python@v', 'supabase/setup-cli@v'):
        if mutable in text:
            fail(f'action mobile interdite: {mutable}')
    if 'persist-credentials: false' not in text:
        fail('credentials Git persistés')
    if "python-version: '3.12.14'" not in text:
        fail('Python 3.12.14 non figé')
    if 'version: 2.111.0' not in text:
        fail('Supabase CLI 2.111.0 non figé')

    pr = section(text, '  pull_request:', '  push:')
    push = section(text, '  push:', '  workflow_dispatch:')
    if 'branches: [main]' not in pr or 'branches: [main]' not in push:
        fail('couverture main PR/push incomplète')
    for marker in TRIGGER_PATHS:
        if marker not in pr:
            fail(f'chemin PR manquant: {marker}')
        if marker not in push:
            fail(f'chemin push main manquant: {marker}')

    if SELF_TEST not in text:
        fail('auto-test du contrat CI absent')
    if SELF_CHECK_LINE not in text:
        fail('validation réelle du contrat CI absente')
    for marker in STATIC_CHECKS:
        if marker not in text:
            fail(f'validateur statique historique absent: {marker}')

    if 'run: supabase start' not in text or 'supabase db start' in text:
        fail('pile Supabase locale complète non garantie')
    for marker in PGTAP_CHECKS:
        if marker not in text:
            fail(f'preuve pgTAP absente: {marker}')
    if 'if: always()' not in text or 'run: supabase stop --no-backup || true' not in text:
        fail('arrêt Supabase local always absent')

    static_index = text.index(STATIC_CHECKS[0])
    start_index = text.index('run: supabase start')
    first_test = min(text.index(marker) for marker in PGTAP_CHECKS)
    last_test = max(text.index(marker) for marker in PGTAP_CHECKS)
    stop_index = text.index('run: supabase stop --no-backup || true')
    if not static_index < start_index < first_test <= last_test < stop_index:
        fail('ordre statique -> start -> pgTAP -> stop non respecté')

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
    yield 'secret GitHub', text + '\nenv:\n  SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}\n'
    yield 'db push distant', text + '\n# supabase db push --linked\n'
    yield 'environnement production', text.replace('jobs:\n', 'jobs:\n  # environment: production\n', 1)
    yield 'push main retiré', remove_push(text)
    yield 'chemin ledger retiré', text.replace("      - 'supabase/production-migration-ledger.txt'\n", '', 2)
    yield 'chemin advisor retiré', text.replace("      - 'supabase/tests/security_advisor_contract_v24_5_24.test.sql'\n", '', 2)
    yield 'chemin contrat retiré', text.replace("      - 'scripts/validate_live_social_safety_workflow_security.py'\n", '', 2)
    yield 'auto-test retiré', text.replace(f'        run: {SELF_TEST}\n', '        run: echo auto-test-retire\n', 1)
    yield 'contrat réel retiré', text.replace(SELF_CHECK_LINE, '        run: echo contrat-retire\n', 1)
    yield 'validateur sécurité retiré', text.replace('python scripts/validate_live_social_safety_v25.py', 'echo safety-retire', 1)
    yield 'pgTAP modération retiré', text.replace(PGTAP_CHECKS[0], 'echo moderation-retire', 1)
    yield 'pgTAP advisor retiré', text.replace(PGTAP_CHECKS[-1], 'echo advisor-retire', 1)
    yield 'arrêt non always', text.replace('if: always()', 'if: success()', 1)
    yield 'arrêt Supabase retiré', text.replace('run: supabase stop --no-backup || true', 'run: echo stop-retire', 1)
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
            raise SystemExit(f'ECHEC auto-test CI En direct: mutation non détectée: {name}')
    if detected != total:
        raise SystemExit(f'ECHEC auto-test CI En direct: {detected}/{total} mutations détectées')
    print(f'OK: {detected} mutations critiques détectées')


def main() -> int:
    if not WORKFLOW.is_file():
        print('ECHEC CI En direct: workflow absent', file=sys.stderr)
        return 1
    text = WORKFLOW.read_text('utf-8')
    try:
        if '--self-test' in sys.argv[1:]:
            self_test(text)
        else:
            validate_text(text)
            print('OK: contrat CI sécurité En direct V25 respecté')
    except ValueError as exc:
        print(f'ECHEC CI sécurité En direct V25: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
