#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/sinjira-v25-production-deploy.yml'

EXPECTED_NAMES = [
    'sinjira_v25_0_security_risk_model_convergence',
    'sinjira_v25_0_personal_consciousness_vault',
    'sinjira_v25_0_conscience_vault_challenge_continuity',
    'sinjira_v25_0_device_key_privacy_and_trust_hardening',
    'sinjira_v25_conscience_vault_audit_session_index',
]


def require(text: str, markers: list[str], label: str) -> None:
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise AssertionError(f'{label}: marqueurs absents: {missing}')


def forbid(text: str, markers: list[str], label: str) -> None:
    found = [marker for marker in markers if marker in text]
    if found:
        raise AssertionError(f'{label}: marqueurs interdits: {found}')


def top_level_block(text: str, start: str, end: str) -> str:
    start_pos = text.find(start)
    if start_pos < 0:
        raise AssertionError(f'Bloc absent: {start.strip()}')
    end_pos = text.find(end, start_pos + len(start))
    if end_pos < 0:
        raise AssertionError(f'Fin de bloc absente: {end.strip()}')
    return text[start_pos:end_pos]


def active_text(text: str) -> str:
    return '\n'.join(
        raw for raw in text.splitlines()
        if not raw.strip().startswith('#')
    )


def trigger_keys(block: str) -> set[str]:
    keys = set()
    for line in block.splitlines()[1:]:
        match = re.match(r'^  ([A-Za-z0-9_-]+):(?:\s|$)', line)
        if match:
            keys.add(match.group(1))
    return keys


def main() -> int:
    if not WORKFLOW.exists():
        raise AssertionError(f'Workflow absent: {WORKFLOW.relative_to(ROOT)}')

    workflow = WORKFLOW.read_text('utf-8', errors='strict')
    triggers = top_level_block(workflow, 'on:\n', '\npermissions:')
    active = active_text(workflow)

    observed_triggers = trigger_keys(triggers)
    if observed_triggers != {'workflow_dispatch'}:
        raise AssertionError(
            'La vérification production V25 doit rester strictement manuelle: '
            f'triggers observés={sorted(observed_triggers)}'
        )

    require(workflow, [
        'name: SINJIRA V25 — Vérification production coffre',
        'Saisir exactement VERIFY-SINJIRA-V25',
        'test "$VERIFY_CONFIRMATION" = "VERIFY-SINJIRA-V25"',
        'environment: production',
        'SUPABASE_PROJECT_REF: gpvivleexywljowcqkru',
        'EXPECTED_REMOTE_BASELINE: "20260901002241"',
        'EXPECTED_REMOTE_BASELINE_NAME: sinjira_v24_5_54_fracture_contribution_atomic_finalize',
        'SUPABASE_MANAGEMENT_API: https://api.supabase.com/v1',
        'SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}',
        'ref: main',
        'persist-credentials: false',
        '/projects/$SUPABASE_PROJECT_REF/database/migrations',
        '--header "Authorization: Bearer $SUPABASE_ACCESS_TOKEN"',
        'after_names[:len(required)] != required',
        'supabase functions list --project-ref "$SUPABASE_PROJECT_REF"',
        "grep -Fq 'conscience-vault'",
        'Aucune migration, aucun secret et aucune Edge Function',
    ], 'contrat de vérification post-déploiement V25')

    for name in EXPECTED_NAMES:
        require(workflow, [f'"{name}"'], f'nom distant V25 {name}')

    forbid(active, [
        '--request POST',
        'supabase functions deploy',
        'supabase db push',
        'continue-on-error: true',
        'set -x',
    ], 'la vérification post-déploiement doit rester en lecture seule')

    if active.count('/projects/$SUPABASE_PROJECT_REF/database/migrations') != 1:
        raise AssertionError('Le workflow doit effectuer une seule lecture explicite de l’historique distant.')

    history = active.find('/projects/$SUPABASE_PROJECT_REF/database/migrations')
    functions = active.find('supabase functions list --project-ref "$SUPABASE_PROJECT_REF"')
    if min(history, functions) < 0 or not history < functions:
        raise AssertionError('Ordre attendu: historique de migrations, puis inventaire Edge en lecture seule.')

    print(
        'OK vérification V25: manuel uniquement, production en lecture seule, '
        'cinq migrations obligatoires présentes dans l’ordre et conscience-vault inventoriée.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
