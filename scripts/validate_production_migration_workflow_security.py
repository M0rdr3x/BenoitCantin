#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY_WORKFLOW = ROOT / '.github/workflows/sinjira-production-migration-history-guard-v25.yml'
VALIDATION_WORKFLOW = ROOT / '.github/workflows/validate-production-ledger.yml'

CHECKOUT_SHA = 'd23441a48e516b6c34aea4fa41551a30e30af803'
SETUP_PYTHON_SHA = 'ece7cb06caefa5fff74198d8649806c4678c61a1'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def active_text(text: str) -> str:
    return '\n'.join(
        line for line in text.splitlines()
        if not line.strip().startswith('#')
    )


def validate_action_integrity(text: str, label: str, *, require_full_history: bool) -> None:
    active = active_text(text)

    require('permissions:\n  contents: read' in text, f'{label}: permissions.contents doit rester read.')
    require(
        f'uses: actions/checkout@{CHECKOUT_SHA}' in text,
        f'{label}: actions/checkout doit être épinglé au SHA vérifié.',
    )
    require('persist-credentials: false' in text, f'{label}: les credentials Git ne doivent pas être persistés.')
    require(
        f'uses: actions/setup-python@{SETUP_PYTHON_SHA}' in text,
        f'{label}: actions/setup-python doit être épinglé au SHA vérifié.',
    )
    require("python-version: '3.12'" in text, f'{label}: Python doit rester figé à 3.12.')

    uses = [line.strip() for line in active.splitlines() if line.strip().startswith('uses: ')]
    require(uses, f'{label}: aucune action réutilisable détectée.')
    for line in uses:
        target = line.split('uses:', 1)[1].strip().split()[0]
        require(
            re.search(r'@[0-9a-f]{40}$', target) is not None,
            f'{label}: référence d’action non immuable: {target}',
        )

    forbidden = (
        'secrets.',
        'persist-credentials: true',
        'permissions:\n  contents: write',
        'supabase db push',
        'supabase migration repair',
        'supabase db reset',
        'supabase functions deploy',
    )
    found = [marker for marker in forbidden if marker in active]
    require(not found, f'{label}: primitive ou portée interdite détectée: {found}')

    if require_full_history:
        require('fetch-depth: 0' in text, 'garde historique: fetch-depth=0 obligatoire pour comparer l’historique Git.')


def validate_validation_workflow_contract(text: str) -> None:
    validate_action_integrity(text, 'validation ledger', require_full_history=False)
    for path in (
        "      - 'scripts/validate_production_migration_workflow_security.py'",
        "      - 'scripts/test_production_migration_workflow_security.py'",
    ):
        require(
            text.count(path) >= 2,
            f'validation ledger: le chemin doit déclencher PR et push main: {path.strip()}',
        )
    require(
        'python scripts/test_production_migration_workflow_security.py' in text,
        'validation ledger: les tests de mutation du garde doivent être exécutés.',
    )
    require(
        'python scripts/validate_production_migration_workflow_security.py' in text,
        'validation ledger: le validateur des actions immuables doit être exécuté.',
    )


def main() -> int:
    require(HISTORY_WORKFLOW.is_file(), f'Workflow absent: {HISTORY_WORKFLOW.relative_to(ROOT)}')
    require(VALIDATION_WORKFLOW.is_file(), f'Workflow absent: {VALIDATION_WORKFLOW.relative_to(ROOT)}')

    validate_action_integrity(
        HISTORY_WORKFLOW.read_text(encoding='utf-8', errors='strict'),
        'garde historique',
        require_full_history=True,
    )
    validate_validation_workflow_contract(
        VALIDATION_WORKFLOW.read_text(encoding='utf-8', errors='strict')
    )

    print(
        'OK workflows migrations production: checkout/setup-python immuables, '
        'credentials Git non persistés, permissions lecture seule et tests anti-régression actifs.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
