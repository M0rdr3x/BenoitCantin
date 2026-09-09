#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/recovery-drill.yml'

CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_CLI_SHA = '3c2f5e2ae34c34e428e8e206e2c4d21fa2d20fbf'
CLI_VERSION = '2.111.0'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def active_text(text: str) -> str:
    return '\n'.join(
        line for line in text.splitlines()
        if not line.strip().startswith('#')
    )


def validate_text(text: str) -> None:
    active = active_text(text)

    require('permissions:\n  contents: read' in text, 'Le recovery drill doit conserver permissions.contents=read uniquement.')
    require("      - 'scripts/validate_recovery_drill_security.py'" in text, 'Le validateur doit déclencher le recovery drill quand il change.')
    require("      - 'scripts/test_recovery_drill_security.py'" in text, 'Les tests du garde doivent déclencher le recovery drill quand ils changent.')

    require(
        f'uses: actions/checkout@{CHECKOUT_SHA}' in text,
        'actions/checkout doit être épinglé au SHA vérifié.',
    )
    require('persist-credentials: false' in text, 'Le checkout doit désactiver la persistance des credentials Git.')
    require(
        f'uses: supabase/setup-cli@{SETUP_CLI_SHA}' in text,
        'supabase/setup-cli doit être épinglé au SHA vérifié.',
    )
    require(f'version: {CLI_VERSION}' in text, f'La Supabase CLI doit rester figée à {CLI_VERSION}.')

    uses = [line.strip() for line in active.splitlines() if line.strip().startswith('uses: ')]
    require(uses, 'Le workflow doit contenir des actions réutilisables attendues.')
    for line in uses:
        target = line.split('uses:', 1)[1].strip().split()[0]
        require(
            re.search(r'@[0-9a-f]{40}$', target) is not None,
            f'Référence d’action non immuable: {target}',
        )

    forbidden = [
        'version: latest',
        'secrets.',
        'SUPABASE_ACCESS_TOKEN',
        'SUPABASE_DB_PASSWORD',
        '--linked',
        '--project-ref',
        'supabase db push',
        'supabase migration repair',
        'supabase functions deploy',
        'supabase secrets set',
        'persist-credentials: true',
    ]
    found = [marker for marker in forbidden if marker in active]
    require(not found, f'Surface non déterministe ou distante interdite: {found}')

    require('python3 scripts/validate_recovery_drill_security.py' in text, 'Le recovery drill doit exécuter son validateur avant la CLI.')
    require('python3 scripts/test_recovery_drill_security.py' in text, 'Le recovery drill doit exécuter les tests du garde avant la CLI.')

    expected_steps = [
        'python3 scripts/validate_recovery_drill_security.py',
        f'uses: supabase/setup-cli@{SETUP_CLI_SHA}',
        'supabase start',
        'supabase db reset',
        'supabase test db',
        'supabase status -o env',
        'supabase stop --no-backup',
    ]
    positions = [text.find(marker) for marker in expected_steps]
    require(min(positions) >= 0, f'Étape recovery attendue absente: {dict(zip(expected_steps, positions))}')
    require(positions == sorted(positions), 'Ordre recovery attendu: garde, CLI, start, reset, pgTAP, Auth local, stop.')


def main() -> int:
    require(WORKFLOW.is_file(), f'Workflow absent: {WORKFLOW.relative_to(ROOT)}')
    validate_text(WORKFLOW.read_text(encoding='utf-8', errors='strict'))
    print(
        'OK recovery drill: actions et CLI immuables, credentials Git non persistés, '
        'aucun secret production et aucune opération Supabase distante.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
