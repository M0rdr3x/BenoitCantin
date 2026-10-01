#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-v25-extended-canon-local.yml'

CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'
SETUP_CLI_SHA = '3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
PYTHON_VERSION = '3.12.14'
CLI_VERSION = '2.111.0'

CANON_MIGRATIONS = (
    'supabase/migrations/20260918193000_sinjira_v25_extended_canon_chronicles.sql',
    'supabase/migrations/20260918201500_sinjira_v25_world_calendar_atlas_continuity.sql',
    'supabase/migrations/20260918220000_sinjira_v25_canon_provenance.sql',
    'supabase/migrations/20260926212000_sinjira_v25_canon_source_locator_guard.sql',
    'supabase/migrations/20260926214500_sinjira_v25_extended_canon_rpc_acl_hardening.sql',
)

CANON_TESTS = (
    'supabase/tests/extended_canon_continuity_v25.test.sql',
    'supabase/tests/canon_provenance_v25.test.sql',
    'supabase/tests/server_only_rls_contract_v25.test.sql',
    'supabase/tests/security_advisor_contract_v24_5_24.test.sql',
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def active_text(text: str) -> str:
    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('#'))


def validate_text(text: str) -> None:
    active = active_text(text)

    require('name: SINJIRA V25 — Canon étendu local' in text, 'Nom du workflow Canon local inattendu.')
    require('permissions:\n  contents: read' in text, 'Le workflow Canon local doit rester en contents: read uniquement.')
    require('runs-on: ubuntu-24.04' in text, 'Le workflow Canon local doit rester figé sur Ubuntu 24.04.')
    require('ubuntu-latest' not in active, 'ubuntu-latest est interdit pour cette preuve reproductible.')
    require('timeout-minutes: 30' in text, 'Le workflow Canon local doit conserver un timeout borné à 30 minutes.')

    require(
        'pull_request:\n    branches: [ main ]' in text,
        'La preuve Canon locale doit rester disponible sur les pull requests vers main, y compris draft.',
    )
    require(
        'github.event.pull_request.draft == false' not in active
        and 'github.event.pull_request.draft != true' not in active,
        'La preuve Canon locale ne doit pas être désactivée sur une PR draft.',
    )

    for path in CANON_MIGRATIONS + CANON_TESTS:
        marker = f"      - '{path}'"
        require(text.count(marker) >= 2, f'Le chemin Canon doit déclencher PR et push main: {path}')

    for path in (
        '.github/workflows/sinjira-v25-extended-canon-local.yml',
        'scripts/validate_extended_canon_local_workflow.py',
        'scripts/test_extended_canon_local_workflow.py',
        'scripts/validate_supabase.py',
        'scripts/validate_admin_sinjira_v18_request_security.py',
        'scripts/validate_character_questionnaire_security.py',
        'supabase/functions/admin-sinjira-v18/index.ts',
        'supabase/functions/submit-character-questionnaire/index.ts',
        'supabase/functions/_shared/auth.ts',
    ):
        marker = f"      - '{path}'"
        require(text.count(marker) >= 2, f'Le chemin de garde doit déclencher PR et push main: {path}')

    require(
        f'uses: actions/checkout@{CHECKOUT_SHA}' in text,
        'actions/checkout doit être épinglé au SHA vérifié.',
    )
    require('persist-credentials: false' in text, 'Le checkout doit désactiver la persistance des credentials Git.')
    require(
        f'uses: actions/setup-python@{SETUP_PYTHON_SHA}' in text,
        'actions/setup-python doit être épinglé au SHA vérifié.',
    )
    require(f"python-version: '{PYTHON_VERSION}'" in text, f'Python doit rester figé à {PYTHON_VERSION}.')
    require(
        f'uses: supabase/setup-cli@{SETUP_CLI_SHA}' in text,
        'supabase/setup-cli doit être épinglé au SHA vérifié.',
    )
    require(f'version: {CLI_VERSION}' in text, f'La Supabase CLI doit rester figée à {CLI_VERSION}.')

    uses = [line.strip() for line in active.splitlines() if line.strip().startswith('uses: ')]
    require(len(uses) == 3, f'Exactement trois actions réutilisables sont attendues; reçu={uses}')
    for line in uses:
        target = line.split('uses:', 1)[1].strip().split()[0]
        require(re.search(r'@[0-9a-f]{40}$', target) is not None, f'Référence d’action non immuable: {target}')

    forbidden = (
        'secrets.',
        'SUPABASE_ACCESS_TOKEN',
        'SUPABASE_DB_PASSWORD',
        'SUPABASE_SERVICE_ROLE_KEY',
        'SUPABASE_SECRET_KEYS',
        '--linked',
        '--project-ref',
        'supabase link',
        'supabase db push',
        'supabase migration repair',
        'supabase functions deploy',
        'supabase secrets set',
        'environment: production',
        'persist-credentials: true',
        'continue-on-error: true',
        '--no-verify-jwt',
        'set -x',
    )
    found = [marker for marker in forbidden if marker in active]
    require(not found, f'Primitive distante, secret ou tolérance interdite dans la preuve Canon locale: {found}')

    required_commands = (
        'python3 scripts/validate_extended_canon_local_workflow.py',
        'python3 scripts/test_extended_canon_local_workflow.py',
        'python3 scripts/validate_admin_sinjira_v18_request_security.py --self-test',
        'python3 scripts/validate_admin_sinjira_v18_request_security.py',
        'python3 scripts/validate_character_questionnaire_security.py --self-test',
        'python3 scripts/validate_character_questionnaire_security.py',
        'python3 scripts/validate_supabase.py',
        'supabase start',
        'supabase db reset',
        'supabase test db '
        'supabase/tests/extended_canon_continuity_v25.test.sql '
        'supabase/tests/canon_provenance_v25.test.sql '
        'supabase/tests/server_only_rls_contract_v25.test.sql '
        'supabase/tests/security_advisor_contract_v24_5_24.test.sql',
        'supabase stop --no-backup',
    )
    positions = [text.find(marker) for marker in required_commands]
    require(min(positions) >= 0, f'Commande Canon locale absente: {dict(zip(required_commands, positions))}')
    require(positions == sorted(positions), 'Ordre attendu: gardes statiques, start, reset, pgTAP ciblé, cleanup.')

    cleanup = text.find('- name: Arrêter et supprimer la pile locale')
    require(cleanup >= 0, 'Étape de nettoyage locale absente.')
    cleanup_section = text[cleanup:]
    require('if: always()' in cleanup_section, 'Le nettoyage Supabase local doit être exécuté avec if: always().')


def main() -> int:
    require(WORKFLOW.is_file(), f'Workflow absent: {WORKFLOW.relative_to(ROOT)}')
    validate_text(WORKFLOW.read_text(encoding='utf-8', errors='strict'))
    print(
        'OK Canon local: PR draft couverte, actions/CLI figées, 5 migrations et 4 contrats suivis, '
        'aucun secret et aucune opération Supabase distante.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
