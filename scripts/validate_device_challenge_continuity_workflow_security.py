#!/usr/bin/env python3
"""Security contract for the V25 device-challenge continuity workflow."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

WORKFLOW = Path('.github/workflows/sinjira-device-challenge-continuity-v25.yml')
CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SUPABASE_SETUP_SHA = '3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
PYTHON_VERSION = '3.12.14'
SUPABASE_VERSION = '2.111.0'
CONTRACT_TRIGGER = "      - 'scripts/validate_device_challenge_continuity_workflow_security.py'"
REBIND_TRIGGER = "      - 'scripts/validate_device_session_rebind_hardening.py'"
SECURITY_MIGRATION_TRIGGER = "      - 'supabase/migrations/**security**.sql'"
CHALLENGE_TRIGGER = "      - 'supabase/tests/device_challenge_continuity_v25.test.sql'"
SELF_TEST_STEP = (
    '      - name: Auto-tester le contrat CI continuité appareils\n'
    '        run: python scripts/validate_device_challenge_continuity_workflow_security.py --self-test\n'
)
CONTRACT_STEP = (
    '      - name: Vérifier le contrat CI continuité appareils\n'
    '        run: python scripts/validate_device_challenge_continuity_workflow_security.py\n'
)
REBIND_SELF_TEST_STEP = (
    '      - name: Auto-tester la réassociation de session appareil\n'
    '        run: python3 scripts/validate_device_session_rebind_hardening.py --self-test\n'
)
REBIND_CONTRACT_STEP = (
    '      - name: Vérifier la réassociation de session appareil\n'
    '        run: python3 scripts/validate_device_session_rebind_hardening.py\n'
)


def fail(message: str) -> None:
    raise SystemExit(f'ERREUR: {message}')


def validate_text(text: str) -> None:
    required = [
        'permissions:\n  contents: read',
        'pull_request:',
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
        SELF_TEST_STEP,
        CONTRACT_STEP,
        REBIND_SELF_TEST_STEP,
        REBIND_CONTRACT_STEP,
        'python3 scripts/validate_conscience_vault_edge_v25.py',
        'python3 scripts/validate_sensitive_aal2_smoke.py',
        'python3 scripts/validate_device_challenge_continuity_smoke.py',
        'python3 scripts/validate_production_schema_manifest.py',
        'supabase start',
        'supabase test db supabase/tests/personal_consciousness_vault_v25.test.sql --local',
        'supabase test db supabase/tests/device_challenge_continuity_v25.test.sql --local',
        'python3 scripts/smoke_device_challenge_continuity_local.py',
        'supabase stop --no-backup || true',
    ]
    for needle in required:
        if needle not in text:
            fail(f'élément obligatoire absent: {needle}')

    if text.count(CONTRACT_TRIGGER) != 2:
        fail('le contrat CI doit déclencher le workflow sur PR et push')
    if text.count(REBIND_TRIGGER) != 2:
        fail('le contrat de réassociation doit déclencher le workflow sur PR et push')
    if text.count(SECURITY_MIGRATION_TRIGGER) != 2:
        fail('les migrations sécurité doivent déclencher le workflow sur PR et push')
    if text.count(CHALLENGE_TRIGGER) != 2:
        fail('le contrat pgTAP challenge doit déclencher PR et push')

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
        '--linked',
        'supabase functions deploy',
        'supabase link',
        'environment: production',
        '--no-verify-jwt',
    ]
    for needle in forbidden:
        if needle in text:
            fail(f'élément mutable, distant ou dangereux détecté: {needle}')

    if re.search(r'\$\{\{\s*secrets\.', text):
        fail('le workflow ne doit référencer aucun secret GitHub')
    if re.search(r'^\s*[A-Za-z0-9_-]+:\s*write\s*$', text, flags=re.MULTILINE):
        fail('permission GitHub en écriture détectée')

    uses_targets = re.findall(r'^\s*-?\s*uses:\s+(\S+)\s*$', text, flags=re.MULTILINE)
    if len(uses_targets) != 3:
        fail(f'nombre inattendu d’actions réutilisables: {len(uses_targets)}')
    for target in uses_targets:
        if '@' not in target or not re.fullmatch(r'[0-9a-f]{40}', target.rsplit('@', 1)[1]):
            fail(f'référence action non immuable: {target}')

    rebind_contract = text.index('python3 scripts/validate_device_session_rebind_hardening.py\n')
    base_pg = text.index('supabase test db supabase/tests/personal_consciousness_vault_v25.test.sql --local')
    challenge_pg = text.index('supabase test db supabase/tests/device_challenge_continuity_v25.test.sql --local')
    smoke = text.index('python3 scripts/smoke_device_challenge_continuity_local.py')
    if not (rebind_contract < base_pg < challenge_pg < smoke):
        fail('ordre attendu: contrat rebind, pgTAP Coffre, pgTAP challenge, puis smoke HTTP')


def self_test(text: str) -> None:
    mutations = {
        'checkout mobile': text.replace(f'actions/checkout@{CHECKOUT_SHA}', 'actions/checkout@v6', 1),
        'setup-python mobile': text.replace(f'actions/setup-python@{SETUP_PYTHON_SHA}', 'actions/setup-python@v6', 1),
        'setup-cli mobile': text.replace(f'supabase/setup-cli@{SUPABASE_SETUP_SHA}', 'supabase/setup-cli@v2', 1),
        'credentials persistés': text.replace('persist-credentials: false', 'persist-credentials: true', 1),
        'runner mobile': text.replace('ubuntu-24.04', 'ubuntu-latest', 1),
        'Python large': text.replace(f"python-version: '{PYTHON_VERSION}'", "python-version: '3.12'", 1),
        'CLI mutable': text.replace(f'version: {SUPABASE_VERSION}', 'version: latest', 1),
        'permission écriture': text.replace('contents: read', 'contents: write', 1),
        'secret GitHub': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\nenv:\n  BAD: ${{ secrets.BAD }}',
            1,
        ),
        'environnement production': text.replace(
            'permissions:\n  contents: read',
            'permissions:\n  contents: read\nenvironment: production',
            1,
        ),
        'opération distante': text.replace(
            '      - name: Démarrer Supabase local complet\n',
            '      - name: Mauvaise opération distante\n        run: supabase db push --linked\n\n      - name: Démarrer Supabase local complet\n',
            1,
        ),
        'push main retiré': text.replace('  push:\n    branches: [main]\n', '', 1),
        'déclencheur contrat retiré': text.replace(CONTRACT_TRIGGER + '\n', '', 1),
        'déclencheur rebind retiré': text.replace(REBIND_TRIGGER + '\n', '', 1),
        'déclencheur migrations sécurité retiré': text.replace(SECURITY_MIGRATION_TRIGGER + '\n', '', 1),
        'déclencheur challenge retiré': text.replace(CHALLENGE_TRIGGER + '\n', '', 1),
        'auto-test retiré': text.replace(SELF_TEST_STEP + '\n', '', 1),
        'contrat CI retiré': text.replace(CONTRACT_STEP + '\n', '', 1),
        'auto-test rebind retiré': text.replace(REBIND_SELF_TEST_STEP + '\n', '', 1),
        'contrat rebind retiré': text.replace(REBIND_CONTRACT_STEP + '\n', '', 1),
        'validateur challenge retiré': text.replace(
            '          python3 scripts/validate_device_challenge_continuity_smoke.py\n',
            '',
            1,
        ),
        'Supabase local retiré': text.replace('        run: supabase start\n', '', 1),
        'pgTAP Coffre retiré': text.replace(
            '        run: supabase test db supabase/tests/personal_consciousness_vault_v25.test.sql --local\n',
            '',
            1,
        ),
        'pgTAP challenge retiré': text.replace(
            '        run: supabase test db supabase/tests/device_challenge_continuity_v25.test.sql --local\n',
            '',
            1,
        ),
        'smoke HTTP retiré': text.replace(
            '            python3 scripts/smoke_device_challenge_continuity_local.py\n',
            '',
            1,
        ),
        'arrêt local retiré': text.replace('        run: supabase stop --no-backup || true\n', '', 1),
        'timeout modifié': text.replace('timeout-minutes: 20', 'timeout-minutes: 30', 1),
    }

    for label, mutated in mutations.items():
        if mutated == text:
            fail(f'auto-test invalide, mutation sans effet: {label}')
        try:
            validate_text(mutated)
        except (SystemExit, ValueError):
            continue
        fail(f'auto-test non détecté: {label}')

    print(f'OK: {len(mutations)} mutations critiques détectées')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    text = WORKFLOW.read_text(encoding='utf-8')
    if args.self_test:
        self_test(text)
    else:
        validate_text(text)
        print('OK: contrat CI continuité challenge appareils V25 respecté')


if __name__ == '__main__':
    main()
