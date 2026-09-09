#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'sinjira-v25-production-deploy.yml'
HARNESS = ROOT / '.github' / 'workflows' / 'sinjira-consciousness-vault-v25.yml'

CHECKOUT = 'actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON = 'actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_CLI = 'supabase/setup-cli@3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
SELF_TEST = 'python3 scripts/validate_v25_production_verification_workflow_security.py --self-test'
SELF_CHECK = 'python3 scripts/validate_v25_production_verification_workflow_security.py'
SELF_TEST_LINE = f'        run: {SELF_TEST}\n'
SELF_CHECK_LINE = f'        run: {SELF_CHECK}\n'
ALLOWED_SECRET = 'SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}'

EXPECTED_NAMES = (
    'sinjira_v25_0_security_risk_model_convergence',
    'sinjira_v25_0_personal_consciousness_vault',
    'sinjira_v25_0_conscience_vault_challenge_continuity',
    'sinjira_v25_0_device_key_privacy_and_trust_hardening',
    'sinjira_v25_conscience_vault_audit_session_index',
)

STATIC_CHECKS = (
    'python3 scripts/validate_conscience_vault_edge_v25.py',
    'python3 scripts/validate_edge_function_inventory.py',
    'python3 scripts/validate_production_schema_manifest.py',
    'python3 scripts/validate_v25_production_deploy_workflow.py',
    SELF_CHECK,
)

FORBIDDEN_ACTIVE = (
    'supabase db push',
    'supabase functions deploy',
    'supabase migration repair',
    'supabase secrets set',
    'supabase link',
    '--linked',
    '--no-verify-jwt',
    '--request',
    '--data',
    '--form',
    '--upload-file',
    'continue-on-error: true',
    'set -x',
    'gh api',
    'wget ',
)


def fail(message: str) -> None:
    raise ValueError(message)


def block(text: str, start: str, end: str) -> str:
    begin = text.find(start)
    if begin < 0:
        fail(f'section absente: {start.strip()}')
    finish = text.find(end, begin + len(start))
    if finish < 0:
        fail(f'fin de section absente: {end.strip()}')
    return text[begin:finish]


def active_text(text: str) -> str:
    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))


def trigger_keys(on_block: str) -> set[str]:
    keys: set[str] = set()
    for line in on_block.splitlines()[1:]:
        match = re.match(r'^  ([A-Za-z0-9_-]+):(?:\s|$)', line)
        if match:
            keys.add(match.group(1))
    return keys


def validate_workflow(text: str) -> None:
    triggers = block(text, 'on:\n', '\npermissions:')
    if trigger_keys(triggers) != {'workflow_dispatch'}:
        fail('vérification production non strictement manuelle')

    required = (
        'name: SINJIRA V25 — Vérification production coffre',
        'description: "Saisir exactement VERIFY-SINJIRA-V25"',
        'test "$VERIFY_CONFIRMATION" = "VERIFY-SINJIRA-V25"',
        'permissions:\n  contents: read',
        'cancel-in-progress: false',
        'runs-on: ubuntu-24.04',
        'timeout-minutes: 20',
        'environment: production',
        'SUPABASE_PROJECT_REF: gpvivleexywljowcqkru',
        'EXPECTED_REMOTE_BASELINE: "20260901002241"',
        'EXPECTED_REMOTE_BASELINE_NAME: sinjira_v24_5_54_fracture_contribution_atomic_finalize',
        'SUPABASE_MANAGEMENT_API: https://api.supabase.com/v1',
        'test "$GITHUB_REF" = "refs/heads/main"',
        'ref: main',
        'persist-credentials: false',
        'fetch-depth: 1',
        "python-version: '3.12.14'",
        'version: 2.111.0',
        '/projects/$SUPABASE_PROJECT_REF/database/migrations',
        '--header "Authorization: Bearer $SUPABASE_ACCESS_TOKEN"',
        'after_names[:len(required)] != required',
        'supabase functions list --project-ref "$SUPABASE_PROJECT_REF"',
        "grep -Fq 'conscience-vault'",
        'Vérification V25 terminée en lecture seule.',
        "Aucune migration, aucun secret et aucune Edge Function n'ont été modifiés par ce workflow.",
    )
    for marker in required:
        if marker not in text:
            fail(f'contrat production absent: {marker}')

    for action in (CHECKOUT, SETUP_PYTHON, SETUP_CLI):
        if action not in text:
            fail(f'action épinglée absente: {action}')
    if text.count('uses:') != 3:
        fail('nombre d actions externe inattendu')
    for mutable in ('actions/checkout@v', 'actions/setup-python@v', 'supabase/setup-cli@v'):
        if mutable in text:
            fail(f'action mobile interdite: {mutable}')

    if text.count(ALLOWED_SECRET) != 3:
        fail('SUPABASE_ACCESS_TOKEN doit être injecté exactement dans trois étapes bornées')
    sanitized = text.replace(ALLOWED_SECRET, '')
    if '${{ secrets.' in sanitized:
        fail('secret GitHub supplémentaire interdit')
    for marker in ('SUPABASE_DB_PASSWORD', 'SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_ROLE_KEY'):
        if marker in text:
            fail(f'secret/capacité supplémentaire interdit: {marker}')

    for marker in STATIC_CHECKS:
        if marker not in text:
            fail(f'validateur statique absent: {marker}')
    for name in EXPECTED_NAMES:
        if f'"{name}"' not in text:
            fail(f'migration V25 attendue absente: {name}')

    active = active_text(text)
    for marker in FORBIDDEN_ACTIVE:
        if marker in active:
            fail(f'opération distante ou affaiblissement interdit: {marker}')

    remote_supabase = [
        line.strip() for line in active.splitlines()
        if line.strip().startswith('supabase ')
    ]
    expected_supabase = ['supabase functions list --project-ref "$SUPABASE_PROJECT_REF" | tee "$functions_list"']
    if remote_supabase != expected_supabase:
        fail(f'commandes Supabase distantes inattendues: {remote_supabase}')

    curls = [line.strip() for line in active.splitlines() if line.strip().startswith('curl ')]
    if curls != ['curl --fail-with-body --silent --show-error \\']:
        fail(f'lecture HTTP inattendue: {curls}')
    if active.count('/projects/$SUPABASE_PROJECT_REF/database/migrations') != 1:
        fail('historique distant doit être lu exactement une fois')

    order = (
        'Refuser les lancements hors main',
        'Vérifier la confirmation et le jeton',
        'Checkout de main',
        'Configurer Python',
        'Vérifier les contrats statiques V25',
        'Vérifier l\'historique V25 en lecture seule',
        'Installer Supabase CLI pour l\'inventaire Edge',
        'Vérifier la présence de conscience-vault',
        'Résumé lecture seule',
    )
    indexes = [text.find(marker) for marker in order]
    if min(indexes) < 0 or indexes != sorted(indexes):
        fail('ordre des barrières production non respecté')


def validate_harness(text: str) -> None:
    pr = block(text, '  pull_request:', '  push:')
    push = block(text, '  push:', '  workflow_dispatch:')
    for marker in (
        "'scripts/validate_v25_production_verification_workflow_security.py'",
        "'.github/workflows/sinjira-v25-production-deploy.yml'",
    ):
        if marker not in pr or marker not in push:
            fail(f'contrat production non couvert PR+push par le Coffre: {marker}')
    if SELF_TEST_LINE not in text:
        fail('auto-test du vérificateur production absent de la CI locale')
    if SELF_CHECK_LINE not in text:
        fail('contrat réel du vérificateur production absent de la CI locale')
    if text.index(SELF_TEST_LINE) > text.index(SELF_CHECK_LINE):
        fail('auto-test production doit précéder le contrat réel')


def validate_pair(workflow: str, harness: str) -> None:
    validate_workflow(workflow)
    validate_harness(harness)


def add_automatic_push(text: str) -> str:
    return text.replace(
        'on:\n  workflow_dispatch:',
        'on:\n  push:\n    branches: [main]\n  workflow_dispatch:',
        1,
    )


def mutations(workflow: str, harness: str):
    yield 'déclencheur push', add_automatic_push(workflow), harness
    yield 'confirmation description altérée', workflow.replace('Saisir exactement VERIFY-SINJIRA-V25', 'Confirmer', 1), harness
    yield 'confirmation test contournée', workflow.replace('test "$VERIFY_CONFIRMATION" = "VERIFY-SINJIRA-V25"', 'test -n "$VERIFY_CONFIRMATION"', 1), harness
    yield 'permissions écriture', workflow.replace('contents: read', 'contents: write', 1), harness
    yield 'runner latest', workflow.replace('runs-on: ubuntu-24.04', 'runs-on: ubuntu-latest', 1), harness
    yield 'environnement production retiré', workflow.replace('    environment: production\n', '', 1), harness
    yield 'checkout mobile', workflow.replace(CHECKOUT, 'actions/checkout@v6', 1), harness
    yield 'setup-python mobile', workflow.replace(SETUP_PYTHON, 'actions/setup-python@v6', 1), harness
    yield 'setup-cli mobile', workflow.replace(SETUP_CLI, 'supabase/setup-cli@v2', 1), harness
    yield 'credentials persistés', workflow.replace('persist-credentials: false', 'persist-credentials: true', 1), harness
    yield 'checkout hors main', workflow.replace('          ref: main', '          ref: develop', 1), harness
    yield 'fetch depth modifié', workflow.replace('fetch-depth: 1', 'fetch-depth: 0', 1), harness
    yield 'python large', workflow.replace("python-version: '3.12.14'", "python-version: '3.12'", 1), harness
    yield 'cli latest', workflow.replace('version: 2.111.0', 'version: latest', 1), harness
    yield 'project ref modifié', workflow.replace('gpvivleexywljowcqkru', 'autreprojet', 1), harness
    yield 'baseline modifiée', workflow.replace('EXPECTED_REMOTE_BASELINE: "20260901002241"', 'EXPECTED_REMOTE_BASELINE: "0"', 1), harness
    yield 'secret supplémentaire', workflow.replace(ALLOWED_SECRET, ALLOWED_SECRET + '\n          SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}', 1), harness
    yield 'HTTP POST', workflow.replace('curl --fail-with-body', 'curl --request POST --fail-with-body', 1), harness
    yield 'HTTP data', workflow.replace('curl --fail-with-body', "curl --data '{}' --fail-with-body", 1), harness
    yield 'db push', workflow.replace('supabase functions list --project-ref', 'supabase db push --linked\n          supabase functions list --project-ref', 1), harness
    yield 'functions deploy', workflow.replace('supabase functions list --project-ref', 'supabase functions deploy conscience-vault\n          supabase functions list --project-ref', 1), harness
    yield 'secrets set', workflow.replace('supabase functions list --project-ref', 'supabase secrets set TEST=value\n          supabase functions list --project-ref', 1), harness
    yield 'migration repair', workflow.replace('supabase functions list --project-ref', 'supabase migration repair 1 --status applied\n          supabase functions list --project-ref', 1), harness
    yield 'continue on error', workflow.replace('    timeout-minutes: 20', '    timeout-minutes: 20\n    continue-on-error: true', 1), harness
    yield 'shell trace', workflow.replace('set -euo pipefail', 'set -x', 1), harness
    yield 'historique retiré', workflow.replace('/projects/$SUPABASE_PROJECT_REF/database/migrations', '/projects/$SUPABASE_PROJECT_REF/database/no-history', 1), harness
    yield 'functions list retiré', workflow.replace('supabase functions list --project-ref "$SUPABASE_PROJECT_REF" | tee "$functions_list"', 'echo functions-list-retire', 1), harness
    yield 'séquence migration retirée', workflow.replace('after_names[:len(required)] != required', 'False', 1), harness
    yield 'migration attendue retirée', workflow.replace(f'              "{EXPECTED_NAMES[0]}",\n', '', 1), harness
    yield 'contrat sécurité retiré du workflow production', workflow.replace(f'          {SELF_CHECK}\n', '          echo contrat-production-retire\n', 1), harness
    yield 'résumé lecture seule retiré', workflow.replace('Vérification V25 terminée en lecture seule.', 'Vérification terminée.', 1), harness
    yield 'auto-test retiré du harness', workflow, harness.replace(SELF_TEST_LINE, '        run: echo auto-test-production-retire\n', 1)
    yield 'contrat réel retiré du harness', workflow, harness.replace(SELF_CHECK_LINE, '        run: echo contrat-production-retire\n', 1)
    yield 'path contrat retiré du harness', workflow, harness.replace("      - 'scripts/validate_v25_production_verification_workflow_security.py'\n", '', 2)
    yield 'path workflow production retiré du harness', workflow, harness.replace("      - '.github/workflows/sinjira-v25-production-deploy.yml'\n", '', 2)


def self_test(workflow: str, harness: str) -> None:
    validate_pair(workflow, harness)
    total = 0
    detected = 0
    for name, mutated_workflow, mutated_harness in mutations(workflow, harness):
        total += 1
        try:
            validate_pair(mutated_workflow, mutated_harness)
        except ValueError:
            detected += 1
        else:
            raise SystemExit(f'ECHEC auto-test vérification production V25: mutation non détectée: {name}')
    print(f'OK: {detected}/{total} mutations critiques détectées')


def main() -> int:
    if not WORKFLOW.is_file() or not HARNESS.is_file():
        print('ECHEC CI vérification production V25: workflow ou harness absent', file=sys.stderr)
        return 1
    workflow = WORKFLOW.read_text('utf-8')
    harness = HARNESS.read_text('utf-8')
    try:
        if '--self-test' in sys.argv[1:]:
            self_test(workflow, harness)
        else:
            validate_pair(workflow, harness)
            print('OK: vérification production V25 manuelle, lecture seule, épinglée et couverte par CI locale')
    except ValueError as exc:
        print(f'ECHEC CI vérification production V25: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
